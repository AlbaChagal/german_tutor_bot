import os
import json
import random
import re
import logging
from dotenv import load_dotenv
from telegram import Update, BotCommand
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
    with open('database/db.json', 'r', encoding='utf-8') as f:
        return json.load(f)


WORDS_DB = load_words()

# --- Application Initialization Setup ---

async def post_init(application):
    """Sets the persistent menu commands for the bot."""
    commands = [
        BotCommand("next", "Get a random exercise"),
        BotCommand("hint", "Get hint for the current question"),
        BotCommand("next_g2e", "German to English exercise"),
        BotCommand("next_e2g", "English to German exercise"),
        BotCommand("next_sentence", "Fill in the blank exercise"),
        BotCommand("next_d2g", "Definition to German exercise"),
        # BotCommand("next_o2g", "Opposite to German exercise")
    ]
    try:
        await application.bot.set_my_commands(commands)
        logging.info("Telegram menu commands set successfully.")
    except Exception as e:
        logging.error(f"Failed to set Telegram commands: {e}")


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
        "/next_o2g - Opposite to German\n"
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
        exercise_types = [1, 2, 3, 4, 5]
        if word_data.get('noun_form'):
            exercise_types.append(6)  # Noun form
        if word_data.get('verb_form'):
            exercise_types.append(7)  # Verb form
        if not word_data.get('plural_form'):
            exercise_types.append(8)  # Plural form
        exercise_type = random.choice(exercise_types)

    question = ""
    correct_answer = ""

    # Logic for each type
    if exercise_type == 1:
        # German word -> Give English translation
        question = f"Translate this into English: \n\n*{word_data['word']}*"
        correct_answer = word_data['translation_en']

    elif exercise_type == 2:
        # English word -> Give German translation (with article)
        question = f"Translate this into German (include article if it's a noun): \n\n*{word_data['translation_en']}*"

        if word_data['article']:
            correct_answer = f"{word_data['article']} {word_data['word']}"
        else:
            correct_answer = word_data['word']

    elif exercise_type == 3:
        # Example sentence with blank
        # We replace the exact word in the sentence with underscores
        sentence = word_data['example_sentence']
        target_word = word_data['word']

        if target_word not in sentence:
            exercise_type = 4

        # Simple string replacement (case insensitive for replacement, but display original case)
        pattern = re.compile(re.escape(target_word), re.IGNORECASE)
        censored_sentence = pattern.sub("\_\_\_\_\_\_\_", sentence)

        question = f"Fill in the missing word:\n\n{censored_sentence}"
        correct_answer = target_word

    if exercise_type == 4:
        # Dictionary Explanation -> Word
        question = f"What word matches this definition?\n\n*{word_data['explanation_de']}*"
        correct_answer = word_data['word']

    if exercise_type == 5:
        # Opposite -> Word
        question = f"What is the opposite of: \n\n*{word_data['opposite']}*?"
        correct_answer = word_data['word']

    if exercise_type == 6:
        # Noun or Verb Form -> Word
        form_type = "Noun" if word_data.get('noun_form') else "Verb"
        form_value = word_data.get('noun_form') or word_data.get('verb_form')
        question = f"What is the {form_type} form of: \n\n*{form_value}*?"
        correct_answer = word_data['word']

    if exercise_type == 8:
        # Word -> Plural Form
        question = f"What is the plural form of the noun: \n\n*{word_data['word']}*?"
        correct_answer = word_data['plural_form']

    question += "\n\nYou can get a /hint if needed"

    # Store state in user_data so we can check the answer later
    context.user_data['current_answer'] = correct_answer
    context.user_data['exercise_type'] = exercise_type  # Saved for the hint logic
    context.user_data['active_exercise'] = True

    await update.message.reply_text(question, parse_mode='Markdown')

# --- Hint Logic ---

