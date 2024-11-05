import logging
import random
import re

import redis
import telegram
from environs import Env
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import argparse

from helpers_quiz import add_quiz
from quiz_generator import give_quizs

logger = logging.getLogger(__name__)

CHOOSING = '1'
custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
main_menu = telegram.ReplyKeyboardMarkup(custom_keyboard)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Бот Викторина"
    )
    parser.add_argument(
        '--folder',
        default='quiz-questions',
        type=str,
        help='Указать путь к данным викторины',
    )
    args = parser.parse_args()
    return args


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    context.chat_data['win'] = []
    context.chat_data['loss'] = []
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=main_menu)
    logger.info(f"User {user.id} started the bot.")
    return CHOOSING


def show_question(update: Update, context: CallbackContext) -> None:
    questionnaire = context.bot_data["questionnaire"]
    chat_id = update.message.chat_id
    quest_amount = int(len(questionnaire) / 2)
    number = random.randint(1, quest_amount)
    question = questionnaire[f'Вопрос {number}']
    answer_full = questionnaire[f'Ответ {number}']
    answer_a = re.split('[.(]', answer_full)
    answer = answer_a[0].strip()
    update.message.reply_text(f'№{number}--{question}')
    context.chat_data["current_quiz"] = question, answer

    logger.info(f"Sent question {number} to user {chat_id}.")

    return CHOOSING


def give_answer(update: Update, context: CallbackContext) -> None:
    question, answer = context.chat_data["current_quiz"]
    text = update.message.text
    chat_id = update.message.chat_id
    if text.lower() == answer.lower():
        update.message.reply_text(
            'Поздравляю!!! хотите продолжить?',
            reply_markup=main_menu)
        context.chat_data['win'].append("Пользователь выиграл игру")
        logger.info(f"User {chat_id} answered correctly.")
    else:
        update.message.reply_text(
            'Неправильно..попробуйте еще раз',
            reply_markup=main_menu)
        context.chat_data['loss'].append("Пользователь проиграл игру")
        logger.info(f"User {chat_id} answered incorrectly.")

    return CHOOSING


def check(update: Update, context: CallbackContext) -> None:
    victory_record = len(context.chat_data["win"])
    loss_record = len(context.chat_data["loss"])
    update.message.reply_text(f'win = {victory_record},loss = {loss_record}')
    logger.info(f"User {update.message.chat_id} checked the score: win={victory_record}, loss={loss_record}.")
    return CHOOSING


def give_up(update: Update, context: CallbackContext) -> None:
    question, answer = context.chat_data["current_quiz"]
    chat_id = update.message.chat_id
    update.message.reply_text(f'your answer: {answer}')
    logger.info(f"User {chat_id} gave up. Correct answer: {answer}.")

    return CHOOSING


def cancel(update: Update, context):
    win = context.chat_data["win"]
    loss = context.chat_data["loss"]
    update.message.reply_text(f' ваш итоговый счет win = {len(win)},loss = {len(loss)} До встречи!')
    logger.info(f"User {update.message.chat_id} ended the game with score: win={len(win)}, loss={len(loss)}.")
    win.clear()
    loss.clear()
    update.message.reply_text('Диалог завершен.')
    return ConversationHandler.END


if __name__ == '__main__':
    env = Env()
    env.read_env()

    tg_token = env.str("TG_TOKEN")
    host = env.str("REDIS_HOST")
    port = env.str("REDIS_PORT")
    phrases_folder = parse_arguments().folder
    file_contents = give_quizs(phrases_folder)

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    updater = Updater(tg_token)
    dp = updater.dispatcher
    dp.bot_data['questionnaire'] = add_quiz(file_contents)
    dp.bot_data['win'] = []
    dp.bot_data['loss'] = []
    dp.bot_data["redis"] = redis.Redis(
        host=host,
        port=port,
        protocol=3,
        decode_responses=True)
    dp.update_persistence()

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
    logger.info("Bot started and ready to receive updates.")
    updater.start_polling()
    updater.idle()
