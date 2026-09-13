import asyncio
import html
import logging
import os
from datetime import datetime

import feedparser
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")

# News RSS feeds
RSS_FEEDS = {
    "English": [
        "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    ],
    "Hindi": [
        "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi",
    ],
    "Urdu": [
        "https://news.google.com/rss?hl=ur&gl=IN&ceid=IN:ur",
    ],
}

# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# =========================
# NEWS FUNCTIONS
# =========================

def get_news(language="English", limit=10):
    """Fetch latest news from RSS."""
    articles = []

    feeds = RSS_FEEDS.get(language, RSS_FEEDS["English"])

    for url in feeds:
        try:
            feed = feedparser.parse(url)

            for entry in feed.entries[:limit]:
                title = entry.get("title", "No title")
                link = entry.get("link", "")

                if title and link:
                    articles.append({
                        "title": title,
                        "link": link,
                    })

        except Exception as e:
            logging.error(f"RSS error: {e}")

    return articles[:limit]


def make_news_text(language):
    news = get_news(language)

    if not news:
        return "❌ Abhi news fetch nahi ho pa rahi. Thodi der baad try karein."

    emoji = {
        "English": "🇬🇧",
        "Hindi": "🇮🇳",
        "Urdu": "🇵🇰",
        "Hinglish": "🔤",
    }.get(language, "📰")

    text = f"{emoji} <b>Latest {html.escape(language)} News</b>\n"
    text += f"🕐 {datetime.now().strftime('%d-%m-%Y %I:%M %p')}\n\n"

    for i, article in enumerate(news, 1):
        title = html.escape(article["title"])
        link = article["link"]

        text += f"{i}. <a href=\"{link}\">{title}</a>\n\n"

    text += "📰 <i>News automatically RSS sources se fetch ki gayi hai.</i>"

    return text


# =========================
# KEYBOARD
# =========================

def language_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="English"),
            InlineKeyboardButton("🇮🇳 Hindi", callback_data="Hindi"),
        ],
        [
            InlineKeyboardButton("🇵🇰 Urdu", callback_data="Urdu"),
            InlineKeyboardButton("🔤 Hinglish", callback_data="Hinglish"),
        ],
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "📰 <b>Welcome to All India News Bot!</b>\n\n"
        "Yahan aap latest news dekh sakte hain:\n\n"
        "🇮🇳 India News\n"
        "🏛 States & UTs\n"
        "🌍 World News\n"
        "💻 Technology\n"
        "🏏 Sports\n"
        "💼 Business\n\n"
        "Language select karein 👇"
    )

    await update.message.reply_text(
        welcome,
        parse_mode="HTML",
        reply_markup=language_keyboard(),
    )


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        make_news_text("English"),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=language_keyboard(),
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data

    if choice == "refresh":
        # Refresh using currently selected/default language
        text = make_news_text("English")
    elif choice == "Hinglish":
        # Hinglish is approximated using English news titles.
        text = make_news_text("English")
        text = "🔤 <b>Hinglish News</b>\n\n" + text
    else:
        text = make_news_text(choice)

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=language_keyboard(),
    )


# =========================
# DAILY AUTO NEWS
# =========================

async def daily_news(context: ContextTypes.DEFAULT_TYPE):
    """Send daily news to users who started the bot."""
    users = context.application.bot_data.get("users", set())

    if not users:
        return

    text = make_news_text("English")

    for user_id in list(users):
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except Exception as e:
            logging.error(f"Could not send news to {user_id}: {e}")


async def save_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        users = context.application.bot_data.setdefault("users", set())
        users.add(update.effective_user.id)


# =========================
# MAIN
# =========================

def main():
    if BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
        print("❌ Please add your Telegram Bot Token.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", news_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Save users whenever they send a command/message handled here
    application.add_handler(
        CommandHandler("subscribe", save_user)
    )

    # Daily news at 9:00 AM server time
    application.job_queue.run_daily(
        daily_news,
        time=datetime.strptime("09:00", "%H:%M").time(),
    )

    print("✅ News Bot is running...")

    application.run_polling()


if __name__ == "__main__":
    main()
