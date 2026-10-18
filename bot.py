import os
import logging
from urllib.parse import quote
import aiohttp
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("ai-universe-bot")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

MODELS = {
    "llama": ("llama-3.3-70b-versatile", "Llama 3.3 · 70B"),
    "fast": ("llama-3.1-8b-instant", "Llama 3.1 · 8B سريع"),
    "oss120": ("openai/gpt-oss-120b", "GPT-OSS · 120B"),
    "oss20": ("openai/gpt-oss-20b", "GPT-OSS · 20B"),
}
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
SYSTEM_PROMPT = (
    "أنت AI Universe، مساعد ذكاء اصطناعي شامل. أجب بنفس لغة المستخدم "
    "(العربية افتراضياً) بدقة ووضوح وبشكل منظم. للبرمجة اكتب كوداً كاملاً."
)
MAX_HISTORY_MESSAGES = 20
# In-memory history: resets when the hosting service restarts.
histories = {}
user_models = {}


def model_for(user_id: int) -> str:
    return user_models.get(user_id, DEFAULT_MODEL)


async def groq_chat(user_id: int, prompt: str) -> str:
    if not GROQ_API_KEY:
        return "⚠️ لم يتم ضبط GROQ_API_KEY في متغيرات الاستضافة."
    history = histories.setdefault(user_id, [])
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-MAX_HISTORY_MESSAGES:])
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model_for(user_id),
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1800,
    }
    timeout = aiohttp.ClientTimeout(total=90)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        ) as response:
            body = await response.text()
            if response.status >= 400:
                log.error("Groq API error %s: %s", response.status, body[:1000])
                return f"⚠️ تعذّر الاتصال بمحرك الذكاء الاصطناعي (HTTP {response.status}). تحقق من مفتاح Groq والنموذج المختار."
            try:
                data = await response.json()
                answer = data["choices"][0]["message"]["content"].strip()
            except Exception:
                log.exception("Could not parse Groq response")
                return "⚠️ وصل رد غير مفهوم من محرك الذكاء الاصطناعي."

    history.extend([
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": answer},
    ])
    histories[user_id] = history[-MAX_HISTORY_MESSAGES:]
    return answer or "لم يصل رد نصي من المحرك."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🌌 أهلاً بك في AI Universe!\n\n"
        "أرسل أي سؤال للدردشة مع الذكاء الاصطناعي.\n\n"
        "الأوامر:\n"
        "/new — بدء محادثة جديدة\n"
        "/models — عرض النماذج\n"
        "/model llama — اختيار نموذج\n"
        "/image وصف الصورة — توليد صورة\n"
        "/help — المساعدة"
    )
    await update.effective_message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    histories.pop(update.effective_user.id, None)
    await update.effective_message.reply_text("بدأنا محادثة جديدة ✨")


async def models_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["🤖 النماذج المتاحة:"]
    for key, (model_id, name) in MODELS.items():
        lines.append(f"• `{key}` — {name}" + (" ✓" if model_for(update.effective_user.id) == model_id else ""))
    lines.append("\nللتغيير: /model fast")
    await update.effective_message.reply_text("\n".join(lines), parse_mode="Markdown")


async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await models_command(update, context)
        return
    key = context.args[0].lower()
    if key not in MODELS:
        await update.effective_message.reply_text("اسم النموذج غير صحيح. استخدم /models")
        return
    user_models[update.effective_user.id] = MODELS[key][0]
    await update.effective_message.reply_text(f"تم اختيار {MODELS[key][1]} ✅")


async def send_long_text(message, text: str):
    # Telegram message limit is 4096 characters; split at line boundaries when possible.
    limit = 4000
    while text:
        if len(text) <= limit:
            chunk, text = text, ""
        else:
            cut = text.rfind("\n", 0, limit)
            if cut < limit // 2:
                cut = limit
            chunk, text = text[:cut], text[cut:].lstrip()
        await message.reply_text(chunk)


async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args).strip()
    if not prompt:
        await update.effective_message.reply_text("اكتب وصف الصورة بعد الأمر، مثال:\n/image قطة رائدة فضاء على القمر")
        return
    message = update.effective_message
    await message.reply_text("🎨 جارٍ تجهيز الصورة، قد يستغرق ذلك بعض الوقت...")
    # Pollinations image endpoint; model choices may vary by provider availability.
    image_url = (
        "https://image.pollinations.ai/prompt/"
        + quote(prompt, safe="")
        + "?width=768&height=768&model=flux&seed=42&nologo=true&enhance=true"
    )
    timeout = aiohttp.ClientTimeout(total=150)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    await message.reply_text("⚠️ تعذّر توليد الصورة حالياً. حاول مرة أخرى لاحقاً.")
                    return
                content_type = response.headers.get("Content-Type", "")
                if not content_type.startswith("image/"):
                    await message.reply_text("⚠️ خدمة الصور لم تُرجع صورة صالحة. حاول مرة أخرى.")
                    return
                image_bytes = await response.read()
        from io import BytesIO
        photo = BytesIO(image_bytes)
        photo.name = "ai-universe.png"
        await message.reply_photo(photo=photo, caption=f"🎨 {prompt[:900]}")
    except Exception:
        log.exception("Image generation failed")
        await message.reply_text("⚠️ فشل توليد الصورة أو انتهت المهلة. حاول مرة أخرى.")


async def chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    prompt = (message.text or "").strip()
    if not prompt:
        return
    await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.TYPING)
    try:
        answer = await groq_chat(user.id, prompt)
        await send_long_text(message, answer)
    except Exception:
        log.exception("Chat request failed")
        await message.reply_text("⚠️ حدث خطأ غير متوقع. حاول مرة أخرى.")


async def post_init(application: Application):
    log.info("AI Universe Telegram bot started")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN environment variable")
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("new", new_chat))
    application.add_handler(CommandHandler("models", models_command))
    application.add_handler(CommandHandler("model", set_model))
    application.add_handler(CommandHandler("image", image_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_message))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
