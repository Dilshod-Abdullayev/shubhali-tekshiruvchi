"""Havola va fayl tekshiruvi: 1-pog'ona (fayl kengaytmasi) va 2-pog'ona (qora/oq ro'yxat, soxta domen)."""
from __future__ import annotations

import ipaddress
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

DATA = Path(__file__).resolve().parent.parent / "data"

# Telefonga yoki kompyuterga o'rnatiladigan dastur — ochish bilan zarar beradi.
XAVFLI_KENGAYTMA = {"apk", "apks", "xapk", "apkm", "exe", "scr", "bat", "cmd", "msi", "jar", "vbs", "js", "ps1", "pif",
                    "com", "lnk", "hta", "wsf"}
# Matn ichida fayl nomi sifatida tilga olinsa ham ushlanadi (masalan forward qilingan xabarda «Rasmlar.apk»).
# «.com» bu yerda yo'q — u domen bilan chalkashadi.
_MATNDAGI_FAYL = re.compile(r"[^\s/\\]{1,120}\.(apk|apks|xapk|exe|scr|bat|msi|jar|vbs|ps1)\b", re.I)
XAVFLI_MIME = {"application/vnd.android.package-archive", "application/x-msdownload", "application/x-ms-installer",
               "application/x-msdos-program", "application/java-archive"}

# Har kim tekin sahifa ochadigan xizmatlar: domen o'zi rasmiy, lekin sahifa egasi noma'lum.
# Firibgarlar karta so'rovchi formani Google Forms/Sites yoki tekin hostingda ochadi (Phishing.Database da
# docs.google.com va sites.google.com bor) — shuning uchun bular hech qachon «rasmiy sayt» deb o'tmaydi.
OCHIQ_HOSTING = {"sites.google.com", "docs.google.com", "forms.gle", "drive.google.com", "storage.googleapis.com",
                 "github.io", "web.app", "firebaseapp.com", "pages.dev", "vercel.app", "netlify.app", "weebly.com",
                 "weeblysite.com", "wixsite.com", "000webhostapp.com", "blogspot.com", "appspot.com", "duckdns.org",
                 "glitch.me", "tilda.ws", "taplink.cc", "linktr.ee", "notion.site", "telegra.ph"}
TASHQI_FAYL = "tashqi_qora.txt"

QISQARTIRUVCHI = {"bit.ly", "tinyurl.com", "cutt.ly", "clck.ru", "goo.su", "t.ly", "is.gd", "rb.gy", "shorturl.at",
                  "tiny.cc", "u.to", "vk.cc", "ow.ly", "s.id", "rebrand.ly", "goo.gl", "qptr.ru"}
TELEGRAM = {"t.me", "telegram.me", "telegram.dog"}
# Arzon, firibgarlar ko'p ishlatadigan zonalar (Spamhaus va boshqa reytinglarda doim yuqorida).
SHUBHALI_ZONA = {"top", "xyz", "click", "icu", "live", "shop", "online", "site", "buzz", "cfd", "sbs", "rest", "monster",
                 "cyou", "bond", "lol", "quest", "tk", "ml", "ga", "cf", "gq", "work", "fun", "pw", "zip", "mov", "info"}

_TLD = r"(?:uz|com|net|org|ru|info|io|me|app|top|xyz|click|icu|live|shop|online|site|buzz|cfd|sbs|rest|link|ly|gl|at|cc|to|id|tk|ml|ga|cf|gq|pw|work|fun|store|pro|biz|dog|su|kz|tj|kg)"
_URL = re.compile(
    r"(?:https?://|www\.)[^\s<>\"'«»()]+"
    r"|(?<![\w@.-])(?:[a-z0-9Ѐ-ӿ](?:[a-z0-9Ѐ-ӿ-]{0,62})\.)+" + _TLD + r"(?![\w-])(?:/[^\s<>\"'«»()]*)?",
    re.I)
_TG_AKKAUNT = re.compile(r"(?<![\w.])@([a-z][a-z0-9_]{3,31})\b", re.I)


@lru_cache(maxsize=None)
def _royxat(nom: str) -> frozenset[str]:
    try:
        qatorlar = (DATA / nom).read_text("utf-8").splitlines()
    except OSError:
        return frozenset()
    return frozenset(q.strip().lower() for q in qatorlar if q.strip() and not q.lstrip().startswith("#"))


def qora() -> frozenset[str]:
    return _royxat("blacklist.txt")


def tashqi_qora() -> frozenset[str]:
    """Ochiq xalqaro fishing bazasi (python -m bot.royxat yuklaydi). Fayl bo'lmasa — bo'sh."""
    return _royxat(TASHQI_FAYL)


