from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import logging

db = SQLAlchemy()

def init_database(app):
    """初始化数据库"""
    db.init_app(app)

    with app.app_context():
        # 创建所有表
        db.create_all()
        app.logger.info("数据库表创建成功")

def test_connection():
    """测试数据库连接"""
    try:
        result = db.session.execute(text('SELECT 1'))
        return True
    except Exception as e:
        logging.error(f"数据库连接失败: {str(e)}")
        return False

def execute_sql_file(file_path):
    """执行SQL文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # 分割SQL语句
        statements = sql_content.split(';')

        for statement in statements:
            statement = statement.strip()
            if statement:
                db.session.execute(text(statement))

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logging.error(f"执行SQL文件失败: {str(e)}")
        return False

def backup_database(backup_path):
    """备份数据库"""
    try:
        # 这里可以实现数据库备份逻辑
        # 例如使用mysqldump等工具
        pass
    except Exception as e:
        logging.error(f"数据库备份失败: {str(e)}")
        return False