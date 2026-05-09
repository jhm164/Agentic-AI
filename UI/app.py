import os
import urllib.error
import urllib.parse
import urllib.request
import requests
import streamlit as st

_FASTAPI_HOST = os.getenv("FASTAPI_HOST", "127.0.0.1")
_FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "9005"))
_FASTAPI_BASE_URL = f"http://{_FASTAPI_HOST}:{_FASTAPI_PORT}"
FASTAPI_CHAT_URL = f"{_FASTAPI_BASE_URL}/chat"
FASTAPI_LOGIN_URL = f"{_FASTAPI_BASE_URL}/login"
FASTAPI_EMAIL_PENDING_URL = f"{_FASTAPI_BASE_URL}/email-approval/pending"
FASTAPI_EMAIL_APPROVE_URL = f"{_FASTAPI_BASE_URL}/email-approval/approve"

if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "approval_requested" not in st.session_state:
    st.session_state.approval_requested = False


def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Log In"):
        response = requests.post(
            FASTAPI_LOGIN_URL,
            json={"username": username, "password": password},
            timeout=30,
        )

        if response.status_code == 200:
            st.session_state.access_token = response.json().get("access_token")
            st.session_state.messages = []
            st.session_state.approval_requested = False
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid credentials")


def chat_interface():
    st.title("Chat with AI")
    st.caption(f"Backend: `{FASTAPI_CHAT_URL}`")

    if st.button("Logout"):
        st.session_state.access_token = None
        st.session_state.messages = []
        st.session_state.approval_requested = False
        st.rerun()

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    pending_email = None
    pending_fetch_error = None
    try:
        pending_resp = requests.get(FASTAPI_EMAIL_PENDING_URL, headers=headers, timeout=15)
        if pending_resp.status_code == 200:
            pending_email = pending_resp.json().get("pending")
        elif pending_resp.status_code != 404:
            pending_fetch_error = pending_resp.text
    except requests.RequestException:
        pending_fetch_error = "Could not reach approval endpoint."

    if pending_fetch_error:
        st.info(f"Approval status unavailable: {pending_fetch_error}")

    if st.session_state.approval_requested and pending_email:
        to_value = pending_email.get("to", "unknown") if pending_email else "unknown"
        subject_value = pending_email.get("subject", "unknown") if pending_email else "unknown"
        st.warning(
            f"Pending email approval: to `{to_value}` "
            f"(subject: `{subject_value}`)"
        )
        if st.button("Approve Send Email"):
            try:
                approve_resp = requests.post(
                    FASTAPI_EMAIL_APPROVE_URL,
                    headers=headers,
                    timeout=15,
                )
                if approve_resp.status_code == 200:
                    approved_payload = approve_resp.json()
                    resumed_message = approved_payload.get("assistant_message", "").strip()
                    if resumed_message:
                        st.session_state.messages.append(
                            {"role": "assistant", "content": resumed_message}
                        )
                    st.session_state.approval_requested = False
                    st.success("Email approved and resumed.")
                    st.rerun()
                else:
                    st.error(f"Approval failed: {approve_resp.text}")
            except requests.RequestException as e:
                st.error(f"Approval request failed: {e}")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not (prompt := st.chat_input("Type your message here...")):
        return

    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        query = urllib.parse.urlencode({"message": prompt})
        req_url = f"{FASTAPI_CHAT_URL}?{query}"
        request = urllib.request.Request(
            req_url,
            headers=headers,
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as resp:
                current_event = "message"
                for raw_line in resp:
                    line = raw_line.decode("utf-8", errors="replace").strip()

                    # Empty line marks end of an SSE event frame.
                    if not line:
                        current_event = "message"
                        continue

                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                        continue

                    if not line.startswith("data:"):
                        continue

                    data = line.split(":", 1)[1].lstrip()

                    if current_event == "done" or data == "[DONE]":
                        break

                    full_response += data + "\n"
                    message_placeholder.markdown(full_response.rstrip("\n") + "▌")
        except urllib.error.HTTPError as e:
            full_response = f"HTTP error from API: {e.code} — {e.read().decode(errors='replace')}"
        except urllib.error.URLError as e:
            full_response = (
                f"Could not reach `{FASTAPI_CHAT_URL}`. "
                f"Start the API (`Agent/main.py`) and ensure FASTAPI_PORT matches uvicorn "
                f"(default **{_FASTAPI_PORT}**). Reason: {e.reason}"
            )

        message_placeholder.markdown(full_response.rstrip("\n"))

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    if "[APPROVAL REQUIRED]" in full_response:
        st.session_state.approval_requested = True
        st.rerun()


if st.session_state.access_token is None:
    login()
else:
    chat_interface()
