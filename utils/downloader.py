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
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            
            formats = []
            for f in info.get('formats', []):
                # فقط فرمت‌هایی که هم ویدیو دارند هم صدا (یا حداقل ویدیو)
                vcodec = f.get('vcodec')
                if vcodec == 'none':
                    continue
                
                # استخراج رزولوشن (height)
                height = f.get('height')
                if not height:
                    # گاهی height در `resolution` هست
                    res = f.get('resolution')
                    if res and 'x' in res:
                        height = int(res.split('x')[1])
                
                if not height:
                    continue
                
                # استخراج حجم
                filesize = f.get('filesize') or f.get('filesize_approx')
                size_mb = round(filesize / (1024 * 1024), 1) if filesize else 'Unknown'
                
                formats.append({
                    'format_id': f['format_id'],
                    'quality': height,  # عددی برای مرتب‌سازی
                    'quality_label': f"{height}p",
                    'size_mb': size_mb,
                    'ext': f.get('ext', 'mp4')
                })
            
            # حذف فرمت‌های تکراری بر اساس ارتفاع (بالاترین کیفیت برای هر ارتفاع)
            unique_formats = {}
            for fmt in formats:
                q = fmt['quality']
                if q not in unique_formats:
                    unique_formats[q] = fmt
                # اگر ارتفاع تکراری بود، فرمتی با حجم مشخص ترجیح داده شود
                elif fmt['size_mb'] != 'Unknown' and unique_formats[q]['size_mb'] == 'Unknown':
                    unique_formats[q] = fmt
            
            # مرتب‌سازی از کم به زیاد
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