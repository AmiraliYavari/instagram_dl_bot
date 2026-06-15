import asyncio
import os
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
    welcome_text = (
        "✨ به ربات دانلودر اینستاگرام خوش آمدید! ✨\n\n"
        "من می‌توانم ویدیو، عکس، ریلز و استوری را از اینستاگرام دانلود کنم.\n\n"
        "✅ فقط کافیست یکی از گزینه‌های زیر را انتخاب کنید."
    )
    await update.message.reply_text(welcome_text, reply_markup=await main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        print(f"Warning: {e}")

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
        help_text = (
            "📖 *راهنما:*\n"
            "1️⃣ دکمه دانلود را بزنید.\n"
            "2️⃣ لینک اینستاگرام را بفرستید.\n"
            "3️⃣ کیفیت مورد نظر را انتخاب کنید.\n"
            "4️⃣ منتظر بمانید تا ویدیو دانلود و ارسال شود.\n\n"
            "⚠️ محدودیت 50 مگابایت برای ویدیو در تلگرام."
        )
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=await back_button())
    elif data == "about":
        about_text = "🤖 ربات دانلودر اینستاگرام - نسخه 2.7\nمتن‌باز"
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
            await query.edit_message_text("❌ لینک منقضی شد.", reply_markup=await back_button())
            return

        is_photo = context.user_data.get('is_photo_message', False)
        # تغییر پیام به "در حال دانلود..."
        try:
            if is_photo:
                await query.edit_message_caption(caption="⏬ در حال دانلود... (ممکن است چند دقیقه طول بکشد)", reply_markup=None)
            else:
                await query.edit_message_text("⏬ در حال دانلود...", reply_markup=None)
        except:
            pass

        file_path = await download_instagram(url, format_id)

        if not file_path or not os.path.exists(file_path):
            error_msg = "❌ دانلود ناموفق. لطفاً دوباره تلاش کنید."
            if is_photo:
                await query.edit_message_caption(caption=error_msg, reply_markup=await back_button())
            else:
                await query.edit_message_text(error_msg, reply_markup=await back_button())
            return

        # ارسال فایل با timeout بیشتر
        try:
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
            await query.message.delete()
        except TimedOut:
            # در صورت timeout، سعی می‌کنیم به صورت document بفرستیم
            try:
                with open(file_path, 'rb') as f:
                    await update.effective_chat.send_document(
                        document=f,
                        filename=os.path.basename(file_path),
                        caption="✅ دانلود شد (ارسال به صورت فایل)",
                        reply_markup=await back_button(),
                        write_timeout=120,
                        read_timeout=120
                    )
                await query.message.delete()
            except Exception as e2:
                await query.edit_message_text(f"❌ خطا در ارسال: {str(e2)[:100]}", reply_markup=await back_button())
        except Exception as e:
            await query.edit_message_text(f"❌ خطا: {str(e)[:100]}", reply_markup=await back_button())
        finally:
            try:
                os.remove(file_path)
            except:
                pass

async def handle_instagram_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "instagram.com" not in url:
        await update.message.reply_text("❌ لینک معتبر اینستاگرام بفرستید.", reply_markup=await back_button())
        return

    status_msg = await update.message.reply_text("⏳ دریافت اطلاعات ویدیو...")
    video_info = await get_video_info(url)

    if not video_info or not video_info.get('formats'):
        await status_msg.edit_text("❌ اطلاعات ویدیو یافت نشد.", reply_markup=await back_button())
        return

    context.user_data['pending_url'] = url

    keyboard = []
    for fmt in video_info['formats']:
        label = fmt['quality_label']  # مثلاً 360p
        size = fmt['size_mb']
        size_str = f" ({size} MB)" if size != 'Unknown' else ""
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
    print(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("⚠️ خطای داخلی", reply_markup=await back_button())

def main():
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

    print("ربات با timeout 120 ثانیه روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()