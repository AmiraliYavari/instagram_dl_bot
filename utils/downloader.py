import yt_dlp
import asyncio
import uuid
import os

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

async def download_instagram(url: str):
    """
    دانلود ویدیو یا تصویر از اینستاگرام
    Returns: مسیر فایل دانلود شده (یا None در صورت خطا)
    """
    unique_id = str(uuid.uuid4())
    output_template = os.path.join(TEMP_DIR, f"insta_{unique_id}.%(ext)s")
    
    ydl_opts = {
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'force_generic_extractor': False,
    }
    
    try:
        # اجرای yt-dlp در یک thread جدا (چون blocking است)
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            # پیدا کردن فایل خروجی
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                # بعضی وقتا پسوند فرق می‌کند (مثلاً mp4)
                for f in os.listdir(TEMP_DIR):
                    if f.startswith(f"insta_{unique_id}"):
                        filename = os.path.join(TEMP_DIR, f)
                        break
            return filename
    except Exception as e:
        print(f"Error downloading: {e}")
        return None