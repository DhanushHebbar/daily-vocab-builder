import json
import os

USER_DATA_PATH = "data/user_data.json"  # Ensure data folder exists in your project root

def load_user_data():
    if not os.path.exists(USER_DATA_PATH):
        # Return default empty data to avoid crashes
        return {
            "streak": 0,
            "last_date": "",
            "goals": {"daily": 1, "weekly": 7},
            "words_learned_today": [],
            "usage_sentences": [],
            "review_words": {}
        }
    with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_data(data):
    os.makedirs(os.path.dirname(USER_DATA_PATH), exist_ok=True)
    with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_dashboard():
    data = load_user_data()
    streak = data.get("streak", 0)
    last_active = data.get("last_date", "N/A")
    goals = data.get("goals", {})
    daily_goal = goals.get("daily", 1)
    weekly_goal = goals.get("weekly", 7)
    words_today = len(data.get("words_learned_today", []))
    review_words = data.get("review_words", {})
    total_reviewed = len(review_words)

    dashboard = f"""
📊 Progress Dashboard
-----------------------
🔥 Streak: {streak} days
📆 Last Active: {last_active}
🎯 Daily Goal: {daily_goal} | Words Learned Today: {words_today}
🎯 Weekly Goal: {weekly_goal}
📚 Words Under Review: {total_reviewed}
-----------------------
"""
    return dashboard
