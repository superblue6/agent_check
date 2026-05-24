
"""初始化数据库脚本 - 创建表结构"""
from db_models import db_manager, Base

if __name__ == "__main__":
    print("正在初始化数据库...")
    db_manager.init_engines()
    
    print("数据库表结构创建完成！")
    print("\n已创建的表:")
    print("- workshop_sessions (教研会话表)")
    print("- dialogue_records (对话历史表)")
    print("- discussion_reports (研讨报告表)")

