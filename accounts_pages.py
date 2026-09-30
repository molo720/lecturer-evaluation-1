"""Account management — same as Flask /admin/users and /change_password."""
from werkzeug.security import check_password_hash, generate_password_hash
import streamlit as st
import pandas as pd

def list_users(get_connection, DATABASE_PATH):
    db = get_connection(DATABASE_PATH)
    rows = db.execute(
        "SELECT id, username, role, lecturer_name, full_name FROM users ORDER BY role, username"
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]

def create_lecturer_account(get_connection, DATABASE_PATH, lecturer_name, username, password):
    lecturer_name = (lecturer_name or "").strip()
    username = (username or "").strip().lower()
    password = password or ""
    if not lecturer_name or not username or not password:
        return False, "All account fields are required."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."
    db = get_connection(DATABASE_PATH)
    try:
        db.execute(
            "INSERT INTO users (username, password_hash, role, lecturer_name, full_name) VALUES (?, ?, ?, ?, ?)",
            (username, generate_password_hash(password), "lecturer", lecturer_name, lecturer_name),
        )
        db.commit()
        db.close()
        return True, f"Lecturer account created for {lecturer_name}."
    except Exception:
        db.close()
        return False, "That username is already in use."

def admin_reset_password(get_connection, DATABASE_PATH, user_id, new_password):
    new_password = (new_password or "").strip()
    if len(new_password) < 4:
        return False, "Password must be at least 4 characters."
    db = get_connection(DATABASE_PATH)
    user = db.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        db.close()
        return False, "Account not found."
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(new_password), user_id))
    db.commit()
    uname = user["username"]
    db.close()
    return True, f"Password updated for '{uname}'."

def admin_delete_user(get_connection, DATABASE_PATH, user_id, current_user_id, delete_feedback=False):
    if current_user_id == user_id:
        return False, "You cannot delete your own active administrator account."
    db = get_connection(DATABASE_PATH)
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        db.close()
        return False, "Account not found."
    username = user["username"]
    lec_name = user["lecturer_name"]
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    fb_count = 0
    if delete_feedback and lec_name:
        cur = db.execute("DELETE FROM feedback WHERE lecturer_name = ?", (lec_name,))
        fb_count = cur.rowcount
    db.commit()
    db.close()
    msg = f"User '{username}' was deleted successfully."
    if fb_count > 0:
        msg += f" Associated {fb_count} feedback evaluations for {lec_name} were also deleted."
    return True, msg

def change_own_password(get_connection, DATABASE_PATH, user_id, current_password, new_password, confirm):
    if not current_password or not new_password:
        return False, "All password fields are required."
    if new_password != confirm:
        return False, "New password and confirmation do not match."
    if len(new_password) < 4:
        return False, "Password must be at least 4 characters."
    db = get_connection(DATABASE_PATH)
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user or not check_password_hash(user["password_hash"], current_password):
        db.close()
        return False, "Current password is incorrect."
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(new_password), user_id))
    db.commit()
    db.close()
    return True, "Password updated successfully."

def page_accounts(get_connection, DATABASE_PATH):
    user = st.session_state.get("user")
    if not user or user.get("role") != "administrator":
        st.error("Administrator access required.")
        return
    st.header("Accounts")
    st.caption("Create lecturer login accounts and manage existing users (same as original admin users page).")
    st.subheader("Create lecturer account")
    with st.form("create_account"):
        c1, c2 = st.columns(2)
        with c1:
            lecturer_name = st.text_input("Full name / lecturer name *", placeholder="e.g. Dr. Okafor")
            username = st.text_input("Username *", placeholder="e.g. okafor")
        with c2:
            password = st.text_input("Password *", type="password", placeholder="Create a secure password")
        if st.form_submit_button("Create account", use_container_width=True):
            ok, msg = create_lecturer_account(get_connection, DATABASE_PATH, lecturer_name, username, password)
            if ok: st.success(msg)
            else: st.error(msg)
    st.divider()
    st.subheader("Existing accounts")
    users = list_users(get_connection, DATABASE_PATH)
    if not users:
        st.info("No users in the database.")
        return
    st.dataframe(pd.DataFrame(users)[["id", "username", "role", "lecturer_name", "full_name"]], use_container_width=True, hide_index=True)
    st.subheader("Reset password")
    with st.form("reset_pw"):
        options = {f"{u['username']} ({u['role']})": u["id"] for u in users}
        pick = st.selectbox("User", list(options.keys()))
        new_pw = st.text_input("New password", type="password")
        if st.form_submit_button("Update password", use_container_width=True):
            ok, msg = admin_reset_password(get_connection, DATABASE_PATH, options[pick], new_pw)
            if ok: st.success(msg)
            else: st.error(msg)
    st.subheader("Delete account")
    with st.form("delete_user"):
        options = {f"{u['username']} ({u['role']}) — id {u['id']}": u["id"] for u in users}
        pick = st.selectbox("User to delete", list(options.keys()))
        del_fb = st.checkbox("Also delete this lecturer's feedback evaluations")
        if st.form_submit_button("Delete account", type="primary"):
            ok, msg = admin_delete_user(get_connection, DATABASE_PATH, options[pick], user.get("id"), delete_feedback=del_fb)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

def page_change_password(get_connection, DATABASE_PATH):
    user = st.session_state.get("user")
    if not user:
        st.error("Please sign in first.")
        return
    st.header("Account security")
    st.caption(f"Signed in as: **{user.get('username')}** ({user.get('role', '')})")
    with st.form("change_pw"):
        current = st.text_input("Current password *", type="password")
        new_pw = st.text_input("New password *", type="password")
        confirm = st.text_input("Confirm new password *", type="password")
        if st.form_submit_button("Update password", use_container_width=True):
            ok, msg = change_own_password(get_connection, DATABASE_PATH, user["id"], current, new_pw, confirm)
            if ok: st.success(msg)
            else: st.error(msg)
