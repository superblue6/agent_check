
# server.py
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from mafs_backend import workflow
from db_models import db_manager, WorkshopSession, DialogueRecord, DiscussionReport
from config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("agent_check")

ROLE_MAP = {
    "peer":   "教学同伴",
    "expert": "教育专家",
    "mentor": "资深教研员",
}

checkpointer = MemorySaver()
app_graph = workflow.compile(checkpointer=checkpointer)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("初始化数据库连接...")
    db_manager.init_engines()
    logger.info("数据库连接初始化完成")
    logger.info("应用启动")
    yield
    logger.info("应用关闭")


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
    session_id: str
    user_id: str
    message: str
    teacher_name: str = "老师"
    lesson_info: dict = {}
    report_content: str = ""


@app.post("/chat")
async def chat(req: ChatRequest):
    logger.info(f"收到 chat 请求 - session_id: {req.session_id}, user_id: {req.user_id}, message: {req.message[:50]}...")

    config = {
        "configurable": {
            "thread_id": req.session_id,
            "teacher_name": req.teacher_name,
            "lesson_info": req.lesson_info,
            "report_content": req.report_content,
        }
    }

    try:
        logger.info(f"开始处理消息 - thread_id: {req.session_id}")
        result = app_graph.invoke(
            {"messages": [HumanMessage(content=req.message)]},
            config=config,
        )
        logger.info(f"消息处理完成 - thread_id: {req.session_id}")
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
        
        try:
            await save_dialogue_to_mysql(
                session_id=req.session_id,
                user_id=req.user_id,
                teacher_name=req.teacher_name,
                lesson_info=req.lesson_info,
                report_summary=req.report_content,
                user_message=req.message,
                ai_role=getattr(last_ai, "name", ""),
                ai_content=last_ai.content
            )
        except Exception as e:
            logger.error(f"保存对话到 MySQL 失败: {str(e)}")

        return {
            "status":  "ok",
            "role":    ROLE_MAP.get(getattr(last_ai, "name", ""), "AI教研助手"),
            "content": last_ai.content,
            "report":  result.get("discussion_report", ""),
        }
    logger.warning("未找到 AI 响应消息")
    return {"status": "ok", "role": "", "content": "", "report": ""}


class TerminateRequest(BaseModel):
    session_id: str
    user_id: str
    teacher_name: str = "老师"
    lesson_info: dict = {}
    report_content: str = ""


@app.post("/terminate")
async def terminate(req: TerminateRequest):
    logger.info(f"收到 terminate 请求 - session_id: {req.session_id}, user_id: {req.user_id}")

    config = {
        "configurable": {
            "thread_id": req.session_id,
            "teacher_name": req.teacher_name,
            "lesson_info": req.lesson_info,
            "report_content": req.report_content,
        }
    }

    try:
        logger.info(f"开始生成报告 - thread_id: {req.session_id}")
        result = app_graph.invoke(
            {"messages": [HumanMessage(content="__terminate__")]},
            config=config,
        )
        logger.info(f"报告生成完成 - thread_id: {req.session_id}")
    except Exception as e:
        logger.error(f"生成报告时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

    report = result.get("discussion_report", "报告生成失败")
    
    try:
        await save_report_to_mysql(
            session_id=req.session_id,
            report_content=report
        )
    except Exception as e:
        logger.error(f"保存报告到 MySQL 失败: {str(e)}")

    return {"status": "ok", "report": report}


async def save_dialogue_to_mysql(session_id: str, user_id: str, teacher_name: str, 
                                  lesson_info: dict, report_summary: str, 
                                  user_message: str, ai_role: str, ai_content: str):
    """保存对话记录到 MySQL"""
    with db_manager.get_master_session() as db_session:
        session = db_session.query(WorkshopSession).filter_by(session_id=session_id).first()
        
        if not session:
            session = WorkshopSession(
                session_id=session_id,
                user_id=user_id,
                teacher_name=teacher_name,
                lesson_info=lesson_info,
                report_summary=report_summary
            )
            db_session.add(session)
        
        user_record = DialogueRecord(
            session_id=session_id,
            role="user",
            role_name="教师",
            content=user_message
        )
        db_session.add(user_record)
        
        ai_record = DialogueRecord(
            session_id=session_id,
            role=ai_role,
            role_name=ROLE_MAP.get(ai_role, "AI教研助手"),
            content=ai_content
        )
        db_session.add(ai_record)
        
        db_session.commit()


async def save_report_to_mysql(session_id: str, report_content: str):
    """保存研讨报告到 MySQL"""
    with db_manager.get_master_session() as db_session:
        report = db_session.query(DiscussionReport).filter_by(session_id=session_id).first()
        
        if report:
            report.report_content = report_content
        else:
            report = DiscussionReport(
                session_id=session_id,
                report_content=report_content
            )
            db_session.add(report)
        
        session = db_session.query(WorkshopSession).filter_by(session_id=session_id).first()
        if session:
            session.is_active = 0
        
        db_session.commit()


@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    """获取会话信息（读操作，使用从库）"""
    with db_manager.get_slave_session() as db_session:
        session = db_session.query(WorkshopSession).filter_by(session_id=session_id).first()
        
        if not session:
            return JSONResponse(status_code=404, content={"error": "会话不存在"})
        
        records = db_session.query(DialogueRecord).filter_by(session_id=session_id).order_by(DialogueRecord.created_at).all()
        report = db_session.query(DiscussionReport).filter_by(session_id=session_id).first()
        
        return {
            "status": "ok",
            "session": {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "teacher_name": session.teacher_name,
                "lesson_info": session.lesson_info,
                "created_at": session.created_at.isoformat(),
                "is_active": session.is_active
            },
            "dialogues": [
                {
                    "role": r.role,
                    "role_name": r.role_name,
                    "content": r.content,
                    "created_at": r.created_at.isoformat()
                } for r in records
            ],
            "report": report.report_content if report else None
        }


if __name__ == "__main__":
    import uvicorn
    
    host = config.HOST
    port = config.PORT
    reload = config.RELOAD
    
    logger.info(f"启动服务 - host: {host}, port: {port}, reload: {reload}")

    uvicorn.run("server:app", host=host, port=port, reload=reload)

