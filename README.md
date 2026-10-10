# Shubhali tekshiruvchi

Sizga g'alati xabar keldimi? «Yutdingiz», «kartangizni tasdiqlang», «kelgan kodni ayting» yoki «Rasmlarni ko'ring.apk»?
Shu xabarni botga yuboring — 10 soniyadan kam vaqtda javob keladi:

- 🔴 **Xavfli** — firibgarlik belgisi aniq. Ochmang, javob bermang.
- 🟡 **Shubhali** — ehtiyot bo'ling, o'zingiz bilgan raqamga qo'ng'iroq qilib tekshiring.
- 🟢 **Ko'rinishidan toza** — belgi topilmadi. Baribir karta ma'lumoti va SMS kodni hech kimga bermang.

Bot hech qachon «100% xavfsiz» demaydi. Xabaringiz hech qayerga saqlanmaydi.

<!-- SKRINSHOT: bot token bilan ishga tushgach, javob rasmini docs/skrinshot.png ga qo'yib, shu yerga ulang. -->

## 3 qadamda ishlatish

1. Telegram'da botni oching va **Start** tugmasini bosing. *(Bot nomi keyin qo'yiladi — hozir bot hali Telegram'da ochilmagan.)*
2. Shubhali xabarni bosib turing → **Forward (Uzatish)** → botni tanlang. Fayl yoki havolani ham shunday yuborasiz.
3. Javobni o'qing: rangi va «Nima qilish kerak» qatoriga qarang.

**Ota-onangizga:** botni ularning telefonida bir marta ochib qo'ying va «g'alati xabar kelsa, shu yerga uzating» deb ko'rsating.

**Hozircha qila olmaydi:** rasm (skrinshot), ovozli xabar va videoni o'qiy olmaydi — bot buni o'zi aytadi. Bunday holatda xabardagi yozuvni nusxalab yuboring.

---

## Botni ishga tushiruvchi uchun

Kompyuterda Python 3.10+ bo'lishi kerak.

**Tokensiz sinab ko'rish** (hech narsa o'rnatish shart emas):

```bash
git clone https://github.com/Dilshod-Abdullayev/shubhali-tekshiruvchi.git && cd shubhali-tekshiruvchi
python3 -m bot.check "Telefoningizga kelgan SMS kodni ayting, yutuqni olasiz"
python3 -m bot.check --fayl "Toy rasmlari.apk" "rasmlarni ko'ring"
```

**Telegram bot:**

1. @BotFather'da yangi bot oching va tokenni oling.
2. `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && python3 -m bot.royxat`
3. `TELEGRAM_TOKEN=<token> .venv/bin/python -m bot.telegram_bot`

`python3 -m bot.royxat` xalqaro fishing bazasini yuklaydi (~10 MB, 5 soniya). Haftada bir marta qayta ishga tushiring — o'zi yangilanmaydi.

Bot o'zi ishga tushmaydi (avtomatik yuklash yo'q) — faqat shu buyruq bilan.

### Qanday tekshiradi (arzondan qimmatga)

1. **Fayl:** `.apk`, `.exe`, `.scr`, `.bat` (ham `hujjat.pdf.apk` kabi niqoblangan) → darhol 🔴. Arxiv (`.zip`, `.rar`) → 🟡: ichida dastur yashirilishi mumkin.
2. **Havola:**
   - `data/blacklist.txt` (O'zbekistonga xos, manbasi yozilgan) va `data/tashqi_qora.txt` (xalqaro fishing bazasi, ~386 ming domen) → 🔴.
   - Har kim sahifa ochadigan joylar (Google Forms/Sites, tekin hosting) — «rasmiy» emas, alohida belgi.
   - `data/whitelist.txt` (gov.uz, click.uz, payme.uz, banklar…) → belgi qo'shmaydi.
   - Rasmiy saytga o'xshatilgan domen (`payme-uz.top`, `kapitalbank.uz.secure-login.ru`, `paymeuz.com`, kirill harfli `рayme.uz`) → 🔴. Brend boshqa so'z ichida bo'lsa (`clickup.com`, `paymentwall.com`) — yo'q.
3. **Matn qoidalari** (`bot/qoidalar.py`): kod so'rash, karta, yutuq, «ovoz bering», Markaziy bank/militsiya niqobi, xavfsiz hisob, oldindan to'lov, shoshiltirish… Lotin, kirill va ruscha.
4. **Noaniq yoki pul haqidagi xabarda AI:** avval FreeLLMAPI (lokal, bepul), javob yaroqsiz bo'lsa — lokal `claude` (obuna). AI'ga yuborishdan oldin karta, telefon va email yashiriladi. AI javob bermasa (o'chiq yoki muddat tugadi) — 🟡, pul haqidagi xabar ham. AI kuchli belgini «toza» deb bekor qila olmaydi.

AI'ni o'chirish: `SHUBHALI_AI=0` yoki `--ai-yoq`.

### Sinov

```bash
python3 -m unittest discover -s tests          # 37 test (Telegram qismi .venv bilan)
python3 tests/olchov.py                        # 15 namuna jadvali
python3 tests/olchov.py tests/yashirin2_namunalar.json --ai
```

O'lchov (2026-10-10):

| To'plam | Faqat qoidalar | AI bilan |
|---|---|---|
| 15 asosiy namuna (kun.uz, anhor.uz, Kiberxavfsizlik markazi) | 14/15 (Payme cheki 🟡) | 15/15 |
| **Yashirin 2** (20 ta, qoidalarni ko'rmagan agent yozgan) | 15/20 — firibgarlik o'tkazib yuborilmagan, 5 ta oddiy xabar ortiqcha 🟡 | 20/20 |

Halol o'lchov faqat «Yashirin 2». «Yashirin 1» to'plamiga qarab qoidalar tuzatilgan — u endi sinov emas (AI bilan 19/20).

Vaqt («Yashirin 2», 20 xabardan 12 tasi AI'ga boradi): FreeLLMAPI yoqiq — median 0.4 s, eng sekini 7.6 s (FreeLLMAPI yaroqsiz javob berib, claude'ga o'tganda); faqat claude — median 4.6 s, eng sekini 5.9 s. AI'ga bormagan xabar — 0.1 s dan kam.

### Cheklovlar (halol)

- O'zbekistonga xos qora ro'yxatda 5 ta domen: rasmiy manbalar (Kiberxavfsizlik markazi, kun.uz, F6 hisoboti) soxta domen nomlarini e'lon qilmaydi. Kenglik xalqaro bazadan keladi.
- AI ishlamasa pul haqidagi har xabar (Payme cheki ham) 🟡 oladi — ataylab: firibgarlikni 🟢 qilishdan ortiqcha ehtiyot yaxshi.
- Ko'p foydalanuvchi bilan claude zaxirasi botni ishga tushirgan odamning obunasi limitini sarflaydi — ommaviy ishga tushirishdan oldin hal qilinadi.
- Skrinshot va ovozli xabar o'qilmaydi.
- AI ba'zan oddiy pul so'rovini 🟡 qiladi (masalan, onaning Click orqali pul so'rashi).
- Rasmiy @CyberQalqonbot fayl va havolani chuqurroq tekshiradi — 🟡 javobda unga ham yo'naltiramiz.
