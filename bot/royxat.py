"""Xalqaro ochiq fishing bazasini yuklab, data/tashqi_qora.txt ga yozadi.

    python -m bot.royxat

Qo'lda (yoki botni ishga tushirishdan oldin) ishga tushiriladi — o'zi avtomatik ishlamaydi.
Manbalar bepul va kalitsiz:
  - Phishing.Database «ACTIVE» domenlari (har kuni yangilanadi, ~400 ming)
  - URLhaus (abuse.ch) — hozir ishlayotgan zararli fayl tarqatuvchi manzillar
Oq ro'yxatdagi va tekin hosting domenlari (docs.google.com kabi) chiqarib tashlanadi — ular butunlay
bloklanmaydi, tekshiruvda alohida «hosting» belgisi oladi.
Bazada butun platformalar ham uchraydi (2026-10-10: github.com, bit.ly, dropbox.com, gitlab.com...) — shuning uchun
Tranco reytingidagi eng mashhur 20 ming domen ham chiqariladi. Tranco yuklanmasa, ro'yxat YANGILANMAYDI
(aks holda github.com havolasi 🔴 olardi).
"""
from __future__ import annotations

import datetime as dt
import io
import re
import sys
import urllib.request
import zipfile

from . import havola

MANBALAR = {
    "Phishing.Database ACTIVE":
        "https://raw.githubusercontent.com/Phishing-Database/Phishing.Database/master/phishing-domains-ACTIVE.txt",
    "URLhaus online": "https://urlhaus.abuse.ch/downloads/text_online/",
}
TRANCO = "https://tranco-list.eu/top-1m.csv.zip"
TRANCO_SONI = 20_000
_HOST = re.compile(r"^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}$")


def _olish(url: str) -> bytes:
    rq = urllib.request.Request(url, headers={"User-Agent": "shubhali-tekshiruvchi/1.0"})
    with urllib.request.urlopen(rq, timeout=120) as r:
        return r.read()


def _yukla(url: str) -> list[str]:
    return _olish(url).decode("utf-8", "replace").splitlines()


def mashhurlar() -> set[str]:
    """Tranco top-1m dan birinchi TRANCO_SONI domen («1,google.com» qatorlari)."""
    with zipfile.ZipFile(io.BytesIO(_olish(TRANCO))) as z:
        qatorlar = z.read(z.namelist()[0]).decode().splitlines()[:TRANCO_SONI]
    return {q.split(",", 1)[1].strip().lower() for q in qatorlar if "," in q}


def main() -> int:
    try:
        mashhur = mashhurlar()
    except Exception as e:  # noqa: BLE001
        print(f"Tranco ro'yxati yuklanmadi ({e}) — mashhur saytlarni ajratib bo'lmaydi, eski ro'yxat o'zgarmadi.",
              file=sys.stderr)
        return 1
    istisno = (set(havola.oq()) | havola.OCHIQ_HOSTING | havola.QISQARTIRUVCHI | havola.TELEGRAM | mashhur)
    domenlar: set[str] = set()
    hisobot = []
    for nom, url in MANBALAR.items():
        try:
            qatorlar = _yukla(url)
        except Exception as e:  # noqa: BLE001 — bitta manba ishlamasa, qolgani bilan davom etamiz
            hisobot.append(f"# {nom}: YUKLANMADI ({e})")
            continue
        oldin = len(domenlar)
        for q in qatorlar:
            q = q.strip().lower()
            if not q or q.startswith("#"):
                continue
            h = havola.host(q)
            if _HOST.match(h) and h not in istisno:
                domenlar.add(h)
        hisobot.append(f"# {nom}: {len(domenlar) - oldin} ta yangi domen — {url}")
    if not domenlar:
        print("Hech qanday manba yuklanmadi — eski ro'yxat o'zgarmadi.", file=sys.stderr)
        return 1
    fayl = havola.DATA / havola.TASHQI_FAYL
    sarlavha = [f"# Avtomatik yuklangan ({dt.date.today().isoformat()}), qo'lda tahrirlanmaydi: python -m bot.royxat",
                f"# Chiqarilgan: oq ro'yxat, tekin hosting, qisqartiruvchilar va Tranco top-{TRANCO_SONI} ({len(mashhur)} ta)"]
    fayl.write_text("\n".join(sarlavha + hisobot + sorted(domenlar)) + "\n", "utf-8")
    print("\n".join(hisobot) + f"\nJami: {len(domenlar)} domen → {fayl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
