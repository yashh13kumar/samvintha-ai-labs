import streamlit as st
from langchain_community.llms import Ollama
from db_utils import (
    init_db, get_user_profile, save_user_profile,
    save_chat_message, get_chat_history, verify_password
)

# ---- Init DB ----
init_db()

# ---- Setup LLM ----
llm = Ollama(model="llama3")

# ---- Soft Profile Questions ----
profile_questions = [
    {"key": "name", "q": "👋 What should I call you?"},
    {"key": "age_group", "q": "📊 Your age group?", "options": ["<25", "25–35", "35–50", ">50"]},
    {"key": "income_range", "q": "💼 Monthly income range?", "options": ["<30K", "30K–50K", "50K–1L", ">1L"]},
    {"key": "savings_style", "q": "💰 Savings style?", "options": ["Fixed", "Varies", "Rarely save"]},
    {"key": "marital_status", "q": "❤️ Are you married?", "options": ["Yes", "No"]},
    {"key": "financial_style", "q": "🧠 Your financial style?", "options": ["Planner", "Impulsive spender", "Flexible saver"]}
]

# ---- Streamlit UI Setup ----
st.set_page_config(page_title="FinAI", layout="centered")
st.title("🤖 FinAI")
st.subheader("Chat with your personal financial AI assistant")

# ---- Logout Button ----
if st.session_state.get("logged_in"):
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

# ---- Login Interface ----
if not st.session_state.get("logged_in"):
    st.sidebar.header("🔐 Login")
    username = st.sidebar.text_input("Username", placeholder="Enter your username")
    password = st.sidebar.text_input("Password (min 8 characters)", type="password")

    if st.sidebar.button("Login"):
        if not username or not password:
            st.warning("Please enter both username and password.")
        elif len(password) < 8:
            st.error("Password must be at least 8 characters.")
        else:
            st.session_state.user_id = username
            st.session_state.password = password
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# ---- Logged In ----
user_id = st.session_state.user_id
password = st.session_state.password

# ---- Warn on first login ----
if not verify_password(user_id, password):
    st.sidebar.warning("🔒 New user or password mismatch. Profile will be saved on submission.")

# ---- Load Existing Profile ----
existing_profile = get_user_profile(user_id)
profile_data = {} if not existing_profile else {
    "user_id": existing_profile[0],
    "name": existing_profile[1],
    "age_group": existing_profile[2],
    "income_range": existing_profile[3],
    "savings_style": existing_profile[4],
    "marital_status": existing_profile[5],
    "financial_style": existing_profile[6],
    "password": existing_profile[7]
}

# ---- Init Chat Session ----
if "messages" not in st.session_state:
    st.session_state.messages = get_chat_history(user_id)

if "profile_index" not in st.session_state:
    st.session_state.profile_index = 0

# ---- Profile Completion Check ----
def is_profile_complete(profile):
    return all(q["key"] in profile and profile[q["key"]] for q in profile_questions)

# ---- Ask Profile Questions ----
if not is_profile_complete(profile_data):
    q = profile_questions[st.session_state.profile_index]
    key = q["key"]
    prompt = q["q"]
    options = q.get("options")

    with st.container():
        if options:
            user_input = st.selectbox(prompt, options, key=f"sel_{key}")
        else:
            user_input = st.text_input(prompt, key=f"text_{key}")
        submitted = st.button("Submit", key=f"btn_{key}")

    if submitted and user_input:
        profile_data[key] = user_input.strip()
        profile_data["password"] = password
        save_user_profile(user_id, profile_data)

        reply_map = {
            "name": f"Nice to meet you, {user_input.strip().capitalize()} 😊",
            "age_group": f"Cool — {user_input} it is!",
            "income_range": f"Got it! That helps me understand your budget better.",
            "savings_style": f"That's a good habit to track. Thanks!",
            "marital_status": f"Alright, noted!",
            "financial_style": f"Interesting! That says a lot about your decisions."
        }

        st.session_state.messages.append({"role": "user", "content": user_input})
        assistant_msg = reply_map.get(key, "Thanks! Got it ✅")
        st.session_state.messages.append({"role": "assistant", "content": assistant_msg})

        save_chat_message(user_id, "user", user_input)
        save_chat_message(user_id, "assistant", assistant_msg)

        st.session_state.profile_index += 1
        if st.session_state.profile_index >= len(profile_questions):
            st.success("🎉 Profile setup complete! You can now chat with FinAI.")

else:
    # ---- Chat Mode ----
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    user_input = st.chat_input("Type your message...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        save_chat_message(user_id, "user", user_input)

        memory_context = "\n".join([f"{k}: {v}" for k, v in profile_data.items() if k != "password"])
        chat_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        full_prompt = f"{memory_context}\n\n{chat_context}\nassistant:"

        response = llm.invoke(full_prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        save_chat_message(user_id, "assistant", response)

        st.chat_message("assistant").write(response)
