import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TimedOut, RetryAfter
from config import BOT_TOKEN
from utils.downloader import download_instagram
import time

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

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
            "3️⃣ لینک را برای ربات بفرستید.\n"
            "4️⃣ چند ثانیه صبر کنید تا فایل دانلود و ارسال شود.\n\n"
            "⚠️ نکات مهم:\n"
            "- فقط محتوای *عمومی* (public) قابل دانلود است.\n"
            "- ویدیوهای بسیار بزرگ (بیش از 50 مگابایت) ممکن است ارسال نشوند.\n"
            "- در صورت خطای Timeout، لطفاً دوباره تلاش کنید."
        )
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]))
    elif data == "about":
        about_text = (
            "🤖 *ربات دانلودر اینستاگرام*\n\n"
            "نسخه: 1.1\n"
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

async def send_with_retry(update: Update, file_path: str, caption: str, retries=2):
    """ارسال فایل با تلاش مجدد در صورت Timeout"""
    ext = os.path.splitext(file_path)[1].lower()
    for attempt in range(retries):
        try:
            if ext in ['.mp4', '.mov', '.webm']:
                with open(file_path, 'rb') as video:
                    await update.message.reply_video(
                        video=video,
                        caption=caption,
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
                        ]),
                        write_timeout=60,
                        read_timeout=60,
                        connect_timeout=60,
                        pool_timeout=60
                    )
            elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                with open(file_path, 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=caption,
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
                        ])
                    )
            else:
                with open(file_path, 'rb') as doc:
                    await update.message.reply_document(
                        document=doc,
                        filename=os.path.basename(file_path),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
                        ])
                    )
            return True
        except (TimedOut, RetryAfter) as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt == retries - 1:
                raise
            await asyncio.sleep(2)
        except Exception as e:
            raise
    return False

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

    status_msg = await update.message.reply_text("⏬ در حال دانلود... لطفاً صبر کنید (ممکن است 30-60 ثانیه طول بکشد).")

    try:
        file_path = await asyncio.wait_for(download_instagram(url), timeout=90)
    except asyncio.TimeoutError:
        await status_msg.edit_text(
            "⏰ زمان دانلود به پایان رسید. ممکن است ویدیو خیلی بزرگ باشد یا اینترنت شما کند است.\n"
            "لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        )
        return

    if not file_path or not os.path.exists(file_path):
        await status_msg.edit_text(
            "❌ دانلود ناموفق.\nدلایل احتمالی:\n- لینک خصوصی است\n- محتوا حذف شده\n- اینستاگرام محدودیت اعمال کرده",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        )
        return

    await status_msg.edit_text("✅ دانلود کامل شد. در حال ارسال به تلگرام...")

    try:
        await send_with_retry(update, file_path, "✅ دانلود شد توسط ربات")
        await status_msg.delete()
    except TimedOut:
        await status_msg.edit_text(
            "❌ خطا: زمان ارسال به پایان رسید. فایل ممکن است خیلی بزرگ باشد (بیش از 50 مگابایت).\n"
            "لطفاً یک ویدیوی کوتاه‌تر را امتحان کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        )
    except Exception as e:
        await status_msg.edit_text(
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
    # افزایش timeouts در سطح اپلیکیشن
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

    print("ربات با منوی دکمه‌ای روشن شد... (timeouts افزایش یافته)")
    app.run_polling()

if __name__ == "__main__":
    main()