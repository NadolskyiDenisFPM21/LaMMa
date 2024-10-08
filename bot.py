import logging
from telegram import ForceReply, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
import requests
import json

import test_embeddings
import os
from dotenv import load_dotenv

load_dotenv()

company_info = ""

with open("company.txt", "r", encoding="utf-8") as file:
    company_info = file.read()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Define states
MAIN_MENU, PRODUCT_SEARCH = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    keyboard = [["Пошук товару"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_html(
        rf"Привіт {user.mention_html()}! Я бот компанії Полімерсервіс. Оберіть опцію або задайте питання...",
        reply_markup=reply_markup,
    )
    context.user_data["context"] = []
    return MAIN_MENU

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.message.text
    if query == "Пошук товару":
        context.user_data["context"] = []
        await update.message.reply_text(
            "Будь ласка, введіть інформацію про товар, який ви шукаєте:",
            reply_markup=ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True)
        )
        return PRODUCT_SEARCH
    elif query == "Назад":
        context.user_data["context"] = []
        return await start(update, context)

async def find_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text

    if "context" not in context.user_data:
        context.user_data["context"] = []
    
    messages = [
        {"role": "system", "content": "Відповідай на запитання, використовуючи лише ту інформацію, яка міститься у наданому контексті. Вибери з контексту кілька варіантів, які найкраще відповідають запитанню, і надай їх користувачеві. Якщо в контексті немає підходящих варіантів, повідом, що товар не знайдено. Подавай відповідь у вигляді переліку товарів з характеристиками і цінами. Відповідай українською мовою, якщо не було вказівок відповідати іншою мовою."},
    ]
    if len(context.user_data["context"]) == 0:
        context.user_data["context"] = messages
        output = test_embeddings.generate_data(user_input)
        prompt = f"Вопрос: {user_input}; Контекст: {output}."
        context.user_data["context"].append({"role": "user", "content": prompt})
    else:
        context.user_data["context"].append({"role": "user", "content": user_input})

    await update.message.reply_text("Формую відповідь...")
    
    response = requests.post('http://localhost:11434/api/chat', 
                             json={
                                 "model": "llama3.1",
                                 "messages": context.user_data["context"]
                             })
    
    if response.status_code == 200:
        result = response.json()
        assistant_message = result['message']['content']
        context.user_data["context"].append({"role": "assistant", "content": assistant_message})
        await update.message.reply_text(assistant_message)
    else:
        await update.message.reply_text("Виникла помилка при отриманні відповіді.")

    return PRODUCT_SEARCH

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global company_info
    user_input = update.message.text
    
    if "context" not in context.user_data:
        context.user_data["context"] = []
    messages = [
        {"role": "system", "content": company_info},
    ]
    if len(context.user_data["context"]) == 0:
        context.user_data["context"] = messages
    context.user_data["context"].append({"role": "user", "content": user_input})

    await update.message.reply_text("Формую відповідь...")
    
    response = requests.post('http://localhost:11434/api/chat', 
                             json={
                                 "model": "llama3.1",
                                 "messages": context.user_data["context"]
                             })
    
    if response.status_code == 200:
        result = response.json()
        assistant_message = result['message']['content']
        context.user_data["context"].append({"role": "assistant", "content": assistant_message})
        await update.message.reply_text(assistant_message)
    else:
        await update.message.reply_text("Виникла помилка при отриманні відповіді.")

    return MAIN_MENU

def main() -> None:
    """Start the bot."""
    TG_TOKEN = os.getenv('TG_TOKEN')
    application = Application.builder().token(TG_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex("^Пошук товару$"), button_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
            ],
            PRODUCT_SEARCH: [
                MessageHandler(filters.Regex("^Назад$"), button_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, find_product),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()