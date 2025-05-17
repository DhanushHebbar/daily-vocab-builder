import csv
import json
import os
from datetime import date
from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_PATH = os.path.join(BASE_DIR, "..", "data", "user_data.json")

def export_progress_csv(filepath="progress_report.csv"):
    with open(USER_DATA_PATH, "r") as f:
        data = json.load(f)

    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Date", "Words Learned"])
        for date_str, words in data.get("learned_words", {}).items():
            writer.writerow([date_str, ", ".join(words)])

    return filepath

def export_progress_pdf(filepath="progress_report.pdf"):
    with open(USER_DATA_PATH, "r") as f:
        data = json.load(f)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Progress Report", ln=True, align="C")

    for date_str, words in data.get("learned_words", {}).items():
        pdf.cell(200, 10, txt=f"{date_str}: {', '.join(words)}", ln=True)

    pdf.output(filepath)
    return filepath