def oq() -> frozenset[str]:
    return _royxat("whitelist.txt")


def _ichida(host: str, toplam: frozenset[str]) -> str:
    """host yoki uning ota domeni to'plamda bo'lsa — o'sha yozuv."""
    qism = host.split(".")
    for i in range(len(qism) - 1):
        d = ".".join(qism[i:])
        if d in toplam:
            return d
    return ""


# --------------------------------------------------------------- fayl ----

def fayl_xavfi(nom: str | None, mime: str | None = None) -> str:
    """Xavfli fayl bo'lsa sabab matni, aks holda ''."""
    if mime and mime.lower() in XAVFLI_MIME:
        return "Bu fayl — telefonga o'rnatiladigan dastur (ilova)."
    if not nom:
        return ""
    n = unicodedata.normalize("NFKC", nom).strip().rstrip(". ").lower()
    kengaytma = n.rsplit(".", 1)[-1] if "." in n else ""
    if kengaytma not in XAVFLI_KENGAYTMA:
        return ""
    if re.search(r"\.(pdf|jpe?g|png|mp4|docx?|xlsx?|foto|video|mp3)\.\w+$", n) or "mp4" in n or "foto" in n or "video" in n:
        return f"«{nom}» — rasm yoki hujjatga o'xshatilgan, aslida telefonga o'rnatiladigan dastur (.{kengaytma})."
    return f"«{nom}» — telefonga o'rnatiladigan dastur (.{kengaytma}), rasm yoki hujjat emas."


ARXIV = {"zip", "rar", "7z", "tar", "gz"}


def arxiv(nom: str | None) -> str:
    """Arxiv fayl: o'zi dastur emas, lekin ichida .apk yuborish keng tarqalgan usul."""
    n = (nom or "").strip().rstrip(". ").lower()
    if "." in n and n.rsplit(".", 1)[-1] in ARXIV:
        return f"«{nom}» — arxiv fayl: ichida nima borligi ko'rinmaydi, firibgarlar .apk dasturni shunday yashiradi."
    return ""


def matndagi_fayllar(matn: str) -> list[str]:
    return [m.group(0) for m in _MATNDAGI_FAYL.finditer(matn or "")]


# ------------------------------------------------------------- havola ----

def havolalar(matn: str) -> list[str]:
    topildi = []
    for m in _URL.finditer(matn or ""):
        u = m.group(0).rstrip(".,;:!?)»")
        # Fayl nomi («Rasmlar.apk») havola emas
        if _MATNDAGI_FAYL.fullmatch(u):
            continue
        topildi.append(u)
    return topildi


