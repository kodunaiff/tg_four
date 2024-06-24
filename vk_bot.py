import logging
import random
import re

import redis
import vk_api as vk
from environs import Env
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import VkLongPoll, VkEventType

from helpers_quiz import add_quiz
from source_folder import give_quizs

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

env = Env()
env.read_env()
_database = None
host = env.str("REDIS_HOST")
port = env.str("REDIS_PORT")
quizs = dict()
win = []
loss = []


def get_database_connection():
    global _database
    if _database is None:
        _database = redis.Redis(host=host, port=port, decode_responses=True)
    return _database


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


def show_question(event, vk_api):
    red_db = get_database_connection()
    quest_amount = int(len(quizs) / 2)
    number = random.randint(1, quest_amount)
    question = quizs[f'Вопрос {number}']
    answer_full = quizs[f'Ответ {number}']
    answer_a = re.split('[.(]', answer_full)
    answer = answer_a[0].strip()
    red_db.set(f'Вопрос {number}', question)
    red_db.set(f'Ответ', answer)
    vk_api.messages.send(
        user_id=event.user_id,
        message=question,
        random_id=random.randint(1, 1000),
    )


def give_up(event, vk_api):
    red_db = get_database_connection()
    text = red_db.get('Ответ')
    vk_api.messages.send(
        user_id=event.user_id,
        message=text,
        random_id=random.randint(1, 1000),
    )


def give_answer(event, vk_api):
    red_db = get_database_connection()
    answer = red_db.get('Ответ')
    if event.text.lower() == answer.lower():
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
    w = len(win)
    l = len(loss)
    vk_api.messages.send(
        user_id=event.user_id,
        message=f'win = {w},loss = {l}',
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
    phrases_folder = 'quiz-questions'
    file_contents = give_quizs(phrases_folder)
    quizs = add_quiz(file_contents)
    red_db = get_database_connection()
    vk_session = vk.VkApi(token=env.str("VK_TOKEN"))
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'Привет':
                start(event, vk_api)
            elif event.text == 'Новый вопрос':
                show_question(event, vk_api)
            elif event.text == 'Сдаться':
                give_up(event, vk_api)
            elif event.text == 'Мой счет':
                check(event, vk_api)
            elif event.text == 'Обнулить счет':
                cancel(event, vk_api)
            else:
                give_answer(event, vk_api)
