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

SUB1_TARGETS = ["@subtesting1", -1003972391229]
SUB2_TARGETS = ["@subtesting2", -1003725353677]

SL_OFFSET = 2

DEFAULT_BUY_GIF_ID = "CgACAgUAAxkBAAPbafXH0UoP44CJLDuZ03L6Ni-lg_UAAkIfAAJ1VbBXF9hQC2hZVUE7BA"
DEFAULT_SELL_GIF_ID = "CgACAgUAAxkBAAPfafXH4BVJwHv6GYLwxRMPydPF0V8AAkMfAAJ1VbBXs-MsWvctzps7BA"

GIF_FILE = "gif_ids.json"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
pending = {}


def load_gifs():
    if os.path.exists(GIF_FILE):
        with open(GIF_FILE, "r") as f:
            return json.load(f)
    return {"buy": None, "sell": None}


def save_gifs():
    with open(GIF_FILE, "w") as f:
        json.dump(gif_ids, f)


gif_ids = load_gifs()


def parse_signal(text):
    pattern = r"^(B|S)\s+(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s+sl\s+(\d+(?:\.\d+)?)\s+p2\s+(\d+(?:\.\d+)?)$"
    m = re.match(pattern, text.strip(), re.IGNORECASE)
    if not m:
        return None

    direction, e1, e2, sl, p2 = m.groups()
    return {
        "direction": "BUY" if direction.upper() == "B" else "SELL",
        "entry": f"{e1} - {e2}",
        "sl": int(float(sl)),
        "p2": p2
    }


def build_brand(signal):
    emoji = "📈" if signal["direction"] == "BUY" else "📉"
    return f"""<b>{emoji} GOLD {signal['direction']} NOW 🔥</b>

Entry Zone : <b>{signal['entry']}</b>

TP 1 : AS YOU LIKE 🫵🏻
TP 2 : <b>{signal['p2']}</b>

🚫 Stop Loss : {signal['sl']}  (Candle Close)

Way to Follow Signal : <b><a href="{FOLLOW_LINK}">Click</a></b> ‼️

DISCLAIMER ⚠️
Signals are shared for reference only. This is general information, not financial advice. Please decide independently."""


def build_sub1(signal):
    return f"""<b>XAUUSD {signal['direction']} : {signal['entry']}</b>

<b>TP 1 : 50pips</b>
<b>TP 2 : {signal['p2']}</b>

<b>Stop Loss : {signal['sl']}</b> (M1 break)"""


def build_sub2(signal):
    if signal["direction"] == "BUY":
        sl = signal["sl"] - SL_OFFSET
        emoji = "📈"
        title = "Gold Buy Now"
    else:
        sl = signal["sl"] + SL_OFFSET
        emoji = "📉"
        title = "Gold Sell Now"

    return f"""<b>{emoji} {title}</b>

<b>Price : {signal['entry']}</b>

<b>Take Profit : OPEN ✔️</b>

<b>Stop Loss : {sl} ‼️</b>"""


def ayd_main():
    return "<b>ARE YOU READY?</b> 🔥🔥🔥"


def ayd_sub1():
    return "<b>Are You Ready ?</b>"


def ayd_sub2():
    return "<b>Are You Ready Everyone!!</b>"


def keyboard():
    m = InlineKeyboardMarkup()
    m.row(
        InlineKeyboardButton("🔓 Public", callback_data="public"),
        InlineKeyboardButton("💎 VIP", callback_data="vip")
    )
    m.row(InlineKeyboardButton("🌍 Both", callback_data="both"))
    return m


def get_gif_id(direction):
    if direction == "BUY":
        return gif_ids.get("buy") or DEFAULT_BUY_GIF_ID
    return gif_ids.get("sell") or DEFAULT_SELL_GIF_ID


def send_brand(target, signal):
    gif = get_gif_id(signal["direction"])

    bot.send_animation(
        target,
        gif,
        caption=build_brand(signal),
        parse_mode="HTML"
    )


def send_text(target, text):
    bot.send_message(target, text, parse_mode="HTML", disable_web_page_preview=True)


@bot.message_handler(commands=["start"])
def start(message):
    if message.from_user.id != OWNER_ID:
        return

    bot.send_message(
        message.chat.id,
        "Signal Bot 已启动。\n\n格式：\nB 3333 - 3331 sl 3299 p2 6000\nS 4603 - 4608 sl 4610 p2 4553\n\nAYD：\nayd"
    )


@bot.message_handler(commands=["setbuygif"])
def set_buy_gif(message):
    if message.from_user.id != OWNER_ID:
        return

    pending[message.chat.id] = {"mode": "set_buy"}
    bot.send_message(message.chat.id, "现在发送 BUY GIF 给我。")


