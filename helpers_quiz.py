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
