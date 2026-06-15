
## 📄 فایل `README.md` (کد کامل برای کپی)

```markdown
<div align="center">

# 📸 اینستاگرام دانلودر (ربات تلگرام)

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-7.0-blue.svg)](https://core.telegram.org/bots/api)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![yt-dlp](https://img.shields.io/badge/powered%20by-yt--dlp-red.svg)](https://github.com/yt-dlp/yt-dlp)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

رباتی پیشرفته و کاربردی برای دانلود **ویدیو، ریلز، عکس و استوری** از اینستاگرام به همراه قابلیت **استخراج صدا (MP3)** و **انتخاب کیفیت دلخواه**، مستقیماً در تلگرام!

[گزارش مشکل](https://github.com/AmiraliYavari/instagram_dl_bot/issues) • [پیشنهاد ویژگی جدید](https://github.com/AmiraliYavari/instagram_dl_bot/issues) • [⭐ ستاره](https://github.com/AmiraliYavari/instagram_dl_bot/stargazers)

</div>

---

## ✨ قابلیت‌های کلیدی

| ویژگی | توضیح |
|:---|:---|
| 🎥 **دانلود محتوای اینستاگرام** | پشتیبانی از پست‌های عادی، ریلز، استوری و هایلایت‌های عمومی |
| 🎵 **تبدیل به MP3** | قابلیت استخراج و دانلود صدای ویدیوها با کیفیت عالی |
| 🎛️ **منوی دکمه‌ای** | رابط کاربری ساده و جذاب با دکمه‌های شیشه‌ای (Inline Keyboard) |
| 📊 **نمایش اطلاعات** | نمایش عنوان، مدت زمان، کاور و حجم ویدیوها قبل از دانلود |
| ⚡ **سرعت بالا** | دانلود سریع با قابلیت ادامه دانلود نیمه‌تمام و تلاش مجدد خودکار |
| 🔒 **حریم خصوصی** | عدم نیاز به لاگین در اینستاگرام؛ حذف خودکار فایل‌های موقت پس از ارسال |
| 🌐 **پشتیبانی از پروکسی** | قابلیت تنظیم پروکسی برای شبکه‌های محدود (SOCKS5/HTTP) |
| 🖥️ **لاگ‌های دقیق** | مشاهده جزئیات کامل دانلود و ارسال در ترمینال برای رفع خطا |

---

## 🚀 نحوه استفاده (برای کاربر نهایی)

1. **شروع**: دستور `/start` را به ربات ارسال کنید.
2. **ارسال لینک**: لینک پست، ریلز، استوری یا هایلایت اینستاگرام را برای ربات بفرستید.
3. **انتخاب کیفیت**: ربات اطلاعات محتوا را نمایش داده و لیست کیفیت‌های موجود (همراه با حجم هرکدام) را به شما نشان می‌دهد.
4. **دریافت فایل**: پس از انتخاب کیفیت، چند ثانیه صبر کنید تا فایل برایتان ارسال شود.

---

## 🛠️ نصب و اجرا (برای توسعه‌دهندگان)

### پیش‌نیازها
- **Python 3.8** یا بالاتر
- **FFmpeg** (برای استخراج صدای MP3) – [راهنمای نصب](#-نصب-ffmpeg)
- **توکن ربات تلگرام** (از [@BotFather](https://t.me/BotFather) بگیرید)

### مراحل نصب

```bash
# 1. کلون کردن ریپازیتوری
git clone https://github.com/AmiraliYavari/instagram_dl_bot.git
cd instagram_dl_bot

# 2. ایجاد و فعالسازی محیط مجاز (پیشنهادی)
python -m venv venv
source venv/bin/activate  # در لینوکس/مک
venv\Scripts\activate     # در ویندوز

# 3. نصب کتابخانه‌های مورد نیاز
pip install -r requirements.txt

# 4. تنظیم توکن ربات
cp .env.example .env
# فایل .env را با یک ویرایشگر باز کرده و توکن واقعی خود را وارد کنید.

# 5. اجرای ربات
python bot.py
```

### 🔧 نصب FFmpeg

برای استفاده از قابلیت تبدیل به MP3، نصب `ffmpeg` ضروری است.

**ویندوز:**
1. فایل ZIP را از [ffmpeg.org](https://ffmpeg.org/download.html) دانلود کرده در مسیری مثل `C:\ffmpeg` از حالت فشرده خارج کنید.
2. مسیر `C:\ffmpeg\bin` را به `PATH` سیستم اضافه کنید.
3. برای تست، دستور `ffmpeg -version` را در CMD اجرا کنید.

**لینوکس (Debian/Ubuntu):**
```bash
sudo apt update && sudo apt install ffmpeg -y
```

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

### 🌐 تنظیم پروکسی (اختیاری)

اگر از v2rayN یا نرم‌افزار مشابهی استفاده می‌کنید، در فایل `.env` پروکسی خود را تنظیم کنید:

```env
BOT_TOKEN=توکن_ربات_شما
PROXY_URL=socks5://127.0.0.1:10808
```

پروکسی‌های پشتیبانی‌شده: `http://`, `https://`, `socks5://`

