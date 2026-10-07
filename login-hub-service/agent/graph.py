"""LangGraph 登录态管理工作流组装"""
from langgraph.graph import END, StateGraph

from agent import nodes
from agent.state import LoginState

MAX_SCAN_RETRIES = 1


def build_login_graph() -> StateGraph:
    graph = StateGraph(LoginState)
    graph.add_node("check_login", nodes.node_check_login)
    graph.add_node("open_login_page", nodes.node_open_login_page)
    graph.add_node("wait_for_scan", nodes.node_wait_for_scan)
    graph.add_node("keepalive", nodes.node_keepalive)
    graph.add_node("finish", nodes.node_finish)

    graph.set_entry_point("check_login")

    # check_login 之后按 action 与登录态分流：
    # 只有 action=login（用户点「登录」按钮）才打开登录页；
    # 状态检测(action=check)未登录时直接结束，绝不弹浏览器
    def _route_after_check(s):
        if s.get("logged_in"):
            return "finish"
        action = s.get("action")
        if action == "keepalive":
            return "keepalive"
        if action == "login":
            return "open_login_page"
        return "finish"  # action=check：未登录，仅返回状态

    graph.add_conditional_edges(
        "check_login",
        _route_after_check,
        {"finish": "finish", "keepalive": "keepalive", "open_login_page": "open_login_page"},
    )

    graph.add_edge("open_login_page", "wait_for_scan")

    # 扫码后：成功→finish；失败且未超重试次数→再开一次登录页
    graph.add_conditional_edges(
        "wait_for_scan",
        lambda s: (
            "finish"
            if s.get("success") or s.get("retries", 0) >= MAX_SCAN_RETRIES
            else "open_login_page"
        ),
        {"finish": "finish", "open_login_page": "open_login_page"},
    )

    graph.add_edge("keepalive", "finish")
    graph.add_edge("finish", END)
    return graph


# 编译后的全局工作流（FastAPI 与调度器共用）
login_graph = build_login_graph().compile()