@bot.message_handler(commands=["setsellgif"])
def set_sell_gif(message):
    if message.from_user.id != OWNER_ID:
        return

    pending[message.chat.id] = {"mode": "set_sell"}
    bot.send_message(message.chat.id, "现在发送 SELL GIF 给我。")


@bot.message_handler(content_types=["animation", "video", "document"])
def save_gif(message):
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
        bot.send_message(message.chat.id, "❌ 没有读取到 GIF file_id")
        return

    if state["mode"] == "set_buy":
        gif_ids["buy"] = file_id
        save_gifs()
        bot.send_message(message.chat.id, "✅ BUY GIF 已保存")

    elif state["mode"] == "set_sell":
        gif_ids["sell"] = file_id
        save_gifs()
        bot.send_message(message.chat.id, "✅ SELL GIF 已保存")

    pending.pop(message.chat.id, None)


@bot.message_handler(func=lambda m: True)
def handle(message):
    if message.from_user.id != OWNER_ID:
        return

    text = message.text.strip().lower()

    if text == "ayd":
        pending[message.chat.id] = {"mode": "ayd"}

        bot.send_message(
            message.chat.id,
            "AYD 已生成，请选择发送范围：\n\n" + ayd_main(),
            reply_markup=keyboard(),
            parse_mode="HTML"
        )
        return

    signal = parse_signal(message.text)

    if not signal:
        bot.send_message(
            message.chat.id,
            "格式错误。\n\n正确格式：\nB 3333 - 3331 sl 3299 p2 6000\nS 4603 - 4608 sl 4610 p2 4553"
        )
        return

    pending[message.chat.id] = {
        "mode": "signal",
        "signal": signal
    }

    bot.send_message(
        message.chat.id,
        "信号已生成，请选择发送范围：\n\n" + build_brand(signal),
        reply_markup=keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    bot.answer_callback_query(call.id)

    if call.from_user.id != OWNER_ID:
        return

    state = pending.get(call.message.chat.id)
    if not state:
        bot.send_message(call.message.chat.id, "这条指令已结束，请重新输入。")
        return

    mode = state["mode"]

    try:
        if mode == "ayd":
            if call.data == "public":
                send_text(PUBLIC_CHANNEL, ayd_main())

                for ch in SUB1_TARGETS:
                    if isinstance(ch, str):
                        send_text(ch, ayd_sub1())

                for ch in SUB2_TARGETS:
                    if isinstance(ch, str):
                        send_text(ch, ayd_sub2())

                bot.send_message(call.message.chat.id, "AYD 已发送到 Public ✅")

            elif call.data == "vip":
                send_text(VIP_CHANNEL, ayd_main())

                for ch in SUB1_TARGETS:
                    if isinstance(ch, int):
                        send_text(ch, ayd_sub1())

                for ch in SUB2_TARGETS:
                    if isinstance(ch, int):
                        send_text(ch, ayd_sub2())

                bot.send_message(call.message.chat.id, "AYD 已发送到 VIP ✅")

            elif call.data == "both":
                send_text(PUBLIC_CHANNEL, ayd_main())
                send_text(VIP_CHANNEL, ayd_main())

                for ch in SUB1_TARGETS:
                    send_text(ch, ayd_sub1())

                for ch in SUB2_TARGETS:
                    send_text(ch, ayd_sub2())

                bot.send_message(call.message.chat.id, "AYD 已发送到 Public + VIP ✅")

        elif mode == "signal":
            s = state["signal"]

            if call.data == "public":
                send_brand(PUBLIC_CHANNEL, s)

                for ch in SUB1_TARGETS:
                    if isinstance(ch, str):
                        send_text(ch, build_sub1(s))

                for ch in SUB2_TARGETS:
                    if isinstance(ch, str):
                        send_text(ch, build_sub2(s))

                bot.send_message(call.message.chat.id, "信号已发送到 Public ✅")

            elif call.data == "vip":
                send_brand(VIP_CHANNEL, s)

                for ch in SUB1_TARGETS:
                    if isinstance(ch, int):
                        send_text(ch, build_sub1(s))

                for ch in SUB2_TARGETS:
                    if isinstance(ch, int):
                        send_text(ch, build_sub2(s))

                bot.send_message(call.message.chat.id, "信号已发送到 VIP ✅")

            elif call.data == "both":
                send_brand(PUBLIC_CHANNEL, s)
                send_brand(VIP_CHANNEL, s)

                for ch in SUB1_TARGETS:
                    send_text(ch, build_sub1(s))

                for ch in SUB2_TARGETS:
                    send_text(ch, build_sub2(s))

                bot.send_message(call.message.chat.id, "信号已发送到 Public + VIP ✅")

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ 发送失败：{e}")


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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
