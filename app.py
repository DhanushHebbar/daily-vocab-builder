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
from utils.progress import get_progress_summary
from utils.export import export_progress_csv, export_progress_pdf
from utils.motivation import get_daily_motivation

app = Flask(__name__)

# ------------------------------------------
# Home Route
# ------------------------------------------
@app.route('/', methods=["GET", "POST"])
def index():
    word = get_word_of_the_day()
    progress = get_progress_summary()
    dashboard = get_dashboard()
    motivation = get_daily_motivation()
    sentence_feedback = None

    if request.method == "POST":
        if request.form.get("new_sentence_request"):
            sentence_feedback = None
        else:
            user_sentence = request.form.get("sentence", "").strip().lower()
            if word["word"].lower() in user_sentence:
                sentence_feedback = "✅ Great! You've used the word correctly."
            else:
                sentence_feedback = "❌ Try again. Make sure you include the word in your sentence."

    return render_template(
        "index.html",
        word=word,
        progress=progress,
        dashboard=dashboard,
        motivation=motivation,
        sentence_feedback=sentence_feedback
    )


# ------------------------------------------
# Review Words Route
# ------------------------------------------
@app.route("/review")
def review():
    due_words = get_words_due_for_review()
    return render_template("review.html", due_words=due_words)

@app.route("/mark_reviewed", methods=["POST"])
def mark_reviewed():
    word = request.form.get("word")
    if word:
        update_review_schedule(word)
    return redirect(url_for('review'))


# ------------------------------------------
# Set Goals Route
# ------------------------------------------
@app.route("/set_goals", methods=["GET", "POST"])
def set_goals():
    BASE_GOALS = {"daily_goal": 1, "weekly_goal": 7}

    if not os.path.exists(USER_DATA_PATH):
        with open(USER_DATA_PATH, "w") as f:
            json.dump(BASE_GOALS, f, indent=2)

    with open(USER_DATA_PATH, "r") as f:
        user_data = json.load(f)

    feedback = ""

    if request.method == "POST":
        try:
            daily_goal = int(request.form.get("daily_goal", 1))
            weekly_goal = int(request.form.get("weekly_goal", 7))
            user_data["daily_goal"] = daily_goal
            user_data["weekly_goal"] = weekly_goal

            with open(USER_DATA_PATH, "w") as f:
                json.dump(user_data, f, indent=2)

            feedback = "✅ Goals updated successfully!"
        except ValueError:
            feedback = "❌ Invalid input. Please enter valid numbers."

    return render_template("set_goals.html", user_data=user_data, feedback=feedback)


# ------------------------------------------
# Word Games Route
# ------------------------------------------
@app.route("/games", methods=["GET", "POST"])
def games():
    with open("data/word_data.json", "r", encoding="utf-8") as f:
        words = json.load(f)

    synonym_words = [w for w in words if w.get("synonyms")]

    if len(synonym_words) < 2:
        return "❌ Not enough words with synonyms to play the game."

    if request.method == "POST":
        quiz_word_text = request.form.get("quiz_word")
        quiz_word = next((w for w in synonym_words if w["word"] == quiz_word_text), None)
        if not quiz_word:
            return "❌ Quiz word not found."

        correct_synonyms = [syn.lower() for syn in quiz_word["synonyms"]]
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


# ------------------------------------------
# Sentence Feedback Page (Manual Access)
# ------------------------------------------
@app.route("/sentence_feedback", methods=["GET", "POST"])
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


# ------------------------------------------
# Export Routes
# ------------------------------------------
@app.route("/export/csv")
def export_csv():
    path = export_progress_csv()
    return send_file(path, as_attachment=True)

@app.route("/export/pdf")
def export_pdf():
    path = export_progress_pdf()
    return send_file(path, as_attachment=True)


# ------------------------------------------
# Historical Word of the Day
# ------------------------------------------
@app.route("/historical_word", methods=["GET", "POST"])
def historical_word():
    word = None
    if request.method == "POST":
        era = request.form.get("era")
        word = get_word_by_era(era)
    return render_template("historical_word.html", word=word)


# ------------------------------------------
# Error Handlers
# ------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", error="404 - Page Not Found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", error="500 - Internal Server Error"), 500


@app.route('/submit_sentence', methods=['POST'])
def submit_sentence():
    data = request.get_json()
    sentence = data.get('sentence', '')
    word = get_word_of_the_day()['word']

    if word.lower() in sentence.lower():
        feedback = f"✅ Good job! You used '{word}' correctly in a sentence."
    else:
        feedback = f"❌ Oops! Your sentence must include the word '{word}'."

    return jsonify({'feedback': feedback})


# ------------------------------------------
# Main Entry
# ------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
