from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
import re
import asyncio

# 👉 Bot token
TOKEN = "8179270567:AAGFEE7rhu0sWdT8aKOm1yRhJqFOaPSj1yk"

# Kurallar
RULES_TEXT = """📌 KURALLAR 📌

🚨 REKLAM YAPMAK !
🚨 LİNK PAYLAŞMAK !
🚨 DİN, IRK, SİYASET VE AYRIMCILIK YAPMAK !
🚨 ÖZELDEN RAHATSIZ ETMEK !

⛔ KESİNLİKLE YASAKTIR VE KURALLARA UYMAYANLAR BANLANACAKTIR.
"""

URL_REGEX = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)

# Admin kontrol
async def is_user_admin(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif ✅ Gruba ekleyip admin yapmayı unutma.")

# /ping
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pong! ✅ Bot çalışıyor.")

# Yeni üye geldiğinde hoş geldin ve kurallar
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Hoş geldin {member.mention_html()}! Umarım iyi vakit geçirirsin.\n\n{RULES_TEXT}",
            parse_mode="HTML",
        )

# Mesaj kontrol: reklam/link varsa sil
async def check_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    text = msg.text or msg.caption or ""
    user = update.effective_user
    if not user or user.is_bot:
        return
    if URL_REGEX.search(text) or "reklam" in text.lower():
        try:
            await msg.delete()
        except:
            pass
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️ {user.mention_html()} link/reklam paylaşmak yasak!",
            parse_mode="HTML",
        )

# /ban komutu (reply veya @username)
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    sender = update.effective_user
    bot = context.bot

    if not await is_user_admin(chat.id, sender.id, context):
        await update.message.reply_text("⚠️ Bu komutu sadece yöneticiler kullanabilir.")
        return

    target_user_id = None
    target_username = None

    # Reply ile
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_user_id = target_user.id
        target_username = target_user.username
    # @username ile
    elif context.args:
        arg = context.args[0]
        if arg.startswith("@"):
            try:
                resolved = await bot.get_chat(arg)
                target_user_id = resolved.id
                target_username = resolved.username
            except Exception as e:
                await update.message.reply_text(f"❌ Kullanıcı bulunamadı: {e}")
                return
        else:
            try:
                target_user_id = int(arg)
            except ValueError:
                await update.message.reply_text("Kullanıcı belirtilmedi veya geçersiz.")
                return
    else:
        await update.message.reply_text("Kullanıcı belirtmelisin: /ban @kullanici veya mesaj reply.")
        return

    try:
        if await is_user_admin(chat.id, target_user_id, context):
            await update.message.reply_text("❌ Bu kullanıcı yönetici/kurucu olduğu için banlanamaz.")
            return
    except:
        pass

    try:
        await bot.ban_chat_member(chat.id, target_user_id)
        name = target_username or str(target_user_id)
        await update.message.reply_text(f"✅ {name} banlandı.")
    except Exception as e:
        await update.message.reply_text(f"❌ Banlanamadı: {e}")

# Botu başlat
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_messages))

    print("✅ Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
