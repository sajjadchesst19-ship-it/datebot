import logging
import os
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_CHAT_ID = 107774980

ASK, PICK_MONTH, PICK_HOUR, PICK_MIN = range(4)

J_MONTHS = ["فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
            "مهر","آبان","آذر","دی","بهمن","اسفند"]

def fa(n):
    return str(n).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))

# ── تبدیل میلادی به شمسی ──────────────────────────────────────
def to_jalali(gy, gm, gd):
    g_days_in_month = [31,28,31,30,31,30,31,31,30,31,30,31]
    j_days_in_month = [31,31,31,31,31,31,30,30,30,30,30,29]

    gy2 = gm > 2 and gy+1 or gy
    days = (365*gy) + (gy2+3)//4 - (gy2+99)//100 + (gy2+399)//400
    for i in range(gm-1):
        days += g_days_in_month[i]
    if gm > 2 and ((gy%4==0 and gy%100!=0) or gy%400==0):
        days += 1
    days += gd

    days -= 226894  # offset

    jy = -1595 + 33*(days//12053)
    days %= 12053
    jy += 4*(days//1461)
    days %= 1461
    if days > 365:
        jy += (days-1)//365
        days = (days-1)%365

    jm = 0
    for i,v in enumerate(j_days_in_month):
        if days < v:
            jm = i+1
            jd = days+1
            break
        days -= v

    return jy, jm, jd

def days_in_jmonth(jy, jm):
    if jm <= 6: return 31
    if jm <= 11: return 30
    leap = [1,5,9,13,17,22,26,30]
    return 30 if (jy % 33) in leap else 29

def today_jalali():
    t = date.today()
    return to_jalali(t.year, t.month, t.day)

# ── /start ────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🖤 آره، میام!", callback_data="yes")],
        [InlineKeyboardButton("نه", callback_data="no_0")],
    ]
    await update.message.reply_text(
        "🕷️\n\n*میای با هم بریم بیرون؟*\n\nبا دقت انتخاب کن…",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return ASK

# ── دکمه نه ──────────────────────────────────────────────────
async def no_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("فرار کردم! 😈")
    count = int(query.data.split("_")[1]) + 1

    if count >= 7:
        kb = [
            [InlineKeyboardButton("🖤 آره، میام!", callback_data="yes")],
            [InlineKeyboardButton("👻 (ناپدید شد!)", callback_data="gone")],
        ]
        await query.edit_message_text(
            "🕷️\n\n*میای با هم بریم بیرون؟*\n\nدکمه نه فرار کرد 😏",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
    else:
        labels = ["نه (سعی کن 😏)","نه (اینجام!)","نه (بازم؟ 😈)","نه… یا آره؟","نه (آخرین بار!)","نه (تقریباً رفتم)"]
        kb = [
            [InlineKeyboardButton("🖤 آره، میام!", callback_data="yes")],
            [InlineKeyboardButton(labels[min(count-1, len(labels)-1)], callback_data=f"no_{count}")],
        ]
        await query.edit_message_text(
            "🕷️\n\n*میای با هم بریم بیرون؟*\n\nبا دقت انتخاب کن…",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
    return ASK

async def gone_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("این دکمه دیگه کار نمیکنه 😄", show_alert=True)
    return ASK

# ── آره → انتخاب ماه/روز ─────────────────────────────────────
async def yes_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("یییس! 🖤")
    jy, jm, _ = today_jalali()
    ctx.user_data['jy'] = jy
    ctx.user_data['jm'] = jm
    await show_calendar(query, ctx, jy, jm)
    return PICK_MONTH

async def show_calendar(query, ctx, jy, jm):
    ty, tm, td = today_jalali()
    rows = []

    # ناوبری ماه
    nav = []
    if (jy, jm) > (ty, tm):
        pm, py = (jm-1, jy) if jm > 1 else (12, jy-1)
        nav.append(InlineKeyboardButton("◀️", callback_data=f"month_{py}_{pm}"))
    else:
        nav.append(InlineKeyboardButton(" ", callback_data="noop"))
    nav.append(InlineKeyboardButton(f"📅 {J_MONTHS[jm-1]} {fa(jy)}", callback_data="noop"))
    nm, ny = (jm+1, jy) if jm < 12 else (1, jy+1)
    nav.append(InlineKeyboardButton("▶️", callback_data=f"month_{ny}_{nm}"))
    rows.append(nav)

    # هدر روزهای هفته
    rows.append([InlineKeyboardButton(d, callback_data="noop") for d in ["ش","ی","د","س","چ","پ","ج"]])

    # روزها
    total = days_in_jmonth(jy, jm)
    row = []
    for d in range(1, total+1):
        if (jy, jm) == (ty, tm):
            is_past = d < td
        else:
            is_past = (jy, jm) < (ty, tm)

        if is_past:
            row.append(InlineKeyboardButton("·", callback_data="noop"))
        else:
            row.append(InlineKeyboardButton(fa(d), callback_data=f"day_{jy}_{jm}_{d}"))
        if len(row) == 7:
            rows.append(row)
            row = []
    if row:
        # پر کردن آخرین ردیف
        while len(row) < 7:
            row.append(InlineKeyboardButton(" ", callback_data="noop"))
        rows.append(row)

    await query.edit_message_text(
        "🕯️ *یه روز انتخاب کن:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def month_nav(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    py, pm = int(parts[1]), int(parts[2])
    await show_calendar(query, ctx, py, pm)
    return PICK_MONTH

# ── انتخاب روز → ساعت ────────────────────────────────────────
async def day_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, jy, jm, jd = query.data.split("_")
    ctx.user_data['jy'] = int(jy)
    ctx.user_data['jm'] = int(jm)
    ctx.user_data['jd'] = int(jd)

    rows = []
    row = []
    for h in range(8, 23):
        row.append(InlineKeyboardButton(fa(h), callback_data=f"hour_{h}"))
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    await query.edit_message_text(
        f"🕰️ *{fa(int(jd))} {J_MONTHS[int(jm)-1]} {fa(int(jy))}*\n\nساعت رو انتخاب کن:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(rows)
    )
    return PICK_HOUR

# ── انتخاب ساعت → دقیقه ─────────────────────────────────────
async def hour_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    h = int(query.data.split("_")[1])
    ctx.user_data['hour'] = h

    jy = ctx.user_data['jy']
    jm = ctx.user_data['jm']
    jd = ctx.user_data['jd']
    kb = [[
        InlineKeyboardButton(f"{fa(h)}:۰۰", callback_data="min_0"),
        InlineKeyboardButton(f"{fa(h)}:۳۰", callback_data="min_30"),
    ]]
    await query.edit_message_text(
        f"🕰️ *{fa(jd)} {J_MONTHS[jm-1]} {fa(jy)} — ساعت {fa(h)}*\n\nدقیقه رو انتخاب کن:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return PICK_MIN

# ── تایید نهایی ───────────────────────────────────────────────
async def min_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🖤 ثبت شد!")

    minute = int(query.data.split("_")[1])
    jy = ctx.user_data['jy']
    jm = ctx.user_data['jm']
    jd = ctx.user_data['jd']
    h  = ctx.user_data['hour']
    m_str = "۰۰" if minute == 0 else "۳۰"

    date_str = f"{fa(jd)} {J_MONTHS[jm-1]} {fa(jy)}"
    time_str = f"{fa(h)}:{m_str}"

    await query.edit_message_text(
        "🧛 *قرارمون ثبت شد!*\n\n"
        f"📅 {date_str}\n"
        f"🕰️ ساعت {time_str}\n\n"
        "منتظرتم 🖤🕷️",
        parse_mode="Markdown"
    )

    user = query.from_user
    name = user.first_name or "اون"
    await query.get_bot().send_message(
        chat_id=OWNER_CHAT_ID,
        text=(
            "🕷️ *قرار تایید شد!*\n\n"
            f"👤 {name} قبول کرد!\n"
            f"📅 تاریخ: {date_str}\n"
            f"🕰️ ساعت: {time_str}\n\n"
            "برو آماده بشو 😏🖤"
        ),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def noop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("کنسل شد.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK: [
                CallbackQueryHandler(yes_handler,  pattern="^yes$"),
                CallbackQueryHandler(no_handler,   pattern="^no_\\d+$"),
                CallbackQueryHandler(gone_handler, pattern="^gone$"),
            ],
            PICK_MONTH: [
                CallbackQueryHandler(month_nav,   pattern="^month_"),
                CallbackQueryHandler(day_handler, pattern="^day_"),
                CallbackQueryHandler(noop,        pattern="^noop$"),
            ],
            PICK_HOUR: [
                CallbackQueryHandler(hour_handler, pattern="^hour_"),
                CallbackQueryHandler(noop,         pattern="^noop$"),
            ],
            PICK_MIN: [
                CallbackQueryHandler(min_handler, pattern="^min_"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(noop, pattern="^noop$"))
    print("🕷️ Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
