from flask import Flask, render_template, redirect, url_for
import json

from services.triage_service import process_dataset
from services.stats_service import get_stats
from services.evaluation_service import calculate_accuracy

from flask import send_file

import os
import pandas as pd
from flask import request

from config import GEMINI_API_KEY

app = Flask(__name__)


@app.route("/")
def dashboard():

    stats = get_stats()

    accuracy = calculate_accuracy()

    try:
        with open("data/results.json", "r") as f:
            results = json.load(f)
    except:
        results = []

    return render_template(
        "dashboard.html",
        stats=stats,
        results=results,
        accuracy=accuracy
    )

@app.route("/export")
def export_results():

    import csv

    with open("data/results.json", "r") as f:
        results = json.load(f)

    csv_file = "data/export.csv"

    with open(
        csv_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "ID",
            "Category",
            "Priority",
            "Confidence"
        ])

        for item in results:

            writer.writerow([
                item["id"],
                item["category"],
                item["priority"],
                item["confidence"]
            ])

    return send_file(
        csv_file,
        as_attachment=True
    )

@app.route("/analyze")
def analyze():

    try:

        process_dataset()

        return redirect(url_for("results"))

    except Exception as e:

        return f"""
        <h2>Error while processing dataset</h2>
        <pre>{str(e)}</pre>
        """


@app.route("/results")
def results():

    try:
        with open("data/results.json", "r") as f:
            results_data = json.load(f)

    except:
        results_data = []

    return render_template(
        "results.html",
        results=results_data
    )


@app.route("/evaluation")
def evaluation():

    accuracy = calculate_accuracy()

    return render_template(
        "evaluation.html",
        accuracy=accuracy
    )

@app.route("/upload", methods=["POST"])
def upload():

    file = request.files["file"]

    if file.filename == "":
        return redirect("/")

    filepath = os.path.join(
        "uploads",
        file.filename
    )

    file.save(filepath)

    df = pd.read_csv(filepath)

    messages = []

    for index, row in df.iterrows():

        messages.append({
            "id": f"MSG-{index+1:03}",
            "message": str(row["message"])
        })

    with open(
        "data/dataset.json",
        "w"
    ) as f:
        json.dump(
            messages,
            f,
            indent=4
        )

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)