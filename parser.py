import requests
import pprint
from bs4 import BeautifulSoup as BS
import re

DEFAULT_TEST_URL = 'https://discopal.ispras.ru/%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F:MediawikiQuizzer/Algs-3-course-ispras-weekly'
REMOVE_TAGS = ['p', 'br/', 'li', 'tt', 'dl', 'dt', 'dd']
NEWLINE_TAGS = ['ul']

DATABASE = []
MAX_TRIES = 10

def explore():
    global DATABASE
    global MAX_TRIES

    for max_tries in range(0, 501):
        DATABASE = []
        MAX_TRIES = max_tries // 5
        fillDatabase()
        results_file = open('explore.txt', 'a')
        if max_tries % 5 == 0:
            results_file.write("\n")
        results_file.write(f'{MAX_TRIES} tries - Collected {len(DATABASE)} questions\n')
        results_file.close()


def fillDatabase():

    useless_tries_count = 0

    while True:
        initial_len = len(DATABASE)
        for question in getTest():
            add_flag = True
            for existing_question in DATABASE:
                if question == existing_question:
                    add_flag = False
            if add_flag:
                DATABASE.append(question)
        final_len = len(DATABASE)
        if final_len > initial_len:
            print(f"\x1b[1;32mAdded {final_len - initial_len} questions\x1b[0m")
            useless_tries_count = 0
        else:
            print("\x1b[1;31mNo new questions added\x1b[0m")
            useless_tries_count += 1

        if useless_tries_count > MAX_TRIES:
            break

    print(f"\x1b[1;33m--------- Found {len(DATABASE)} questions with {MAX_TRIES} retries --------\x1b[0m")

def getTest(url = DEFAULT_TEST_URL):
    html_markup = requests.get(url).text
    soup = BS(html_markup, 'html.parser')
    questions = list(map(str, soup.findAll('div', class_='mwq-question')))
    choices = [list(map(str, choice.findAll('li'))) for choice in soup.findAll('ol', class_='mwq-choices')]
    test = processTest(list(zip(questions, choices)))
    #printTest(test)
    return test

def processQuestion(question):
    result = re.findall(r'<div class="mwq-question"><p>([\s\S]*)<\/p><\/div>', question)
    if len(result) > 1:
        print("\x1b[1;31mParsing error occured!\x1b[0m")
        return None

    question_text = result[0]

    question_text = processPictures(question_text)
    question_text = processTags(question_text)
    question_text = removeExtraNewlines(question_text)
    question_text = processStaticPictures(question_text)

    return question_text

def processAnswers(answers_list):
    answer_texts_list = []

    for answer in answers_list:
        result = re.findall(r'<li class="mwq-choice"><input name="([\s\S]*?)" type="[\s\S]*?" value="(\d+?)"\/>([\s\S]*)<\/li>', answer)
        if len(result) > 1:
            print("\x1b[1;31mParsing error occured!\x1b[0m")
            return None

        input_name, value, answer_text = result[0]

        answer_text = processPictures(answer_text)
        answer_text = processTags(answer_text)
        answer_text = removeExtraNewlines(answer_text)
        answer_text = removeNonPrintableSymbols(answer_text)
        answer_text = processStaticPictures(answer_text)

        answer_texts_list.append(answer_text)

    return sorted(answer_texts_list)

def processPictures(html_markup):
    pictures = re.findall(r'(<object data=".*?" height="(\d*?)" style=".*?" type=".*?" width="(\d*?)"><img src="(.*?)"\/><\/object>)', html_markup)
    for picture_markup, height, width, url in pictures:
        html_markup = html_markup.replace(picture_markup, f"[discopal.ispras.ru{url}, {height}x{width}]")
    return html_markup

def processStaticPictures(html_markup):
    pictures = re.findall(r'((?:<[\s\S]+?>)*<img[\s\S]*?height="(\d+?)"[\s\S]*?src="([\s\S]+?)"[\s\S]*?width="(\d+?)"/>(?:<[\s\S]+?>)*)', html_markup)
    for picture_markup, height, url, width in pictures:
        html_markup = html_markup.replace(picture_markup, f"[discopal.ispras.ru{url}, {height}x{width}]")
    return html_markup

def processTags(html_markup):
    for tag in REMOVE_TAGS:
        html_markup = html_markup.replace(f'<{tag}>', '')
        html_markup = html_markup.replace(f'</{tag}>', '')
    for tag in NEWLINE_TAGS:
        html_markup = html_markup.replace(f'<{tag}>', '\n')
        html_markup = html_markup.replace(f'</{tag}>', '\n')
    return html_markup

def removeExtraNewlines(text):
    return re.sub(r'\n+', '\n', text)

def removeNonPrintableSymbols(text):
    return text.replace('\xa0', '')

def processTest(test):
    processed_test = []
    for question, answers in test:
        processed_test.append((processQuestion(question), processAnswers(answers)))

    return processed_test

def printTest(test):
    for question, answers in test:
        print("\n===========================\n")
        print(question)

        for answer, number in zip(answers, range(1, len(answers) + 1)):
            print(f'\t{number}. {answer}')

def exportTxt(test, filename):
    txt = open(f"{filename}.txt", 'w')
    for question, answers, number in zip(test, range(1, len(test) + 1):
        txt.write("\n===========================\n\n")
        txt.write(question)

        for answer, number in zip(answers, range(1, len(answers) + 1)):
            txt.write(f'\t{number}. {answer}\n')
    txt.close()

def exportTex(test, filename):
    tex = open(f"{filename}.tex")
    tex.write("""
    \documentclass[12pt]{article}
    \usepackage{hyperref}
    \usepackage[warn]{mathtext}
    \usepackage[T2A]{fontenc}
    \usepackage[utf8]{inputenc}
    \usepackage[russian]{babel}
    \usepackage{cite}
    \usepackage{amsfonts}
    \usepackage{lineno}
    \usepackage{subfig}
    \usepackage{graphicx}
    \usepackage{xcolor}
    \usepackage{bm}
    \usepackage{graphicx}
    \usepackage{amssymb}
    \usepackage{hyperref}
    \usepackage[left=2cm,right=2cm,top=2cm,bottom=2cm]{geometry}
    \usepackage{indentfirst}
    \DeclareSymbolFont{T2Aletters}{T2A}{cmr}{m}{it}
    \DeclareGraphicsExtensions{.png,.jpg,.svg,.pdf}
    \title{Еженедельный созвонный тест

    База вопросов}

    \begin{document}
    """)

    tex.write("\end{document}")
