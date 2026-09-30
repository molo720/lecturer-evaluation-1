"""Training entry point — same structure as original (Nigerian synthetic data + SVM/NB)."""
import os
import json
import random
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

random.seed(42)
np.random.seed(42)

def generate_synthetic_dataset(num_samples=1600):
    # Nigerian lecturers / courses — same style as original training pipeline
    courses = [
        ("CSC410", "Special Computing"), ("CSC412", "Data Science & Big Data"),
        ("CSC406", "Cloud Computing Architectures"), ("CSC101", "Introduction to Computer Science"),
        ("CSC408", "Machine Learning & Neural Nets"), ("CSC302", "Database Design & Management"),
    ]
    lecturers = [
        "Dr. Okafor", "Dr. Adeyemi", "Prof. Martins", "Dr. Faith",
        "Dr. Pomele", "Prof. Balogun", "Dr. Chukwu", "Dr. (Mrs) Adeleke",
    ]
    pos = [
        "Explains complex concepts with clarity and precision.",
        "Always punctual and starts every class right on time.",
        "Grading is fair, objective, and transparently communicated.",
        "Always available during office hours for student consultation.",
    ]
    neg = [
        "Explanations are confusing and lack structure.",
        "Habitually late to lectures and wastes valuable class time.",
        "Grading is arbitrary, inconsistent, and unfairly penalized.",
        "Virtually impossible to locate outside scheduled lecture hours.",
    ]
    neu = [
        "Lectures follow the textbook explanations adequately.",
        "The course follows the institutional standard syllabus.",
    ]
    rows = []
    for i in range(num_samples):
        target = random.choices(["positive", "negative", "neutral"], weights=[0.42, 0.38, 0.20])[0]
        bank = {"positive": pos, "negative": neg, "neutral": neu}[target]
        comment = " ".join(random.sample(bank, k=min(2, len(bank))))
        rating = {"positive": random.choice([4, 5]), "negative": random.choice([1, 2]), "neutral": 3}[target]
        ccode, cname = random.choice(courses)
        rows.append({
            "id": i + 1,
            "lecturer_name": random.choice(lecturers),
            "course": cname,
            "course_code": ccode,
            "rating": rating,
            "comment": comment,
            "document_sentiment": target,
        })
    return pd.DataFrame(rows)

def main():
    print("Training SVM and Naive Bayes on Nigerian synthetic evaluations...")
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    df = generate_synthetic_dataset(1600)
    df.to_csv("data/synthetic_evaluations.csv", index=False)
    texts = df["comment"].astype(str).tolist()
    labels = df["document_sentiment"].astype(str).tolist()
    vec = TfidfVectorizer(max_features=4000, ngram_range=(1, 2), stop_words="english")
    X = vec.fit_transform(texts)
    Xtr, Xte, ytr, yte = train_test_split(X, labels, test_size=0.2, random_state=42, stratify=labels)
    svm = LinearSVC(random_state=42, dual="auto")
    svm.fit(Xtr, ytr)
    nb = MultinomialNB()
    nb.fit(Xtr, ytr)
    classes = ["positive", "neutral", "negative"]
    def pack(model):
        pred = model.predict(Xte)
        p, r, f, _ = precision_recall_fscore_support(yte, pred, average="macro", zero_division=0)
        _, _, wf, _ = precision_recall_fscore_support(yte, pred, average="weighted", zero_division=0)
        return {
            "accuracy": float(accuracy_score(yte, pred)),
            "macro_precision": float(p),
            "macro_recall": float(r),
            "macro_f1": float(f),
            "weighted_f1": float(wf),
            "confusion_matrix": confusion_matrix(yte, pred, labels=classes).tolist(),
            "classes": classes,
        }
    metrics = {
        "document_level": {
            "majority_baseline_accuracy": float(pd.Series(yte).value_counts(normalize=True).max()),
            "svm": pack(svm),
            "naive_bayes": pack(nb),
        },
        "aspect_level": [],
    }
    with open("data/model_evaluation_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    with open("model_evaluation_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    import joblib
    joblib.dump(svm, "models/svm_document.pkl")
    joblib.dump(nb, "models/nb_document.pkl")
    joblib.dump(vec, "models/vectorizer_document.pkl")
    print("Training complete. Metrics written to data/model_evaluation_metrics.json")

if __name__ == "__main__":
    main()
