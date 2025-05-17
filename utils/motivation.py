import json
import random
import os

MOTIVATION_FILE = "data/motivation.json"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOTIVATION_PATH = os.path.join(BASE_DIR, "..", "data", "motivation.json")

def get_daily_motivation():
    if not os.path.exists(MOTIVATION_FILE):
        return "Keep learning and growing every day!"
    
    with open(MOTIVATION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if random.choice(["quote", "trivia"]) == "quote":
        return f"💬 Quote of the Day:\n{random.choice(data.get('quotes', []))}"
    else:
        return f"📜 Word Trivia:\n{random.choice(data.get('trivia', []))}"
    


