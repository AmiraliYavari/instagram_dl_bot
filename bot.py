import asyncio
import os
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TimedOut, RetryAfter
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
        "من می‌توانم ویدیو، عکس، ریلز و استوری را از اینستاگرام دانلود کنم.\n\n"
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
        help_text = "📖 راهنما: لینک اینستاگرام را بفرستید، سپس کیفیت را انتخاب کنید."
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=await back_button())
    elif data == "about":
        about_text = "🤖 ربات دانلودر اینستاگرام - نسخه 2.8\nمتن‌باز"
        await query.edit_message_text(about_text, parse_mode="Markdown", reply_markup=await back_button())
    elif data == "back_to_menu":
        await query.edit_message_text("✨ منوی اصلی:", reply_markup=await main_menu())
    elif data == "size_error":
        try:
            await query.answer("حجم ویدیو بیشتر از 48 مگابایت است!", show_alert=True)
        except:
            pass
    elif data.startswith("download_format_"):
        format_id = data.replace("download_format_", "")
        url = context.user_data.get('pending_url')
        if not url:
            print("❌ لینک در user_data یافت نشد")
            await query.edit_message_text("❌ لینک منقضی شد.", reply_markup=await back_button())
            return

        is_photo = context.user_data.get('is_photo_message', False)
        print(f"⬇️ شروع دانلود برای: {url} با فرمت {format_id}")
        # تغییر پیام منو به "در حال دانلود..."
        try:
            if is_photo:
                await query.edit_message_caption(caption="⏬ در حال دانلود... (ممکن است چند دقیقه طول بکشد)", reply_markup=None)
            else:
                await query.edit_message_text("⏬ در حال دانلود... (ممکن است چند دقیقه طول بکشد)", reply_markup=None)
        except Exception as e:
            print(f"⚠️ خطا در تغییر پیام منو: {e}")

        start_time = time.time()
        file_path = await download_instagram(url, format_id)
        download_time = time.time() - start_time
        print(f"✅ دانلود پایان یافت. زمان: {download_time:.2f} ثانیه. مسیر: {file_path}")

        if not file_path or not os.path.exists(file_path):
            print("❌ فایل دانلود شده پیدا نشد یا None است")
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

        # ارسال فایل به تلگرام با لاگ کامل
        try:
            print("📤 شروع ارسال ویدیو به تلگرام...")
            with open(file_path, 'rb') as video:
                await update.effective_chat.send_video(
                    video=video,
                    caption="✅ دانلود شد",
                    reply_markup=await back_button(),
                    write_timeout=120,
                    read_timeout=120,
                    connect_timeout=120,
                    pool_timeout=120
                )
            print("✅ ویدیو با موفقیت ارسال شد")
            await query.message.delete()
        except TimedOut as e:
            print(f"⏰ خطای Timeout در ارسال ویدیو: {e}")
            # تلاش مجدد به صورت document
            try:
                print("🔄 تلاش برای ارسال به عنوان Document...")
                with open(file_path, 'rb') as f:
                    await update.effective_chat.send_document(
                        document=f,
                        filename=os.path.basename(file_path),
                        caption="✅ دانلود شد (ارسال به صورت فایل به دلیل Timeout)",
                        reply_markup=await back_button(),
                        write_timeout=120,
                        read_timeout=120
                    )
                print("✅ Document با موفقیت ارسال شد")
                await query.message.delete()
            except Exception as e2:
                print(f"❌ خطا در ارسال Document: {e2}")
                try:
                    if is_photo:
                        await query.edit_message_caption(caption=f"❌ خطا: {str(e2)[:100]}", reply_markup=await back_button())
                    else:
                        await query.edit_message_text(f"❌ خطا: {str(e2)[:100]}", reply_markup=await back_button())
                except:
                    pass
        except Exception as e:
            print(f"❌ خطای غیرمنتظره در ارسال: {type(e).__name__}: {e}")
            try:
                if is_photo:
                    await query.edit_message_caption(caption=f"❌ خطا: {str(e)[:100]}", reply_markup=await back_button())
                else:
                    await query.edit_message_text(f"❌ خطا: {str(e)[:100]}", reply_markup=await back_button())
            except:
                pass
        finally:
            try:
                os.remove(file_path)
                print(f"🗑️ فایل موقت حذف شد: {file_path}")
            except Exception as e:
                print(f"⚠️ خطا در حذف فایل: {e}")

async def handle_instagram_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    print(f"🔗 لینک دریافت شد: {url}")
    if "instagram.com" not in url:
        await update.message.reply_text("❌ لینک معتبر اینستاگرام بفرستید.", reply_markup=await back_button())
        return

    status_msg = await update.message.reply_text("⏳ دریافت اطلاعات ویدیو...")
    print("📡 در حال دریافت اطلاعات از yt-dlp...")
    video_info = await get_video_info(url)

    if not video_info or not video_info.get('formats'):
        print("❌ اطلاعات ویدیو دریافت نشد")
        await status_msg.edit_text("❌ اطلاعات ویدیو یافت نشد.", reply_markup=await back_button())
        return

    print(f"✅ اطلاعات دریافت شد. عنوان: {video_info.get('title', 'N/A')}")
    context.user_data['pending_url'] = url

    keyboard = []
    for fmt in video_info['formats']:
        label = fmt['quality_label']
        size = fmt['size_mb']
        size_str = f" ({size} MB)" if size != 'Unknown' else ""
        print(f"   کیفیت: {label}, حجم: {size_str}")
        if size != 'Unknown' and size > MAX_VIDEO_SIZE_MB:
            keyboard.append([InlineKeyboardButton(f"⚠️ {label}{size_str} (بزرگ) ⚠️", callback_data="size_error")])
        else:
            keyboard.append([InlineKeyboardButton(f"📹 {label}{size_str}", callback_data=f"download_format_{fmt['format_id']}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")])

    duration = video_info.get('duration')
    if duration:
        mins, secs = divmod(int(duration), 60)
        dur_str = f"{mins}:{secs:02d}"
    else:
        dur_str = "نامشخص"

    caption = f"🎬 *{video_info['title'][:50]}*\n⏱️ {dur_str}\n📊 کیفیت‌های موجود:"

    if video_info.get('thumbnail'):
        await status_msg.delete()
        print("🖼️ ارسال منو با کاور")
        await update.message.reply_photo(
            photo=video_info['thumbnail'],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        context.user_data['is_photo_message'] = True
    else:
        print("📝 ارسال منو به صورت متن (بدون کاور)")
        await status_msg.edit_text(caption, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        context.user_data['is_photo_message'] = False

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🚨 خطای全局: {context.error}")
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

    print("✅ ربات روشن شد. در حال انتظار برای پیام‌ها...")
    app.run_polling()

if __name__ == "__main__":
    main()