import sqlite3
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============ CONFIG ============
TOKEN = "8662384922:AAH6AEptvxIUud8diSOuxGxTDpeJng_Jy8o"
ADMIN_CHAT_ID = 5665625481

CHANNEL_LINKS = {
    1: ["https://t.me/+z0PFr19YOkNiYTM1"],
    2: [
        "https://t.me/+z0PFr19YOkNiYTM1",
        "https://t.me/+c34fsmeIrMBhNTA1",
    ],
    3: [
        "https://t.me/+z0PFr19YOkNiYTM1",
        "https://t.me/+c34fsmeIrMBhNTA1",
        "https://t.me/+_CVibjrnJBQzZmRl",
    ],
    5: [
        "https://t.me/+z0PFr19YOkNiYTM1",
        "https://t.me/+c34fsmeIrMBhNTA1",
        "https://t.me/+_CVibjrnJBQzZmRl",
        "https://t.me/datasciencestudies",
        "https://t.me/phimhayo",
    ],
}

QR_IMAGE = "qr.png"
DB_FILE = "users.db"
# ================================


# ============ DATABASE ============
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    approved INTEGER DEFAULT 0,
    plan INTEGER DEFAULT 0
)
""")
conn.commit()

# Fix old DB (ignore if exists)
try:
    cur.execute("ALTER TABLE users ADD COLUMN plan INTEGER DEFAULT 0")
    conn.commit()
except:
    pass


def add_user(user_id: int):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()


def approve_user(user_id: int, plan: int):
    cur.execute(
        "UPDATE users SET approved = 1, plan = ? WHERE user_id = ?",
        (plan, user_id),
    )
    conn.commit()


def get_user(user_id: int):
    cur.execute("SELECT approved, plan FROM users WHERE user_id = ?", (user_id,))
    return cur.fetchone()


# ============ HANDLERS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    add_user(user_id)

    user = get_user(user_id)

    if user and user[0] == 1:
        plan = user[1]
        links = CHANNEL_LINKS.get(plan)

        if not links:
            await update.message.reply_text("❌ Invalid plan. Contact admin.")
            return

        msg = "✅ Payment Verified!\n\n🔓 Your Group Links:\n"
        for link in links:
            msg += f"{link}\n"

        await update.message.reply_text(msg)
        return

    # User is not approved
    await update.message.reply_text(
        "📢 READ AND UNDERSTAND\n\n"
        "⚡ How it Works:\n"
        "• Select your plan and pay amount\n\n"
        "💳 Choose Your Plan:\n"
        "• ₹10 — 1 Group\n"
        "• ₹15 — 2 Groups\n"
        "• ₹20 — 3 Groups #Popular\n"
        "• ₹30 — 5 Groups #Best\n\n"
        "💰 Please pay using the QR code below.\n"
        "📸 After payment, send screenshot here.\n"
        "⚠️ After approval, type /start again."
    )

    try:
        await update.message.reply_photo(photo=open(QR_IMAGE, "rb"))
    except:
        await update.message.reply_text("❌ QR image not found.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user
    add_user(user.id)

    await update.message.reply_text(
        "✅ Payment screenshot received.\n"
        "⏳ Please wait for admin verification.\n\n"
        "📩 Contact for help: @MsgTo_Help"
    )

    # Forward screenshot to admin
    await context.bot.forward_message(
        chat_id=ADMIN_CHAT_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id,
    )

    # Notify admin
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            "💳 New Payment Proof Received\n\n"
            f"👤 User ID: {user.id}\n"
            f"👤 Username: @{user.username or 'No username'}\n\n"
            "Approve using:\n"
            "/approve USER_ID PLAN\n\n"
            "Approve with:\n"
            f"/approve {user.id} 1\n"
            f"/approve {user.id} 2\n"
            f"/approve {user.id} 3\n"
            f"/approve {user.id} 5"
        )
    )


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Only admin can approve
    if update.message.chat_id != ADMIN_CHAT_ID:
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /approve USER_ID PLAN")
        return

    user_id = int(context.args[0])
    plan = int(context.args[1])

    if plan not in [1, 2, 3, 5]:
        await update.message.reply_text("❌ Invalid plan (use 1,2,3,5)")
        return

    approve_user(user_id, plan)

    await update.message.reply_text(
        f"✅ User {user_id} approved for {plan} channel(s).\n"
        "Tell user to type /start."
    )


# ============ MAIN ============
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
