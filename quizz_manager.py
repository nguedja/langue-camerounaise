import random

class QuizManager:
    def __init__(self, questions):
        self.questions = list(questions.items())
        random.shuffle(self.questions)
        self.index = 0
        self.score = 0

    def question_actuelle(self):
        if self.index >= len(self.questions):
            return None

        question, options = self.questions[self.index]
        bonne_reponse = options[0]
        options = options.copy()
        random.shuffle(options)

        return question, options, bonne_reponse

    def verifier(self, reponse, bonne_reponse):
        if reponse == bonne_reponse:
            self.score += 1
            return True
        return False

