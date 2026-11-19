"""
auth.py
-------
Kaam: login aur naya account banane ka page (authentication).

Kaise kaam karta hai:
1. User ka username + password form me aata hai.
2. Password ko hash karke `.streamlit/users.json` me save karte hain
   (plain password kabhi save nahi hota).
3. Login hone par `st.session_state.user` me username aa jata hai.
4. Logout par wahi key delete ho jati hai.

Note: Ye simple college-project level login hai. Asli product me
database + email verification + OTP use hota hai.

Pehla demo account (jab tak koi naya account na bane):
    username: kisan
    password: kisan123
"""

import hashlib
import json
import os
import secrets
import textwrap

import streamlit as st

from style import GREEN, INK, MUTED

# Users kahan save honge (ye file git me nahi jati)
USERS_FILE = os.path.join(".streamlit", "users.json")

# Demo account -- pehli baar app kholne par yahi chalega
DEMO_USERNAME = "kisan"
DEMO_PASSWORD = "kisan123"

# Password hashing ki settings
HASH_ROUNDS = 120_000


# ---------------- Password helpers ----------------
def _hash_password(password: str, salt: str | None = None) -> str:
    """
    Password ko hash me badalta hai: "salt$hash".

    Hash se password wapas nahi ban sakta, isliye file me
    password padhne par bhi koi use nahi kar sakta.
    """
    if salt is None:
        salt = secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        HASH_ROUNDS,
    ).hex()

    return f"{salt}${digest}"


def _check_password(password: str, stored: str) -> bool:
    """User ke diye password ko saved hash se milata hai."""
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False

    return _hash_password(password, salt) == stored


# ---------------- Users file helpers ----------------
def _load_users() -> dict:
    """users.json padhta hai. File na mile to khali dict."""
    if not os.path.exists(USERS_FILE):
        return {}

    try:
        with open(USERS_FILE, encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_users(users: dict) -> None:
    """users.json me users likhta hai."""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)

    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=2, ensure_ascii=False)


def _ensure_demo_user() -> dict:
    """
    Pehli baar chalne par demo account bana deta hai,
    taaki app bina setup ke turant chale.
    """
    users = _load_users()

    if not users:
        users = {
            DEMO_USERNAME: {
                "password": _hash_password(DEMO_PASSWORD),
                "name": "Demo Kisan",
            }
        }
        _save_users(users)

    return users


# ---------------- Login / signup ka logic ----------------
def login(username: str, password: str):
    """
    Username + password check karta hai.

    Return: (success, message)
    """
    username = (username or "").strip().lower()

    if not username or not password:
        return False, "Username aur password dono bharein."

    users = _ensure_demo_user()

    if username not in users:
        return False, "Is username ka koi account nahi hai. New account banayein."

    if not _check_password(password, users[username]["password"]):
        return False, "Password galat hai. Dobara koshish karein."

    return True, f"Swagat hai, {users[username].get('name') or username}!"


def signup(username: str, password: str, confirm: str, name: str = ""):
    """
    Naya account banata hai.

    Return: (success, message)
    """
    username = (username or "").strip().lower()
    name = (name or "").strip()

    if len(username) < 3:
        return False, "Username kam se kam 3 akshar ka hona chahiye."

    if not username.replace("_", "").isalnum():
        return False, "Username me sirf letters, numbers aur _ chalein ge."

    if len(password) < 6:
        return False, "Password kam se kam 6 akshar ka rakhein."

    if password != confirm:
        return False, "Dono password ek jaise nahi hain."

    users = _ensure_demo_user()

    if username in users:
        return False, "Ye username pehle se liya hua hai. Doosra chunein."

    users[username] = {
        "password": _hash_password(password),
        "name": name or username.title(),
    }
    _save_users(users)

    return True, "Account ban gaya! Ab login karein."


def is_logged_in() -> bool:
    """Kya user login hai?"""
    return "user" in st.session_state


