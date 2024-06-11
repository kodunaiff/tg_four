
phrases_folder = 'quiz-questions'
phrases = ['1vs1200.txt', '1vs1201.txt', '1vs1298.txt']


with open(f"{phrases_folder}/{phrases[1]}", "r", encoding="KOI8-R") as file:
    file_contents = file.read()
print(file_contents)