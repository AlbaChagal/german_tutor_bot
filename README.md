# German Telegram Bot Tutor

A Telegram bot to help users practice German vocabulary, grammar, and sentence structure using a local JSON database.

## Project Structure

german_bot.py: The main Python script that runs the bot.

words.json: The database containing words, translations, examples, and grammar rules.

requirements.txt: A list of Python libraries required to run the bot.

.env: A configuration file to store your sensitive Telegram API key.

## Prerequisites

Python 3.8+ installed on your machine.

A Telegram Bot Token. (Message @BotFather on Telegram to create a new bot and get a token).

## Installation

Download the files: Ensure german_bot.py, words.json, .env, and requirements.txt are in the same folder.

Install Libraries:
Open your terminal or command prompt in that folder and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Open the file named .env in a text editor.

Replace the placeholder text with your actual token:

TELEGRAM_KEY=123456789:ABC... (your actual token)


Note: Do not wrap the token in quotes.

Running the Bot

In your terminal, run:

```bash
python src/bot.py
```

You should see the message: 
```
Bot is running...
```

Usage Guide

Open your bot in Telegram and click Start or type /start. You can then use the following commands:

```/next``` : Get a random exercise from any category.

```/next_g2e``` : German -> English. Translate the given word.

```/next_e2g``` : English -> German. Translate the word (include articles for nouns, e.g., "die Entscheidung").

```/next_sentence``` : Fill in the blank. Complete the sentence contextually.

```/next_d2g``` : Definition. Guess the word based on its German explanation.

```/next_o2g``` : Opposite. Guess the word based on its antonym.

## Adding New Words

To expand your vocabulary list, simply edit the words.json file. Copy an existing block and change the values, ensuring you maintain valid JSON syntax (commas between objects).