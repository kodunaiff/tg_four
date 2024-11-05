import os
import random

def give_quizs(phrases_folder):
    files = os.listdir(phrases_folder)
    phrases = random.choice(files)
    with open(f"{phrases_folder}/{phrases}", "r", encoding="KOI8-R") as file:
        file_contents = file.read()

    return file_contents
