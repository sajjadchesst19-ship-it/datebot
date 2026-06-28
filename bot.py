import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)

logging.basicConfig(level=logging.INFO)

TOKEN = "8873174346:AAF3HJgDHjm_5oWOb5HGE0uBUSeMzgOr9L4"
OWNER_CHAT_ID = 107774980

ASK, GET_DATE, GET_TIME = range(3)

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

async def no_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("فرار کردم! 😈")
    count = int(query.data.split("_")[1]) + 1

    if count >= 7:
        kb = [
            [InlineKeyboardButton("🖤 آره، میام!", callback_data="yes")],
            [InlineKeyboardButton("👻 ناپدید شد!", callback_data="gone")],
        ]
        await query.edit_message_text(
            "🕷️\n\n*میای با هم بریم بیرون؟*\n\nدکمه نه فرار کرد 😏",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
    else:
        labels = [
            "نه — یه بار دیگه فکر کن",
            "نه — به نظر مطمئن نمیای",
            "نه — بیخیال دیگه",
            "نه… یا آره؟",
            "نه (آخرین بار!)",
            "نه (تقریباً رفتم)",
        ]
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

async def yes_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("یییس! 🖤")
    await query.edit_message_text(
        "🕯️ *عالیه!*\n\nچه روزی برات خوبه؟",
        parse_mode="Markdown"
    )
    return GET_DATE

async def get_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['date'] = update.message.text.strip()
    await update.message.reply_text(
        "🕰️ چه ساعتی؟",
        parse_mode="Markdown"
    )
    return GET_TIME

async def get_time(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    date_str = ctx.user_data.get('date', '؟')
    time_str = update.message.text.strip()
    user = update.effective_user
    name = user.first_name or "اون"

    await update.message.reply_text(
        "🖤 *عالی، برنامه‌مون هماهنگ شد.*\n\n"
        f"📅 {date_str}\n"
        f"🕰️ {time_str}\n\n"
        "منتظرتم 🕷️",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

    await update.get_bot().send_message(
        chat_id=OWNER_CHAT_ID,
        text=(
            "🕷️ *قرار تایید شد!*\n\n"
            f"👤 {name} قبول کرد!\n"
            f"📅 روز: {date_str}\n"
            f"🕰️ ساعت: {time_str}\n\n"
            "برو آماده بشو 😏🖤"
        ),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

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
            GET_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_date),
            ],
            GET_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_time),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )
    app.add_handler(conv)
    print("🕷️ Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
