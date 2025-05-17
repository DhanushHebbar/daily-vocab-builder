import json
import os
from datetime import datetime, timedelta, date
import random

MAX_DATE = date.max

# Use absolute path based on this file location (recommended)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORD_DATA_PATH = os.path.join(BASE_DIR, "..", "data", "word_data.json")
REVIEW_SCHEDULE_PATH = os.path.join(BASE_DIR, "..", "data", "review_schedule.json")
USER_DATA_PATH = os.path.join(BASE_DIR, "..", "data", "user_data.json")

def get_word_of_the_day():
    if not os.path.exists(WORD_DATA_PATH):
        raise FileNotFoundError(f"Missing {WORD_DATA_PATH}, please create this file.")
    with open(WORD_DATA_PATH, "r", encoding="utf-8") as f:
        words = json.load(f)
    today = date.today()
    index = today.toordinal() % len(words)
    return words[index]

def update_review_schedule(word):
    if not os.path.exists(REVIEW_SCHEDULE_PATH):
        with open(REVIEW_SCHEDULE_PATH, "w") as f:
            json.dump({}, f)

    with open(REVIEW_SCHEDULE_PATH, "r") as f:
        data = json.load(f)

    today = date.today().isoformat()
    if word not in data:
        interval = 1
        next_review_date = date.today() + timedelta(days=interval)
    else:
        last_review_date_str = data[word]["last_review_date"]
        interval = data[word]["interval"] * 2
        last_review_date = datetime.strptime(last_review_date_str, "%Y-%m-%d").date()

        try:
            next_review_date = last_review_date + timedelta(days=interval)
            if next_review_date > MAX_DATE:
                next_review_date = MAX_DATE
        except OverflowError:
            next_review_date = MAX_DATE

    data[word] = {
        "interval": interval,
        "last_review_date": today,
        "next_review_date": next_review_date.isoformat()
    }

    with open(REVIEW_SCHEDULE_PATH, "w") as f:
        json.dump(data, f, indent=2)

def get_words_due_for_review():
    if not os.path.exists(USER_DATA_PATH):
        return []

    with open(USER_DATA_PATH, "r") as f:
        data = json.load(f)

    today = date.today().isoformat()
    due_words = []

    for word, dates in data.get("review_words", {}).items():
        if dates and dates[-1] == today:
            due_words.append(word)

    return due_words

BASE_DIR = os.path.dirname(__file__)

def get_word_by_era(era):
    try:
        file_path = os.path.join(BASE_DIR, "..", "assets", "vocab_by_year.json")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if era in data and data[era]:
            return random.choice(data[era])
        else:
            return None
    except Exception as e:
        print(f"Error loading vocab by year: {e}")
        return None
    
def get_daily_motivation():
    try:
        with open("data/motivations.json", "r") as f:
            motivations = json.load(f)
        today = datetime.now().date()
        index = today.toordinal() % len(motivations)
        return motivations[index]
    except Exception as e:
        print("Error loading motivation:", e)
        return "Stay motivated!"


    
    

