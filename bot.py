import json
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------- CONFIG ----------
API_ID = 26708304
API_HASH = "d5f0d15f493f36672600111795b49d31"
BOT_TOKEN = "8574149039:AAFVQJmGr13Rua4Oskl6fGsPzprXjdaigBk"

ADMIN_ID = 6186511950
FORCE_CHANNEL = "weoobots"

DUMP_FILE = "dump_channels.json"
INDEX_FILE = "file_index.json"

RESULTS_PER_PAGE = 10

# ---------- BOT ----------
app = Client(
    "ultimate_file_search_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------- UTILS ----------
def load(file, default):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return default

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def human(size):
    for u in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f}{u}"
        size /= 1024

async def is_joined(user_id):
    try:
        member = await app.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ("member", "administrator", "owner")
    except:
        return False

# ---------- FORCE SUB ----------
@app.on_message(filters.private & filters.text)
async def force_sub_check(_, msg):
    if not await is_joined(msg.from_user.id):
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{FORCE_CHANNEL}")]]
        )
        return await msg.reply("🔒 Join channel to use this bot", reply_markup=btn)

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(_, msg):
    # Check force subscribe
    if not await is_joined(msg.from_user.id):
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{FORCE_CHANNEL}")]]
        )
        return await msg.reply(
            "🔒 You must join the channel to use this bot",
            reply_markup=btn
        )

    # Welcome message
    text = (
        f"👋 Hello {msg.from_user.first_name}!\n\n"
        "I am your File Search Bot. Here's how to use me:\n\n"
        "1️⃣ Type the **name of the file/movie/anime** you want to search. Pretty Simple."
    )

    await msg.reply(text)

@app.on_message(filters.command("help") & filters.private)
async def start_cmd(_, msg):
    # Check force subscribe
    if not await is_joined(msg.from_user.id):
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{FORCE_CHANNEL}")]]
        )
        return await msg.reply(
            "🔒 You must join the channel to use this bot",
            reply_markup=btn
        )

    # Welcome message
    text = (
        f"To Get Help Go To @WeooBots Or Dev @Weoo_Weox ⚠️"
    )

    await msg.reply(text)

# ---------- ADMIN ----------
@app.on_message(filters.command("add") & filters.user(ADMIN_ID))
async def add_dump(_, msg):
    try:
        cid = int(msg.text.split()[1])
        await app.get_chat(cid)

        dumps = load(DUMP_FILE, [])
        if cid not in dumps:
            dumps.append(cid)
            save(DUMP_FILE, dumps)
            await msg.reply("✅ Dump channel added")
        else:
            await msg.reply("⚠️ Already added")
    except Exception as e:
        await msg.reply(f"❌ Error\n{e}")

@app.on_message(filters.command("r") & filters.user(ADMIN_ID))
async def remove_dump(_, msg):
    try:
        cid = int(msg.text.split()[1])
        dumps = load(DUMP_FILE, [])
        if cid in dumps:
            dumps.remove(cid)
            save(DUMP_FILE, dumps)

        index = load(INDEX_FILE, [])
        index = [i for i in index if i["channel"] != cid]
        save(INDEX_FILE, index)

        await msg.reply("❌ Dump removed")
    except:
        await msg.reply("Usage: /r -100xxxxxxxxxx")

# ---------- REINDEX ----------
@app.on_message(filters.command("reindex") & filters.user(ADMIN_ID))
async def reindex(_, msg):
    dumps = load(DUMP_FILE, [])
    index = []

    await msg.reply("🔁 Reindexing started...")

    for channel in dumps:
        async for m in app.get_chat_history(channel, limit=1000):
            if m.document:
                index.append({
                    "channel": channel,
                    "msg_id": m.id,
                    "name": m.document.file_name.lower(),
                    "size": m.document.file_size
                })

    save(INDEX_FILE, index)
    await msg.reply(f"✅ Reindex complete ({len(index)} files)")

# ---------- AUTO INDEX ----------
@app.on_message(filters.document)
async def auto_index(_, msg):
    dumps = load(DUMP_FILE, [])
    if msg.chat.id not in dumps:
        return

    index = load(INDEX_FILE, [])
    index.append({
        "channel": msg.chat.id,
        "msg_id": msg.id,
        "name": msg.document.file_name.lower(),
        "size": msg.document.file_size
    })
    save(INDEX_FILE, index)

# ---------- SEARCH ----------
@app.on_message(filters.private & filters.text & ~filters.regex(r"^/"))
async def search(_, msg):
    if not await is_joined(msg.from_user.id):
        return

    query = msg.text.lower().split()
    index = load(INDEX_FILE, [])

    results = []
    seen_names = set()

    for i in reversed(index):
        if all(w in i["name"] for w in query):
            # Deduplicate by filename only (different sizes allowed)
            if i["name"] in seen_names:
                continue
            seen_names.add(i["name"])
            results.append(i)

    if not results:
        return await msg.reply("❌ No results found\n\nRequest Your File To @WeooBots ⚠️")

    await send_page(msg.chat.id, results, 0, msg.text)

async def send_page(chat_id, results, page, query_text):
    start = page * RESULTS_PER_PAGE
    end = start + RESULTS_PER_PAGE
    slice = results[start:end]

    buttons = []
    for i in slice:
        buttons.append([
            InlineKeyboardButton(
                f"{human(i['size'])} | {i['name']}",
                callback_data=f"get|{i['channel']}|{i['msg_id']}"
            )
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅ Prev", callback_data=f"page|{page-1}|{query_text}"))
    if end < len(results):
        nav.append(InlineKeyboardButton("Next ➡", callback_data=f"page|{page+1}|{query_text}"))

    if nav:
        buttons.append(nav)

    await app.send_message(
        chat_id,
        "🔍 Search Results:\n",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------- CALLBACKS ----------
@app.on_callback_query(filters.regex("^page"))
async def change_page(_, cq):
    _, page, query_text = cq.data.split("|", 2)
    page = int(page)
    query = query_text.lower().split()
    index = load(INDEX_FILE, [])

    results = []
    seen_names = set()
    for i in reversed(index):
        if all(w in i["name"] for w in query):
            if i["name"] in seen_names:
                continue
            seen_names.add(i["name"])
            results.append(i)

    await cq.message.delete()
    await send_page(cq.message.chat.id, results, page, query_text)

@app.on_callback_query(filters.regex("^get"))
async def send_file(_, cq):
    _, channel, msg_id = cq.data.split("|")
    channel = int(channel)
    msg_id = int(msg_id)

    m = await app.get_messages(channel, msg_id)

    sent = await app.copy_message(
        chat_id=cq.message.chat.id,
        from_chat_id=channel,
        message_id=msg_id,
        caption=(
            f"📄`{m.document.file_name}`\n\n"
            "📤 Forward this file SomeWhere\n"
            "⏳ File Will Auto delete in 5 minutes"
        )
    )

    await cq.answer("📥 Sent")
    await asyncio.sleep(300)
    await sent.delete()

import threading
from flask import Flask
from pyrogram import Client
import asyncio

app_web = Flask("")

@app_web.route("/")
def home():
    return "Bot is alive"

def run_flask():
    app_web.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()

# Start Pyrogram bot asynchronously
app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def main():
    await app.start()
    print("Bot started")
    await app.idle()

asyncio.run(main())
