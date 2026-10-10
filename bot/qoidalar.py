"""Matn qoidalari: firibgarlik belgilarini AI'siz topadi (3-pog'ona).

Matn avval bir xil ko'rinishga keltiriladi: kichik harf, kirill → lotin, turli apostroflar → «'».
Shunda bitta qoidalar to'plami lotin, kirill o'zbekcha va qisman ruscha xabarlarni ushlaydi.
Har belgi — (kod, og'irlik, odamga tushunarli sabab, nima qilish kerak).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Kirill (o'zbekcha + ruscha) → lotin. Ruscha so'zlar ham shu orqali lotinga o'tadi («код» → «kod»).
_KIR = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "'", "ы": "i", "ь": "",
    "э": "e", "ю": "yu", "я": "ya", "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h",
}
_APOSTROF = re.compile(r"[ʻʼ’‘`´]")


def normallash(matn: str) -> str:
    m = unicodedata.normalize("NFC", matn or "").lower()
    m = "".join(_KIR.get(h, h) for h in m)
    m = _APOSTROF.sub("'", m)
    return re.sub(r"\s+", " ", m)


@dataclass(frozen=True)
class Belgi:
    kod: str
    ogirlik: int      # 3 — kuchli, 2 — o'rta, 1 — kuchsiz
    sabab: str        # odamga: nima topildi
    maslahat: str     # odamga: nima qilish kerak


KOD_M = "Kodni hech kimga aytmang — bank va idoralar hech qachon SMS kod so'ramaydi. Shubha bo'lsa, bankingizga o'zingiz qo'ng'iroq qiling."
KARTA_M = "Karta raqami, muddati va kodni hech qayerga yozmang. Kiritib qo'ygan bo'lsangiz — darhol bankingizga qo'ng'iroq qilib kartani bloklang."
HAVOLA_M = "Havolani bosmang va unga kod kiritmang. Kiritgan bo'lsangiz: Telegram → Sozlamalar → Qurilmalar → «Boshqa seanslarni yakunlash»."
IDORA_M = "Markaziy bank, militsiya va boshqa idoralar Telegram yoki telefonda tergov qilmaydi va pul so'ramaydi. Javob bermang, 102 ga qo'ng'iroq qiling."
PUL_M = "Oldindan pul o'tkazmang. Yaqiningiz yoki rahbaringiz nomidan yozishsa — unga o'zingiz qo'ng'iroq qilib tekshiring."
ILOVA_M = "Hech qanday ilova o'rnatmang va ekraningizni begonaga ko'rsatmang."

# (kod, og'irlik, regex, sabab, maslahat). Regexlar normallashgan (lotin, kichik harf) matnga qo'llanadi.
_QOIDALAR: list[tuple[str, int, str, str, str]] = [
    ("KOD_SORASH", 3,
     r"(sms|tasdiqlash|maxfiy|kelgan|keladigan|yuborilgan|yuboriladigan|telegram)\W+(\w+\W+){0,2}kod\w*\W+(\w+\W+){0,4}"
     r"(ayt|yubor|yoz|kirit|ber|tashla|ko'rsat|o'qib|nazov|soobsh|skaj|prodikt|otprav|vved)"
     r"|kod\w*\W+(\w+\W+){0,3}(aytib yuboring|ayting|aytishingiz|yuboring|yozib yuboring|kiriting|bering|tashlang)"
     r"|kod\w* (iz|s) sms|nazovite kod|skajite kod|kod podtverjdeniya",
     "SMS yoki tasdiqlash kodini so'rashyapti — firibgarlarning eng asosiy usuli.", KOD_M),
    ("KARTA", 3,
     r"karta(ngiz)?\w* (raqam|ma'lumot|rekvizit)\w*\W+(\w+\W+){0,4}(kirit|yubor|yoz|ayt|tasdiql|ber)"
     r"|kartangizni (tasdiqlang|faollashtiring|ro'yxatdan o'tkazing|yangilang)"
     r"|(amal qilish muddat|srok deystviya)\w*\W+(\w+\W+){0,4}(ayt|yoz|yubor|kirit|nazov|skaj)"
     r"|\bcvv\b|\bcvc\b|nomer karti|dannie karti",
     "Karta ma'lumotini kiritish yoki aytishni so'rashyapti.", KARTA_M),
    ("ILOVA", 3,
     r"\bapk\b|ilova\w* (yuklab|o'rnat)|o'rnatib oling|anydesk|rustdesk|teamviewer|ekran\w* (ulash|namoyish)"
     r"|ustanovite prilojeni|skachayte prilojeni",
     "Begona ilova o'rnatishni yoki ekranni ko'rsatishni so'rashyapti.", ILOVA_M),
    ("XAVFSIZ_HISOB", 3,
     r"xavfsiz (hisob|schyot|karta)|bezopasn\w* schet|nomingizga (kredit|qarz)|kredit (rasmiylashtir|oling|olib)"
     r"|qarshi kredit|vstrechn\w* kredit|kredit (oformit|oformlen)",
     "Pulni «xavfsiz hisob»ga o'tkazish yoki nomingizga kredit olishni so'rashyapti — bu firibgarlik sxemasi.", IDORA_M),
    ("RASMIY_NIQOB", 2,
     r"markaziy bank|moliyaviy nazorat|tergov|jinoyat ishi|jinoiy javobgarlik|korrupsiyaga qarshi|prokuratura"
     r"|sud qarori|sud chaqiruv|iib\w*|militsiya|politsiya|xavfsizlik xizmati|sluj\w* bezopasnost|tsentrobank|tsentraln\w* bank"
     r"|sledstv|sledovatel|ugolovn|\bmvd\b|\biiv\b",
     "Idora (Markaziy bank, militsiya, sud) nomidan gapirishyapti — firibgarlar ko'pincha shunday qo'rqitadi.", IDORA_M),
    ("YUTUQ", 2,
     r"yutib ol|yutdingiz|yutuq|g'olib bo'ldingiz|sovrin|sovg'a|mukofot|meros|pul ajratildi|fond tomonidan"
     r"|har bir (bolali )?oila\w* .{0,30}(to'lov|pul|so'm)|kompensatsiya|bepul premium|premium sovg'a|telegram premium"
     r"|vyigral|vash priz|podarok",
     "Yutuq, sovg'a yoki tekin pul va'da qilinyapti — firibgarlarning eng ko'p ishlatadigan qarmog'i.", HAVOLA_M),
    ("OVOZ", 2,
     r"ovoz ber|golosu|progolosu|tanlov\w* (qatnash|ishtirok)|konkurs",
     "Tanlovda ovoz berishni so'rashyapti — bunday havolalar Telegram akkauntni o'g'irlaydi.", HAVOLA_M),
    ("OLDINDAN_TOLOV", 2,
     r"yetkazib berish\w* (uchun|xizmati)\w* .{0,30}(to'la|pul)|oldindan to'la|pulning yarmini|komissiya\w* to'la"
     r"|(pul|summa)ni? qabul qilib oling|pulni qabul qilish uchun|predoplat",
     "Oldindan pul to'lash yoki «pulni qabul qilish» uchun ma'lumot kiritish so'ralyapti.", PUL_M),
    ("IDENTIFIKATSIYA", 2,
     r"identifikatsiya\w* (dan )?o'ting|shaxsingizni tasdiqlang|akkaunt\w* (tasdiqlang|bloklanadi)|kartangiz bloklan"
     r"|karta\w* bloklandi|vasha karta zablokirovan",
     "«Tasdiqlang», «bloklanadi» deb qo'rqitib, ma'lumot olishga urinishyapti.", KARTA_M),
    ("INVESTITSIYA", 2,
     r"pul\w* (ikki|2) baravar|kunlik \d+ ?%|kafolatlangan daromad|oson pul|investitsiya\w* .{0,30}foyda|kripto\w* .{0,20}daromad",
     "Tez va kafolatlangan daromad va'da qilinyapti — bu odatda piramida yoki aldov.", PUL_M),
    ("PUL_SORASH", 2,
     r"(pul|summa|mablag')\w* (o'tkaz|tashla|yubor)\w*\W+(\w+\W+){0,4}(zudlik|tez|darhol|hoziroq|srochno|shoshilinch)"
     r"|(zudlik|tez|darhol|hoziroq|srochno|shoshilinch)\w*\W+(\w+\W+){0,4}(pul|summa|mablag')\w* (o'tkaz|tashla|yubor)"
     r"|(zudlik|tez|darhol|hoziroq|srochno|shoshilinch)\w*\W+(\w+\W+){0,6}\d+[\s.,]*(mln|million|ming|so'm|\$|dollar)\w*\W+(\w+\W+){0,3}(o'tkaz|tashla)"
     r"|(o'tkazib|tashlab) (tur|yubor)\w*\W+(\w+\W+){0,4}qaytaraman|perevedi\w*\W+(\w+\W+){0,4}verny",
     "Shoshiltirib pul o'tkazishni so'rashyapti.", PUL_M),
    ("SIR_SAQLASH", 2,
     r"bu (haqda|to'g'rida|suhbat\w*)\W+(\w+\W+){0,2}(hech kimga|yaqinlaringizga|oilangizga|bankka)"
     r"|(yaqinlaringizga|oilangizga|bank xodim\w*ga|bankka) (aytmang|xabar bermang|bildirmang)"
     r"|tergov sir\w*|ob etom nikomu|hech kimga (aytmang|bildirmang|gapirmang)|nikomu ne (govorite|soobshayte|rasskazivayte)",
     "Hech kimga aytmaslikni so'rashyapti — firibgarlar yaqinlaringiz ogohlantirib qo'yishidan qo'rqadi.", IDORA_M),
    ("YANGI_RAQAM", 2,
     r"yangi raqam\w*dan|eski raqam\w* ishla|telefonim (buzil|yo'qol|o'g'irla)|gaplasha olmayman|qo'ng'iroq qila olmayman"
     r"|majlisdaman|ne mogu govorit|eto moy novi\w* nomer|novi\w* nomer",
     "Tanishingiz nomidan «yangi raqamdan yozyapman, gaplasha olmayman» deyishyapti — akkaunt o'g'irlanganda shunday yozishadi.", PUL_M),
    ("SHOSHILTIRISH", 1,
     r"zudlik bilan|darhol|hoziroq|shoshiling|\d+ (soat|daqiqa) ichida|bugun oxirgi|aks holda|srochno|nemedlenno",
     "Shoshiltirishyapti — o'ylab ko'rishga vaqt bermaslik firibgarlarga xos.", PUL_M),
    ("HAVOLA_BOS", 1,
     r"havola(ga| orqali| ustiga)|link(ka|ni bos| orqali)|ssilk|bosing va|perediite",
     "Havolaga kirishga undashyapti.", HAVOLA_M),
]
_QOIDALAR_RE = [(k, o, re.compile(r, re.I), s, m) for k, o, r, s, m in _QOIDALAR]

# Bank va xizmatlarning o'zi yuboradigan ogohlantirish: «kodni hech kimga bermang».
# Bunday matnda «kod» so'zi bor, lekin u kodni SO'RAMAYDI — KOD_SORASH bekor qilinadi.
_OGOHLANTIRISH = re.compile(
    r"(kod|parol|pin|cvv|karta ma'lumot)\w*\W+(\w+\W+){0,4}"
    r"(bermang|aytmang|ko'rsatmang|yubormang|so'ramaydi|ne soobshayte|ne peredavayte|ne govorite|ne zaprashivaet|ne prosit)"
    r"|(ne soobshayte|ne peredavayte|ne govorite|ne nazivayte)\W+(\w+\W+){0,2}(kod|parol|pin)", re.I)
# Firibgarlik haqidagi ogohlantirish yoki yangilik: idora nomi tilga olinadi, lekin u niqob emas.
_YANGILIK = re.compile(r"(firibgar|moshenni)", re.I)
_YANGILIK2 = re.compile(r"ogohlantir|ehtiyot bo'l|aldanmang|hushyor bo'l|preduprejda|bud'te ostorojn|ostorojno", re.I)


# Pul, karta yoki daromad haqida gap — kalit so'z topilmasa ham AI'ga ko'rsatishga arziydi
# (yangi so'zlar bilan yozilgan «qarindosh muammoda», «ish taklifi», «treyding» xabarlari).
_PUL_MAVZU = re.compile(
    r"\bpul|karta|o'tkaz|to'lov|\bso'm|\bmln\b|million|dollar|\$|kredit|qarz|daromad|maosh|oylik|ish haqi|treyding|kripto"
    r"|investitsiya|bonus|depozit|hisob raqam|dengi|perevod|kart[uy]|zarplat|zarabot|\d+ ?ming\b", re.I)


def pul_mavzusi(matn: str) -> bool:
    return bool(_PUL_MAVZU.search(normallash(matn)))


def belgilar(matn: str) -> list[Belgi]:
    """Matndagi firibgarlik belgilari (kuchlidan kuchsizga)."""
    n = normallash(matn)
    ogoh = bool(_OGOHLANTIRISH.search(n))
    topildi = []
    for kod, ogirlik, rx, sabab, maslahat in _QOIDALAR_RE:
        if not rx.search(n):
            continue
        # Ogohlantiruvchi matn («kodni hech kimga bermang») — kod so'rash ham, sir saqlash talabi ham emas.
        if ogoh and kod in ("KOD_SORASH", "PUL_SORASH", "KARTA", "SIR_SAQLASH"):
            if not _ogohdan_tashqari(n, rx):
                continue
        if kod == "RASMIY_NIQOB" and _YANGILIK.search(n) and _YANGILIK2.search(n):
            continue
        topildi.append(Belgi(kod, ogirlik, sabab, maslahat))
    return sorted(topildi, key=lambda b: -b.ogirlik)


def _ogohdan_tashqari(n: str, rx: re.Pattern) -> bool:
    """Ogohlantirish iboralarini olib tashlagandan keyin ham belgi qoladimi."""
    toza = _OGOHLANTIRISH.sub(" ", n)
    toza = re.sub(r"(sms\W+)?kod\w*\W+(\w+\W+){0,3}(hech kimga|nikomu)", " ", toza)
    return bool(rx.search(toza))
