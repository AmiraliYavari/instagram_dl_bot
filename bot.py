import asyncio
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
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
            "- در صورت قطع شدن دانلود، ربات به شما اطلاع می‌دهد."
        )
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]))
    elif data == "about":
        about_text = (
            "🤖 *ربات دانلودر اینستاگرام*\n\n"
            "نسخه: 2.3\n"
            "ساخته شده با پایتون\n\n"
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
    elif data == "size_error":
        await query.answer("حجم این ویدیو بیشتر از حد مجاز 50 مگابایت است!", show_alert=True)
    elif data.startswith("download_format_"):
        format_id = data.replace("download_format_", "")
        url = context.user_data.get('pending_url')
        if not url:
            if context.user_data.get('is_photo_message'):
                await query.edit_message_caption(
                    caption="❌ لینک منقضی شده است. لطفاً دوباره لینک را ارسال کنید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
                    ])
                )
            else:
                await query.edit_message_text(
                    "❌ لینک منقضی شده است. لطفاً دوباره لینک را ارسال کنید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
                    ])
                )
            return

        # نمایش پیام در حال دانلود
        if context.user_data.get('is_photo_message'):
            await query.edit_message_caption(
                caption="⏬ در حال دانلود ویدیو با کیفیت انتخابی... (لطفاً صبر کنید)",
                reply_markup=None
            )
        else:
            await query.edit_message_text("⏬ در حال دانلود ویدیو با کیفیت انتخابی... (لطفاً صبر کنید)")

        file_path = await download_instagram(url, format_id)

        if not file_path or not os.path.exists(file_path):
            error_msg = (
                "❌ دانلود ناتمام ماند.\n"
                "دلایل احتمالی:\n"
                "- اینترنت قطع شده است\n"
                "- اینستاگرام درخواست را مسدود کرده\n"
                "- حجم ویدیو بسیار بالا است\n\n"
                "لطفاً دوباره تلاش کنید یا کیفیت پایین‌تری انتخاب کنید."
            )
            if context.user_data.get('is_photo_message'):
                await query.edit_message_caption(
                    caption=error_msg,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
                    ])
                )
            else:
                await query.edit_message_text(
                    error_msg,
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
            err_msg = f"❌ خطا در ارسال فایل: {str(e)[:100]}"
            if context.user_data.get('is_photo_message'):
                await query.edit_message_caption(
                    caption=err_msg,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
                    ])
                )
            else:
                await query.edit_message_text(
                    err_msg,
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

    video_info = await get_video_info(url)

    if not video_info:
        await status_msg.edit_text(
            "❌ نتوانستم اطلاعات ویدیو را دریافت کنم.\nممکن است لینک خصوصی باشد یا اینستاگرام محدودیت ایجاد کرده باشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        )
        return

    formats = video_info.get('formats', [])
    if not formats:
        await status_msg.edit_text(
            "❌ هیچ فرمت ویدیویی قابل دانلودی پیدا نشد.\n\n"
            "دلایل احتمالی:\n"
            "- لینک مربوط به یک عکس (نه ویدیو) است\n"
            "- محتوا خصوصی است\n"
            "- اینستاگرام محدودیت ایجاد کرده\n\n"
            "لطفاً یک لینک ویدیوی عمومی دیگر امتحان کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        )
        return

    context.user_data['pending_url'] = url

    keyboard = []
    for fmt in formats:
        quality_label = fmt['quality_label']
        size_mb = fmt['size_mb']
        size_text = f" ({size_mb} MB)" if size_mb != 'Unknown' else ""
        format_id = fmt['format_id']

        if size_mb != 'Unknown' and size_mb > MAX_VIDEO_SIZE_MB:
            button_text = f"⚠️ {quality_label}{size_text} - حجم بالاست ⚠️"
            keyboard.append([InlineKeyboardButton(button_text, callback_data="size_error")])
        else:
            button_text = f"📹 {quality_label}{size_text}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"download_format_{format_id}")])

    keyboard.append([InlineKeyboardButton("🔙 انصراف و بازگشت به منو", callback_data="back_to_menu")])

    duration = video_info.get('duration')
    if duration and isinstance(duration, (int, float)):
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        duration_str = f"{minutes}:{seconds:02d}"
    else:
        duration_str = "نامشخص"

    caption = (
        f"🎬 *{video_info['title'][:50]}*\n\n"
        f"⏱️ مدت زمان: {duration_str}\n\n"
        f"📊 کیفیت‌های موجود:\n"
        f"لطفاً کیفیت مورد نظر خود را انتخاب کنید:"
    )

    thumbnail = video_info.get('thumbnail')
    if thumbnail:
        await status_msg.delete()
        sent_photo = await update.message.reply_photo(
            photo=thumbnail,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        context.user_data['is_photo_message'] = True
        context.user_data['menu_message_id'] = sent_photo.message_id
    else:
        await status_msg.edit_text(
            caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        context.user_data['is_photo_message'] = False

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

    print("ربات با منوی انتخاب کیفیت (نسخه نهایی با مدیریت خطای دانلود) روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()