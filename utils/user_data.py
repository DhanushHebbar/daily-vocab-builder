import json
import os
from datetime import datetime

USER_DATA_PATH = "data/user_data.json"

def load_user_data():
    if not os.path.exists(USER_DATA_PATH):
        return {}
    with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_data(data):
    os.makedirs(os.path.dirname(USER_DATA_PATH), exist_ok=True)
    with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def update_last_active_date():
    data = load_user_data()
    data["last_date"] = datetime.now().strftime("%Y-%m-%d")
    save_user_data(data)
