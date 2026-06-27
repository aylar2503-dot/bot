import os
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, Update
​
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "my-secret-key")
PORT = int(os.getenv("PORT", 10000))
HOST = "0.0.0.0"
WEBHOOK_PATH = f"/webhook/{WEBHOOK_SECRET}"
router = Router()
@router.message(CommandStart())
async def start_command(message: Message):
await message.answer("Привет! Бот работает через webhook ")
@router.message()
async def echo_message(message: Message):
await message.answer(f"Ты написал: {message.text}")
async def handle_webhook(request: web.Request):
bot: Bot = request.app["bot"]
dispatcher: Dispatcher = request.app["dispatcher"]
secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
if secret_token != WEBHOOK_SECRET:
return web.Response(status=403, text="Forbidden")
data = await request.json()
update = Update.model_validate(data, context={"bot": bot})
await dispatcher.feed_update(bot, update)
return web.Response(text="OK")
async def health_check(request: web.Request):
return web.Response(text="Bot is running")
async def on_startup(app: web.Application):
bot: Bot = app["bot"]
if not WEBHOOK_URL:
logging.warning("WEBHOOK_URL is not set. Webhook was not configured.")
return
webhook_full_url = WEBHOOK_URL + WEBHOOK_PATH
await bot.set_webhook(
url=webhook_full_url,
secret_token=WEBHOOK_SECRET,
)
logging.info(f"Webhook set to: {webhook_full_url}")
async def on_shutdown(app: web.Application):
bot: Bot = app["bot"]
await bot.session.close()
def main():
if not BOT_TOKEN:
raise RuntimeError("BOT_TOKEN environment variable is not set")
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher()
dispatcher.include_router(router)
app = web.Application()
app["bot"] = bot
app["dispatcher"] = dispatcher
app.router.add_get("/", health_check)
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
web.run_app(app, host=HOST, port=PORT)
if name == "main":
main()
