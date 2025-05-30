from quart import Quart, request
import redis
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import asyncio

quart_app = Quart(__name__)

# --- ENVIRONMENT VALUES (Yahan apne token aur redis url bharna) ---
BOT_TOKEN = "7343823130:AAFE4FbY_BZGb4Jdx_FsITLKDi8zv09IEh8"
REDIS_URL = "rediss://default:AaqBAAIjcDFlMTc1MzViMjczZWM0YjU1OTlmMmVjZGY3ZGNlODA2ZXAxMA@growing-squirrel-43649.upstash.io:6379"

# --- REDIS CLIENT ---
r = redis.from_url(REDIS_URL, decode_responses=True)

# --- TELEGRAM APPLICATION ---
application = Application.builder().token(BOT_TOKEN).build()
application_ready = False

# --- CHANNEL POST HANDLER ---
async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post:
        channel_id = update.channel_post.chat_id
        message_id = update.channel_post.message_id
        timestamp = update.channel_post.date.timestamp()

        last_timestamp = r.get("last_post_time")
        if last_timestamp:
            last_time = float(last_timestamp)
            if timestamp - last_time <= 600:  # 10 minutes = 600 seconds
                try:
                    await context.bot.delete_message(chat_id=channel_id, message_id=message_id)
                    print(f"Deleted message {message_id} in channel {channel_id}")
                except Exception as e:
                    print(f"Failed to delete message: {e}")

        r.set("last_post_time", timestamp)

# --- ADD HANDLER TO APPLICATION ---
application.add_handler(MessageHandler(filters.ALL & filters.ChatType.CHANNEL, handle_channel_post))

# --- INITIALIZE TELEGRAM APPLICATION ON STARTUP ---
async def initialize_app():
    global application_ready
    if not application_ready:
        await application.initialize()
        application_ready = True

# Initialize the application on startup
asyncio.get_event_loop().run_until_complete(initialize_app())

# --- WEBHOOK ROUTE ---
@quart_app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    json_update = await request.get_json(force=True)
    update = Update.de_json(json_update, application.bot)
    await application.process_update(update)
    return "ok", 200

# --- HOME ROUTE ---
@quart_app.route("/")
async def home():
    return "Bot is running!", 200


if __name__ == "__main__":
    import hypercorn.asyncio
    import asyncio

    # Hypercorn config
    config = hypercorn.Config()
    config.bind = ["0.0.0.0:10000"]

    asyncio.run(hypercorn.asyncio.serve(quart_app, config))
