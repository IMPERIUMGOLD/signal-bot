import re, json, os
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
pending = {}

@bot.message_handler(commands=["setbuygif"])
def set_buy(message):
    if message.from_user.id != OWNER_ID:
        return
    pending[message.chat.id] = {"mode": "buy"}
    bot.send_message(message.chat.id, "发送 BUY GIF 给我")

@bot.message_handler(commands=["setsellgif"])
def set_sell(message):
    if message.from_user.id != OWNER_ID:
        return
    pending[message.chat.id] = {"mode": "sell"}
    bot.send_message(message.chat.id, "发送 SELL GIF 给我")

@bot.message_handler(content_types=["animation", "video", "document"])
def get_file_id(message):
    if message.from_user.id != OWNER_ID:
        return

    state = pending.get(message.chat.id)
    if not state:
        return

    file_id = None
    if message.animation:
        file_id = message.animation.file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id

    if not file_id:
        bot.send_message(message.chat.id, "❌ 没抓到 file_id")
        return

    if state["mode"] == "buy":
        bot.send_message(message.chat.id, f"BUY_GIF_ID = \"{file_id}\"")
    elif state["mode"] == "sell":
        bot.send_message(message.chat.id, f"SELL_GIF_ID = \"{file_id}\"")

    pending.pop(message.chat.id, None)

@app.route("/", methods=["GET"])
def home():
    return "OK"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

bot.remove_webhook()
bot.set_webhook(url=f"https://signal-bot-luyh.onrender.com/{BOT_TOKEN}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
