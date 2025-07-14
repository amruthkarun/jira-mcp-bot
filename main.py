import streamlit as st
import asyncio
from llm_utils import get_intent
from mcp_client import perform_jira_action

st.set_page_config(page_title="Jira Chatbot", layout="wide")
st.title("🤖 Jira Assistant")
st.caption("Talk to your Jira instance — Create or fetch issues with natural language.")


# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Show chat history
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

# Chat input
user_input = st.chat_input("Ask me something like 'Create a task to fix login bug'...")

if user_input:
    # Show user input
    st.chat_message("user").markdown(user_input)
    st.session_state.chat_history.append(("user", user_input))

    with st.chat_message("assistant"):
        with st.spinner("💬 Thinking..."):
            # Intent detection
            intent = get_intent(user_input)
            st.markdown(f"🧠 Intent: `{intent}`")

            # Call Jira action via MCP
            try:
                result = asyncio.run(perform_jira_action(intent, user_input))
                st.success(result)
                st.session_state.chat_history.append(("assistant", result))
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.chat_history.append(("assistant", error_msg))
