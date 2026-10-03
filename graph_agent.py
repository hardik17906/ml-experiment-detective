"""The V2 agent loop expressed as a small LangGraph StateGraph.

The nodes call the same Ollama request, tool registry, policy, renderer, and
session state as v2_agent.py. LangGraph organizes transitions; it does not
replace the model or perform the experiment calculations.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from v2_agent import (
    MAX_TOOL_CALLS, ask_ollama, available_tool_names, execute_call,
    finish_turn, policy_call, prepare_turn,
)
from v2_state import SessionState
from v2_tools import tool_menu


class GraphState(TypedDict):
    payload: dict


def agent_node(state: GraphState) -> GraphState:
    payload = state["payload"]
    names = available_tool_names(payload)
    payload["trace"].append({"kind": "TOOL MENU", "data": names})
    message = ask_ollama(payload["messages"], tool_menu(names))
    calls = message.get("tool_calls") or []
    if calls:
        if payload["tool_count"] >= MAX_TOOL_CALLS:
            raise RuntimeError("V2 graph agent reached its tool-call limit")
        payload["pending_calls"] = [
            {"name": calls[0]["function"]["name"], "arguments": calls[0]["function"]["arguments"], "origin": "AGENT"}
        ]
    else:
        needed = policy_call(payload)
        if needed and payload["tool_count"] < MAX_TOOL_CALLS:
            payload["pending_calls"] = [{"name": needed[0], "arguments": needed[1], "origin": "APP POLICY"}]
        else:
            if not payload["tool_results"]:
                raise RuntimeError("The graph model stopped before evidence was collected")
            payload["pending_calls"] = []
    return {"payload": payload}


def route_after_agent(state: GraphState) -> str:
    return "tools" if state["payload"]["pending_calls"] else "final"


def tools_node(state: GraphState) -> GraphState:
    payload = state["payload"]
    calls = payload["pending_calls"]
    payload["pending_calls"] = []
    for call in calls:
        execute_call(payload, call["name"], call["arguments"], origin=call["origin"])
    return {"payload": payload}


def final_node(state: GraphState) -> GraphState:
    payload = state["payload"]
    finish_turn(payload)
    return {"payload": payload}


def build_graph():
    builder = StateGraph(GraphState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tools_node)
    builder.add_node("final", final_node)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "final": "final"})
    builder.add_edge("tools", "agent")
    builder.add_edge("final", END)
    return builder.compile()


GRAPH = build_graph()


def run_graph(question: str, session: SessionState | None = None, *, rerank: bool = False) -> dict:
    initial = prepare_turn(question, session, rerank=rerank)
    final = GRAPH.invoke({"payload": initial}, config={"recursion_limit": 2 * MAX_TOOL_CALLS + 5})["payload"]
    return {
        "answer": final["answer"],
        "trace": final["trace"],
        "session": final["session"],
        "tool_results": final["tool_results"],
    }
