import re
import json
import os
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8671810673:AAGKTjNugTeqGHfSHdHQnYkzvqSFmx7ptHg"
OWNER_ID = 5085494476

VIP_CHANNEL = -1003774299026
PUBLIC_CHANNEL = "@imperiumgoldmars"

FOLLOW_LINK = "http://t.me/imperiumgoldmars/16"
WEBHOOK_URL = "https://signal-bot-luyh.onrender.com"

# === 下线群配置 ===
DOWNLINE_PUBLIC = [
    "@testingonlybotgtm",
    "@subtesting1",
    "@subtesting2"
]

DOWNLINE_VIP = [
    -1003972391229,
    -1003725353677
]

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


def parse_signal(text):
    pattern = r"^(B|S)\s+(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s+sl\s+(\d+(?:\.\d+)?)\s+p2\s+(\d+(?:\.\d+)?)$"
    m = re.match(pattern, text.strip(), re.IGNORECASE)

    if not m:
        return None

    direction, e1, e2, sl, p2 = m.groups()

    return {
        "direction": "BUY" if direction.upper() == "B" else "SELL",
        "entry": f"{e1} - {e2}",
        "sl": sl,
        "p2": p2
    }


def build_caption(signal):
    return f"""<b>GOLD {signal['direction']} NOW 🔥</b>

Entry Zone : <b>{signal['entry']}</b>

TP 1 : AS YOU LIKE 🫵🏻
TP 2 : <b>{signal['p2']}</b>

🚫 Stop Loss : {signal['sl']}  (Candle Close)

Way to Follow Signal : <b><a href="{FOLLOW_LINK}">Click</a></b> ‼️

DISCLAIMER ⚠️
Signals are shared for reference only. This is general information, not financial advice. Please decide independently."""


def send_signal(target, signal):
    gif_id = gif_ids["buy"] if signal["direction"] == "BUY" else gif_ids["sell"]

    if not gif_id:
        raise Exception(f"{signal['direction']} GIF 还没设置")

    bot.send_animation(
        target,
        gif_id,
        caption=build_caption(signal),
        parse_mode="HTML"
    )


def make_keyboard(sent_count):
    markup = InlineKeyboardMarkup()

    if sent_count == 0:
        markup.row(
            InlineKeyboardButton("🔓 Public", callback_data="public"),
            InlineKeyboardButton("💎 VIP", callback_data="vip")
        )
        markup.row(
            InlineKeyboardButton("🌍 Both", callback_data="both")
        )

    elif sent_count == 1:
        markup.row(
            InlineKeyboardButton("🔓 Public", callback_data="public"),
            InlineKeyboardButton("💎 VIP", callback_data="vip")
        )
        markup.row(
            InlineKeyboardButton("🌍 Both", callback_data="both"),
            InlineKeyboardButton("✅ Done", callback_data="done")
        )

    else:
        markup.row(
            InlineKeyboardButton("✅ Done", callback_data="done")
        )

    return markup


@bot.message_handler(commands=["start"])
def start(message):
    if message.from_user.id != OWNER_ID:
        return

    bot.send_message(
        message.chat.id,
        "Signal Bot 已启动。\n\n格式：\nB 3333 - 3331 sl 3299 p2 6000\nS 4603 - 4608 sl 4610 p2 4553"
    )


@bot.message_handler(commands=["setbuygif"])
def set_buy_gif(message):
    if message.from_user.id != OWNER_ID:
        return

    pending[message.chat.id] = {"mode": "set_buy"}
    bot.send_message(message.chat.id, "现在发送 Buy GIF 给我。")


@bot.message_handler(commands=["setsellgif"])
def set_sell_gif(message):
    if message.from_user.id != OWNER_ID:
        return

    pending[message.chat.id] = {"mode": "set_sell"}
    bot.send_message(message.chat.id, "现在发送 Sell GIF 给我。")


