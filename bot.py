# bot.py
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TimedOut, RetryAfter
from config import BOT_TOKEN
from utils.downloader import get_video_info, download_instagram

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

MAX_VIDEO_SIZE_MB = 48  # حاشیه امن برای محدودیت 50 مگابایتی تلگرام

async def main_menu():
    keyboard = [
        [InlineKeyboardButton("📥 دانلود از اینستاگرام", callback_data="download")],
        [InlineKeyboardButton("📖 راهنما", callback_data="help")],
        [InlineKeyboardButton("ℹ️ درباره ربات", callback_data="about")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "✨ به ربات دانلودر اینستاگرام خوش آمدید! ✨\n\n"
        "من می‌توانم برای شما ویدیو، عکس، ریلز و استوری را از اینستاگرام دانلود کنم.\n\n"
        "✅ فقط کافیست یکی از گزینه‌های زیر را انتخاب کنید."
    )
    await update.message.reply_text(welcome_text, reply_markup=await main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        print(f"Error answering callback query: {e}")
        if update.effective_message:
            await update.effective_message.reply_text("⏰ زمان کلیک شما منقضی شده است. لطفاً مجدداً /start را بزنید.")
        return

    data = query.data

    if data == "download":
        await query.edit_message_text(
            "🔗 لطفاً لینک پست، استوری، ریلز یا هایلایت اینستاگرام را ارسال کنید.\n\n"
            "مثال: `https://www.instagram.com/p/Cxample/`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        )
    elif data == "help":
        help_text = (
            "📖 *راهنمای استفاده:*\n\n"
            "1️⃣ دکمه «دانلود از اینستاگرام» را بزنید.\n"
            "2️⃣ لینک مطلب مورد نظر را از اینستاگرام کپی کنید.\n"
            "3️⃣ ربات اطلاعات ویدیو را دریافت کرده و گزینه‌های کیفیت را نمایش می‌دهد.\n"
            "4️⃣ کیفیت مورد نظر خود را انتخاب کنید.\n"
            "5️⃣ ربات فایل را دانلود کرده و برای شما ارسال می‌کند.\n\n"
            "⚠️ نکات مهم:\n"
            "- فقط محتوای *عمومی* (public) قابل دانلود است.\n"
            "- حداکثر حجم مجاز برای ارسال ویدیو در تلگرام **50 مگابایت** است.\n"
            "- در صورت بزرگ بودن حجم ویدیو، ربات به شما اخطار می‌دهد و دانلود نمی‌کند."
        )
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]))
    elif data == "about":
        about_text = (
            "🤖 *ربات دانلودر اینستاگرام*\n\n"
            "نسخه: 2.0\n"
            "ساخته شده با پایتون و کتابخانه‌های:\n"
            "- python-telegram-bot\n"
            "- yt-dlp\n\n"
            "📂 کد منبع:\n[GitHub Repository](https://github.com/YOUR_USERNAME/instagram_downloader_telegram_bot)\n\n"
            "💡 ربات متن‌باز است."
        )
        await query.edit_message_text(about_text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]))
    elif data == "back_to_menu":
        await query.edit_message_text(
            "✨ منوی اصلی:\nلطفاً یکی از گزینه‌ها را انتخاب کنید.",
            reply_markup=await main_menu()
        )
    elif data.startswith("download_format_"):
        # کاربر یک کیفیت را انتخاب کرده است
        format_id = data.replace("download_format_", "")
        url = context.user_data.get('pending_url')
        if not url:
            await query.edit_message_text(
                "❌ لینک منقضی شده است. لطفاً دوباره لینک را ارسال کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
                ])
            )
            return
        
        await query.edit_message_text("⏬ در حال دانلود ویدیو با کیفیت انتخابی...")
        
        file_path = await download_instagram(url, format_id)
        
        if not file_path or not os.path.exists(file_path):
            await query.edit_message_text(
                "❌ دانلود ناموفق.\nلطفاً دوباره تلاش کنید یا کیفیت دیگری را انتخاب کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
                ])
            )
            return
        
        # ارسال فایل
        try:
            with open(file_path, 'rb') as video:
                await update.effective_chat.send_video(
                    video=video,
                    caption="✅ دانلود شد توسط ربات",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
                    ])
                )
            await query.message.delete()
        except Exception as e:
            await query.edit_message_text(
                f"❌ خطا در ارسال فایل: {str(e)[:100]}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
                ])
            )
        finally:
            try:
                os.remove(file_path)
            except:
                pass

async def handle_instagram_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not ("instagram.com" in url or "instagr.am" in url):
        await update.message.reply_text(
            "❌ لطفاً یک لینک معتبر اینستاگرام بفرستید.\nمثال: `https://www.instagram.com/p/Cxample/`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        )
        return

    status_msg = await update.message.reply_text("⏳ در حال دریافت اطلاعات ویدیو...")

    # دریافت اطلاعات ویدیو
    video_info = await get_video_info(url)
    
    if not video_info or not video_info.get('formats'):
        await status_msg.edit_text(
            "❌ نتوانستم اطلاعات ویدیو را دریافت کنم.\nممکن است لینک خصوصی باشد یا اینستاگرام محدودیت ایجاد کرده باشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        )
        return

    # ذخیره لینک در user_data برای استفاده بعدی
    context.user_data['pending_url'] = url

    # ساخت دکمه‌های کیفیت
    keyboard = []
    for fmt in video_info['formats']:
        size_text = f" ({fmt['size_mb']} MB)" if fmt['size_mb'] != 'Unknown' else ""
        # بررسی حجم فایل
        if fmt['size_mb'] != 'Unknown' and fmt['size_mb'] > MAX_VIDEO_SIZE_MB:
            # اگر حجم بیشتر از حد مجاز بود، دکمه را غیرفعال (یا با اخطار) نشان بده
            button_text = f"⚠️ {fmt['quality']}{size_text} - حجم بالاست ⚠️"
            keyboard.append([InlineKeyboardButton(button_text, callback_data="size_error")])
        else:
            button_text = f"📹 {fmt['quality']}{size_text}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"download_format_{fmt['format_id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 انصراف و بازگشت به منو", callback_data="back_to_menu")])
    
    # نمایش اطلاعات ویدیو با کاور
    caption = (
        f"🎬 *{video_info['title'][:50]}*\n\n"
        f"⏱️ مدت زمان: {video_info['duration'] // 60}:{video_info['duration'] % 60:02d} دقیقه\n\n"
        f"📊 کیفیت‌های موجود:\n"
        f"لطفاً کیفیت مورد نظر خود را انتخاب کنید:"
    )
    
    try:
        # ارسال کاور (thumbnail) اگر وجود داشته باشد
        if video_info.get('thumbnail'):
            await status_msg.delete()
            await update.message.reply_photo(
                photo=video_info['thumbnail'],
                caption=caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await status_msg.edit_text(
                caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        print(f"Error sending menu: {e}")
        await status_msg.edit_text(
            caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ یک خطای داخلی رخ داد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        )

def main():
    app = Application.builder() \
        .token(BOT_TOKEN) \
        .connect_timeout(60.0) \
        .read_timeout(60.0) \
        .write_timeout(60.0) \
        .pool_timeout(60.0) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instagram_link))
    app.add_error_handler(error_handler)

    print("ربات با منوی انتخاب کیفیت روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()