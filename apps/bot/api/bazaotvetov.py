import random

import requests
from bs4 import BeautifulSoup

from apps.bot.api.handler import API


class BazaOtvetovPoll:
    def __init__(self, question: str, answers: list[str], correct_answer: str):
        # self.id:int = _id
        self.question: str = question
        self.answers: list[str] = answers
        self.correct_answer: str = correct_answer
        self.correct_answer_index: int = self.answers.index(self.correct_answer)


class BazaOtvetov(API):
    URL = "https://baza-otvetov.ru/quiz"
    GET_QUESTION_URL = f"{URL}/ask"
    CHECK_ANSWER_URL = f"{URL}/check"

    HEADERS = {
        "X-Requested-With": "XMLHttpRequest",
    }

    def get_question(self) -> BazaOtvetovPoll:
        r = requests.post(self.GET_QUESTION_URL, headers=self.HEADERS)
        bs4 = BeautifulSoup(r.content, 'html.parser')
        question_html = bs4.select_one("h3")
        question = question_html.text
        answers = [x.text for x in bs4.select('center h4')]

        _id = int(question_html.attrs['id'])
        _answer = answers[random.randint(0, 3)]
        answer = self.get_correct_answer(_id, _answer)

        return BazaOtvetovPoll(question, answers, answer)

    def get_correct_answer(self, question_id: int, answer: str) -> str:
        data = {
            "q_id": question_id,
            "answer": answer
        }
        r = requests.post(self.CHECK_ANSWER_URL, headers=self.HEADERS, data=data)
        bs4 = BeautifulSoup(r.content, 'html.parser')
        h3 = bs4.select("h3")[1]
        return h3.contents[3].text.replace("Правильный ответ: ", "")
