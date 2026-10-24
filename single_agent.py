
import streamlit as st
from src.app.single_agent_system.single_agent import agent_invoke

st.set_page_config(
    page_title="Gopal AI Agent Chat",
    page_icon="🤖",
    layout="centered",
)

st.title("Gopal AI Agent Chat")
st.caption("Powered by LangChain, Groq, Tavily Search, and WeatherStack")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm your AI assistant. "
                "Ask me about AI news, weather, or general topics."
            ),
        }
    ]

# Sidebar controls
with st.sidebar:
    st.header("Settings")
    st.write("**Available capabilities**")
    st.markdown("- Web search with Tavily")
    st.markdown("- Weather information with WeatherStack")
    st.markdown("- AI-powered responses with Groq")

    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask your AI agent anything..."):
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Agent is thinking and using tools if needed..."):
                response = agent_invoke(prompt)

            if not isinstance(response, str):
                response = str(response)

            st.markdown(response)

            st.session_state.messages.append(
                {"role": "assistant", "content": response}
            )

        except Exception as exc:
            st.error(f"Agent request failed: {exc}")
