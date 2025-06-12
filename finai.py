import streamlit as st
from langchain_community.llms import Ollama # type: ignore
from db_utils import (
    init_db, get_user_profile, save_user_profile,
    save_chat_message, get_chat_history, verify_password,
    fetch_recent_emails, fetch_sms_data
)

# ---- Init DB ----
init_db()

# ---- Setup LLM ----
llm = Ollama(model="llama3")

# ---- Extended Profile Questions for better advice ----
profile_questions = [
    {"key": "name", "q": "👋 What should I call you?"},
    {"key": "age_group", "q": "📊 Your age group?", "options": ["<25", "25–35", "35–50", ">50"]},
    {"key": "income_range", "q": "💼 Monthly income range?", "options": ["<30K", "30K–50K", "50K–1L", ">1L"]},
    {"key": "savings_style", "q": "💰 Savings style?", "options": ["Fixed", "Varies", "Rarely save"]},
    {"key": "marital_status", "q": "❤️ Are you married?", "options": ["Yes", "No"]},
    {"key": "financial_style", "q": "🧠 Your financial style?", "options": ["Planner", "Impulsive spender", "Flexible saver"]},
    {"key": "monthly_expenses", "q": "💸 Approximate monthly expenses?", "options": ["<20K", "20K–40K", "40K–70K", ">70K"]},
    {"key": "investment_experience", "q": "📈 Do you invest regularly?", "options": ["Yes", "No", "Sometimes"]},
    {"key": "debt_status", "q": "💳 Do you have outstanding debts?", "options": ["No debts", "Some debts", "Heavy debts"]},
    {"key": "financial_goals", "q": "🎯 Your main financial goal?", "options": ["Savings", "Investment", "Debt clearance", "Retirement planning"]}
]

# ---- Streamlit UI Setup ----
st.set_page_config(page_title="FinAI", layout="centered")
st.title("🤖 FinAI")
st.subheader("Chat with your personal financial AI assistant")

# ---- Sidebar: Login + Email/SMS Fetch Section ----
with st.sidebar:
    if st.session_state.get("logged_in"):
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.experimental_rerun()

        st.markdown("---")
        st.header("📧 Fetch Emails & SMS")
        email_user = st.text_input("Gmail Address", key="email_user")
        app_password = st.text_input("App Password (Gmail IMAP)", type="password", key="app_password")
        fetch_emails_btn = st.button("Fetch Recent Emails")
        fetch_sms_btn = st.button("Fetch SMS Data")

        if fetch_emails_btn:
            if email_user and app_password:
                with st.spinner("Fetching emails..."):
                    emails = fetch_recent_emails(email_user, app_password, n=5)
                st.markdown("**Recent Emails:**")
                for e in emails:
                    st.text(e)
            else:
                st.warning("Please enter Gmail address and app password.")

        if fetch_sms_btn:
            with st.spinner("Fetching SMS data..."):
                sms_list = fetch_sms_data()
            st.markdown("**Recent SMS:**")
            for sms in sms_list:
                st.text(sms)

    else:
        st.header("🔐 Login")
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password (min 8 characters)", type="password")

        if st.button("Login"):
            if not username or not password:
                st.warning("Please enter both username and password.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                st.session_state.user_id = username
                st.session_state.password = password
                st.session_state.logged_in = True
                st.experimental_rerun()
        st.stop()

# ---- After login, main app logic ----
user_id = st.session_state.user_id
password = st.session_state.password

# ---- Verify or warn new user ----
if not verify_password(user_id, password):
    st.sidebar.warning("🔒 New user or password mismatch. Profile will be saved on submission.")

# ---- Load existing profile ----
existing_profile = get_user_profile(user_id)
profile_data = {} if not existing_profile else {
    "user_id": existing_profile[0],
    "name": existing_profile[1],
    "age_group": existing_profile[2],
    "income_range": existing_profile[3],
    "savings_style": existing_profile[4],
    "marital_status": existing_profile[5],
    "financial_style": existing_profile[6],
    "password": existing_profile[7],
    "monthly_expenses": existing_profile[8] if len(existing_profile) > 8 else "",
    "investment_experience": existing_profile[9] if len(existing_profile) > 9 else "",
    "debt_status": existing_profile[10] if len(existing_profile) > 10 else "",
    "financial_goals": existing_profile[11] if len(existing_profile) > 11 else "",
}

# ---- Initialize chat session ----
if "messages" not in st.session_state:
    st.session_state.messages = get_chat_history(user_id)

if "profile_index" not in st.session_state:
    st.session_state.profile_index = 0

# ---- Profile completion checker ----
def is_profile_complete(profile):
    return all(q["key"] in profile and profile[q["key"]] for q in profile_questions)

# ---- Ask profile questions if incomplete ----
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
            "financial_style": f"Interesting! That says a lot about your decisions.",
            "monthly_expenses": f"Thanks for sharing your expenses info.",
            "investment_experience": f"Good to know your investing habits.",
            "debt_status": f"Debt status noted.",
            "financial_goals": f"Your goals are clear — I will keep that in mind."
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

        # Compose prompt with profile and chat history
        memory_context = "\n".join([f"{k}: {v}" for k, v in profile_data.items() if k != "password"])
        chat_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        full_prompt = f"{memory_context}\n\n{chat_context}\nassistant:"

        response = llm.invoke(full_prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        save_chat_message(user_id, "assistant", response)

        st.chat_message("assistant").write(response)
