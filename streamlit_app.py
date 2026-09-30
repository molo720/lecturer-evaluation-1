"""EvalAI Streamlit – Nigerian lecturer evaluation (12k synthetic + Model Evaluation)"""
import json, random, hashlib
from pathlib import Path
import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

st.set_page_config(page_title="EvalAI", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")
BASE, DATA_DIR = Path(__file__).parent, Path(__file__).parent / "data"
CSV_PATH = DATA_DIR / "synthetic_evaluations.csv"
USERS = {"admin": hashlib.sha256(b"admin123").hexdigest(), "staff": hashlib.sha256(b"staff123").hexdigest()}

POS = ["Explains concepts clearly and with good examples.", "Breaks down difficult topics well.", "Always punctual and well prepared.", "Available for students after class.", "Fair grading with useful feedback.", "Uses WhatsApp group effectively for updates.", "Encourages questions and class participation.", "Shares slides and notes on the portal."]
NEG = ["Explanations are confusing and rushed.", "Often late or cancels without notice.", "Hard to reach outside lecture hours.", "Grading feels unfair and opaque.", "Does not share materials or notes.", "Ignores student questions in class.", "Poor communication about tests and venues.", "Reads slides without proper explanation."]
NEU = ["Follows the standard syllabus adequately.", "Punctuality and teaching are average.", "Communication is normal for a large class."]
COURSES = [("CSC410","Special Computing"),("CSC412","Data Science & Big Data"),("CSC406","Cloud Computing"),("CSC101","Intro to Computer Science"),("CSC408","Machine Learning"),("CSC302","Database Design"),("CSC304","Operating Systems"),("CSC201","Data Structures"),("CSC401","Artificial Intelligence"),("CSC403","Computer Networks")]
LECTURERS = ["Dr. Okafor","Dr. Adeyemi","Prof. Martins","Dr. Faith","Prof. Balogun","Dr. Chukwu","Dr. (Mrs) Adeleke","Dr. Okonkwo","Prof. Eze","Dr. Bello","Dr. Adebayo","Dr. Yusuf","Dr. Nwosu","Dr. Akinola","Prof. Ibrahim"]

def generate_dataset(n=12000):
    random.seed(42)
    rows = []
    for i in range(n):
        target = random.choices(["positive","negative","neutral"], weights=[0.42,0.38,0.20])[0]
        bank = {"positive": POS, "negative": NEG, "neutral": NEU}[target]
        k = random.randint(1, 3)
        comment = " ".join(random.sample(bank, min(k, len(bank))))
        rating = {"positive": random.choice([4,5]), "negative": random.choice([1,2]), "neutral": 3}[target]
        ccode, cname = random.choice(COURSES)
        rows.append({"id": i+1, "lecturer_name": random.choice(LECTURERS), "course": cname, "course_code": ccode,
                     "rating": rating, "comment": comment, "document_sentiment": target, "aspect_labels": "[]"})
    return pd.DataFrame(rows)

def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None

def login_form():
    st.markdown("## 🎓 EvalAI Login")
    st.caption("Lecturer Evaluation & Sentiment Analysis (Nigeria)")
    with st.form("login"):
        user = st.text_input("Username", placeholder="admin or staff")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Sign in", use_container_width=True):
            h = hashlib.sha256(pwd.encode()).hexdigest()
            if user in USERS and USERS[user] == h:
                st.session_state.logged_in = True
                st.session_state.username = user
                st.session_state.role = "admin" if user == "admin" else "staff"
                st.rerun()
            else:
                st.error("Invalid credentials. Try admin / admin123 or staff / staff123")

@st.cache_data(show_spinner="Loading Nigerian evaluation dataset…")
def load_dataset():
    if CSV_PATH.exists():
        return pd.read_csv(CSV_PATH)
    DATA_DIR.mkdir(exist_ok=True)
    df = generate_dataset(12000)
    df.to_csv(CSV_PATH, index=False)
    return df

@st.cache_resource(show_spinner="Training SVM & Naive Bayes…")
def train_models(df):
    texts, labels = df["comment"].astype(str).tolist(), df["document_sentiment"].astype(str).tolist()
    vec = TfidfVectorizer(max_features=4000, ngram_range=(1, 2), stop_words="english")
    X = vec.fit_transform(texts)
    Xtr, Xte, ytr, yte = train_test_split(X, labels, test_size=0.2, random_state=42, stratify=labels)
    svm, nb = LinearSVC(random_state=42, dual="auto"), MultinomialNB()
    svm.fit(Xtr, ytr); nb.fit(Xtr, ytr)
    classes = ["positive", "neutral", "negative"]
    ys, yn = svm.predict(Xte), nb.predict(Xte)
    m = {"n_train": len(ytr), "n_test": len(yte), "classes": classes,
         "svm": {"accuracy": float(accuracy_score(yte, ys)), "report": classification_report(yte, ys, output_dict=True), "cm": confusion_matrix(yte, ys, labels=classes).tolist()},
         "nb": {"accuracy": float(accuracy_score(yte, yn)), "report": classification_report(yte, yn, output_dict=True), "cm": confusion_matrix(yte, yn, labels=classes).tolist()}}
    return vec, {"svm": svm, "nb": nb}, m

def predict(text, vec, models):
    return models["svm"].predict(vec.transform([text]))[0] if text and models else "neutral"

def page_eval(df, vec, models):
    st.header("📝 Student Evaluation")
    with st.form("eval"):
        c1, c2 = st.columns(2)
        with c1:
            lecturer = st.selectbox("Lecturer", sorted(df["lecturer_name"].unique()))
            course = st.selectbox("Course", sorted(df["course"].unique()))
        with c2:
            rating = st.slider("Rating", 1, 5, 3)
            comment = st.text_area("Feedback", height=120)
        if st.form_submit_button("Submit", use_container_width=True):
            if not comment.strip():
                st.warning("Write a comment.")
            else:
                st.success(f"Submitted! Sentiment: **{predict(comment, vec, models).upper()}**")
                st.info(f"{lecturer} · {course} · {rating}/5")

def page_dash(df):
    st.header("📊 Dashboard")
    a,b,c,d = st.columns(4)
    a.metric("Evaluations", f"{len(df):,}"); b.metric("Lecturers", df["lecturer_name"].nunique())
    c.metric("Courses", df["course"].nunique()); d.metric("Avg rating", f"{df['rating'].mean():.2f}")
    st.bar_chart(df["document_sentiment"].value_counts())
    st.bar_chart(df.groupby("lecturer_name")["rating"].mean().sort_values(ascending=False))
    st.dataframe(df[["lecturer_name","course","rating","document_sentiment","comment"]].head(25), use_container_width=True)

def page_sent(df, vec, models):
    st.header("🔍 Sentiment Analysis")
    text = st.text_area("Paste feedback", height=150)
    if st.button("Analyse", use_container_width=True) and text.strip():
        pred = predict(text, vec, models)
        col = {"positive":"green","negative":"red","neutral":"orange"}.get(pred,"gray")
        st.markdown(f"### Predicted: :{col}[**{pred.upper()}**]")

def page_report(df):
    st.header("👤 Lecturer Report")
    chosen = st.selectbox("Lecturer", sorted(df["lecturer_name"].unique()))
    sub = df[df["lecturer_name"]==chosen]
    st.metric("Evaluations", len(sub)); st.metric("Avg rating", f"{sub['rating'].mean():.2f}")
    st.bar_chart(sub["document_sentiment"].value_counts())
    for _, r in sub.head(12).iterrows():
        st.markdown(f"- **{r['document_sentiment']}** ({r['rating']}/5): {r['comment'][:200]}")

def page_model(df, m):
    st.header("📈 Model Evaluation – SVM vs Naive Bayes")
    st.success(f"Dataset: **{len(df):,}** · Train {m['n_train']:,} / Test {m['n_test']:,}")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("SVM"); st.metric("Accuracy", f"{m['svm']['accuracy']:.4f}")
        st.dataframe(pd.DataFrame(m["svm"]["cm"], index=m["classes"], columns=m["classes"]), use_container_width=True)
        st.json(m["svm"]["report"])
    with c2:
        st.subheader("Naive Bayes"); st.metric("Accuracy", f"{m['nb']['accuracy']:.4f}")
        st.dataframe(pd.DataFrame(m["nb"]["cm"], index=m["classes"], columns=m["classes"]), use_container_width=True)
        st.json(m["nb"]["report"])

def main():
    init_session()
    if not st.session_state.logged_in:
        login_form(); st.caption("Demo: **admin / admin123** or **staff / staff123**"); return
    st.sidebar.title("EvalAI")
    st.sidebar.markdown(f"**{st.session_state.username}** ({st.session_state.role})")
    page = st.sidebar.radio("Navigate", ["Student Evaluation","Dashboard","Sentiment Analysis","Lecturer Report","Model Evaluation","Logout"])
    df = load_dataset()
    vec, models, metrics = train_models(df)
    if page == "Logout":
        st.session_state.logged_in = False; st.session_state.role = None; st.session_state.username = None; st.rerun()
    elif page == "Student Evaluation": page_eval(df, vec, models)
    elif page == "Dashboard": page_dash(df)
    elif page == "Sentiment Analysis": page_sent(df, vec, models)
    elif page == "Lecturer Report": page_report(df)
    elif page == "Model Evaluation": page_model(df, metrics)

if __name__ == "__main__":
    main()
