import requests
import pprint
from bs4 import BeautifulSoup as BS
import re
import json

DEFAULT_TEST_URL = 'https://discopal.ispras.ru/%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F:MediawikiQuizzer/Algs-3-course-ispras-weekly'
REMOVE_TAGS = ['p', 'br/', 'li', 'tt', 'dl', 'dt', 'dd']
NEWLINE_TAGS = ['ul']

class Discoparser:
    def __init__(self, test_url, max_retries = 10):
        self.tasks = []
        self.test_url = test_url
        self.max_retries = max_retries

    def importDatabase(self):
        with open('tasks_database.json', 'r') as db_file:
            tasks = json.loads(db_file.read())
            for task in tasks:
                self.tasks.append(tuple(task))

    def exportDatabase(self):
        with open('tasks_database.json', 'w') as db_file:
            db_file.write(json.dumps(self.tasks, indent = 4, ensure_ascii = False))

    def poll(self):
        pass

    def fillDatabase(self):
        useless_tries_count = 0

        while useless_tries_count <= self.max_retries:
            if self.updateDatabase():
                useless_tries_count = 0
            else:
                useless_tries_count += 1

    def updateDatabase(self):
        html_markup = requests.get(self.test_url).text
        soup = BS(html_markup, 'html.parser')
        questions = list(map(str, soup.findAll('div', class_='mwq-question')))
        choices = [list(map(str, choice.findAll('li'))) for choice in soup.findAll('ol', class_='mwq-choices')]
        test = self.processTest(list(zip(questions, choices)))

        initial_len = len(self.tasks)
        for task in test:
            self.addNewTask(task)
        final_len = len(self.tasks)

        return final_len > initial_len

    def addNewTask(self, task):
        add_flag = True
        for existing_task in self.tasks:
            if task == existing_task:
                add_flag = False
        if add_flag:
            self.tasks.append(task)

    def __str__(self):
        string = ''
        for question, answers in self.tasks:
            string += f'\n===========================\n\n{question}\n'

            for answer, number in zip(answers, range(1, len(answers) + 1)):
                string += f'\t{number}. {answer}\n'

        return string

    def processQuestion(self, question):
        result = re.findall(r'<div class="mwq-question"><p>([\s\S]*)<\/p><\/div>', question)
        if len(result) > 1:
            print("\x1b[1;31mParsing error occured!\x1b[0m")
            return None

        question_text = result[0]

        question_text = self.processPictures(question_text)
        question_text = self.processTags(question_text)
        question_text = self.removeExtraNewlines(question_text)
        question_text = self.processStaticPictures(question_text)

        return question_text

    def processAnswers(self, answers_list):
        answer_texts_list = []

        for answer in answers_list:
            result = re.findall(r'<li class="mwq-choice"><input name="([\s\S]*?)" type="[\s\S]*?" value="(\d+?)"\/>([\s\S]*)<\/li>', answer)
            if len(result) > 1:
                print("\x1b[1;31mParsing error occured!\x1b[0m")
                return None

            input_name, value, answer_text = result[0]

            answer_text = self.processPictures(answer_text)
            answer_text = self.processTags(answer_text)
            answer_text = self.removeExtraNewlines(answer_text)
            answer_text = self.removeNonPrintableSymbols(answer_text)
            answer_text = self.processStaticPictures(answer_text)

            answer_texts_list.append(answer_text)

        return sorted(answer_texts_list)

    def processPictures(self, html_markup):
        pictures = re.findall(r'(<object data=".*?" height="(\d*?)" style=".*?" type=".*?" width="(\d*?)"><img src="(.*?)"\/><\/object>)', html_markup)
        for picture_markup, height, width, url in pictures:
            html_markup = html_markup.replace(picture_markup, f"[discopal.ispras.ru{url}, {height}x{width}]")
        return html_markup

    def processStaticPictures(self, html_markup):
        pictures = re.findall(r'((?:<[\s\S]+?>)*<img[\s\S]*?height="(\d+?)"[\s\S]*?src="([\s\S]+?)"[\s\S]*?width="(\d+?)"/>(?:<[\s\S]+?>)*)', html_markup)
        for picture_markup, height, url, width in pictures:
            html_markup = html_markup.replace(picture_markup, f"[discopal.ispras.ru{url}, {height}x{width}]")
        return html_markup

    def processTags(self, html_markup):
        for tag in REMOVE_TAGS:
            html_markup = html_markup.replace(f'<{tag}>', '')
            html_markup = html_markup.replace(f'</{tag}>', '')
        for tag in NEWLINE_TAGS:
            html_markup = html_markup.replace(f'<{tag}>', '\n')
            html_markup = html_markup.replace(f'</{tag}>', '\n')
        return html_markup

    def removeExtraNewlines(self, text):
        return re.sub(r'\n+', '\n', text)

    def removeNonPrintableSymbols(self, text):
        return text.replace('\xa0', '')

    def processTest(self, test):
        processed_test = []
        for question, answers in test:
            processed_test.append((self.processQuestion(question), self.processAnswers(answers)))

        return processed_test


def exportTxt(test, filename):
    txt = open(f"{filename}.txt", 'w')
    for question, answers, number in zip(test, range(1, len(test) + 1)):
        txt.write("\n===========================\n\n")
        txt.write(question)

        for answer, number in zip(answers, range(1, len(answers) + 1)):
            txt.write(f'\t{number}. {answer}\n')
    txt.close()

def exportTex(test, filename):
    tex = open(f"{filename}.tex")
    tex.write(r"""
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

    tex.write(r"\end{document}")
