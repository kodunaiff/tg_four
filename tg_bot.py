import logging
import random
from typing import Union, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import telegram
from environs import Env

from telegram import Update, ForceReply, bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from helpers_quiz import add_quiz

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=reply_markup)

def question(update: Update, context: CallbackContext) -> None:
    number = random.randint(1, 24)
    question1 = context.bot_data['quest']
    text_q = question1[f'Вопрос {number}']
    update.message.reply_text(text_q)



def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.message.text)

def mess(update: Update, context: CallbackContext) -> None:
    chat_id = 951680654
    context.bot.send_message(chat_id=chat_id, text="I'm sorry Dave I'm afraid I can't do that.")

def main() -> None:
    env = Env()
    env.read_env()
    tg_token = env.str("TG_TOKEN")

    phrases_folder = 'quiz-questions'
    phrases = ['1vs1200.txt', '1vs1201.txt', '1vs1298.txt']
    with open(f"{phrases_folder}/{phrases[1]}", "r", encoding="KOI8-R") as file:
        file_contents = file.read()

    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['quest'] = add_quiz(file_contents)

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("mess", mess))
    dispatcher.add_handler(MessageHandler(Filters.regex("^Новый вопрос$"), question))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
