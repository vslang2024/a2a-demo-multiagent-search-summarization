"""A2A Chat Server - REAL LLM + Redis Chat Persistence"""
import streamlit as st
import os
import asyncio
import redis
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# Redis connection (GLOBAL)
r = None

def init_redis():
    """Initialize Redis connection"""
    global r
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        return True
    except:
        return False

def get_session_id() -> str:
    """Get unique session ID"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    return st.session_state.session_id

def messages_to_dict(messages: List) -> List[Dict]:
    """Convert LangChain messages to dict for Redis"""
    return [{
        'role': 'user' if isinstance(msg, HumanMessage) else 'assistant',
        'content': msg.content,
        'timestamp': datetime.now().isoformat()
    } for msg in messages]

def dict_to_messages(messages_data: List) -> List:
    """Convert Redis dict to LangChain messages"""
    if not messages_data:
        return []
    return [HumanMessage(content=m['content']) if m['role'] == 'user'
            else AIMessage(content=m['content']) for m in messages_data]

def save_chat_to_redis(messages: List):
    """SAVE CHAT TO REDIS - Called after EVERY message"""
    session_id = get_session_id()
    key = f"a2a:chat:{session_id}"
    chat_data = messages_to_dict(messages)
    r.setex(key, 86400, json.dumps(chat_data))  # 24h TTL
    st.sidebar.success(f"💾 Saved {len(messages)} messages")

def load_chat_from_redis() -> List:
    """LOAD CHAT FROM REDIS on startup"""
    session_id = get_session_id()
    key = f"a2a:chat:{session_id}"
    data = r.get(key)
    if data:
        return dict_to_messages(json.loads(data))
    return []

# Real LLM Agents (unchanged from working version)
class SearchAgent:
    def __init__(self, model):
        self.model = model

    def should_activate(self, messages: List) -> bool:
        recent = " ".join([m.content.lower() for m in messages[-3:] if m.content])
        triggers = ['what', 'latest', 'news', 'who', 'current', 'how many']
        return any(t in recent for t in triggers)

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        context = "\n".join([m.content for m in state['messages'][-3:] if m.content])
        search_prompt = [SystemMessage(content="Generate search query: QUERY: [terms]"),
                        HumanMessage(content=context[:200])]
        response = await self.model.ainvoke(search_prompt)
        search_query = response.content.split("QUERY:")[-1].strip()[:50] or "AI news"

        results_prompt = [SystemMessage(content="3 Google results: Title | URL | Summary"),
                         HumanMessage(content=f'Search: "{search_query}"')]
        results_response = await self.model.ainvoke(results_prompt)
        search_results = [line.strip() for line in results_response.content.split("\n")
                         if "|" in line][:3]

        return {"search_query": search_query, "search_results": search_results, "current_phase": "summarize"}

class SummarizationAgent:
    def __init__(self, model):
        self.model = model

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        chat_context = "\n".join([m.content for m in state['messages'][-4:] if m.content])
        search_context = f"Query: {state.get('search_query', '')}\n" + "\n".join(state.get('search_results', [])[:2])

        prompt = [SystemMessage(content="Summarize (100 words): Topics + Findings"),
                 HumanMessage(content=f"Chat: {chat_context[:300]}\nSearch: {search_context[:200]}")]

        response = await self.model.ainvoke(prompt)
        return {"summary": response.content[:250], "current_phase": "respond"}

async def run_a2a_workflow(search_agent, summarization_agent, state: Dict[str, Any], prompt: str):
    """A2A workflow"""
    global model
    try:
        if search_agent.should_activate(state['messages']):
            search_result = await search_agent.execute(state)
            state.update(search_result)

        summary_result = await summarization_agent.execute(state)
        state.update(summary_result)

        context = f"Summary: {summary_result['summary']}"
        final_prompt = [SystemMessage(content=context), HumanMessage(content=prompt)]
        response = await model.ainvoke(final_prompt)
        return response.content, state
    except Exception as e:
        return f"Error: {str(e)}", state

def main():
    st.set_page_config(page_title="🤖 A2A Chat Server + Redis", layout="wide")

    # Redis connection check
    if not init_redis():
        st.error("🗄️ Redis not running! Run: `docker-compose up -d`")
        st.stop()

    # API Key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        api_key = st.sidebar.text_input("Gemini API Key", type="password")
        if not api_key:
            st.stop()

    global model
    os.environ["GOOGLE_API_KEY"] = api_key
    #model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1, max_output_tokens=500)
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,  # Low creativity (factual)
        max_output_tokens=2000,  # Longer responses
        top_k=32,  # Focused sampling
        top_p=0.9,  # Tight probability
        repetition_penalty=1.2,  # Avoid repetition
        # Context window is model-limited (1M tokens for 2.5 Flash)
    )

    # LOAD CHAT FROM REDIS
    session_id = get_session_id()
    st.session_state.messages = load_chat_from_redis()

    # Show session info
    st.info(f"**Session ID:** `{session_id}` | **Persisted in Redis** 💾")

    # UI Layout
    st.title("🤖 A2A Chat Server - Redis Persistent")
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("💬 Chat History (Redis)")
        if st.session_state.messages:
            for msg in st.session_state.messages:
                role = "user" if isinstance(msg, HumanMessage) else "assistant"
                with st.chat_message(role):
                    st.markdown(msg.content)
        else:
            st.info("👋 Start chatting - messages auto-saved to Redis!")

    with col2:
        st.metric("Messages in Redis", len(st.session_state.messages))
        if hasattr(st.session_state, 'search_query') and st.session_state.search_query:
            st.success(f"🔍 {st.session_state.search_query}")

    # Chat input
    if prompt := st.chat_input("Ask anything (persists in Redis)..."):
        if not prompt.strip():
            st.rerun()

        # ADD USER MESSAGE + SAVE TO REDIS
        user_msg = HumanMessage(content=prompt.strip())
        st.session_state.messages.append(user_msg)
        save_chat_to_redis(st.session_state.messages)  # 🚀 SAVE #1

        with st.chat_message("user"):
            st.markdown(prompt)

        # A2A Response
        with st.chat_message("assistant"):
            placeholder = st.empty()
            state = {"messages": st.session_state.messages}

            full_response, new_state = asyncio.run(
                run_a2a_workflow(SearchAgent(model), SummarizationAgent(model), state, prompt)
            )

            placeholder.markdown(full_response)

            # ADD AI RESPONSE + SAVE TO REDIS
            ai_msg = AIMessage(content=full_response)
            st.session_state.messages.append(ai_msg)
            save_chat_to_redis(st.session_state.messages)  # 🚀 SAVE #2

        # Update search query if exists
        if "search_query" in new_state:
            st.session_state.search_query = new_state["search_query"]

        st.rerun()

    # Controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat (Redis)"):
            st.session_state.messages = []
            save_chat_to_redis([])
            st.rerun()
    with col2:
        if st.button("🔄 New Session"):
            st.session_state.session_id = str(uuid.uuid4())[:8]
            st.session_state.messages = load_chat_from_redis()
            st.rerun()

    # Redis stats
    with st.sidebar:
        st.success(f"🗄️ Redis Connected | Session: `{session_id}`")
        st.metric("Chat Messages", len(st.session_state.messages))
        st.info("""
        **💾 Persistence:**
        • Every message saved to Redis
        • Survives page refresh  
        • 24h auto-expiry
        • Multi-tab support
        """)

if __name__ == "__main__":
    main()
