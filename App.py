import os
import json
import asyncio
import streamlit as st

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage


def extract_text(msg):
    content = msg.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(item.get("text", ""))
        return "\n".join(texts)

    return str(content)


def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
        # already running → create new loop
        new_loop = asyncio.new_event_loop()
        return new_loop.run_until_complete(coro)
    except RuntimeError:
        # no loop → create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


# ─────────────────────────────
# YOUR SERVERS (Windows fixed)
# ─────────────────────────────
SERVERS = {
    "math": {
        "transport": "stdio",
        "command": "C:\\Users\\Likhit Gaikwad\\AppData\\Roaming\\Python\\Python310\\Scripts\\uv.exe",
        "args": [
            "run",
            "fastmcp",
            "run",
            "C:\\Users\\Likhit Gaikwad\\Desktop\\mcp-math-server\\main.py",
        ],
    },
    "expense": {
        "transport": "streamable_http",
        "url": "https://binding-white-wolf.fastmcp.app/mcp",
        "headers": {
            "Authorization": f"Bearer {os.getenv('FASTMCP_API_KEY')}"
        },
    },
    "manim-server": {
        "transport": "stdio",
        "command": "C:\\Users\\Likhit Gaikwad\\.venv\\Scripts\\python.exe",
        "args": [
            "C:\\Users\\Likhit Gaikwad\\Desktop\\manim mcp server\\manim-mcp-server\\src\\manim_server.py"
        ],
        "env": {
            "MANIM_EXECUTABLE": "C:\\Users\\Likhit Gaikwad\\AppData\\Roaming\\Python\\Python310\\Scripts\\manim.exe"
        },
    },
}

import logging

logging.getLogger("langchain_google_genai._function_utils").setLevel(logging.ERROR)


# ─────────────────────────────
SYSTEM_PROMPT = (
    "You have access to tools. When you call tools, do not explain the process. "
    "Return only the final answer."
)

st.set_page_config(page_title="MCP Chat", page_icon="🧰")
st.title("🧰 MCP Chat")


# ─────────────────────────────
# INITIALIZATION (RUNS ONCE)
# ─────────────────────────────
if "initialized" not in st.session_state:

    # Gemini model
    st.session_state.llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite-preview",
        google_api_key="YOUR_API_KEY",
        temperature=0,
    )

    # MCP client
    st.session_state.client = MultiServerMCPClient(SERVERS)

    # IMPORTANT: async call (only once)
    tools = run_async(st.session_state.client.get_tools())

    st.session_state.tools = tools
    st.session_state.tool_by_name = {t.name: t for t in tools}

    # Bind tools
    st.session_state.llm_with_tools = st.session_state.llm.bind_tools(tools)

    # Conversation memory
    st.session_state.history = [SystemMessage(content=SYSTEM_PROMPT)]

    st.session_state.initialized = True


# ─────────────────────────────
# DISPLAY CHAT
# ─────────────────────────────
for msg in st.session_state.history:

    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)

    elif isinstance(msg, AIMessage):
        # skip tool-call messages
        if getattr(msg, "tool_calls", None):
            continue

        with st.chat_message("assistant"):
            st.markdown(msg.content)


# ─────────────────────────────
# USER INPUT
# ─────────────────────────────
user_text = st.chat_input("Type a message...")

if user_text:

    # show user message
    with st.chat_message("user"):
        st.markdown(user_text)

    st.session_state.history.append(HumanMessage(content=user_text))

    # ───────── STEP 1: model decides tool or not
    first = run_async(st.session_state.llm_with_tools.ainvoke(st.session_state.history))

    tool_calls = getattr(first, "tool_calls", None)

    # ───────── NO TOOL CASE
    if not tool_calls:

        with st.chat_message("assistant"):
            st.markdown(extract_text(first))

        st.session_state.history.append(first)

    # ───────── TOOL CASE
    else:
        # 1️) store assistant tool call (DO NOT SHOW)
        st.session_state.history.append(first)

        tool_msgs = []

        # 2) execute tools
        for tc in tool_calls:
            name = tc["name"]
            args = tc.get("args") or {}

            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except:
                    pass

            tool = st.session_state.tool_by_name[name]

            try:
                res = run_async(tool.ainvoke(args))
            except Exception as e:
                res = {"error": str(e)}

            tool_msgs.append(
                ToolMessage(tool_call_id=tc["id"], content=json.dumps(res))
            )

        # append tool results
        st.session_state.history.extend(tool_msgs)

        # 3️) FINAL RESPONSE (IMPORTANT: use tool-enabled model)
        final = run_async(
            st.session_state.llm_with_tools.ainvoke(st.session_state.history)
        )

        with st.chat_message("assistant"):
            st.markdown(extract_text(final))

        st.session_state.history.append(AIMessage(content=final.content or ""))
