# utils/downloader.py
import yt_dlp
import asyncio
import uuid
import os
from config import PROXY_URL

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

async def get_video_info(url: str):
    """دریافت اطلاعات و فرمت‌های موجود ویدیو (بدون دانلود)"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'force_generic_extractor': False,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
    }
    if PROXY_URL:
        ydl_opts['proxy'] = PROXY_URL

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # فقط اطلاعات را دریافت کن، دانلود نکن
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            
            formats = []
            for f in info.get('formats', []):
                # فیلتر کردن فرمت‌های ویدیویی معتبر
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    format_note = f.get('format_note') or f.get('resolution') or 'Unknown'
                    # تبدیل حجم به MB
                    file_size = f.get('filesize')
                    if not file_size and f.get('filesize_approx'):
                        file_size = f.get('filesize_approx')
                    
                    size_mb = round(file_size / (1024 * 1024), 1) if file_size else 'Unknown'
                    format_id = f['format_id']
                    
                    formats.append({
                        'format_id': format_id,
                        'quality': format_note,
                        'size_mb': size_mb,
                        'ext': f.get('ext', 'mp4')
                    })
            
            # حذف فرمت‌های تکراری بر اساس کیفیت (بهترین کیفیت را نگه دار)
            unique_formats = {}
            for f in formats:
                key = f['quality']
                if key not in unique_formats or (f['size_mb'] != 'Unknown' and unique_formats[key].get('size_mb') == 'Unknown'):
                    unique_formats[key] = f
            
            # مرتب‌سازی از کم کیفیت به پرکیفیت (بر اساس وضوح)
            sorted_formats = sorted(unique_formats.values(), key=lambda x: x['quality'])
            
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration'),
                'thumbnail': info.get('thumbnail'),
                'formats': sorted_formats
            }
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None

async def download_instagram(url: str, format_id: str = None):
    """دانلود ویدیو با فرمت انتخاب شده"""
    unique_id = str(uuid.uuid4())
    output_template = os.path.join(TEMP_DIR, f"insta_{unique_id}.%(ext)s")

    ydl_opts = {
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        'socket_timeout': 60,
        'retries': 10,
        'fragment_retries': 10,
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
            return filename if os.path.exists(filename) else None
    except Exception as e:
        print(f"Error in download_instagram: {e}")
        return None