import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "8873174346:AAF3HJgDHjm_5oWOb5HGE0uBUSeMzgOr9L4")
OWNER_CHAT_ID = 107774980

# States
ASK, PICK_MONTH, PICK_DAY, PICK_HOUR, PICK_MIN = range(5)

# ── Jalali helpers ──────────────────────────────────────────────
J_MONTHS = ["فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
            "مهر","آبان","آذر","دی","بهمن","اسفند"]

def to_jalali(gy, gm, gd):
    g_d_no = 365*(gy-1) + (gy-1+3)//4 - (gy-1+99)//100 + (gy-1+399)//400
    for i in range(1, gm):
        g_d_no += [0,31,29 if (gy%4==0 and (gy%100!=0 or gy%400==0)) else 28,
                   31,30,31,30,31,31,30,31,30,31][i]
    g_d_no += gd
    j = g_d_no - 79
    j_np = j // 12053
    j %= 12053
    jy = 979 + 33*j_np + 4*(j//1461)
    j %= 1461
    if j >= 366:
        jy += (j-1)//365
        j = (j-1) % 365
    jdm = [31,31,31,31,31,31,30,30,30,30,30]
    jm = 0
    for v in jdm:
        if j < v:
            break
        j -= v
        jm += 1
    return jy, jm, j+1

def to_gregorian(jy, jm, jd):
    jy += 1595
    days = -355779 + 365*jy + (jy//33)*8 + ((jy%33+3)//4) + jd
    jdm = [31,31,31,31,31,31,30,30,30,30,30,29]
    for i in range(jm-1):
        days += jdm[i]
    gy = 400*(days//146097)
    days %= 146097
    if days > 36524:
        gy += 100*((days-1)//36524)
        days = (days-1) % 36524
        if days >= 365:
            days += 1
    gy += 4*(days//1461)
    days %= 1461
    if days > 365:
        gy += (days-1)//365
        days = (days-1) % 365
    gdm = [0,31,29,31,30,31,30,31,31,30,31,30,31]
    gm, gd = 0, days+1
    for i in range(1, 13):
        if gd <= gdm[i]:
            gm = i
            break
        gd -= gdm[i]
    return gy, gm, gd

def days_in_jmonth(jy, jm):
    if jm <= 6: return 31
    if jm <= 11: return 30
    leap = [1,5,9,13,17,22,26,30]
    return 30 if (jy % 33) in leap else 29

def today_jalali():
    from datetime import date
    t = date.today()
    return to_jalali(t.year, t.month, t.day)

def fa(n):
    return str(n).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))

# ── /start ──────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🖤 آره، میام!", callback_data="yes")],
        [InlineKeyboardButton("نه", callback_data="no_0")],
    ]
    await update.message.reply_text(
        "🕷️\n\n"
        "*میای با هم بریم بیرون؟*\n\n"
        "با دقت انتخاب کن…",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return ASK

# ── NO button — regenerates itself with a new callback ──────────
async def no_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("فرار کردم! 😈", show_alert=False)

    count = int(query.data.split("_")[1])
    count += 1

    if count >= 7:
        # vanish — replace No with nothing, just tease
        kb = [
            [InlineKeyboardButton("🖤 آره، میام!", callback_data="yes")],
            [InlineKeyboardButton("نه (ناپدید شد! 👻)", callback_data="gone")],
        ]
        await query.edit_message_text(
            "🕷️\n\n"
            "*میای با هم بریم بیرون؟*\n\n"
            "دکمه نه… فرار کرد 😏",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
    else:
        funny = [
            "نه (سعی کن 😏)",
            "نه (اینجام!)",
            "نه (بازم؟ 😈)",
            "نه… یا آره؟",
            "نه (آخرین بار!)",
            "نه (تقریباً رفتم)",
            "نه…",
        ]
        label = funny[min(count-1, len(funny)-1)]
        kb = [
            [InlineKeyboardButton("🖤 آره، میام!", callback_data="yes")],
            [InlineKeyboardButton(label, callback_data=f"no_{count}")],
        ]
        await query.edit_message_text(
            "🕷️\n\n"
            "*میای با هم بریم بیرون؟*\n\n"
            "با دقت انتخاب کن…",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
    return ASK

async def gone_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("این دکمه دیگه کار نمیکنه 😄", show_alert=True)
    return ASK

# ── YES → pick month ─────────────────────────────────────────────
async def yes_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("یییس! 🖤")
    jy, jm, _ = today_jalali()
    ctx.user_data['jy'] = jy
    ctx.user_data['jm'] = jm
    await send_month_picker(query, ctx, jy, jm)
    return PICK_MONTH

async def send_month_picker(query, ctx, jy, jm):
    jy_d, jm_d, _ = today_jalali()
    rows = []
    # prev/next month nav
    nav = []
    # can go to prev only if not current month
    if (jy, jm) > (jy_d, jm_d):
        pm, py = (jm-1, jy) if jm > 1 else (12, jy-1)
        nav.append(InlineKeyboardButton("◀️", callback_data=f"month_{py}_{pm}"))
    else:
        nav.append(InlineKeyboardButton(" ", callback_data="noop"))
    nav.append(InlineKeyboardButton(f"📅 {J_MONTHS[jm-1]} {fa(jy)}", callback_data="noop"))
    nm, ny = (jm+1, jy) if jm < 12 else (1, jy+1)
    nav.append(InlineKeyboardButton("▶️", callback_data=f"month_{ny}_{nm}"))
    rows.append(nav)

    # day grid — 7 columns
    days = days_in_jmonth(jy, jm)
    row = []
    for d in range(1, days+1):
        # grey out past days
        is_past = (jy, jm, d) < (jy_d, jm_d, _) if (jy, jm) == (jy_d, jm_d) else (jy, jm) < (jy_d, jm_d)
        if is_past:
            row.append(InlineKeyboardButton("·", callback_data="noop"))
        else:
            row.append(InlineKeyboardButton(fa(d), callback_data=f"day_{jy}_{jm}_{d}"))
        if len(row) == 7:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    await query.edit_message_text(
        "🕯️ *یه روز انتخاب کن:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def month_nav(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, py, pm = query.data.split("_")
    await send_month_picker(query, ctx, int(py), int(pm))
    return PICK_MONTH

# ── pick day → pick hour ─────────────────────────────────────────
async def day_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, jy, jm, jd = query.data.split("_")
    ctx.user_data['jy'] = int(jy)
    ctx.user_data['jm'] = int(jm)
    ctx.user_data['jd'] = int(jd)

    # hour picker 8–22
    rows = []
    row = []
    for h in range(8, 23):
        row.append(InlineKeyboardButton(fa(h), callback_data=f"hour_{h}"))
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    jy_i,jm_i,jd_i = int(jy),int(jm),int(jd)
    await query.edit_message_text(
        f"🕰️ *{fa(jd_i)} {J_MONTHS[jm_i-1]} {fa(jy_i)}*\n\nحالا ساعت رو انتخاب کن:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(rows)
    )
    return PICK_HOUR

# ── pick hour → pick minute ──────────────────────────────────────
async def hour_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    h = int(query.data.split("_")[1])
    ctx.user_data['hour'] = h

    kb = [
        [
            InlineKeyboardButton(f"{fa(h)}:۰۰", callback_data="min_0"),
            InlineKeyboardButton(f"{fa(h)}:۳۰", callback_data="min_30"),
        ]
    ]
    jy = ctx.user_data['jy']
    jm = ctx.user_data['jm']
    jd = ctx.user_data['jd']
    await query.edit_message_text(
        f"🕰️ *{fa(jd)} {J_MONTHS[jm-1]} {fa(jy)} — ساعت {fa(h)}*\n\nدقیقه رو انتخاب کن:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return PICK_MIN

# ── pick minute → confirm ────────────────────────────────────────
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

    # show success to her
    await query.edit_message_text(
        "🧛 *قرارمون ثبت شد!*\n\n"
        f"📅 {date_str}\n"
        f"🕰️ ساعت {time_str}\n\n"
        "منتظرتم 🖤🕷️",
        parse_mode="Markdown"
    )

    # notify owner
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

# ── main ─────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK: [
                CallbackQueryHandler(yes_handler,   pattern="^yes$"),
                CallbackQueryHandler(no_handler,    pattern="^no_\\d+$"),
                CallbackQueryHandler(gone_handler,  pattern="^gone$"),
            ],
            PICK_MONTH: [
                CallbackQueryHandler(month_nav,    pattern="^month_"),
                CallbackQueryHandler(day_handler,  pattern="^day_"),
                CallbackQueryHandler(noop,         pattern="^noop$"),
            ],
            PICK_DAY: [
                CallbackQueryHandler(day_handler,  pattern="^day_"),
            ],
            PICK_HOUR: [
                CallbackQueryHandler(hour_handler, pattern="^hour_"),
            ],
            PICK_MIN: [
                CallbackQueryHandler(min_handler,  pattern="^min_"),
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
