import json
import os
from datetime import date, datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
USER_DATA_PATH = os.path.join(DATA_DIR, "user_data.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def load_user_data():
    if not os.path.exists(USER_DATA_PATH):
        return {
            "last_active": "",
            "streak": 0,
            "daily_goal": 1,
            "weekly_goal": 7,
            "words_learned_today": [],
            "words_under_review": []
        }
    with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_data(data):
    with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def update_daily_progress():
    data = load_user_data()

    today_str = date.today().isoformat()
    last_active_str = data.get("last_active", "")

    # Update streak
    if last_active_str:
        last_active_date = datetime.strptime(last_active_str, "%Y-%m-%d").date()
        diff_days = (date.today() - last_active_date).days
        if diff_days == 1:
            data["streak"] = data.get("streak", 0) + 1
        elif diff_days > 1:
            data["streak"] = 0
    else:
        data["streak"] = 1  # First time

    # Update last_active to today
    data["last_active"] = today_str

    # Reset words learned today if last active is not today
    if last_active_str != today_str:
        data["words_learned_today"] = []

    # Count words under review (non-empty list)
    words_under_review = data.get("words_under_review", [])
    data["words_under_review"] = words_under_review  # just for clarity

    save_user_data(data)
    return data

def add_word_learned(word):
    data = load_user_data()
    today_str = date.today().isoformat()

    # Reset words_learned_today if last_active is not today
    if data.get("last_active") != today_str:
        data["words_learned_today"] = []

    if word not in data.get("words_learned_today", []):
        data["words_learned_today"].append(word)

    data["last_active"] = today_str
    save_user_data(data)

def get_progress_summary():
    data = update_daily_progress()
    return {
        "streak": data.get("streak", 0),
        "last_active": data.get("last_active", ""),
        "daily_goal": data.get("daily_goal", 1),
        "weekly_goal": data.get("weekly_goal", 7),
        "words_learned_today_count": len(data.get("words_learned_today", [])),
        "words_under_review_count": len(data.get("words_under_review", []))
    }
