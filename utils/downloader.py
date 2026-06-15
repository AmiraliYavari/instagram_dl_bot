import yt_dlp
import asyncio
import uuid
import os
import traceback
from config import PROXY_URL

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

async def get_video_info(url: str):
    """دریافت اطلاعات ویدیو، همه فرمت‌های ویدیویی (همراه با صدا یا بدون صدا) و فرمت صوتی"""
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

            # دریافت همه فرمت‌های ویدیویی (حتی بدون صدا)
            video_formats = []
            for f in info.get('formats', []):
                if f.get('vcodec') == 'none':
                    continue
                height = f.get('height')
                if not height:
                    res = f.get('resolution')
                    if res and 'x' in res:
                        try:
                            height = int(res.split('x')[1])
                        except:
                            pass
                if not height:
                    # اگر ارتفاع نداره، برچسب بگذاریم
                    label = f.get('format_note') or 'Unknown'
                    height = label
                else:
                    label = f"{height}p"
                
                filesize = f.get('filesize') or f.get('filesize_approx')
                size_mb = round(filesize / (1024 * 1024), 1) if filesize else 'Unknown'
                
                video_formats.append({
                    'format_id': f['format_id'],
                    'quality': height,  # می‌تواند عدد یا رشته باشد
                    'quality_label': label,
                    'size_mb': size_mb,
                    'ext': f.get('ext', 'mp4'),
                    'has_audio': f.get('acodec') != 'none'
                })

            # حذف تکراری‌ها (بر اساس quality_label)
            unique_video = {}
            for fmt in video_formats:
                key = fmt['quality_label']
                if key not in unique_video:
                    unique_video[key] = fmt
                elif fmt['size_mb'] != 'Unknown' and unique_video[key]['size_mb'] == 'Unknown':
                    unique_video[key] = fmt
            
            # مرتب‌سازی سعی می‌کند عددی باشد، وگرنه ترتیب اولیه
            def sort_key(item):
                val = item[1]['quality']
                if isinstance(val, int):
                    return val
                return 9999
            sorted_video = sorted(unique_video.values(), key=lambda x: x['quality'] if isinstance(x['quality'], int) else 9999)

            # بهترین فرمت صوتی (برای دانلود جداگانه)
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
                    break

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
    """دانلود ویدیو (با بهترین صدا) یا فقط صدا"""
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
        'merge_output_format': 'mp4',
    }

    if is_audio:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif format_id:
        # ویدیو را با بهترین صدا ترکیب کن
        ydl_opts['format'] = f'{format_id}+bestaudio/best'
    else:
        # اگر format_id نداد (اتفاق نمی‌افتد)، بهترین کیفیت ویدیو+صدا را بگیر
        ydl_opts['format'] = 'bestvideo+bestaudio/best'

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