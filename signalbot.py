import re, json, os
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))

VIP_CHANNEL = -1003774299026
PUBLIC_CHANNEL = "@imperiumgoldmars"

FOLLOW_LINK = "http://t.me/imperiumgoldmars/16"
WEBHOOK_URL = "https://signal-bot-luyh.onrender.com"

# ===== 下线分组 =====
SUB1_TARGETS = [
    "@subtesting1",
    -1003972391229
]

SUB2_TARGETS = [
    "@subtesting2",
    -1003725353677
]

# ===== SL 调整（以后你改这里就行）=====
SL_OFFSET = 2

GIF_FILE = "gif_ids.json"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
pending = {}

def load_gifs():
    if os.path.exists(GIF_FILE):
        with open(GIF_FILE, "r") as f:
            return json.load(f)
    return {"buy": None, "sell": None}

def save_gifs(data):
    with open(GIF_FILE, "w") as f:
        json.dump(data, f)

gif_ids = load_gifs()

# ===== 解析信号 =====
def parse_signal(text):
    pattern = r"^(B|S)\s+(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s+sl\s+(\d+(?:\.\d+)?)\s+p2\s+(\d+(?:\.\d+)?)$"
    m = re.match(pattern, text.strip(), re.IGNORECASE)
    if not m:
        return None
    direction, e1, e2, sl, p2 = m.groups()
    return {
        "direction": "BUY" if direction.upper()=="B" else "SELL",
        "entry": f"{e1} - {e2}",
        "sl": int(float(sl)),
        "p2": p2
    }

# ===== 主群模板 =====
def build_brand_caption(signal):
    emoji = "📈" if signal["direction"]=="BUY" else "📉"
    return f"""<b>{emoji} GOLD {signal['direction']} NOW 🔥</b>

Entry Zone : <b>{signal['entry']}</b>

TP 1 : AS YOU LIKE 🫵🏻
TP 2 : <b>{signal['p2']}</b>

🚫 Stop Loss : {signal['sl']}  (Candle Close)

Way to Follow Signal : <b><a href="{FOLLOW_LINK}">Click</a></b> ‼️

DISCLAIMER ⚠️
Signals are shared for reference only. This is general information, not financial advice. Please decide independently."""

# ===== Sub1 =====
def build_sub1(signal):
    return f"""<b>XAUUSD {signal['direction']} : {signal['entry']}</b>

<b>TP 1 : 50pips</b>
<b>TP 2 : {signal['p2']}</b>

<b>Stop Loss : {signal['sl']}</b> (Candle Close)"""

# ===== Sub2 =====
def build_sub2(signal):
    if signal["direction"]=="BUY":
        sl = signal["sl"] - SL_OFFSET
        emoji = "📈"
        text = "Gold Buy Now"
    else:
        sl = signal["sl"] + SL_OFFSET
        emoji = "📉"
        text = "Gold Sell Now"

    return f"""<b>{emoji} {text}</b>

<b>Price : {signal['entry']}</b>

<b>Take Profit : OPEN ✔️</b>

<b>Stop Loss : {sl} ‼️</b>"""

# ===== AYD =====
def ayd_main():
    return "<b>ARE YOU READY?</b> 🔥🔥🔥"

def ayd_sub1():
    return "<b>Are You Ready ?</b>"

def ayd_sub2():
    return "<b>Are You Ready Everyone!!</b>"

# ===== 发送 =====
def send_brand(target, signal):
    gif = gif_ids["buy"] if signal["direction"]=="BUY" else gif_ids["sell"]
    bot.send_animation(target, gif, caption=build_brand_caption(signal), parse_mode="HTML")

def send_text(target, text):
    bot.send_message(target, text, parse_mode="HTML")

# ===== 按钮 =====
def make_keyboard():
    m = InlineKeyboardMarkup()
    m.row(
        InlineKeyboardButton("🔓 Public", callback_data="public"),
        InlineKeyboardButton("💎 VIP", callback_data="vip")
    )
    m.row(InlineKeyboardButton("🌍 Both", callback_data="both"))
    return m

# ===== 主处理 =====
@bot.message_handler(func=lambda m: True)
def handle(message):
    if message.from_user.id != OWNER_ID:
        return

    text = message.text.lower()

    if text == "ayd":
        pending[message.chat.id] = {"mode":"ayd"}
        bot.send_message(message.chat.id, "选择发送范围", reply_markup=make_keyboard())
        return

    signal = parse_signal(message.text)
    if not signal:
        return

    pending[message.chat.id] = {"mode":"signal","signal":signal}
    bot.send_message(message.chat.id, "选择发送范围", reply_markup=make_keyboard())

# ===== callback =====
@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    state = pending.get(call.message.chat.id)
    if not state:
        return

    mode = state["mode"]

    if mode=="ayd":
        if call.data in ["public","both"]:
            send_text(PUBLIC_CHANNEL, ayd_main())
        if call.data in ["vip","both"]:
            send_text(VIP_CHANNEL, ayd_main())

        for ch in SUB1_TARGETS:
            send_text(ch, ayd_sub1())
        for ch in SUB2_TARGETS:
            send_text(ch, ayd_sub2())

    else:
        s = state["signal"]

        if call.data in ["public","both"]:
            send_brand(PUBLIC_CHANNEL, s)
        if call.data in ["vip","both"]:
            send_brand(VIP_CHANNEL, s)

        for ch in SUB1_TARGETS:
            send_text(ch, build_sub1(s))
        for ch in SUB2_TARGETS:
            send_text(ch, build_sub2(s))

@app.route("/", methods=["GET"])
def home():
    return "OK"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

bot.remove_webhook()
bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
