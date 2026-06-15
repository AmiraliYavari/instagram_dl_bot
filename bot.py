import asyncio
import os
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TimedOut
from config import BOT_TOKEN
from utils.downloader import get_video_info, download_instagram

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

MAX_VIDEO_SIZE_MB = 48

async def main_menu():
    keyboard = [
        [InlineKeyboardButton("📥 دانلود از اینستاگرام", callback_data="download")],
        [InlineKeyboardButton("📖 راهنما", callback_data="help")],
        [InlineKeyboardButton("ℹ️ درباره ربات", callback_data="about")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📩 دستور /start دریافت شد")
    welcome_text = (
        "✨ به ربات دانلودر اینستاگرام خوش آمدید! ✨\n\n"
        "من می‌توانم ویدیو و صوت را از اینستاگرام دانلود کنم.\n\n"
        "✅ فقط کافیست یکی از گزینه‌های زیر را انتخاب کنید."
    )
    await update.message.reply_text(welcome_text, reply_markup=await main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    print(f"🔘 دکمه فشرده شد: {query.data}")
    try:
        await query.answer()
    except Exception as e:
        print(f"⚠️ خطا در answer: {e}")

    data = query.data

    if data == "download":
        await query.edit_message_text(
            "🔗 لطفاً لینک اینستاگرام را ارسال کنید.\nمثال: `https://www.instagram.com/p/Cxample/`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        )
    elif data == "help":
        help_text = "📖 راهنما: لینک اینستاگرام را بفرستید، سپس کیفیت ویدیو یا صوت را انتخاب کنید."
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=await back_button())
    elif data == "about":
        about_text = "🤖 ربات دانلودر اینستاگرام - نسخه 3.2\nقابلیت دانلود ویدیو و MP3"
        await query.edit_message_text(about_text, parse_mode="Markdown", reply_markup=await back_button())
    elif data == "back_to_menu":
        await query.edit_message_text("✨ منوی اصلی:", reply_markup=await main_menu())
    elif data == "size_error":
        try:
            await query.answer("حجم ویدیو بیشتر از 48 مگابایت است!", show_alert=True)
        except:
            pass
    elif data.startswith("download_video_"):
        format_id = data.replace("download_video_", "")
        url = context.user_data.get('pending_url')
        if not url:
            await query.edit_message_text("❌ لینک منقضی شد.", reply_markup=await back_button())
            return
        is_photo = context.user_data.get('is_photo_message', False)
        try:
            if is_photo:
                await query.edit_message_caption(caption="⏬ در حال دانلود ویدیو...", reply_markup=None)
            else:
                await query.edit_message_text("⏬ در حال دانلود ویدیو...", reply_markup=None)
        except:
            pass
        await download_and_send(update, query, url, format_id, is_photo, is_audio=False)
    elif data == "download_audio":
        url = context.user_data.get('pending_url')
        if not url:
            await query.edit_message_text("❌ لینک منقضی شد.", reply_markup=await back_button())
            return
        is_photo = context.user_data.get('is_photo_message', False)
        try:
            if is_photo:
                await query.edit_message_caption(caption="⏬ در حال استخراج صدا...", reply_markup=None)
            else:
                await query.edit_message_text("⏬ در حال استخراج صدا...", reply_markup=None)
        except:
            pass
        await download_and_send(update, query, url, None, is_photo, is_audio=True)

async def download_and_send(update, query, url, format_id, is_photo, is_audio=False):
    print(f"⬇️ شروع دانلود {'صوت' if is_audio else 'ویدیو'} برای: {url}")
    start_time = time.time()
    file_path = await download_instagram(url, format_id, is_audio=is_audio)
    download_time = time.time() - start_time
    print(f"✅ دانلود پایان یافت. زمان: {download_time:.2f} ثانیه. مسیر: {file_path}")

    if not file_path or not os.path.exists(file_path):
        error_msg = "❌ دانلود ناموفق. لطفاً دوباره تلاش کنید."
        try:
            if is_photo:
                await query.edit_message_caption(caption=error_msg, reply_markup=await back_button())
            else:
                await query.edit_message_text(error_msg, reply_markup=await back_button())
        except Exception as e:
            print(f"⚠️ خطا در ویرایش پیام خطا: {e}")
        return

    file_size = os.path.getsize(file_path) / (1024 * 1024)
    print(f"📦 حجم فایل: {file_size:.2f} MB")

    try:
        print(f"📤 شروع ارسال به تلگرام...")
        if is_audio:
            with open(file_path, 'rb') as audio:
                await update.effective_chat.send_audio(
                    audio=audio,
                    caption="✅ صوت استخراج شد",
                    reply_markup=await back_button(),
                    write_timeout=120,
                    read_timeout=120
                )
        else:
            with open(file_path, 'rb') as video:
                await update.effective_chat.send_video(
                    video=video,
                    caption="✅ ویدیو دانلود شد",
                    reply_markup=await back_button(),
                    write_timeout=120,
                    read_timeout=120
                )
        print("✅ فایل با موفقیت ارسال شد")
        await query.message.delete()
    except TimedOut as e:
        print(f"⏰ خطای Timeout: {e}")
        try:
            with open(file_path, 'rb') as f:
                await update.effective_chat.send_document(
                    document=f,
                    filename=os.path.basename(file_path),
                    caption="✅ دانلود شد (ارسال به صورت فایل به دلیل Timeout)",
                    reply_markup=await back_button()
                )
            await query.message.delete()
        except Exception as e2:
            await query.edit_message_text(f"❌ خطا در ارسال: {str(e2)[:100]}", reply_markup=await back_button())
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        await query.edit_message_text(f"❌ خطا: {str(e)[:100]}", reply_markup=await back_button())
    finally:
        try:
            os.remove(file_path)
            print(f"🗑️ فایل موقت حذف شد: {file_path}")
        except:
            pass

async def handle_instagram_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    print(f"🔗 لینک دریافت شد: {url}")
    if "instagram.com" not in url:
        await update.message.reply_text("❌ لینک معتبر اینستاگرام بفرستید.", reply_markup=await back_button())
        return

    status_msg = await update.message.reply_text("⏳ دریافت اطلاعات ویدیو...")
    video_info = await get_video_info(url)

    if not video_info:
        await status_msg.edit_text("❌ اطلاعات ویدیو یافت نشد.", reply_markup=await back_button())
        return

    context.user_data['pending_url'] = url

    keyboard = []
    # نمایش همه فرمت‌های ویدیویی
    for fmt in video_info.get('video_formats', []):
        label = fmt['quality_label']
        size = fmt['size_mb']
        size_str = f" ({size} MB)" if size != 'Unknown' else ""
        if size != 'Unknown' and size > MAX_VIDEO_SIZE_MB:
            keyboard.append([InlineKeyboardButton(f"⚠️ {label}{size_str} (بزرگ) ⚠️", callback_data="size_error")])
        else:
            keyboard.append([InlineKeyboardButton(f"📹 {label}{size_str}", callback_data=f"download_video_{fmt['format_id']}")])

    # دکمه دانلود صدا
    if video_info.get('audio_format'):
        audio = video_info['audio_format']
        size_str = f" ({audio['size_mb']} MB)" if audio['size_mb'] != 'Unknown' else ""
        keyboard.append([InlineKeyboardButton(f"🎵 MP3 (فقط صدا){size_str}", callback_data="download_audio")])

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")])

    duration = video_info.get('duration')
    if duration:
        mins, secs = divmod(int(duration), 60)
        dur_str = f"{mins}:{secs:02d}"
    else:
        dur_str = "نامشخص"

    caption = f"🎬 *{video_info['title'][:50]}*\n⏱️ {dur_str}\n📊 گزینه‌های موجود:"

    if video_info.get('thumbnail'):
        await status_msg.delete()
        await update.message.reply_photo(
            photo=video_info['thumbnail'],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        context.user_data['is_photo_message'] = True
    else:
        await status_msg.edit_text(caption, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        context.user_data['is_photo_message'] = False

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🚨 خطای سراسری: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("⚠️ خطای داخلی", reply_markup=await back_button())

def main():
    print("🚀 ربات در حال راه‌اندازی...")
    app = Application.builder() \
        .token(BOT_TOKEN) \
        .connect_timeout(120.0) \
        .read_timeout(120.0) \
        .write_timeout(120.0) \
        .pool_timeout(120.0) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instagram_link))
    app.add_error_handler(error_handler)

    print("✅ ربات با قابلیت دانلود همه کیفیت‌های ویدیو (به همراه صدا) و MP3 روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()