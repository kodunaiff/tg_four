
def add_quiz(file_contents):
    quizzes = file_contents.split('\n' + '\n')
    quizs = {}
    total = 0
    for number, quiz in enumerate(quizzes, start=1):
        if 'Вопрос ' in quiz:
            quiz = quiz.replace("\n", " ")
            question = quiz.split(': ')
            total += 1
            quizs[f'Вопрос {total}'] = question[1]

        elif 'Ответ:' in quiz:
            quiz = quiz.replace("\n", " ")
            answer = quiz.split(': ')
            quizs[f'Ответ {total}'] = answer[1]

    return quizs


def main():
    phrases_folder = 'quiz-questions'
    phrases = ['1vs1200.txt', '1vs1201.txt', '1vs1298.txt']
    with open(f"{phrases_folder}/{phrases[1]}", "r", encoding="KOI8-R") as file:
        file_contents = file.read()

    ffff = add_quiz(file_contents)
    print(ffff['Вопрос 1'])



if __name__ == '__main__':
    main()