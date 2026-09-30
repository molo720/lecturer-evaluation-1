"""Upload evaluation data — same as Flask /upload (CSV or Excel)."""
import streamlit as st
import pandas as pd

def _analyze(comment, rating):
    try:
        from ml_engine import run_analysis
        return run_analysis(comment, rating)
    except Exception:
        if rating >= 4:
            sent = "positive"
        elif rating <= 2:
            sent = "negative"
        else:
            sent = "neutral"
        return {"document_sentiment": sent, "aspects": [], "comment": comment, "rating": rating}

def page_upload(get_connection, DATABASE_PATH):
    user = st.session_state.get("user")
    if not user or user.get("role") != "administrator":
        st.error("Administrator access required.")
        return

    st.header("Upload evaluation data")
    st.caption("Ingest institutional student evaluation datasets (CSV or Excel) — same as Flask /upload.")

    st.markdown(
        """
**Expected columns:** `comment`, `rating` (required).  
Optional: `lecturer_name` / `lecturer`, `course`, `course_code`.  
Student identity columns are optional and stored as anonymous.
"""
    )

    uploaded = st.file_uploader(
        "Select CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="Upload a file with at least comment and rating columns",
    )

    retrain_after = st.checkbox("Retrain models after import", value=False)

    if st.button("Upload and process dataset", type="primary", disabled=uploaded is None):
        if uploaded is None:
            st.error("No file selected.")
            return
        fn = uploaded.name.lower()
        try:
            if fn.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return

        cols_lower = {c.lower(): c for c in df.columns}
        if not {"comment", "rating"}.issubset(set(cols_lower.keys())):
            st.error(
                f"Uploaded file must contain 'comment' and 'rating' columns. Found: {list(df.columns)}"
            )
            return

        comment_col = cols_lower["comment"]
        rating_col = cols_lower["rating"]
        lec_col = cols_lower.get("lecturer_name") or cols_lower.get("lecturer")
        course_col = cols_lower.get("course")
        code_col = cols_lower.get("course_code")

        db = get_connection(DATABASE_PATH)
        count_added = 0
        results = []

        try:
            for _, row in df.iterrows():
                c_text = str(row[comment_col]).strip()
                if not c_text or c_text.lower() == "nan":
                    continue
                try:
                    r_val = int(row[rating_col])
                except Exception:
                    r_val = 3

                lec = (
                    str(row[lec_col]).strip()
                    if lec_col and pd.notna(row[lec_col])
                    else "Dr. Okafor"
                )
                crs = (
                    str(row[course_col]).strip()
                    if course_col and pd.notna(row[course_col])
                    else "Computer Science"
                )
                cdc = (
                    str(row[code_col]).strip()
                    if code_col and pd.notna(row[code_col])
                    else "CSC"
                )

                analysis = _analyze(c_text, r_val)
                sent = analysis.get("document_sentiment", "neutral")

                db.execute(
                    """
                    INSERT INTO feedback
                    (student_name, matric_number, lecturer_name, course, course_code, rating, comment, document_sentiment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    ("Anonymous", "ANON", lec, crs, cdc, r_val, c_text, sent),
                )

                if len(results) < 15:
                    results.append(
                        {
                            "lecturer": lec,
                            "course": crs,
                            "rating": r_val,
                            "document_sentiment": sent,
                            "comment": c_text[:120],
                        }
                    )
                count_added += 1

            db.commit()
        except Exception as e:
            try:
                db.close()
            except Exception:
                pass
            st.error(f"Error processing file: {e}")
            return
        finally:
            try:
                db.close()
            except Exception:
                pass

        st.success(f"Successfully imported and evaluated {count_added} records!")

        if results:
            st.subheader(f"Processed sample (first {len(results)} records)")
            st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

        if retrain_after and count_added > 0:
            with st.spinner("Retraining models on updated data…"):
                try:
                    from train_models import main as run_train
                    run_train()
                    try:
                        from ml_engine import load_all_models
                        load_all_models()
                    except Exception:
                        pass
                    st.success("Models retrained successfully.")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Retraining error: {e}")
