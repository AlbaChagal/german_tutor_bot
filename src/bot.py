import os
import json
import random
import re
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_KEY')

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# Load the JSON database
def load_words():
    with open('db.json', 'r', encoding='utf-8') as f:
        return json.load(f)


WORDS_DB = load_words()


# --- Exercise Logic ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message."""
    welcome_msg = (
        "Willkommen! I am your German tutor.\n\n"
        "Use the following commands to practice:\n"
        "/next - Random exercise\n"
        "/next_g2e - German to English\n"
        "/next_e2g - English to German\n"
        "/next_sentence - Fill in the blank\n"
        "/next_d2g - Definition to German\n"
        "/next_o2g - Opposite to German"
    )
    await update.message.reply_text(welcome_msg)


async def generate_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE, exercise_type=None):
    """
    Selects a random word and generates a question based on the exercise type.

    Exercise Types:
    1: German -> English
    2: English -> German (w/ Article if noun)
    3: Fill in the blank
    4: Definition -> German
    5: Opposite -> German
    """
    word_data = random.choice(WORDS_DB)

    # If no specific type is requested, pick a random one
    if exercise_type is None:
        exercise_type = random.randint(1, 5)

    question = ""
    correct_answer = ""

    # Logic for each type
    if exercise_type == 1:
        # German word -> Give English translation
        question = f"Translate this into English: *{word_data['word']}*"
        correct_answer = word_data['translation_en']

    elif exercise_type == 2:
        # English word -> Give German translation (with article)
        question = f"Translate this into German (include article if it's a noun): *{word_data['translation_en']}*"

        if word_data['article']:
            correct_answer = f"{word_data['article']} {word_data['word']}"
        else:
            correct_answer = word_data['word']

    elif exercise_type == 3:
        # Example sentence with blank
        # We replace the exact word in the sentence with underscores
        sentence = word_data['example_sentence']
        target_word = word_data['word']

        # Simple string replacement (case insensitive for replacement, but display original case)
        pattern = re.compile(re.escape(target_word), re.IGNORECASE)
        censored_sentence = pattern.sub("\_\_\_\_\_\_\_", sentence)

        question = f"Fill in the missing word:\n\n{censored_sentence}"
        correct_answer = target_word

    elif exercise_type == 4:
        # Dictionary Explanation -> Word
        question = f"What word matches this definition?\n\n*{word_data['explanation_de']}*"
        correct_answer = word_data['word']

    elif exercise_type == 5:
        # Opposite -> Word
        question = f"What is the opposite of: *{word_data['opposite']}*?"
        correct_answer = word_data['word']

    # Store state in user_data so we can check the answer later
    context.user_data['current_answer'] = correct_answer
    context.user_data['active_exercise'] = True

    await update.message.reply_text(question, parse_mode='Markdown')


# --- Command Wrappers ---

async def cmd_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generate_exercise(update, context, exercise_type=None)


async def cmd_g2e(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generate_exercise(update, context, exercise_type=1)


async def cmd_e2g(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generate_exercise(update, context, exercise_type=2)


async def cmd_sentence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This corresponds to Type 3
    await generate_exercise(update, context, exercise_type=3)


async def cmd_d2g(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generate_exercise(update, context, exercise_type=4)


async def cmd_o2g(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generate_exercise(update, context, exercise_type=5)


# --- Answer Checking ---

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks the user's text message against the stored correct answer."""

    # If no exercise is active, ignore or give help
    if not context.user_data.get('active_exercise'):
        # Optional: You could allow chatting here, but for now we do nothing
        return

    user_input = update.message.text.strip()
    correct_answer = context.user_data.get('current_answer', "")

    # Clean strings for comparison (lowercase)
    if user_input.lower() == correct_answer.lower():
        response = "Congrats! You got the right answer. 🎉"
        # Clear state
        context.user_data['active_exercise'] = False
        context.user_data['current_answer'] = None
    else:
        # As per instructions: "If it's not exactly the same return: So close!..."
        response = f"So close! The right answer is: {correct_answer}"
        # We clear state here too, effectively ending the specific question
        context.user_data['active_exercise'] = False
        context.user_data['current_answer'] = None

    await update.message.reply_text(response)


# --- Main Application ---

if __name__ == '__main__':
    if not TOKEN:
        print("Error: TELEGRAM_KEY not found in .env file.")
        exit(1)

    application = ApplicationBuilder().token(TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('next', cmd_next))
    application.add_handler(CommandHandler('next_g2e', cmd_g2e))
    application.add_handler(CommandHandler('next_e2g', cmd_e2g))
    # Note: mapped 'next_sentences' for the fill-in-blank type 3
    application.add_handler(CommandHandler('next_sentence', cmd_sentence))
    application.add_handler(CommandHandler('next_d2g', cmd_d2g))
    application.add_handler(CommandHandler('next_o2g', cmd_o2g))

    # Message Handler (Filters text and not commands)
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_answer))

    print("Bot is running...")
    application.run_polling()