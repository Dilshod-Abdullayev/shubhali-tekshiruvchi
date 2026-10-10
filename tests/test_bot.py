"""Telegram qismi tarmoqsiz: soxta update'lar to'g'ri handler'ga tushadimi va javob nima.

python-telegram-bot o'rnatilmagan bo'lsa (masalan tizim python3 da) — o'tkazib yuboriladi:
    .venv/bin/python -m unittest discover -s tests
"""
import asyncio
import datetime as dt
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from telegram import Chat, Document, Message, MessageEntity, PhotoSize, Update, User, Voice
    from bot import telegram_bot as tb
except ImportError:  # kutubxona yo'q
    tb = None


@unittest.skipIf(tb is None, "python-telegram-bot o'rnatilmagan")
class Bot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = tb.ilova("123456:TEST")
        cls.app.bot._bot_user = User(9, "Bot", True, username="shubhali_bot")   # getMe'siz (tarmoqsiz)

    def yubor(self, **kw) -> tuple[str, str]:
        m = Message(1, dt.datetime.now(), Chat(1, "private"), from_user=User(1, "D", False), **kw)
        m.set_bot(self.app.bot)
        up = Update(1, message=m)
        h = next(h for h in self.app.handlers[0] if h.check_update(up))
        javob = []

        async def rep(_self, text, **_):
            javob.append(text)

        async def act(*_, **__):
            pass

        with mock.patch.dict(os.environ, {"SHUBHALI_AI": "0"}), mock.patch.object(Message, "reply_text", rep), \
             mock.patch.object(Chat, "send_action", act):
            asyncio.run(h.callback(up, None))
        return h.callback.__name__, javob[0]

    def test_start(self):
        self.assertEqual(self.yubor(text="/start", entities=[MessageEntity("bot_command", 0, 6)])[0], "salom")

    def test_matn_va_fayl(self):
        self.assertTrue(self.yubor(text="Kelgan SMS kodni ayting, yutuq sizniki")[1].startswith("🔴"))
        doc = Document("f", "u", file_name="Toy rasmlari.apk", mime_type="application/vnd.android.package-archive")
        self.assertTrue(self.yubor(document=doc)[1].startswith("🔴"))
        self.assertTrue(self.yubor(text="Bugun soat 6 da majlis bor")[1].startswith("🟢"))

    def test_rasm_ovoz_halol_javob(self):
        self.assertEqual(self.yubor(photo=[PhotoSize("p", "u", 10, 10)])[1], tb.QOLLAB_EMAS)
        self.assertEqual(self.yubor(voice=Voice("v", "u", 3))[1], tb.QOLLAB_EMAS)
        # Yozuv toza bo'lsa ham rasmga 🟢 berilmaydi; yozuvda xavf bo'lsa — aytiladi
        self.assertEqual(self.yubor(photo=[PhotoSize("p", "u", 10, 10)], caption="Ona, non olaymi?")[1], tb.QOLLAB_EMAS)
        self.assertTrue(self.yubor(photo=[PhotoSize("p", "u", 10, 10)], caption="SMS kodni ayting")[1][0] in "🔴🟡")


if __name__ == "__main__":
    unittest.main()
