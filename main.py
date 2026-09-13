import os
import logging
import feedparser

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")

RSS_FEEDS = {
    "English": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    "Hindi": "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi",
    "Urdu": "https://news.google.com/rss?hl=ur&gl=IN&ceid=IN:ur",
}

logging.basicConfig(level=logging.INFO)


def get_news(language="English", limit=10):
    feed = feedparser.parse(RSS_FEEDS[language])
    news = []

    for item in feed.entries[:limit]:
        title = item.get("title", "No title")
        link = item.get("link", "")

        # RSS media image
        image = None

        if hasattr(item, "media_content"):
            media = item.media_content
            if media:
                image = media[0].get("url")

        if not image and hasattr(item, "media_thumbnail"):
            thumb = item.media_thumbnail
            if thumb:
                image = thumb[0].get("url")

        news.append({
            "title": title,
            "link": link,
            "image": image
        })

    return news


def keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="English"),
            InlineKeyboardButton("🇮🇳 Hindi", callback_data="Hindi"),
        ],
        [
            InlineKeyboardButton("🇵🇰 Urdu", callback_data="Urdu"),
            InlineKeyboardButton("🔤 Hinglish", callback_data="Hinglish"),
        ],
    ])


async def send_news(chat_id, context, language="English"):
    news = get_news(language)

    if not news:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ News abhi available nahi hai."
        )
        return

    for item in news:
        title = item["title"]
        link = item["link"]
        image = item["image"]

        caption = (
            f"📰 <b>{title}</b>\n\n"
            f"🔗 <a href='{link}'>Read Full News</a>\n\n"
            f"📢 Faizan News Hub"
        )

        try:
            if image:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=image,
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    parse_mode="HTML"
                )

        except Exception as e:
            logging.error(f"Photo error: {e}")

            await context.bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode="HTML"
            )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📰 <b>FAIZAN NEWS HUB</b>\n\n"
        "Daily latest news ke liye language select karein 👇",
        parse_mode="HTML",
        reply_markup=keyboard()
    )


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_news(update.effective_chat.id, context, "English")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    language = query.data

    # Hinglish ke liye English feed
    if language == "Hinglish":
        language = "English"

    await query.message.reply_text(
        f"⏳ <b>{query.data} news loading...</b>",
        parse_mode="HTML"
    )

    await send_news(
        query.message.chat_id,
        context,
        language
    )


def main():
    if BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
        print("❌ BOT_TOKEN add karo.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ FAIZAN NEWS HUB BOT RUNNING...")

    app.run_polling()


if __name__ == "__main__":
    main()
