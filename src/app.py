import flet as ft
import random
import json
import re


def load_words():
    try:
        # Ensuring it points to your database folder
        with open('database/db.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading database: {e}")
        return []


class GermanApp(ft.Column):
    def __init__(self):
        super().__init__()
        self.words_db = load_words()
        self.current_word_data = None
        self.current_answer = ""
        self.exercise_type = None

        # UI Elements
        self.question_display = ft.Markdown(
            "Willkommen! Press **Next** to start practicing.",
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            selectable=True
        )
        self.answer_input = ft.TextField(
            label="Your answer",
            on_submit=self.check_answer,
            autofocus=True
        )
        self.result_text = ft.Text("", size=16, weight="bold")

        # Hint UI (Buttons that appear when 'Hint' is clicked)
        self.hint_options = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER)

        self.controls = [
            ft.Text("German B1.2 Tutor", size=30, weight="bold"),
            self.question_display,
            self.answer_input,
            ft.Row([
                ft.ElevatedButton("Check", on_click=self.check_answer, icon=ft.Icons.CHECK),
                ft.ElevatedButton("Next", on_click=self.generate_exercise, icon=ft.Icons.ARROW_FORWARD),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.TextButton("Need a hint?", icon=ft.Icons.LIGHTBULB_OUTLINE, on_click=self.show_hints),
            self.hint_options,
            self.result_text
        ]
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20

    def generate_exercise(self, e=None):
        if not self.words_db:
            self.result_text.value = "Database empty! Check your db.json path."
            self.update()
            return

        self.current_word_data = random.choice(self.words_db)
        # Using the random logic from your bot.py
        self.exercise_type = random.randint(1, 5)

        if self.exercise_type == 1:
            question = f"Translate to English: \n\n## **{self.current_word_data['word']}**"
            self.current_answer = self.current_word_data['translation_en']
        elif self.exercise_type == 2:
            question = f"Translate to German (+ article): \n\n## **{self.current_word_data['translation_en']}**"
            self.current_answer = f"{self.current_word_data['article']} {self.current_word_data['word']}" if \
            self.current_word_data['article'] else self.current_word_data['word']
        elif self.exercise_type == 3:
            sentence = self.current_word_data['example_sentence']
            target = self.current_word_data['word']
            pattern = re.compile(re.escape(target), re.IGNORECASE)
            question = f"Fill in the blank:\n\n*\"{pattern.sub('_______', sentence)}\"* "
            self.current_answer = target
        elif self.exercise_type == 4:
            question = f"What word matches this definition?\n\n*\"{self.current_word_data['explanation_de']}\"* "
            self.current_answer = self.current_word_data['word']
        elif self.exercise_type == 5:
            question = f"What is the opposite of: \n\n## **{self.current_word_data['opposite']}**?"
            self.current_answer = self.current_word_data['word']

        self.question_display.value = question
        self.answer_input.value = ""
        self.result_text.value = ""
        self.hint_options.controls.clear()  # Hide previous hints
        self.update()

    def show_hints(self, e):
        """Generates 4 multiple choice options like in bot.py"""
        if not self.current_answer:
            return

        # Simplified hint logic from your bot's cmd_hint
        distractors = []
        attempts = 0
        correct_clean = self.current_answer.split(',')[0].strip()

        while len(distractors) < 3 and attempts < 50:
            attempts += 1
            rand_word = random.choice(self.words_db)

            # Format candidate based on current exercise type
            if self.exercise_type == 1:
                cand = rand_word['translation_en'].split(',')[0].strip()
            elif self.exercise_type == 2:
                cand = f"{rand_word['article']} {rand_word['word']}" if rand_word['article'] else rand_word['word']
            else:
                cand = rand_word['word']

            if cand.lower() != correct_clean.lower() and cand not in distractors:
                distractors.append(cand)

        options = distractors + [correct_clean]
        random.shuffle(options)

        self.hint_options.controls = [
            ft.OutlinedButton(text=opt, on_click=lambda e, val=opt: self.use_hint(val))
            for opt in options
        ]
        self.update()

    def use_hint(self, value):
        self.answer_input.value = value
        self.update()

    def check_answer(self, e):
        user_input = self.answer_input.value.strip().lower()
        # German-to-English (Type 1) allows multiple comma-separated answers
        if self.exercise_type == 1:
            is_correct = user_input in [a.strip().lower() for a in self.current_answer.split(',')]
        else:
            is_correct = user_input == self.current_answer.lower()

        if is_correct:
            self.result_text.value = "Richtig! 🎉"
            self.result_text.color = "green"
        else:
            self.result_text.value = f"Leider falsch. Correct: {self.current_answer}"
            self.result_text.color = "red"
        self.update()


def main(page: ft.Page):
    page.title = "German B1.2 Tutor"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.add(GermanApp())


if __name__ == "__main__":
    ft.app(target=main)