def host(url: str) -> str:
    u = url if re.match(r"(?i)^https?://", url) else "http://" + url
    try:
        h = (urlsplit(u).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""
    return h[4:] if h.startswith("www.") else h


# Yangilik saytlari va umumiy so'zlar soxta-brend tekshiruviga kirmaydi (gazeta.ru — gazeta.uz soxtasi emas).
_BREND_EMAS = {"google", "youtube", "youtu", "telegram", "daryo", "gazeta", "spot", "apple", "zoom", "wikipedia"}
# Oddiy so'z ham bo'lgan brendlar: «apelsin-kafe.uz», «oson-taksi.uz» — mahalliy biznes. Bular chiziqcha bilan
# faqat .uz dan tashqari zonada soxta sanaladi (click-bonus.com, uzum-sovga.top).
_UMUMIY_SOZ = {"click", "oson", "apelsin", "uzum", "korzinka", "hayot", "davr", "turon", "trast", "garant", "poytaxt"}


def _brendlar() -> dict[str, str]:
    """Oq ro'yxatdagi nom → domen: «anorbank» → anorbank.uz. Juda umumiy qisqalar chiqarib tashlanadi."""
    b = {}
    for d in oq():
        nom = d.split(".")[0]
        if len(nom) >= 4 and nom not in _BREND_EMAS:
            b[nom] = d
    b.update({"mygov": "gov.uz", "humo": "humocard.uz", "cbu": "cbu.uz", "markaziybank": "cbu.uz"})
    return b


def _soxta_brend(h: str) -> str:
    """Brend nomi soxta manzilga yopishtirilganmi — topilsa asl domen, aks holda ''.

    Faqat brend ALOHIDA qism bo'lsa ushlanadi: payme-uz.top, click-bonus.com, kapitalbank.uz.secure-login.ru,
    paymeuz.com. So'z ichidagi tasodifiy moslik (clickup.com, paymentwall.com, apelsinka.ru) — yo'q.
    Brend butun domen nomi bo'lib, boshqa zonada turgani (click.ru) ham soxta emas — bu boshqa davlatdagi
    o'z kompaniyasi bo'lishi mumkin; faqat arzon firibgar zonasida (payme.top) soxta.
    """
    yorliq = h.split(".")
    zona, asosiy = yorliq[-1], (yorliq[-2] if len(yorliq) >= 2 else "")
    for nom, asl in _brendlar().items():
        # 1) subdomen sifatida: kapitalbank.uz.secure-login.ru, payme.login-verify.com
        if nom in yorliq[:-2]:
            return asl
        bolak = asosiy.split("-")
        # 2) chiziqcha bilan boshqa so'zga ulangan: click-bonus.com, mygov-kompensatsiya.com, cbu-uz.xyz
        if len(bolak) > 1 and nom in bolak and (zona != "uz" or nom not in _UMUMIY_SOZ):
            return asl
        # 3) «uz» bilan qo'shib yozilgan: paymeuz.com, uzpayme.net, clickuz.top
        if asosiy in (nom + "uz", "uz" + nom):
            return asl
        # 4) brend o'zi, lekin arzon firibgar zonasida: payme.top, uzum.xyz
        if asosiy == nom and zona in SHUBHALI_ZONA:
            return asl
    return ""


def _aralash_yozuv(h: str) -> bool:
    """Lotin va kirill harflari bitta domenda — klassik soxta domen (раyme.uz)."""
    lotin = bool(re.search(r"[a-z]", h))
    boshqa = any(ord(c) > 127 for c in h)
    return (lotin and boshqa) or "xn--" in h


def havola_bahosi(url: str) -> tuple[str, int, str]:
    """(holat, og'irlik, sabab). holat: qora | soxta | hosting | oq | qisqa | telegram | shubhali_zona | ip | nomalum."""
    h = host(url)
    if not h:
        return "nomalum", 1, f"«{url[:60]}» havolasini o'qib bo'lmadi."
    if d := _ichida(h, qora()):
        return "qora", 4, f"«{h}» — firibgarlikda ishlatilgan sayt (qora ro'yxatda)."
    if (d := _ichida(h, tashqi_qora())) and d not in OCHIQ_HOSTING | QISQARTIRUVCHI | TELEGRAM and d not in oq():
        return "qora", 4, f"«{h}» — xalqaro fishing bazasida firibgar sayt sifatida qayd etilgan."
    if d := _ichida(h, frozenset(OCHIQ_HOSTING)):
        return "hosting", 2, (f"«{h}» — har kim tekin sahifa ochadigan xizmat ({d}). Bank yoki davlat idorasi "
                              "karta va kodni bunday sahifada so'ramaydi.")
    if d := _ichida(h, oq()):
        return "oq", 0, f"«{d}» — rasmiy sayt."
    try:
        ipaddress.ip_address(h)
        return "ip", 3, "Havola sayt nomi o'rniga raqamlardan (IP manzil) iborat — rasmiy tashkilotlar bunday qilmaydi."
    except ValueError:
        pass
    if _aralash_yozuv(h):
        return "soxta", 4, f"«{h}» manzilida boshqa alifbo harflari yashiringan — rasmiy saytga o'xshatilgan soxta manzil."
    if asl := _soxta_brend(h):
        return "soxta", 4, f"«{h}» — {asl} ga o'xshatilgan, lekin u emas. Bu soxta sayt."
    if re.search(r"\.uz[.-]", h):
        return "soxta", 4, f"«{h}» — «.uz» sayti kabi ko'rinadi, aslida boshqa joyga olib boradi."
    if h in QISQARTIRUVCHI:
        return "qisqa", 2, "Havola qisqartirilgan — qayerga olib borishi yashirilgan."
    if h in TELEGRAM or h.endswith(".t.me"):
        return "telegram", 1, "Telegram kanal yoki botga havola — kimniki ekani noma'lum."
    if h.rsplit(".", 1)[-1] in SHUBHALI_ZONA:
        return "shubhali_zona", 2, f"«{h}» — firibgarlar ko'p ishlatadigan arzon domen zonasida."
    return "nomalum", 1, f"«{h}» — notanish sayt."


def tg_akkauntlar(matn: str) -> list[str]:
    return ["@" + m.group(1).lower() for m in _TG_AKKAUNT.finditer(matn or "")]


def akkaunt_bahosi(nom: str) -> tuple[str, int, str]:
    if nom.lower() in qora():
        return "qora", 4, f"{nom} — firibgarlikda ishlatilgan akkaunt (qora ro'yxatda)."
    return "nomalum", 0, ""
