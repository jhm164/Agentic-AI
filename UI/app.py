import os
import urllib.error
import urllib.parse
import urllib.request

import streamlit as st

# FastAPI listens on whatever uvicorn uses in Agent/main.py (default 9005).
# Streamlit does not "listen" on that port — it calls this URL as an HTTP client.
_FASTAPI_HOST = os.getenv("FASTAPI_HOST", "127.0.0.1")
_FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "9005"))
FASTAPI_URL = f"http://{_FASTAPI_HOST}:{_FASTAPI_PORT}/chat"

st.title("🤖 My Local Chatbot")
st.caption(f"Backend: `{FASTAPI_URL}` (set FASTAPI_HOST / FASTAPI_PORT to match uvicorn)")

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Type your message here..."):
    
    # 1. Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 3. Call FastAPI GET /chat?message=... and stream SSE tokens progressively.
    with st.chat_message("assistant"):

        message_placeholder = st.empty()
        full_response = ""
        query = urllib.parse.urlencode({"message": prompt})
        req_url = f"{FASTAPI_URL}?{query}"
        try:
            with urllib.request.urlopen(req_url, timeout=120) as resp:
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

                    # Control marker from backend - do not render as chat text.
                    if current_event == "done" or data == "[DONE]":
                        break

                    full_response += data + "\n"
                    message_placeholder.markdown(full_response.rstrip("\n") + "▌")
        except urllib.error.HTTPError as e:
            full_response = f"HTTP error from API: {e.code} — {e.read().decode(errors='replace')}"
        except urllib.error.URLError as e:
            full_response = (
                f"Could not reach `{FASTAPI_URL}`. "
                f"Start the API (`Agent/main.py`) and ensure FASTAPI_PORT matches uvicorn "
                f"(default **{_FASTAPI_PORT}**). Reason: {e.reason}"
            )

        message_placeholder.markdown(full_response.rstrip("\n"))
        
    # 4. Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
