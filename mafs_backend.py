import os
import logging
import traceback
from typing import Annotated, Literal, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages

# ── 日志配置 ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# ── 1. 环境配置 ────────────────────────────────────────────────────────────────
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "false")
os.environ["LANGCHAIN_PROJECT"] = "deepseek-v3-2-251201"

_langchain_key = os.getenv("LANGCHAIN_API_KEY", "")
if _langchain_key:
    os.environ["LANGCHAIN_API_KEY"] = _langchain_key

_deepseek_key = os.getenv("ARK_API_KEY", "")
if not _deepseek_key:
    raise EnvironmentError(
        "缺少 ARK_API_KEY 环境变量配置。"
    )
os.environ["ARK_API_KEY"] = _deepseek_key

# ── 2. 初始化模型 ──────────────────────────────────────────────────────────────
# 确保代理环境变量设置（这样 openai 库会自动使用）
_http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
_https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")

if _http_proxy:
    os.environ["HTTP_PROXY"] = _http_proxy
if _https_proxy:
    os.environ["HTTPS_PROXY"] = _https_proxy

if _http_proxy or _https_proxy:
    logger.info(f"使用代理配置 - HTTP_PROXY: {_http_proxy}, HTTPS_PROXY: {_https_proxy}")

model = ChatOpenAI(
    model="ep-20260518113327-5rkl7",
    openai_api_key=_deepseek_key,
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
    max_tokens=4096,
    temperature=0.3,
    timeout=120.0,  # 2分钟超时
    max_retries=3,  # 最多重试3次
    verbose=True,   # 开启详细日志
)

router_model = ChatOpenAI(
    model="ep-20260518113327-5rkl7",
    openai_api_key=_deepseek_key,
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
    max_tokens=10,
    temperature=0.1,
    timeout=60.0,   # 1分钟超时
    max_retries=3,  # 最多重试3次
    verbose=True,   # 开启详细日志
)

# ── 3. State 定义 ──────────────────────────────────────────────────────────────
class TeacherState(TypedDict):
    messages:          Annotated[list, add_messages]  # 对话历史
    report_summary:    str                            # 报告维度文档内容（外部注入）
    discussion_report: str                            # 最终研讨报告
    initialized:       bool                           # 是否已完成初始化（防止重复加载）
    teacher_name:      str                            # 研讨教师姓名
    lesson_info:       dict                           # 课例基本信息

# ── 4. 会话上下文（以每次 /chat 请求中的 configurable 为准）────────────────────
def _format_lesson_info(lesson_info: dict) -> str:
    if not lesson_info:
        return "（无）"
    return "\n".join(f"- {k}：{v}" for k, v in lesson_info.items())


def _sync_session_from_config(state: TeacherState, config: RunnableConfig) -> dict:
    """每次调用均同步课例信息与报告；report_content 非空时覆盖 state。"""
    cfg = config.get("configurable", {})
    lesson_info = cfg.get("lesson_info") if cfg.get("lesson_info") else state.get("lesson_info", {})
    teacher_name = cfg.get("teacher_name") or state.get("teacher_name", "老师")
    incoming_report = cfg.get("report_content")
    if incoming_report:
        report_content = incoming_report
    else:
        report_content = state.get("report_summary", "")
    if not report_content.strip():
        logger.warning("本次请求未携带有效的 report_content，智能体将无法依据课堂报告作答")
    return {
        "teacher_name":   teacher_name,
        "lesson_info":    lesson_info,
        "report_summary": report_content,
        "initialized":    True,
    }


def _dialogue_messages(messages: list) -> list:
    """对话历史仅保留人机往返，报告由 state.report_summary 在调用时注入。"""
    return [
        m for m in messages
        if not (isinstance(m, SystemMessage) and getattr(m, "name", None) == "report_context")
    ]


def _build_agent_messages(state: TeacherState, role_prompt: str) -> list:
    teacher_name = state.get("teacher_name", "老师")
    lesson_info = state.get("lesson_info", {})
    report = (state.get("report_summary") or "").strip()
    lesson_block = (
        _format_lesson_info(lesson_info)
        if isinstance(lesson_info, dict)
        else str(lesson_info)
    )
    if report:
        report_block = (
            "【课堂观察报告】以下为观察数据，仅在用户讨论课堂、教学或报告相关内容时参考；"
            "用户仅为问候、寒暄、感谢或与课堂无关的闲聊时，自然简短回应即可，"
            "不要主动引用或追问报告中的数据。\n"
            "引用报告时：不得编造报告中不存在的数值；"
            "须区分「报告描述的授课教师/本课」与「当前对话者」（对话者可能是观摩教师，"
            "勿用「您在课上」等默认对方授课的表述，可说「报告中本课…」「授课教师…」）。\n"
            f"{report}"
        )
    else:
        report_block = "【课堂观察报告】当前未提供，请勿编造任何课堂观测数据。"
    system_content = (
        f"{role_prompt}\n\n"
        f"当前交流对象是【{teacher_name}】。\n"
        f"【课例基本信息】\n{lesson_block}\n\n"
        f"{report_block}"
    )
    return [SystemMessage(content=system_content)] + _dialogue_messages(state.get("messages", []))