@bot.message_handler(content_types=["animation", "video", "document"])
def receive_gif(message):
    if message.from_user.id != OWNER_ID:
        return

    state = pending.get(message.chat.id)

    if not state:
        bot.send_message(message.chat.id, "请先输入 /setbuygif 或 /setsellgif")
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
        save_gifs(gif_ids)
        bot.send_message(message.chat.id, "✅ Buy GIF 已保存")

    elif state["mode"] == "set_sell":
        gif_ids["sell"] = file_id
        save_gifs(gif_ids)
        bot.send_message(message.chat.id, "✅ Sell GIF 已保存")

    pending.pop(message.chat.id, None)


@bot.message_handler(func=lambda message: True)
def handle_signal(message):
    if message.from_user.id != OWNER_ID:
        return

    signal = parse_signal(message.text)

    if not signal:
        bot.send_message(
            message.chat.id,
            "格式错误。\n\n正确格式：\nB 3333 - 3331 sl 3299 p2 6000\nS 4603 - 4608 sl 4610 p2 4553"
        )
        return

    pending[message.chat.id] = {
        "mode": "send",
        "signal": signal,
        "sent_count": 0
    }

    bot.send_message(
        message.chat.id,
        "信号已生成，请选择发送范围：\n\n" + build_caption(signal),
        reply_markup=make_keyboard(0),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.from_user.id != OWNER_ID:
        return

    state = pending.get(call.message.chat.id)

    if not state or state.get("mode") != "send":
        bot.answer_callback_query(call.id, "这条信号已结束，请重新输入信号")
        return

    signal = state["signal"]
    sent_count = state["sent_count"]

    if call.data == "done":
        pending.pop(call.message.chat.id, None)
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
        bot.send_message(call.message.chat.id, "✅ 已完成。这条信号已结束。")
        return

    if sent_count >= 2:
        bot.send_message(call.message.chat.id, "⚠️ 已达到最多选择次数，请点击 Done。")
        return

    try:
        if call.data == "public":
            send_signal(PUBLIC_CHANNEL, signal)

            for ch in DOWNLINE_PUBLIC:
                try:
                    send_signal(ch, signal)
                except Exception as e:
                    bot.send_message(call.message.chat.id, f"❌ 下线Public发送失败 {ch}: {e}")

            result_text = "已发送到 Public ✅"

        elif call.data == "vip":
            try:
                send_signal(VIP_CHANNEL, signal)
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ 主VIP发送失败: {e}")

            for ch in DOWNLINE_VIP:
                try:
                    send_signal(ch, signal)
                except Exception as e:
                    bot.send_message(call.message.chat.id, f"❌ 下线VIP发送失败 {ch}: {e}")

            result_text = "已发送到 VIP ✅"

        elif call.data == "both":
            try:
                send_signal(PUBLIC_CHANNEL, signal)
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ 主Public发送失败: {e}")

            try:
                send_signal(VIP_CHANNEL, signal)
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ 主VIP发送失败: {e}")

            for ch in DOWNLINE_PUBLIC:
                try:
                    send_signal(ch, signal)
                except Exception as e:
                    bot.send_message(call.message.chat.id, f"❌ 下线Public发送失败 {ch}: {e}")

            for ch in DOWNLINE_VIP:
                try:
                    send_signal(ch, signal)
                except Exception as e:
                    bot.send_message(call.message.chat.id, f"❌ 下线VIP发送失败 {ch}: {e}")

            result_text = "已发送到 Public + VIP ✅"

        else:
            return

        state["sent_count"] += 1

        if state["sent_count"] >= 2:
            bot.send_message(
                call.message.chat.id,
                result_text + "\n\n已达到最多选择次数，请点击 Done。",
                reply_markup=make_keyboard(2)
            )
        else:
            bot.send_message(
                call.message.chat.id,
                result_text + "\n\n是否还要发送到其他地方？",
                reply_markup=make_keyboard(1)
            )

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ 发送失败：{e}")


@app.route("/", methods=["GET"])
def home():
    return "Signal Bot is running"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200


bot.remove_webhook()
bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")

print("Webhook Signal Bot is running")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
