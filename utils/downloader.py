import yt_dlp
import asyncio
import uuid
import os
import traceback
from config import PROXY_URL

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# لیست رزولوشن‌های مجاز (به ترتیب از کم به زیاد)
ALLOWED_RESOLUTIONS = [144, 360, 480, 720, 1080]

async def get_video_info(url: str):
    """دریافت اطلاعات ویدیو، فرمت‌های ویدیویی مجاز و فرمت صوتی"""
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

            # پردازش فرمت‌های ویدیویی (با صدا)
            video_formats = []
            for f in info.get('formats', []):
                # فقط فرمت‌هایی که هم ویدیو دارند هم صدا
                if f.get('vcodec') == 'none' or f.get('acodec') == 'none':
                    continue
                height = f.get('height')
                if not height:
                    res = f.get('resolution')
                    if res and 'x' in res:
                        try:
                            height = int(res.split('x')[1])
                        except:
                            pass
                if not height or height not in ALLOWED_RESOLUTIONS:
                    continue
                
                filesize = f.get('filesize') or f.get('filesize_approx')
                size_mb = round(filesize / (1024 * 1024), 1) if filesize else 'Unknown'
                
                video_formats.append({
                    'format_id': f['format_id'],
                    'quality': height,
                    'quality_label': f"{height}p",
                    'size_mb': size_mb,
                    'ext': f.get('ext', 'mp4')
                })

            # حذف تکراری‌ها (بهترین فرمت برای هر رزولوشن)
            unique_video = {}
            for fmt in video_formats:
                q = fmt['quality']
                if q not in unique_video:
                    unique_video[q] = fmt
                elif fmt['size_mb'] != 'Unknown' and unique_video[q]['size_mb'] == 'Unknown':
                    unique_video[q] = fmt
            
            # مرتب‌سازی بر اساس کیفیت (صعودی)
            sorted_video = sorted(unique_video.values(), key=lambda x: x['quality'])

            # پردازش فرمت صوتی (بهترین فرمت صوتی موجود)
            audio_format = None
            for f in info.get('formats', []):
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    filesize = f.get('filesize') or f.get('filesize_approx')
                    size_mb = round(filesize / (1024 * 1024), 1) if filesize else 'Unknown'
                    audio_format = {
                        'format_id': f['format_id'],
                        'quality_label': 'MP3 (فقط صدا)',
                        'size_mb': size_mb,
                        'ext': 'mp3'
                    }
                    break  # اولین فرمت صوتی (معمولا بهترین کیفیت)

            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration'),
                'thumbnail': info.get('thumbnail'),
                'video_formats': sorted_video,
                'audio_format': audio_format
            }
    except Exception as e:
        print(f"Error in get_video_info: {e}")
        traceback.print_exc()
        return None

async def download_instagram(url: str, format_id: str = None, is_audio: bool = False):
    """دانلود ویدیو یا صدا با فرمت مشخص"""
    unique_id = str(uuid.uuid4())
    output_template = os.path.join(TEMP_DIR, f"insta_{unique_id}.%(ext)s")

    ydl_opts = {
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': False,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        'socket_timeout': 90,
        'retries': 20,
        'fragment_retries': 20,
        'continuedl': True,
    }

    if is_audio:
        # دانلود صدا و تبدیل به mp3
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif format_id:
        ydl_opts['format'] = format_id

    if PROXY_URL:
        ydl_opts['proxy'] = PROXY_URL
        print(f"✅ از پروکسی استفاده می‌شود: {PROXY_URL}")

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)
            if is_audio:
                base = os.path.splitext(filename)[0]
                filename = base + '.mp3'
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