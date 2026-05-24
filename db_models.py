
from sqlalchemy import create_engine, Column, String, Text, DateTime, JSON, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()


class WorkshopSession(Base):
    """教研会话表 - 存储每次会话的基本信息"""
    __tablename__ = "workshop_sessions"

    session_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), index=True, nullable=False)
    teacher_name = Column(String(100), default="老师")
    lesson_info = Column(JSON)
    report_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Integer, default=1)

    dialogue_records = relationship("DialogueRecord", back_populates="session", cascade="all, delete-orphan")
    discussion_report = relationship("DiscussionReport", back_populates="session", uselist=False, cascade="all, delete-orphan")


class DialogueRecord(Base):
    """对话历史表 - 存储每条消息"""
    __tablename__ = "dialogue_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("workshop_sessions.session_id"), index=True)
    role = Column(String(32), nullable=False)  # "user", "peer", "expert", "mentor"
    role_name = Column(String(100))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    session = relationship("WorkshopSession", back_populates="dialogue_records")


class DiscussionReport(Base):
    """研讨报告表 - 存储生成的研讨报告"""
    __tablename__ = "discussion_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("workshop_sessions.session_id"), unique=True, index=True)
    report_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    session = relationship("WorkshopSession", back_populates="discussion_report")


class DatabaseManager:
    """数据库管理器 - 实现读写分离"""

    def __init__(self):
        self.master_engine = None
        self.slave_engine = None
        self.MasterSession = None
        self.SlaveSession = None

    def init_engines(self, master_url: str = "", slave_url: str = ""):
        if not master_url:
            from config import config
            master_url = config.MYSQL_MASTER_URL
            slave_url = config.MYSQL_SLAVE_URL if config.MYSQL_SLAVE_URL else master_url

        if not master_url:
            raise EnvironmentError("缺少 MYSQL_MASTER_URL 配置，请检查 config.yaml")

        self.master_engine = create_engine(
            master_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.slave_engine = create_engine(
            slave_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )

        self.MasterSession = sessionmaker(bind=self.master_engine)
        self.SlaveSession = sessionmaker(bind=self.slave_engine)

        Base.metadata.create_all(self.master_engine)

    def get_master_session(self):
        if not self.MasterSession:
            raise RuntimeError("数据库管理器未初始化，请先调用 init_engines()")
        from contextlib import contextmanager
        
        @contextmanager
        def session_scope():
            session = self.MasterSession()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        return session_scope()

    def get_slave_session(self):
        if not self.SlaveSession:
            raise RuntimeError("数据库管理器未初始化，请先调用 init_engines()")
        from contextlib import contextmanager
        
        @contextmanager
        def session_scope():
            session = self.SlaveSession()
            try:
                yield session
            finally:
                session.close()
        return session_scope()


db_manager = DatabaseManager()
