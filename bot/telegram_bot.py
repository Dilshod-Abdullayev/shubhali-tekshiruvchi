"""Telegram bot: odam shubhali xabar/havola/faylni forward qiladi — bot 🔴/🟡/🟢 bilan javob beradi.

    TELEGRAM_TOKEN=123:ABC python -m bot.telegram_bot

Xabarlar hech qayerga saqlanmaydi: matn faqat xotirada tekshiriladi va javobdan keyin unutiladi.
Fayl yuklab olinmaydi — nomi va turi (mime) yetarli (.apk/.exe xavfi shundan bilinadi).
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .check import tekshir

SALOM = (
    "Assalomu alaykum! Menga shubhali xabar, havola yoki faylni yuboring (forward qilsangiz ham bo'ladi) — "
    "10 soniyada aytaman:\n"
    "🔴 Xavfli · 🟡 Shubhali · 🟢 Ko'rinishidan toza\n\n"
    "Esda tuting: bank va davlat idoralari hech qachon SMS kod yoki karta ma'lumotini so'ramaydi."
)
QOLLAB_EMAS = ("Hozircha rasm, ovozli xabar va videoni o'qiy olmayman. Xabardagi yozuvni nusxalab "
               "(yoki havolani) matn qilib yuboring — darhol tekshiraman.")

log = logging.getLogger("shubhali")


async def salom(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(SALOM)


async def tekshiruv(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    matn = msg.text or msg.caption or ""
    fayl = msg.document.file_name if msg.document else None
    mime = msg.document.mime_type if msg.document else None
    if not matn.strip() and not fayl:
        await msg.reply_text(QOLLAB_EMAS)
        return
    await msg.chat.send_action(ChatAction.TYPING)
    # tekshir() sinxron (AI uchun subprocess/HTTP) — bot boshqa foydalanuvchilarni kutib qolmasligi uchun alohida oqimda
    n = await asyncio.to_thread(tekshir, matn, fayl, mime)
    log.info("daraja=%s pogona=%s manba=%s %.2fs", n.daraja, n.pogona, n.manba, n.soniya)   # matn logga yozilmaydi
    await msg.reply_text(n.matn(), reply_to_message_id=msg.message_id)


async def qollab_emas(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg.caption:   # rasm/video ostidagi yozuvni baribir tekshiramiz
        n = await asyncio.to_thread(tekshir, msg.caption)
        # Rasmning o'zini o'qimaymiz — yozuv toza chiqsa ham 🟢 bermaymiz (firibgarlik rasm ichida bo'lishi mumkin)
        if n.daraja != "toza":
            await msg.reply_text(n.matn() + "\n\n(Faqat rasm ostidagi yozuv tekshirildi.)")
            return
    await msg.reply_text(QOLLAB_EMAS)


def ilova(token: str) -> Application:
    app = Application.builder().token(token).concurrent_updates(True).build()
    app.add_handler(CommandHandler(["start", "help"], salom))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.VOICE | filters.AUDIO
                                   | filters.VIDEO_NOTE | filters.Sticker.ALL, qollab_emas))
    app.add_handler(MessageHandler((filters.TEXT & ~filters.COMMAND) | filters.Document.ALL | filters.CAPTION, tekshiruv))
    return app


def main() -> int:
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    if not token:
        print("TELEGRAM_TOKEN topilmadi. Tokensiz sinash: python -m bot.check 'xabar matni'", file=sys.stderr)
        return 1
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)   # httpx so'rov URL'ida token ko'rinadi
    ilova(token).run_polling(allowed_updates=Update.ALL_TYPES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