async def cmd_hint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Provides 4 random options, one of which is correct."""

    if not context.user_data.get('active_exercise'):
        await update.message.reply_text("No active exercise. Start one with /next")
        return

    if len(WORDS_DB) < 4:
        await update.message.reply_text("Not enough words in the database to generate hints.")
        return

    correct_answer = context.user_data.get('current_answer')
    exercise_type = context.user_data.get('exercise_type')

    distractors = []

    # Try to find 3 unique wrong answers
    # Limit attempts to prevent infinite loop if DB is small or repetitive
    attempts = 0
    while len(distractors) < 3 and attempts < 50:
        attempts += 1
        random_word = random.choice(WORDS_DB)
        candidate = ""

        # Format the candidate based on the current exercise type
        if exercise_type == 1:
            candidate = random_word['translation_en'].split(',')[0].strip()
        elif exercise_type == 2:
            if random_word['article']:
                candidate = f"{random_word['article']} {random_word['word']}"
            else:
                candidate = random_word['word']
        elif exercise_type in [3, 4, 5]:
             candidate = random_word['word']

        # Ensure candidate is not the correct answer and not already in our list
        # We use lower() to be forgiving on matching
        if candidate and candidate.lower() != correct_answer.lower() and candidate not in distractors:
            distractors.append(candidate)

    # Combine and shuffle
    options = distractors + [correct_answer.split(',')[0].strip() if exercise_type == 1 else correct_answer]
    random.shuffle(options)

    # Format output
    option_text = ""
    for i, opt in enumerate(options, 1):
        option_text += f"{i}. {opt}\n"

    await update.message.reply_text(f"Here is a hint! Choose one:\n\n{option_text}")

# --- Command Wrappers ---

async def cmd_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generate_exercise(update, context, exercise_type=None)


async def cmd_g2e(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generate_exercise(update, context, exercise_type=1)


async def cmd_e2g(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generate_exercise(update, context, exercise_type=2)


async def cmd_sentence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generate_exercise(update, context, exercise_type=3)


async def cmd_d2g(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generate_exercise(update, context, exercise_type=4)


async def cmd_o2g(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generate_exercise(update, context, exercise_type=5)


# --- Answer Checking ---

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks the user's text message against the stored correct answer."""


    if not context.user_data.get('active_exercise'):
        return

    user_input = update.message.text.strip()
    correct_answer_raw = context.user_data.get('current_answer', "")
    exercise_type = context.user_data.get('exercise_type')

    is_correct = False

    if exercise_type == 1:
        # Exercise Type 1 (German to English) supports multiple answers separated by commas
        # 1. Split the raw answer string (e.g., "waste, rubbish, garbage")
        # 2. Strip whitespace and convert to lowercase for comparison
        possible_answers = [ans.strip().lower() for ans in correct_answer_raw.split(',')]
        user_input_lower = user_input.lower()

        # Check if the user's input matches any of the possible correct answers
        if user_input_lower in possible_answers:
            is_correct = True
    else:
        # For all other exercise types, exact match (case insensitive) is required
        if user_input.lower() == correct_answer_raw.lower():
            is_correct = True

    # Clean strings for comparison (lowercase)
    if is_correct:
        response = "Congrats! You got the right answer. 🎉\n press /next to try another one."
        context.user_data['active_exercise'] = False
        context.user_data['current_answer'] = None
    else:
        response = f"So close! The right answer is: {correct_answer_raw}\n Press /next to try another one."
        context.user_data['active_exercise'] = False
        context.user_data['current_answer'] = None

    await update.message.reply_text(response)

# --- Main Application ---

if __name__ == '__main__':
    if not TOKEN:
        print("Error: TELEGRAM_KEY not found in .env file.")
        exit(1)

    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    # Command Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('next', cmd_next))
    application.add_handler(CommandHandler('next_g2e', cmd_g2e))
    application.add_handler(CommandHandler('next_e2g', cmd_e2g))
    application.add_handler(CommandHandler('next_sentence', cmd_sentence))
    application.add_handler(CommandHandler('next_d2g', cmd_d2g))
    application.add_handler(CommandHandler('next_o2g', cmd_o2g))

    # Hint Handler
    application.add_handler(CommandHandler('hint', cmd_hint))

    # Message Handler (Filters text and not commands)
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_answer))

    print("Bot is running...")
    application.run_polling()