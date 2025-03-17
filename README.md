# LLaMA-3.1-8B-Chatbot
LLaMA 3.1-8B Chatbot
A simple interactive chatbot powered by LLaMA 3.1-8B using Streamlit and Ollama. The chatbot maintains conversation history and can be customized to respond in a specific way, such as introducing itself as "Yash Kumar" when asked.

🚀 Features
Runs LLaMA 3.1-8B Locally: No external APIs required.
Streamlit UI: Simple and interactive chat interface.
Context Memory: Remembers previous messages in the conversation.
Custom Identity: Responds with "I am Yash Kumar, your AI assistant!" when asked Who are you?.


pip install streamlit langchain_community ollama
2️⃣ Install & Run Ollama
Download and install Ollama from https://ollama.com, then pull the LLaMA 3 model:

🎯 How It Works
User sends a message via the chat input.
Chat history is stored in st.session_state.messages.
LLaMA 3 processes the conversation, keeping context in memory.
Special handling for "Who are you?" to return "I am Yash Kumar, your AI assistant!"
