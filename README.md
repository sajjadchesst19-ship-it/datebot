# 🕷️ Date Invitation Bot

## Deploy on Railway (رایگان، ۳ دقیقه‌ای)

### ۱. آپلود به GitHub
1. برو [github.com](https://github.com) → New repository
2. اسمش رو بذار `datebot` → Create
3. فایل‌های `bot.py` و `requirements.txt` و `Procfile` رو آپلود کن

### ۲. Deploy روی Railway
1. برو [railway.app](https://railway.app) → Login with GitHub
2. کلیک کن **New Project** → **Deploy from GitHub repo**
3. ریپو `datebot` رو انتخاب کن
4. بعد از deploy، برو **Variables** و اضافه کن:
   ```
   BOT_TOKEN = 8873174346:AAF3HJgDHjm_5oWOb5HGE0uBUSeMzgOr9L4
   ```
5. بات رو restart کن — تمومه! ✅

### ۳. لینک بات رو بفرست
بعد از اجرا، لینک بات رو برای اون بفرست:
```
https://t.me/YOUR_BOT_USERNAME
```

## جریان بات
1. اون `/start` می‌زنه
2. سوال «میای با هم بریم بیرون؟» با دکمه آره/نه
3. اگه «نه» بزنه — دکمه عوض میشه و فرار می‌کنه (۷ بار) بعد ناپدید میشه
4. اگه «آره» بزنه — تقویم شمسی میاد
5. روز → ساعت → دقیقه رو انتخاب می‌کنه
6. بهت نوتیف میاد با اسمش + تاریخ و ساعت 🖤
