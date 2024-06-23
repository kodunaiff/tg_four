import logging
import random
import re

import redis
import telegram
from environs import Env
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

from helpers_quiz import add_quiz

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

_database = None
quizs = dict()
CHOOSING = '1'
custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
main_menu = telegram.ReplyKeyboardMarkup(custom_keyboard)
win = []
loss = []


def get_database_connection():
    global _database
    if _database is None:
        _database = redis.Redis(host='localhost', port=6379, decode_responses=True)
    return _database


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=main_menu)
    return CHOOSING


def show_question(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    red_db = get_database_connection()
    quest_amount = int(len(quizs)/2)
    number = random.randint(1, quest_amount)
    question = quizs[f'Вопрос {number}']
    answer_full = quizs[f'Ответ {number}']
    answer_a = re.split('[.(]', answer_full)
    answer = answer_a[0].strip()
    red_db.set(f'{chat_id} Вопрос {number}', question)
    red_db.set(f'{chat_id} Ответ', answer)
    update.message.reply_text(f'№{number}--{question}')

    return CHOOSING


def give_answer(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    chat_id = update.message.chat_id
    red_db = get_database_connection()
    if text == red_db.get(f'{chat_id} Ответ'):
        update.message.reply_text(
            'Поздравляю!!! хотите продолжить?',
            reply_markup=main_menu)
        win.append('win')
    else:
        update.message.reply_text(
            'Неправильно..попробуйте еще раз',
            reply_markup=main_menu)
        loss.append('loss')

    return CHOOSING


def check(update: Update, context: CallbackContext) -> None:
    w = len(win)
    l = len(loss)
    update.message.reply_text(f'win = {w},loss = {l}')
    return CHOOSING


def give_up(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    red_db = get_database_connection()
    text = red_db.get(f'{chat_id} Ответ')
    update.message.reply_text(f'your answer: {text}')

    return CHOOSING


def cancel(update: Update, context):
    update.message.reply_text(f' ваш итоговый счет win = {len(win)},loss = {len(loss)} До встречи!')
    win.clear()
    loss.clear()
    update.message.reply_text('Диалог завершен.')
    return ConversationHandler.END


if __name__ == '__main__':
    env = Env()
    env.read_env()
    tg_token = env.str("TG_TOKEN")

    phrases_folder = 'quiz-questions'
    phrases = ['1vs1200.txt', '1vs1201.txt', '1vs1298.txt']
    with open(f"{phrases_folder}/{phrases[1]}", "r", encoding="KOI8-R") as file:
        file_contents = file.read()
    updater = Updater(tg_token)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOOSING: [
                MessageHandler(Filters.regex(r"^Новый вопрос$"), show_question),
                MessageHandler(Filters.regex(r"^Мой счет$"), check),
                MessageHandler(Filters.regex(r"^Сдаться$"), give_up),
                MessageHandler(Filters.text & ~Filters.command, give_answer),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    quizs = add_quiz(file_contents)
    updater.start_polling()
    updater.idle()
