import argparse
import logging
import random
import re

import redis
import vk_api as vk
from environs import Env
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import VkLongPoll, VkEventType

from helpers_quiz import add_quiz
from quiz_generator import give_quizs

logger = logging.getLogger(__name__)


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


def start(event, vk_api):
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Новый вопрос')
    keyboard.add_button('Сдаться')
    keyboard.add_line()
    keyboard.add_button('Мой счет')
    keyboard.add_button('Обнулить счет')
    vk_api.messages.send(
        user_id=event.user_id,
        message='Вас приветствует Викторина',
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard(),
    )
    logger.info(f"User {event.user_id} started the bot.")


def show_question(event, vk_api, red_db):
    quest_amount = int(len(quizs) / 2)
    number = random.randint(1, quest_amount)
    question = quizs[f'Вопрос {number}']
    answer_full = re.split('[.(]', quizs[f'Ответ {number}'])
    answer = answer_full[0].strip()
    red_db.hset(event.user_id, "question", question)
    red_db.hset(event.user_id, "answer", answer)
    vk_api.messages.send(
        user_id=event.user_id,
        message=question,
        random_id=random.randint(1, 1000),
    )
    logger.info(f"Sent question {number} to user {event.user_id}.")


def give_up(event, vk_api, red_db):
    correct_answer = red_db.hgetall(event.user_id)["answer"]
    vk_api.messages.send(
        user_id=event.user_id,
        message=correct_answer,
        random_id=random.randint(1, 1000),
    )


def give_answer(event, vk_api, red_db):
    correct_answer = red_db.hgetall(event.user_id)["answer"]
    if event.text.lower() == correct_answer.lower():
        vk_api.messages.send(
            user_id=event.user_id,
            message='Поздравляю!!! хотите продолжить?',
            random_id=random.randint(1, 1000),
        )
        win.append('win')
    else:
        vk_api.messages.send(
            user_id=event.user_id,
            message='Неправильно..попробуйте еще раз',
            random_id=random.randint(1, 1000),
        )
        loss.append('loss')


def check(event, vk_api):
    victory_record = len(win)
    loss_record = len(loss)
    vk_api.messages.send(
        user_id=event.user_id,
        message=f'win = {victory_record},loss = {loss_record}',
        random_id=random.randint(1, 1000),
    )


def cancel(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        message=f' ваш итоговый счет win = {len(win)},loss = {len(loss)} До встречи!',
        random_id=random.randint(1, 1000),
    )
    win.clear()
    loss.clear()
    vk_api.messages.send(
        user_id=event.user_id,
        message='Диалог завершен.',
        random_id=random.randint(1, 1000),
    )


if __name__ == "__main__":
    env = Env()
    env.read_env()

    host = env.str("REDIS_HOST")
    port = env.str("REDIS_PORT")
    win = []
    loss = []

    phrases_folder = parse_arguments().folder
    file_contents = give_quizs(phrases_folder)
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    quizs = add_quiz(file_contents)
    red_db = redis.Redis(
        host=host,
        port=port,
        decode_responses=True)
    vk_session = vk.VkApi(token=env.str("VK_TOKEN"))
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'Привет':
                start(event, vk_api)
            elif event.text == 'Новый вопрос':
                show_question(event, vk_api, red_db)
            elif event.text == 'Сдаться':
                give_up(event, vk_api, red_db)
            elif event.text == 'Мой счет':
                check(event, vk_api)
            elif event.text == 'Обнулить счет':
                cancel(event, vk_api)
            else:
                give_answer(event, vk_api, red_db)
