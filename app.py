from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
import os
import json
import random

from utils.word_manager import (
    get_word_of_the_day,
    get_words_due_for_review,
    update_review_schedule,
    get_word_by_era,
    USER_DATA_PATH
)
from utils.dashboard import get_dashboard
from utils.progress import get_progress_summary, save_sentence_history
from utils.export import export_progress_csv, export_progress_pdf
from utils.motivation import get_daily_motivation

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user  
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# Database setup
db = SQLAlchemy(app)

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# File paths
USERS_FILE = 'data/users.json'
WORDS_FILE = 'data/word_data.json'

# Ensure users file exists
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

# Load users from JSON

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save users to JSON
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

# User class
class User(UserMixin):
    def __init__(self, username):
        self.id = username

# User loader
@login_manager.user_loader
def load_user(username):
    users = load_users()
    if username in users:
        return User(username)
    return None

# Load vocabulary
with open(WORDS_FILE) as f:
    words_data = json.load(f)

# Home route
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    word = get_word_of_the_day()
    progress = get_progress_summary()
    dashboard = get_dashboard()
    motivation = get_daily_motivation()
    sentence_feedback = None

    if request.method == "POST":
        user_sentence = request.form.get("sentence", "").strip().lower()
        if word["word"].lower() in user_sentence:
            sentence_feedback = "✅ Great! You've used the word correctly."
        else:
            sentence_feedback = "❌ Try again. Make sure you include the word in your sentence."

    return render_template("index.html", word=word, progress=progress,
                           dashboard=dashboard, motivation=motivation,
                           sentence_feedback=sentence_feedback, username=current_user.id)

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        users = load_users()

        if username in users:
            flash('Username already exists.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        users[username] = {'password': hashed_password, 'history': []}
        save_users(users)

        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        users = load_users()

        if username in users:
            stored_hash = users[username]['password']
            if check_password_hash(stored_hash, password):
                user = User(username)
                login_user(user)
                flash('✅ Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('❌ Incorrect password.', 'danger')
        else:
            flash('❌ Username does not exist.', 'danger')

    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

# Learn route
@app.route('/learn')
@login_required
def learn():
    return render_template('learn.html', words=words_data)

# Review route
@app.route('/review')
@login_required
def review():
    due_words = get_words_due_for_review()
    users = load_users()
    history = users.get(current_user.id, {}).get('history', [])
    return render_template('review.html', due_words=due_words, history=history)


# Test route
from flask import session

@app.route('/test', methods=['GET', 'POST'])
@login_required
def test():
    # Load words data
    with open('data/word_data.json', 'r', encoding='utf-8') as f:
        words_data = json.load(f)

    # Filter valid words with synonyms
    valid_words = [w for w in words_data if isinstance(w, dict) and w.get("word") and w.get("synonyms")]

    if not valid_words:
        return "❌ Not enough valid words with synonyms."

    # Initialize history and score in session if not present
    if 'history' not in session:
        session['history'] = []
    if 'score' not in session:
        session['score'] = 0

    feedback = None
    result = None

    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip().lower()
        correct_answer = request.form.get('correct_answer', '').strip().lower()
        word = request.form.get('word', '').strip()

        is_correct = user_answer == correct_answer

        # Update score and history
        result = {
            'is_correct': is_correct,
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'word': word
        }

        if is_correct:
            session['score'] += 1
            feedback = f"✅ Correct! '{user_answer}' is a synonym of '{word}'."
        else:
            feedback = f"❌ Incorrect. The correct synonym of '{word}' is '{correct_answer}'."

        session['history'].append(result)
        session.modified = True

    # Prepare new question
    word_entry = random.choice(valid_words)
    correct_synonym = random.choice(word_entry["synonyms"])

    # Prepare wrong options
    other_synonyms = list({
        syn.lower()
        for w in valid_words if w["word"] != word_entry["word"]
        for syn in w.get("synonyms", [])
    })

    if len(other_synonyms) < 3:
        return "❌ Not enough unique synonym options to generate a quiz."

    wrong_options = random.sample(other_synonyms, k=3)
    options = wrong_options + [correct_synonym]
    random.shuffle(options)

    return render_template('test.html',
                           word=word_entry["word"],
                           options=options,
                           correct_answer=correct_synonym,
                           result=result,
                           feedback=feedback,
                           score=session['score'],
                           history=session['history'])




# Mark reviewed
@app.route('/mark_reviewed', methods=['POST'])
@login_required
def mark_reviewed():
    word = request.form.get('word')
    if word:
        update_review_schedule(word)
    return redirect(url_for('review'))

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html", username=current_user.id)

# Set goals
@app.route('/set_goals', methods=['GET', 'POST'])
@login_required
def set_goals():
    BASE_GOALS = {"daily_goal": 1, "weekly_goal": 7}

    if not os.path.exists(USER_DATA_PATH):
        with open(USER_DATA_PATH, 'w') as f:
            json.dump(BASE_GOALS, f, indent=2)

    with open(USER_DATA_PATH, 'r') as f:
        user_data = json.load(f)

    feedback = ""

    if request.method == 'POST':
        try:
            daily_goal = int(request.form.get("daily_goal", 1))
            weekly_goal = int(request.form.get("weekly_goal", 7))
            user_data["daily_goal"] = daily_goal
            user_data["weekly_goal"] = weekly_goal

            with open(USER_DATA_PATH, 'w') as f:
                json.dump(user_data, f, indent=2)

            feedback = "✅ Goals updated successfully!"
        except ValueError:
            feedback = "❌ Invalid input. Please enter valid numbers."

    return render_template("set_goals.html", user_data=user_data, feedback=feedback)

# Games
@app.route("/games", methods=["GET", "POST"])
@login_required
def games():
    with open("data/word_data.json", "r", encoding="utf-8") as f:
        words = json.load(f)

    # ✅ Only keep items that are dictionaries and have 'word' and 'synonyms' keys
    synonym_words = [
        w for w in words 
        if isinstance(w, dict) and 'word' in w and 'synonyms' in w and isinstance(w.get('synonyms'), list)
    ]

    if len(synonym_words) < 2:
        return "❌ Not enough words with synonyms to play the game."


    if request.method == "POST":
        quiz_word_text = request.form.get("quiz_word")
        quiz_word = next((w for w in synonym_words if w["word"] == quiz_word_text), None)
        if not quiz_word:
            return "❌ Quiz word not found."

        correct_synonyms = [syn.lower() for syn in quiz_word["synonyms"]if isinstance(syn, str)]

        other_synonyms = list({
            syn.lower()
            for w in synonym_words if w["word"] != quiz_word["word"]
            for syn in w.get("synonyms", []) if isinstance(syn, str)
        })
        user_answer = request.form.get("answer", "").strip().lower()

        if user_answer in correct_synonyms:
            result = f"✅ Correct! The word '{quiz_word['word']}' synonyms include: {', '.join(quiz_word['synonyms'])}"
        else:
            result = f"❌ Incorrect! The word '{quiz_word['word']}' synonyms include: {', '.join(quiz_word['synonyms'])}"

        options = request.form.getlist("options")
        quiz = {"word": quiz_word["word"], "options": options}
    else:
        quiz_word = random.choice(synonym_words)
        correct_synonyms = [syn.lower() for syn in quiz_word["synonyms"]]
        other_synonyms = list({syn.lower() for w in synonym_words if w["word"] != quiz_word["word"] for syn in w.get("synonyms", [])})
        wrong_options = random.sample(other_synonyms, max(0, 4 - len(correct_synonyms)))
        options = list(set(correct_synonyms + wrong_options))
        random.shuffle(options)
        result = None
        quiz = {"word": quiz_word["word"], "options": options}

    return render_template("games.html", quiz=quiz, result=result)

# Historical word
@app.route('/historical_word', methods=['GET', 'POST'])
@login_required
def historical_word():
    word = None
    if request.method == 'POST':
        era = request.form.get("era")
        word = get_word_by_era(era)
    return render_template("historical_word.html", word=word)

# Sentence feedback
@app.route('/sentence_feedback', methods=['GET', 'POST'])
@login_required
def sentence_feedback():
    feedback = ""
    word = get_word_of_the_day()["word"]

    if request.method == "POST":
        user_sentence = request.form.get("sentence", "").lower()
        if word.lower() in user_sentence:
            feedback = "✅ Good job! You used the word correctly."
        else:
            feedback = "❌ Try again. Make sure you include the word in your sentence."

    return render_template("sentence_feedback.html", word=word, feedback=feedback)

# Export
@app.route("/export/csv")
@login_required
def export_csv():
    path = export_progress_csv()
    return send_file(path, as_attachment=True)

@app.route("/export/pdf")
@login_required
def export_pdf():
    path = export_progress_pdf()
    return send_file(path, as_attachment=True)

# Submit sentence (AJAX)
@app.route('/submit_sentence', methods=['POST'])
@login_required
def submit_sentence():
    data = request.get_json()
    sentence = data.get("sentence", "")
    word = get_word_of_the_day()
    save_sentence_history(word["word"], sentence)

    if word["word"].lower() in sentence.lower():
        feedback = f"✅ Great! You used the word '{word['word']}' correctly."
    else:
        feedback = f"❌ Try again. Your sentence must include the word '{word['word']}'."

    return jsonify({'feedback': feedback})

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", error="404 - Page Not Found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", error="500 - Internal Server Error"), 500

if __name__ == '__main__':
    app.run(debug=True)
