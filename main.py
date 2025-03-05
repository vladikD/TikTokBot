import logging
import os
import re

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import yt_dlp
import nest_asyncio
from dotenv import load_dotenv
nest_asyncio.apply()

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не знайдено!")


# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Обмеження Telegram для файлів (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

def is_valid_tiktok_url(url: str) -> bool:
    """
    Перевіряє, чи URL відповідає патерну TikTok.
    Допускаються посилання з доменів www.tiktok.com, m.tiktok.com, vm.tiktok.com, vt.tiktok.com.
    """
    pattern = r"https?://(www\.)?(m\.)?((vm|vt)\.)?tiktok\.com/.*"
    return re.match(pattern, url) is not None


def download_tiktok_video(url: str) -> str:
    """
    Завантажує відео з TikTok за допомогою yt-dlp та повертає шлях до файлу.
    """
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'noplaylist': True,
    }
    os.makedirs("downloads", exist_ok=True)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info_dict)
    return filename


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Надішли мені посилання на TikTok відео, і я завантажу його для тебе.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    # Перевірка валідності URL
    if not is_valid_tiktok_url(url):
        await update.message.reply_text("Це не виглядає як валідне посилання на TikTok. Перевір його і спробуй ще раз.")
        return

    await update.message.reply_text("Скачую відео, зачекай...")
    try:
        video_path = download_tiktok_video(url)

        # Перевірка розміру файлу
        file_size = os.path.getsize(video_path)
        if file_size > MAX_FILE_SIZE:
            await update.message.reply_text("Відео занадто велике для відправки через Telegram (максимум 50 MB).")
            os.remove(video_path)
            return

        with open(video_path, 'rb') as video_file:
            await update.message.reply_video(video=video_file)
        os.remove(video_path)
    except Exception as e:
        logging.error(f"Помилка при завантаженні відео: {e}")
        await update.message.reply_text("Виникла помилка при завантаженні відео. Перевір посилання та спробуй ще раз.")

async def main():
    # Заміни 'YOUR_TELEGRAM_BOT_TOKEN' на свій токен
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    logger.info("Бот запущено. Очікую повідомлень...")
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
