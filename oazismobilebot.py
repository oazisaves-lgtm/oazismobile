import os
import asyncio
import logging
import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import yt_dlp

BOT_TOKEN = "8862010292:AAFmfIvMOUQ-xtLupRzpFKmH_pRw-Q5uGEw"

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def is_instagram_url(url: str) -> bool:
    return "instagram.com" in url or "instagr.am" in url


def download_instagram_video(url: str, output_dir: str):
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            return None

        if "entries" in info:
            info = info["entries"][0]

        filename = ydl.prepare_filename(info)
        path = Path(filename).with_suffix(".mp4")
        if path.exists():
            return str(path)

        for f in Path(output_dir).iterdir():
            if f.stem == Path(filename).stem:
                return str(f)

    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Salom! Men Instagram Video Yuklovchi botman.\n\n"
        "📲 Instagram post yoki Reel havolasini yuboring!\n\n"
        "Misol:\n"
        "https://www.instagram.com/reel/XXXXXXXXXXX/"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ Yordam\n\n"
        "1. Instagram post yoki Reel havolasini yuboring\n"
        "2. Bot videoni yuklab sizga jo'natadi\n\n"
        "Eslatma: Shaxsiy akkauntlar yuklanmasligi mumkin.",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()

    if not is_instagram_url(text):
        await update.message.reply_text(
            "⚠️ Iltimos, to'g'ri Instagram havolasini yuboring.\n"
            "Misol: https://www.instagram.com/reel/XXXXXXXXXXX/"
        )
        return

    status_msg = await update.message.reply_text("⏳ Video yuklanmoqda, iltimos kuting...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = await asyncio.get_event_loop().run_in_executor(
                None, download_instagram_video, text, tmpdir
            )

            if not filepath or not Path(filepath).exists():
                await status_msg.edit_text(
                    "❌ Videoni yuklab bo'lmadi.\n\n"
                    "Mumkin bo'lgan sabablar:\n"
                    "• Post shaxsiy (private)\n"
                    "• Havola noto'g'ri\n"
                    "• Faqat rasm post"
                )
                return

            file_size_mb = Path(filepath).stat().st_size / (1024 * 1024)

            if file_size_mb > 50:
                await status_msg.edit_text(
                    f"⚠️ Video hajmi {file_size_mb:.1f} MB — Telegram chegarasi 50 MB."
                )
                return

            await status_msg.edit_text("📤 Video jo'natilmoqda...")

            with open(filepath, "rb") as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption="✅ Mana sizning videongiz!\n\n🤖 @oazismobilebot",
                    supports_streaming=True,
                )

            await status_msg.delete()

    except Exception as e:
        logger.exception("Xato: %s", e)
        await status_msg.edit_text("❌ Xato yuz berdi. Keyinroq qayta urinib ko'ring.")


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
