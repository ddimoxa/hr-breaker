from __future__ import annotations

import hmac
import os

import streamlit as st


def _auth_enabled() -> bool:
    if os.getenv("HR_BREAKER_AUTH_ENABLED", "").lower() in ("0", "false", "no"):
        return False
    # Enable automatically if credentials are provided.
    if os.getenv("HR_BREAKER_AUTH_PASSWORD") and os.getenv("HR_BREAKER_AUTH_USERNAME"):
        return True
    return os.getenv("HR_BREAKER_AUTH_ENABLED", "").lower() in ("1", "true", "yes")


def _check_login(username: str, password: str) -> bool:
    expected_user = os.getenv("HR_BREAKER_AUTH_USERNAME", "")
    expected_pass = os.getenv("HR_BREAKER_AUTH_PASSWORD", "")
    if not expected_user or not expected_pass:
        return False
    # Constant-time compare to avoid trivial timing attacks.
    return hmac.compare_digest(username, expected_user) and hmac.compare_digest(
        password, expected_pass
    )


def require_auth() -> None:
    """Gate the Streamlit app behind a simple login form (env-configured)."""
    if not _auth_enabled():
        return

    if st.session_state.get("auth_ok"):
        return

    st.title("HR-Breaker Login")
    st.caption("Authentication is enabled for this instance.")

    with st.form("login", clear_on_submit=False):
        username = st.text_input("Username", value="")
        password = st.text_input("Password", value="", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if _check_login(username, password):
            st.session_state["auth_ok"] = True
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()


def logout_button() -> None:
    if not _auth_enabled():
        return
    if st.sidebar.button("Logout"):
        st.session_state.pop("auth_ok", None)
        st.rerun()

