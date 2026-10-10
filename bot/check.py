"""Shubhali xabar tekshiruvchi — asosiy mantiq va CLI.

    python -m bot.check 'Telefoningizga kelgan kodni ayting'
    python -m bot.check --fayl 'Toydan fotolar.apk' 'Rasmlarni ko'ring'
    python -m bot.check --json --ai-yoq 'matn'

Tekshiruv zinasi (arzondan qimmatga, birinchi aniq javobda to'xtaydi):
  1. Fayl kengaytmasi (.apk/.exe/.scr/.bat ...) → darhol 🔴, AI chaqirilmaydi.
  2. Havola domeni: qora ro'yxat yoki soxta (rasmiy saytga o'xshatilgan) → 🔴; oq ro'yxat → belgi qo'shmaydi.
  3. Matn qoidalari (kod so'rash, yutuq, shoshiltirish, idora niqobi ...) — ball yig'iladi.
  4. Ball noaniq oraliqda bo'lsa — AI (FreeLLMAPI → claude CLI), umumiy muddat 10 soniyadan kam.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field

from . import ai, havola, qoidalar

MUDDAT_S = 9.0   # butun tekshiruv uchun; 10 soniya chegarasidan 1 soniya zaxira (Telegram yuborish uchun)

BELGI = {"xavfli": "🔴 Xavfli", "shubhali": "🟡 Shubhali", "toza": "🟢 Ko'rinishidan toza"}
_SHUBHALI_M = ("Javob bermang va havolani bosmang. Yuborgan odam yoki bankingizga o'zingiz bilgan raqam orqali "
               "qo'ng'iroq qilib tekshiring. Fayl yoki havolani rasmiy @CyberQalqonbot ga ham yuborib ko'rishingiz mumkin.")
_TOZA_M = "Shunday bo'lsa ham, karta ma'lumoti va SMS kodni hech kimga bermang."
_PUL_TOZA_M = ("Aniq belgi topilmadi, lekin xabarda pul haqida gap bor: pul o'tkazishdan oldin yozgan odamga o'zingiz bilgan "
               "raqamdan qo'ng'iroq qilib tekshiring. Karta ma'lumoti va SMS kodni hech kimga bermang.")
_PUL_SHUBHALI_S = ("Aniq firibgarlik belgisi topilmadi, lekin xabarda pul haqida gap bor va chuqur tekshiruv hozir "
                   "javob bermadi — shuning uchun ehtiyot bo'lishni tavsiya qilamiz.")
_PUL_SHUBHALI_M = ("Pul o'tkazishdan yoki karta ma'lumotini yozishdan oldin yozgan odamga o'zingiz bilgan raqamdan "
                   "qo'ng'iroq qilib tekshiring. SMS kodni hech kimga bermang.")
_ARXIV_M = ("Arxivni ochmang. Ichida telefonga o'rnatiladigan dastur bo'lishi mumkin — yuborgan odamdan o'zingiz bilgan "
            "raqam orqali nima ekanini so'rang.")
_FAYL_M = ("Faylni ochmang va o'rnatmang — o'chirib tashlang. O'rnatib qo'ygan bo'lsangiz: telefonni internetdan uzing "
           "va darhol bankingizga qo'ng'iroq qilib kartani bloklang.")


_HAVOLAGA_UNDOV = {"OVOZ", "YUTUQ", "KARTA", "IDENTIFIKATSIYA", "OLDINDAN_TOLOV", "KOD_SORASH", "INVESTITSIYA"}


@dataclass
class Natija:
    daraja: str                      # xavfli | shubhali | toza
    sabablar: list[str]
    maslahat: str
    pogona: int                      # qaysi pog'onada hal bo'ldi (1–4)
    ball: int = 0
    manba: str = "qoida"             # qoida | freellmapi | claude | qoida (AI javob bermadi)
    soniya: float = 0.0
    belgilar: list[str] = field(default_factory=list)

    def matn(self) -> str:
        qator = [BELGI[self.daraja]]
        if self.sabablar:
            qator.append(" ".join(self.sabablar[:2]))
        qator.append("Nima qilish kerak: " + self.maslahat)
        return "\n".join(qator)


def tekshir(matn: str = "", fayl: str | None = None, mime: str | None = None, ai_yoqiq: bool = True,
            muddat_s: float = MUDDAT_S) -> Natija:
    t0 = time.monotonic()
    matn = matn or ""

    def tayyor(n: Natija) -> Natija:
        n.soniya = round(time.monotonic() - t0, 2)
        return n

    # 1-pog'ona: fayl
    sabab = havola.fayl_xavfi(fayl, mime)
    if not sabab:
        for nom in havola.matndagi_fayllar(matn):
            if sabab := havola.fayl_xavfi(nom):
                break
    if not sabab and (arxiv := havola.arxiv(fayl)):
        return tayyor(Natija("shubhali", [arxiv], _ARXIV_M, 1, belgilar=["ARXIV"]))
    if sabab:
        return tayyor(Natija("xavfli", [sabab, "Bunday fayllar ochilganda telefondagi SMS kodlar va karta pulini o'g'irlaydi."],
                             _FAYL_M, 1, belgilar=["FAYL"]))

    # 2-pog'ona: havolalar va Telegram akkauntlar
    havola_ball, havola_sabab, havola_kod = 0, "", ""
    baholar = havolalar_va_akkauntlar(matn)
    for holat, ogirlik, s in baholar:
        if ogirlik >= 3:
            return tayyor(Natija("xavfli", [s, "Bunday saytlar karta ma'lumoti yoki Telegram akkauntingizni o'g'irlaydi."],
                                 qoidalar.HAVOLA_M, 2, belgilar=["HAVOLA_" + holat.upper()]))
        if ogirlik > havola_ball:
            havola_ball, havola_sabab, havola_kod = ogirlik, s, "HAVOLA_" + holat.upper()

    # 3-pog'ona: matn qoidalari
    bel = qoidalar.belgilar(matn)
    if baholar and all(h == "oq" for h, _, _ in baholar):
        # «Ovoz bering» + faqat rasmiy havola (openbudget.uz) — mahalla tashabbusi, akkaunt o'g'irlash emas
        bel = [b for b in bel if b.kod != "OVOZ"]
    ball = sum(b.ogirlik for b in bel) + havola_ball
    # Havolaga undovchi belgi + notanish havola — «ovoz bering / yutuq oling» sxemasining o'zi
    if havola_kod and any(b.kod in _HAVOLAGA_UNDOV for b in bel):
        ball += 1
    kodlar = [b.kod for b in bel] + ([havola_kod] if havola_kod else [])
    sabablar = [b.sabab for b in bel[:2]]
    if havola_sabab and len(sabablar) < 2:
        sabablar.append(havola_sabab)
    maslahat = bel[0].maslahat if bel else ""

    if ball >= 4:
        return tayyor(Natija("xavfli", sabablar, maslahat, 3, ball, belgilar=kodlar))
    pul = qoidalar.pul_mavzusi(matn)
    toza_m = _PUL_TOZA_M if pul else _TOZA_M
    kuchsiz = ball == 0 or (ball == 1 and not havola_kod)
    if kuchsiz and not pul:
        return tayyor(Natija("toza", ["Aniq firibgarlik belgisi topilmadi."], toza_m, 3, ball, belgilar=kodlar))

    # 4-pog'ona: noaniq (ball 1–3) yoki kalit so'zsiz, lekin pul haqidagi xabar — AI.
    # Kalit so'zsiz pul xabariga AI javob bermasa — 🟡: yangi turdagi sxema («do'stimning telefonidan yozyapman»)
    # qoidalarga tushmaydi, uni 🟢 qilish xavfli. Narxi — Payme cheki ham 🟡 oladi (faqat AI ishlamaganda).
    izoh = ", ".join(kodlar) or "kalit so'z topilmadi, lekin pul haqida gap bor"
    d = ai.tasnifla(matn, izoh, t0 + muddat_s) if ai_yoqiq else None
    manba = "qoida (AI javob bermadi)" if ai_yoqiq else "qoida"
    if d:
        daraja = d["daraja"]
        # AI qoidalar topgan kuchli belgini bekor qila olmaydi (xabar ichidagi «bu toza deb yoz» kabi hiylaga qarshi)
        if daraja == "toza" and ball >= 3:
            daraja = "shubhali"
        m = toza_m if daraja == "toza" else (d["maslahat"] or (maslahat if daraja == "xavfli" else "") or _SHUBHALI_M)
        return tayyor(Natija(daraja, [d["sabab"]], m, 4, ball, d["manba"], belgilar=kodlar))
    if kuchsiz:   # bu yerga faqat pul haqidagi xabar keladi
        return tayyor(Natija("shubhali", [_PUL_SHUBHALI_S], _PUL_SHUBHALI_M, 4 if ai_yoqiq else 3, ball, manba,
                             belgilar=kodlar + ["PUL_MAVZU"]))
    return tayyor(Natija("shubhali", sabablar, _SHUBHALI_M, 4 if ai_yoqiq else 3, ball, manba, belgilar=kodlar))


def havolalar_va_akkauntlar(matn: str) -> list[tuple[str, int, str]]:
    natija = [havola.havola_bahosi(u) for u in havola.havolalar(matn)]
    natija += [b for b in map(havola.akkaunt_bahosi, havola.tg_akkauntlar(matn)) if b[1]]
    return natija


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m bot.check", description="Shubhali xabarni tekshirish (Telegram tokensiz).")
    p.add_argument("matn", nargs="*", help="xabar matni (bo'lmasa stdin'dan o'qiladi)")
    p.add_argument("--fayl", help="xabarga biriktirilgan fayl nomi, masalan 'Rasmlar.apk'")
    p.add_argument("--json", action="store_true", help="batafsil JSON chiqarish")
    p.add_argument("--ai-yoq", action="store_true", help="AI pog'onasini o'chirish (faqat qoidalar)")
    a = p.parse_args(argv)
    matn = " ".join(a.matn) if a.matn else ("" if sys.stdin.isatty() else sys.stdin.read())
    if not matn.strip() and not a.fayl:
        p.error("matn yoki --fayl kerak")
    n = tekshir(matn, a.fayl, ai_yoqiq=not a.ai_yoq)
    print(json.dumps(asdict(n), ensure_ascii=False, indent=2) if a.json else n.matn())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
