from quart import Quart, request
import redis.asyncio as redis
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import asyncio

# --- Bot config ---
BOT_TOKEN = "7343823130:AAFE4FbY_BZGb4Jdx_FsITLKDi8zv09IEh8"
REDIS_URL = "rediss://default:AaqBAAIjcDFlMTc1MzViMjczZWM0YjU1OTlmMmVjZGY3ZGNlODA2ZXAxMA@growing-squirrel-43649.upstash.io:6379"

# --- Initialize Quart app ---
quart_app = Quart(__name__)

# --- Redis client (async) ---
r = redis.from_url(REDIS_URL, decode_responses=True)

# --- Telegram Application ---
application = Application.builder().token(BOT_TOKEN).build()

# --- Handler for channel posts ---
async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post:
        channel_id = update.channel_post.chat_id
        message_id = update.channel_post.message_id
        timestamp = update.channel_post.date.timestamp()

        last_timestamp = await r.get("last_post_time")
        if last_timestamp:
            last_time = float(last_timestamp)
            # Agar pichla post 10 minute (600s) ke andar ho, to delete karo naya post
            if timestamp - last_time <= 600:
                try:
                    await context.bot.delete_message(chat_id=channel_id, message_id=message_id)
                    print(f"Deleted message {message_id} in channel {channel_id}")
                except Exception as e:
                    print(f"Failed to delete message: {e}")

        await r.set("last_post_time", timestamp)

# --- Add handler ---
application.add_handler(MessageHandler(filters.ALL & filters.ChatType.CHANNEL, handle_channel_post))

# --- Initialize bot (to be called once at startup) ---
async def startup():
    await application.initialize()

asyncio.get_event_loop().run_until_complete(startup())

# --- Webhook route for Telegram updates ---
@quart_app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    data = await request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return "ok", 200

# --- Home route for health check ---
@quart_app.route("/")
async def home():
    return "Bot is running!", 200

# --- Main entrypoint ---
if __name__ == "__main__":
    import hypercorn.asyncio
    import asyncio

    config = hypercorn.Config()
    config.bind = ["0.0.0.0:10000"]
    asyncio.run(hypercorn.asyncio.serve(quart_app, config))