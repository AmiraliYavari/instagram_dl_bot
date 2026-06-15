import asyncio
import os
import shutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import BOT_TOKEN
from utils.downloader import download_instagram

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# ========== منو و دکمه‌ها ==========
async def main_menu():
    keyboard = [
        [InlineKeyboardButton("📥 دانلود از اینستاگرام", callback_data="download")],
        [InlineKeyboardButton("📖 راهنما", callback_data="help")],
        [InlineKeyboardButton("ℹ️ درباره ربات", callback_data="about")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== دستور /start ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "✨ به ربات دانلودر اینستاگرام خوش آمدید! ✨\n\n"
        "من می‌توانم برای شما ویدیو، عکس، ریلز و استوری را از اینستاگرام دانلود کنم.\n\n"
        "✅ فقط کافیست یکی از گزینه‌های زیر را انتخاب کنید."
    )
    await update.message.reply_text(welcome_text, reply_markup=await main_menu())

# ========== پردازش دکمه‌ها ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # اعلان کوتاه به تلگرام که کلیک ثبت شد

    if query.data == "download":
        await query.edit_message_text(
            "🔗 لطفاً لینک پست، استوری، ریلز یا هایلایت اینستاگرام را ارسال کنید.\n\n"
            "مثال: `https://www.instagram.com/p/Cxample/`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        )
    elif query.data == "help":
        help_text = (
            "📖 *راهنمای استفاده:*\n\n"
            "1️⃣ دکمه «دانلود از اینستاگرام» را بزنید.\n"
            "2️⃣ لینک مطلب مورد نظر را از اینستاگرام کپی کنید.\n"
            "3️⃣ لینک را برای ربات بفرستید.\n"
            "4️⃣ چند ثانیه صبر کنید تا فایل دانلود و ارسال شود.\n\n"
            "⚠️ نکات مهم:\n"
            "- فقط محتوای *عمومی* (public) قابل دانلود است.\n"
            "- استوری‌های خصوصی و پیج‌های قفل شده پشتیبانی نمی‌شوند.\n"
            "- حداکثر حجم فایل ارسالی تلگرام 50 مگابایت است (ویدیوهای طولانی ممکن است ارسال نشوند)."
        )
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]))
    elif query.data == "about":
        about_text = (
            "🤖 *ربات دانلودر اینستاگرام*\n\n"
            "نسخه: 1.0\n"
            "ساخته شده با پایتون و کتابخانه‌های:\n"
            "- python-telegram-bot\n"
            "- yt-dlp\n\n"
            "📂 کد منبع و مستندات:\n"
            "[GitHub Repository](https://github.com/YOUR_USERNAME/instagram_downloader_telegram_bot)\n\n"
            "💡 این ربات متن‌باز است و برای استفاده شخصی طراحی شده."
        )
        await query.edit_message_text(about_text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]))
    elif query.data == "back_to_menu":
        await query.edit_message_text(
            "✨ منوی اصلی:\nلطفاً یکی از گزینه‌ها را انتخاب کنید.",
            reply_markup=await main_menu()
        )

# ========== پردازش لینک اینستاگرام ==========
async def handle_instagram_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.effective_chat.id

    if not ("instagram.com" in url or "instagr.am" in url):
        await update.message.reply_text(
            "❌ لطفاً یک لینک معتبر اینستاگرام بفرستید.\n"
            "مثال: `https://www.instagram.com/p/Cxample/`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        )
        return

    status_msg = await update.message.reply_text("⏬ در حال دانلود... لطفاً صبر کنید (ممکن است چند ثانیه طول بکشد).")

    file_path = await download_instagram(url)

    if not file_path or not os.path.exists(file_path):
        await status_msg.edit_text(
            "❌ دانلود ناموفق.\nدلایل احتمالی:\n- لینک خصوصی است\n- محتوا حذف شده\n- اینستاگرام محدودیت اعمال کرده",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        )
        return

    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext in ['.mp4', '.mov', '.webm']:
            with open(file_path, 'rb') as video:
                await update.message.reply_video(
                    video=video,
                    caption="✅ دانلود شد توسط ربات اینستاگرام دانلودر",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
                    ])
                )
        elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
            with open(file_path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption="✅ عکس مورد نظر",
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
        await status_msg.delete()
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
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instagram_link))
    app.add_error_handler(error_handler)

    print("ربات با منوی دکمه‌ای روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()