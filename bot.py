import os
import redis
import asyncio
from quart import Quart, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Environment variables se token aur redis url le rahe hain
BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")

# Redis client initialize karo
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Quart app create karo
quart_app = Quart(__name__)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Main tumhara Telegram Quart bot hoon.")

# Echo handler - jo bhi message aata hai, wahi reply karta hai
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_received = update.message.text
    await update.message.reply_text(f"Aapne yeh likha: {text_received}")

# Telegram bot setup function
async def setup_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    return app

# Webhook route - Telegram se updates receive karne ke liye
@quart_app.route('/webhook', methods=['POST'])
async def webhook():
    data = await request.get_json(force=True)
    app = await setup_bot()
    update = Update.de_json(data, app.bot)
    await app.update_queue.put(update)
    return "OK"

if __name__ == '__main__':
    import hypercorn.asyncio
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:10000"]

    asyncio.run(hypercorn.asyncio.serve(quart_app, config))