def current_user() -> str | None:
    """Login wale user ka naam."""
    return st.session_state.get("user")


def logout() -> None:
    """User ko logout karta hai."""
    st.session_state.pop("user", None)


# ---------------- Login page ka design ----------------
def _brand_panel():
    """Login page ke left taraf ka green panel."""
    html = f"""
    <div style="background: linear-gradient(150deg, {GREEN} 0%, #1F7A3D 60%, #2C8F4B 100%); border-radius: 18px; padding: 30px 28px; color: #FFFFFF; min-height: 430px; box-shadow: 0 10px 28px rgba(22, 101, 52, 0.20);">
    <div style="font-size: 12px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: #CFF3D8;">Cropora AI</div>
    <div style="font-size: 30px; font-weight: 800; line-height: 1.2; margin-top: 10px;">Mandi Bhav Bot</div>
    <div style="font-size: 15px; color: #DCF3E2; margin-top: 10px;">Login karke apna crop, mandi aur bechne ki salah dekho.</div>
    <div style="margin-top: 26px; font-size: 14px; line-height: 2; color: #EAF7EE;">
    <div>&#10003; 12 crops ka bhav, per kg aur per quintal</div>
    <div>&#10003; 10 mandiyon ka comparison</div>
    <div>&#10003; AI anumaan + kab beche ki salah</div>
    <div>&#10003; Hindi chatbot</div>
    </div>
    <div style="margin-top: 34px; background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.25); border-radius: 12px; padding: 12px 14px; font-size: 13px; color: #EAF7EE;">
    <b>Demo login</b><br>username: <b>{DEMO_USERNAME}</b> &nbsp;|&nbsp; password: <b>{DEMO_PASSWORD}</b>
    </div>
    </div>
    """
    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)


def _login_form():
    """Login tab ka form."""
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="jaise: kisan")
        password = st.text_input("Password", type="password", placeholder="******")
        submitted = st.form_submit_button("Login", type="primary")

    if not submitted:
        return

    ok, message = login(username, password)

    if ok:
        st.session_state.user = username.strip().lower()
        st.session_state.flash = message
        st.rerun()

    st.error(message)


def _signup_form():
    """Naya account tab ka form."""
    with st.form("signup_form"):
        name = st.text_input("Aapka naam", placeholder="jaise: Ramesh Kumar")
        username = st.text_input("Username", placeholder="kam se kam 3 akshar")
        password = st.text_input("Password", type="password", placeholder="kam se kam 6 akshar")
        confirm = st.text_input("Password dobara", type="password")
        submitted = st.form_submit_button("Create account", type="primary")

    if not submitted:
        return

    ok, message = signup(username, password, confirm, name)

    if ok:
        st.success(message)
    else:
        st.error(message)


def require_login() -> None:
    """
    App ka darwaza. Login nahi hai to login page dikha kar
    app ko wahin rok deta hai.
    """
    if is_logged_in():
        return

    # Page ke liye thodi jagah (form screen ke beech me)
    st.write("")
    st.write("")

    left, right = st.columns([1.05, 1], gap="large")

    with left:
        _brand_panel()

    with right:
        # Card jaisa look
        st.markdown(
            textwrap.dedent(
                f"""
                <div style="font-size: 22px; font-weight: 800; color: {INK}; margin-bottom: 2px;">Welcome back</div>
                <div style="font-size: 14px; color: {MUTED}; margin-bottom: 14px;">Login karein ya new account banayein.</div>
                """
            ).strip(),
            unsafe_allow_html=True,
        )

        tab_login, tab_signup = st.tabs(["Login", "New account"])

        with tab_login:
            _login_form()

        with tab_signup:
            _signup_form()

        st.caption(
            f"Password hash karke local file me rakha jata hai. "
            f"demo: {DEMO_USERNAME} / {DEMO_PASSWORD}"
        )

    st.stop()
