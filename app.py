import streamlit as st
from langchain_community.llms import Ollama

# Load LLaMA 3
llm = Ollama(model="llama3")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("LLaMA 3.1-8B Chatbot")

# Display chat history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# User Input
user_input = st.chat_input("Type your message...")

if user_input:
    # Store user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Format chat history as context
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    # Ensure the model remembers your name
    if "who are you" in user_input.lower():
        response = "I am Yash Kumar, your AI assistant!"
    else:
        response = llm.invoke(f"{context}\nAssistant:")  # Pass full conversation history

    # Store assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Display response
    st.chat_message("assistant").write(response)

