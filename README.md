# MCP-Orchestrator
MCP Orchestrator is a multi-tool LLM system that uses Gemini and MCP to dynamically route queries between direct responses and external tools. It integrates local and cloud services with async execution, enabling scalable, real-time tool orchestration across distributed environments.

# Features
1) Chat-based interface using Streamlit
2) Gemini LLM with dynamic tool-calling
3) MCP-based multi-tool orchestration
4) Asynchronous execution using asyncio
5) Multi-step reasoning (LLM → Tool → Response)
6) Hybrid architecture (local + cloud tools)
7) Stateful conversational memory

# Architecture
Components
Frontend: Streamlit chat interface
LLM Layer: Gemini 3.1 Flash via LangChain
Orchestration Layer: MultiServerMCPClient (MCP)
Tool Servers:
1) Math Server (local, FastMCP)
2) Expense API (remote, FastMCP)
3) Manim Server (third-party integration)

# How It Works
1) User inputs a query
2) LLM decides:
   1) Direct response OR
   2) Tool invocation 
3) MCP executes tools asynchronously
4) Results are passed back to LLM
5) Final response is generated

# Tech Stack
1) Python
2) Streamlit
3) LangChain
4) Google Gemini (Gemini 3.1 Flash)
5) MCP (Model Context Protocol)
6) FastMCP
7) asyncio

# Deployment
1) Hybrid Setup
    1) Local: Streamlit app + Math + Manim servers
    2) Cloud: Expense API (FastMCP hosted)
2) Communication
    1) stdio → Local tools
    2) HTTP streaming → Remote tools

# Acknowledgements
Manim MCP Server (third-party)


