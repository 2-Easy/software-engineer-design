from flask import Flask, render_template, jsonify, send_from_directory
import os
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from models import db
from utils.database import test_connection

# 导入路由
from routes.auth import auth_bp
from routes.user import user_bp
from routes.booking import booking_bp
from routes.payment import payment_bp
from routes.match import match_bp

def create_app():
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化扩展
    db.init_app(app)
    jwt = JWTManager(app)
    CORS(app)

    # 创建数据库表
    with app.app_context():
        db.create_all()

    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(match_bp)

    # 错误处理
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'success': False, 'message': '请求参数错误'}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'success': False, 'message': '未授权访问'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'message': '资源不存在'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'success': False, 'message': '服务器内部错误'}), 500

    # JWT错误处理
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'success': False, 'message': '令牌已过期'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'success': False, 'message': '无效令牌'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'success': False, 'message': '缺少访问令牌'}), 401

    # 根路由
    @app.route('/')
    def index():
        """首页"""
        return render_template('index.html')

    # 登录页面
    @app.route('/login')
    def login_page():
        """登录页面"""
        return render_template('login.html')

    # 注册页面
    @app.route('/register')
    def register_page():
        """注册页面"""
        return render_template('register.html')

    # 健康检查
    @app.route('/api/health')
    def health_check():
        """健康检查接口"""
        db_status = test_connection()
        return jsonify({
            'status': 'healthy' if db_status else 'unhealthy',
            'database': 'connected' if db_status else 'disconnected',
            'version': '1.0.0'
        })

    # API文档路由
    @app.route('/api/docs')
    def api_docs():
        """API文档"""
        return render_template('api_docs.html')

    # 前端文件服务
    @app.route('/frontend/<path:filename>')
    def frontend_files(filename):
        """提供前端静态文件"""
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        return send_from_directory(frontend_path, filename)

    return app

if __name__ == '__main__':
    app = create_app()

    # 开发环境配置
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        threaded=True
    )