---

## 📂 ساختار پروژه

```
instagram_dl_bot/
│
├── bot.py                 # کد اصلی ربات
├── config.py              # تنظیمات و خواندن متغیرهای محیطی
├── requirements.txt       # لیست کتابخانه‌ها
├── .env.example           # نمونه فایل متغیرهای محیطی
├── .gitignore             # فایل‌های نادیده گرفته شده در گیت
├── utils/
│   └── downloader.py      # منطق دانلود و استخراج اطلاعات با yt-dlp
└── temp/                  # پوشه موقت برای فایل‌های دانلودی (به‌طور خودکار ساخته می‌شود)
```

---

## 🧪 فناوری‌های استفاده شده

| کتابخانه | کاربرد |
|:---|:---|
| [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) | ارتباط با API تلگرام و مدیریت دکمه‌ها (نسخه 20.x) |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | استخراج اطلاعات و دانلود از اینستاگرام با قابلیت ترکیب ویدیو و صدا |
| [PySocks](https://github.com/Anorov/PySocks) | پشتیبانی از پروکسی SOCKS5 |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | مدیریت متغیرهای محیطی |
| [FFmpeg](https://ffmpeg.org/) | پردازش و تبدیل فایل‌های صوتی |

---

## ❓ عیب‌یابی

### ❌ خطای `WinError 10061` یا `Connection refused`
- مطمئن شوید پروکسی شما (مثل v2rayN) فعال است.
- پورت صحیح را در `.env` تنظیم کنید (SOCKS5 معمولاً `10808`، HTTP معمولاً `10809`).
- ربات و برنامه پروکسی را با دسترسی Administrator اجرا کنید.

### ❌ خطای `Query is too old`
- هنگام کلیک روی دکمه‌ها رخ می‌دهد. ربات را ریستارت کرده و دوباره تلاش کنید.
- در نسخه‌های اخیر این مشکل برطرف شده است.

### ❌ خطای `Timed out` در ارسال فایل
- ویدیو احتمالاً بیش از ۵۰ مگابایت حجم دارد. کیفیت پایین‌تری انتخاب کنید.
- اتصال اینترنت خود را بررسی کنید.

### ❌ ویدیو صدا ندارد
- ربات به‌طور خودکار بهترین فرمت صوتی را با ویدیو ترکیب می‌کند. لطفاً مطمئن شوید `ffmpeg` روی سیستم نصب است.
- برخی ویدیوهای اینستاگرام به طور ذاتی فاقد جریان صوتی هستند.

### ❌ خطای `ffmpeg is not installed`
- دستورالعمل نصب `ffmpeg` را در بخش [نصب FFmpeg](#-نصب-ffmpeg) دنبال کنید.

---

## 🤝 مشارکت در توسعه

هرگونه Pull Request، گزارش Issue یا ایده جدید با آغوش باز پذیرفته می‌شود.

1. ریپازیتوری را Fork کنید.
2. شاخه (`branch`) جدیدی برای تغییرات خود بسازید: `git checkout -b feature/amazing-feature`
3. تغییرات را Commit کنید: `git commit -m 'Add some amazing feature'`
4. به شاخه خود Push کنید: `git push origin feature/amazing-feature`
5. یک Pull Request جدید باز کنید.

---

## ⚖️ مجوز

این پروژه تحت مجوز **MIT** منتشر شده است. برای جزئیات بیشتر به فایل [LICENSE](LICENSE) مراجعه کنید.

---

## ⚠️ توجه قانونی

این ربات صرفاً برای استفاده شخصی و محتوای **عمومی** اینستاگرام ساخته شده است. لطفاً به قوانین کپی‌رایت و حقوق مالکیت معنوی احترام بگذارید. استفاده از این ربات برای دانلود محتوای خصوصی یا نقض قوانین اینستاگرام ممنوع است.

---

<div align="center">

**ساخته شده با ❤️ و پایتون**

[⭐ Give a Star ⭐](https://github.com/AmiraliYavari/instagram_dl_bot) • [📧 Report Bug](https://github.com/AmiraliYavari/instagram_dl_bot/issues)

</div>