# ── 5. 节点定义 ────────────────────────────────────────────────────────────────
def initialization_node(state: TeacherState, config: RunnableConfig) -> dict:
    return _sync_session_from_config(state, config)

def peer_agent(state: TeacherState) -> dict:
    """教学同伴：引导老师还原课堂细节，严禁直接给建议"""
    role_prompt = (
        "你是一线教师的教学同伴，正在与教师进行教研对话。\n"
        "注意：当前对话者不一定是本课授课教师，可能是观摩教师；"
        "勿用「您在课上」等默认对方授课的表述。\n"
        "任务：在用户愿意研讨课堂后，引导还原课堂细节，多问学生反应、掌握情况。\n"
        "要求1：用户仅打招呼（如你好、在吗）或闲聊时，友好回应即可，"
        "可简要邀请对方说说想从哪个角度聊这节课，不要引用报告数据、不要追问报告指标。\n"
        "要求2：仅当用户已开始讨论课堂、教学或报告内容时，再结合报告提1个具体问题。\n"
        "要求3：每次只问1个问题，问题要具体；严禁直接给建议。"
    )
    messages = _build_agent_messages(state, role_prompt)
    try:
        response = model.invoke(messages)
        response.name = "peer"
        return {"messages": [response]}
    except Exception as e:
        logger.error("=" * 80)
        logger.error("peer_agent 调用失败！")
        logger.error("错误类型: %s", type(e).__name__)
        logger.error("错误信息: %s", str(e))
        logger.error("API 端点: %s", model.openai_api_base)
        logger.error("API 模型: %s", model.model)
        logger.error("请求消息数: %d", len(messages))
        logger.error("完整错误堆栈:")
        for line in traceback.format_exc().split('\n'):
            logger.error("  %s", line)
        logger.error("=" * 80)
        raise

def expert_agent(state: TeacherState) -> dict:
    """教育专家：用教育理论解释课堂现象"""
    role_prompt = (
        "你是一个资深教育专家，正在指导一位老师。\n"
        "注意：对话者不一定是授课教师；勿用「您在课上」等默认对方授课的表述。\n"
        "任务：在用户讨论具体教学现象时，结合报告用教育理论做简短解释。\n"
        "要求1：用户仅为问候或闲聊时，简短回应，不引用报告、不展开理论分析。\n"
        "要求2：不要直接给建议；有实质讨论时，解释控制在100字以内，专业但易懂。"
    )
    messages = _build_agent_messages(state, role_prompt)
    try:
        response = model.invoke(messages)
        response.name = "expert"
        return {"messages": [response]}
    except Exception as e:
        logger.error("=" * 80)
        logger.error("expert_agent 调用失败！")
        logger.error("错误类型: %s", type(e).__name__)
        logger.error("错误信息: %s", str(e))
        logger.error("API 端点: %s", model.openai_api_base)
        logger.error("API 模型: %s", model.model)
        logger.error("请求消息数: %d", len(messages))
        logger.error("完整错误堆栈:")
        for line in traceback.format_exc().split('\n'):
            logger.error("  %s", line)
        logger.error("=" * 80)
        raise

def mentor_agent(state: TeacherState) -> dict:
    """资深教研员：给出具体可操作的教学策略建议"""
    role_prompt = (
        "你是一个经验丰富的教研员，正在协助一位老师制定教学策略。\n"
        "注意：对话者不一定是授课教师；勿用「您在课上」等默认对方授课的表述。\n"
        "任务：在用户明确希望听建议或讨论改进方向时，结合报告给出可操作建议。\n"
        "要求1：用户仅为问候或闲聊时，简短回应，不给建议、不引用报告数据。\n"
        "要求2：有实质讨论时，每次1-2条建议，100字以内，具体可操作。"
    )
    messages = _build_agent_messages(state, role_prompt)
    try:
        response = model.invoke(messages)
        response.name = "mentor"
        return {"messages": [response]}
    except Exception as e:
        logger.error("=" * 80)
        logger.error("mentor_agent 调用失败！")
        logger.error("错误类型: %s", type(e).__name__)
        logger.error("错误信息: %s", str(e))
        logger.error("API 端点: %s", model.openai_api_base)
        logger.error("API 模型: %s", model.model)
        logger.error("请求消息数: %d", len(messages))
        logger.error("完整错误堆栈:")
        for line in traceback.format_exc().split('\n'):
            logger.error("  %s", line)
        logger.error("=" * 80)
        raise

