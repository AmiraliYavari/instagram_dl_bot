import yt_dlp
import asyncio
import uuid
import os
import traceback
from config import PROXY_URL

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

async def get_video_info(url: str):
    """دریافت اطلاعات و فرمت‌های موجود ویدیو (بدون دانلود)"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
    }
    if PROXY_URL:
        ydl_opts['proxy'] = PROXY_URL

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))

            formats = []
            for f in info.get('formats', []):
                vcodec = f.get('vcodec')
                if vcodec == 'none':
                    continue
                height = f.get('height')
                if not height and f.get('resolution'):
                    try:
                        height = int(f['resolution'].split('x')[1])
                    except:
                        pass
                if not height:
                    continue
                filesize = f.get('filesize') or f.get('filesize_approx')
                size_mb = round(filesize / (1024 * 1024), 1) if filesize else 'Unknown'
                formats.append({
                    'format_id': f['format_id'],
                    'quality': height,
                    'quality_label': f"{height}p",
                    'size_mb': size_mb,
                    'ext': f.get('ext', 'mp4')
                })

            # حذف تکراری‌ها (بهترین فرمت برای هر کیفیت)
            unique = {}
            for fmt in formats:
                q = fmt['quality']
                if q not in unique or (fmt['size_mb'] != 'Unknown' and unique[q]['size_mb'] == 'Unknown'):
                    unique[q] = fmt
            sorted_formats = sorted(unique.values(), key=lambda x: x['quality'])

            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration'),
                'thumbnail': info.get('thumbnail'),
                'formats': sorted_formats
            }
    except Exception as e:
        print(f"Error in get_video_info: {e}")
        traceback.print_exc()
        return None

async def download_instagram(url: str, format_id: str = None):
    """دانلود ویدیو با فرمت انتخاب شده (با لاگ کامل و تلاش مجدد)"""
    unique_id = str(uuid.uuid4())
    output_template = os.path.join(TEMP_DIR, f"insta_{unique_id}.%(ext)s")

    ydl_opts = {
        'outtmpl': output_template,
        'quiet': False,               # نمایش خروجی کامل در ترمینال
        'no_warnings': False,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        },
        'socket_timeout': 90,
        'retries': 20,                # تعداد تلاش مجدد
        'fragment_retries': 20,
        'skip_unavailable_fragments': False,
        'continuedl': True,           # ادامه دانلود نیمه‌تمام
    }

    if format_id:
        ydl_opts['format'] = format_id

    if PROXY_URL:
        ydl_opts['proxy'] = PROXY_URL
        print(f"✅ از پروکسی استفاده می‌شود: {PROXY_URL}")

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                for f in os.listdir(TEMP_DIR):
                    if f.startswith(f"insta_{unique_id}"):
                        filename = os.path.join(TEMP_DIR, f)
                        break
            if os.path.exists(filename):
                print(f"✅ دانلود کامل شد: {filename}")
                return filename
            else:
                print("❌ فایل پیدا نشد بعد از دانلود")
                return None
    except Exception as e:
        print(f"❌ خطا در download_instagram: {e}")
        traceback.print_exc()
        return None