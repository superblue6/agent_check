# server.py
import os
import sqlite3
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from mafs_backend import workflow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("agent_check")

DB_PATH = os.getenv("DB_PATH", "teacher_workshop.db")

ROLE_MAP = {
    "peer":   "教学同伴",
    "expert": "教育专家",
    "mentor": "资深教研员",
}

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(conn)
app_graph = workflow.compile(checkpointer=checkpointer)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("应用启动")
    yield
    logger.info("应用关闭")
    conn.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_index():
    logger.info("收到首页请求")
    return FileResponse("mafs_frontend.html")

@app.get("/test01.txt")
async def read_report():
    logger.info("收到 test01.txt 请求")
    return FileResponse("test01.txt")

class ChatRequest(BaseModel):
    report_id:  str
    message:    str
    teacher_name: str = "老师"
    lesson_info: dict = {}
    report_content: str = ""

@app.post("/chat")
async def chat(req: ChatRequest):
    logger.info(f"收到 chat 请求 - report_id: {req.report_id}, message: {req.message[:50]}...")
    
    config = {
        "configurable": {
            "thread_id": req.report_id,
            "teacher_name": req.teacher_name,
            "lesson_info": req.lesson_info,
            "report_content": req.report_content,
        }
    }

    try:
        logger.info(f"开始处理消息 - thread_id: {req.report_id}")
        result = app_graph.invoke(
            {"messages": [HumanMessage(content=req.message)]},
            config=config,
        )
        logger.info(f"消息处理完成 - thread_id: {req.report_id}")
    except Exception as e:
        logger.error(f"处理消息时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

    messages = result.get("messages", [])
    last_ai = None
    for m in reversed(messages):
        if getattr(m, "type", "") == "ai":
            last_ai = m
            break

    if last_ai:
        logger.info(f"返回 AI 响应 - role: {getattr(last_ai, 'name', '')}")
        return {
            "status":  "ok",
            "role":    ROLE_MAP.get(getattr(last_ai, "name", ""), "AI教研助手"),
            "content": last_ai.content,
            "report":  result.get("discussion_report", ""),
        }
    logger.warning("未找到 AI 响应消息")
    return {"status": "ok", "role": "", "content": "", "report": ""}


class TerminateRequest(BaseModel):
    report_id:  str
    teacher_name: str = "老师"
    lesson_info: dict = {}
    report_content: str = ""

@app.post("/terminate")
async def terminate(req: TerminateRequest):
    logger.info(f"收到 terminate 请求 - report_id: {req.report_id}")
    
    config = {
        "configurable": {
            "thread_id": req.report_id,
            "teacher_name": req.teacher_name,
            "lesson_info": req.lesson_info,
            "report_content": req.report_content,
        }
    }

    try:
        logger.info(f"开始生成报告 - thread_id: {req.report_id}")
        result = app_graph.invoke(
            {"messages": [HumanMessage(content="__terminate__")]},
            config=config,
        )
        logger.info(f"报告生成完成 - thread_id: {req.report_id}")
    except Exception as e:
        logger.error(f"生成报告时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

    report = result.get("discussion_report", "报告生成失败")
    return {"status": "ok", "report": report}


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8001"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    logger.info(f"启动服务 - host: {host}, port: {port}, reload: {reload}")

    uvicorn.run("server:app", host=host, port=port, reload=reload)