def report_node(state: TeacherState) -> dict:
    """汇总整轮对话，生成结构化研讨报告"""
    messages = state.get("messages", [])
    teacher_name = state.get("teacher_name", "老师")
    lesson_info = state.get("lesson_info", {})
    
    dialogue_text = ""
    role_map = {"peer": "教学同伴", "expert": "教育专家", "mentor": "资深教研员"}
    for m in messages:
        if isinstance(m, HumanMessage):
            if m.content == "__terminate__":
                continue
            dialogue_text += f"【教师】{m.content}\n"
        elif getattr(m, "type", "") == "ai":
            role = role_map.get(getattr(m, "name", ""), "AI")
            dialogue_text += f"【{role}】{m.content}\n"

    report_prompt = f"""你是一位专业教研报告撰写者。
    请根据以下教研对话记录，为教师生成一份【教研研讨报告】。

    【重要】严格按照以下格式输出，不得改变标题文字和符合：
    # 教研研讨报告
    教师：{teacher_name}  学科：{lesson_info.get('subject', '')}  时间：{__import__('datetime').date.today()}

    ## 一、教学问题聚焦
    （本次研讨聚焦的核心问题，1-3条）

    ## 二、多视角分析
    （分别概括同伴、专家、教研员的核心观点）
    【🤔 教学同伴视角】
    【🔬 教育专家视角】
    【💡 教研员视角】

    ## 三、教师反思
    （提炼教师在对话中表达的自我认知和改进方向）

    ## 四、后续行动计划
    （建议教师的下一步跟进事项）

以下是本次对话记录，请据此生成报告：
    {dialogue_text}"""
    try:
        response = model.invoke([SystemMessage(content=report_prompt)])
        report_content = response.content
    except Exception as e:
        logger.error("=" * 80)
        logger.error("报告生成节点调用失败！")
        logger.error("错误类型: %s", type(e).__name__)
        logger.error("错误信息: %s", str(e))
        logger.error("API 端点: %s", model.openai_api_base)
        logger.error("API 模型: %s", model.model)
        logger.error("对话记录长度: %d", len(dialogue_text))
        logger.error("完整错误堆栈:")
        for line in traceback.format_exc().split('\n'):
            logger.error("  %s", line)
        logger.error("=" * 80)
        report_content = "报告生成失败，请手动整理对话记录。"
    return {"discussion_report": report_content}


# ── 6. 路由器 ──────────────────────────────────────────────────────────────────
def smart_router(state: TeacherState) -> Literal["peer", "expert", "mentor", "end"]:
    """语义路由：让模型根据最新用户消息决定由哪个智能体接手"""
    messages = state.get("messages", [])
    if not messages:
        return "end"
    user_messages = [m for m in messages if isinstance(m, HumanMessage)]
    if not user_messages:
        return "peer"
    last_user_msg = user_messages[-1].content
    if last_user_msg == "__terminate__":
        return "end"
    router_prompt = f"""你是一个对话流调度员。请分析用户的意图，决定下一步由谁接手对话。

【核心准则】
- 只要用户还在提问、表达困惑或谈论课堂情况，严禁返回 'end'。
- 哪怕用户的提问很简短（如"然后呢？""怎么看？"），也必须分配一个角色。

【角色分配指南】
- 用户在@同伴、刚开始对话、描述课堂场景、或请求帮助 -> peer
- 用户在@专家、表示认同、追问原因、或想听理论解释 -> expert
- 用户在@教研员、想知道具体做法、认可理论后询问"怎么办"、或要求给建议 -> mentor
- 用户表示感谢、明确说话题结束、或不需要进一步帮助 -> end

当前用户输入："{last_user_msg}"
【输出要求】
你的回复必须且只能是以下四个英文单词之一，不得包含其他字符、标点或解释：
peer
expert
mentor
end
直接输出单词本身。
"""

    try:
        decision = router_model.invoke([
            {"role": "system", "content": router_prompt}
        ]).content.strip().lower()
    except Exception as e:
        logger.error("=" * 80)
        logger.error("smart_router 调用失败！")
        logger.error("错误类型: %s", type(e).__name__)
        logger.error("错误信息: %s", str(e))
        logger.error("API 端点: %s", router_model.openai_api_base)
        logger.error("API 模型: %s", router_model.model)
        logger.error("路由提示词长度: %d", len(router_prompt))
        logger.error("完整错误堆栈:")
        for line in traceback.format_exc().split('\n'):
            logger.error("  %s", line)
        logger.error("=" * 80)
        return "peer"

    for option in ["peer", "expert", "mentor", "end"]:
        if option in decision:
            return option

    logger.warning("smart_router 返回了无法识别的结果：%s，默认路由到 peer", decision)
    return "peer"


# ── 7. 图结构 ──────────────────────────────────────────────────────────────────
workflow = StateGraph(TeacherState)

workflow.add_node("initialization", initialization_node)
workflow.add_node("peer",           peer_agent)
workflow.add_node("expert",         expert_agent)
workflow.add_node("mentor",         mentor_agent)
workflow.add_node("report",         report_node)

workflow.add_edge(START, "initialization")

workflow.add_conditional_edges(
    "initialization",
    smart_router,
    {
        "peer":   "peer",
        "expert": "expert",
        "mentor": "mentor",
        "end":    "report",
    }
)

workflow.add_edge("peer",   END)
workflow.add_edge("expert", END)
workflow.add_edge("mentor", END)
workflow.add_edge("report", END)

