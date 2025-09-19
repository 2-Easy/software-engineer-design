from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
import bcrypt
import re
from models import User, SystemLog, db

def hash_password(password):
    """密码加密"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    """密码验证"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def validate_email(email):
    """邮箱格式验证"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """手机号格式验证"""
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, phone) is not None

def validate_password(password):
    """密码强度验证"""
    if len(password) < 6 or len(password) > 16:
        return False, "密码长度必须在6-16位之间"

    if not re.search(r'[a-zA-Z]', password):
        return False, "密码必须包含字母"

    if not re.search(r'\d', password):
        return False, "密码必须包含数字"

    return True, "密码格式正确"

def get_current_user():
    """获取当前登录用户"""
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        if current_user_id:
            return User.query.get(current_user_id)
    except:
        pass
    return None

def require_auth(user_types=None):
    """认证装饰器"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': '用户未登录'}), 401

            if user_types and current_user.user_type not in user_types:
                return jsonify({'error': '权限不足'}), 403

            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator

def log_action(user_id, action, description=None, ip_address=None):
    """记录系统日志"""
    try:
        if not ip_address:
            ip_address = request.remote_addr

        log = SystemLog(
            user_id=user_id,
            action=action,
            description=description,
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"记录日志失败: {str(e)}")

def success_response(data=None, message="操作成功"):
    """成功响应格式"""
    response = {
        'success': True,
        'message': message
    }
    if data is not None:
        response['data'] = data
    return jsonify(response)

def error_response(message="操作失败", code=400):
    """错误响应格式"""
    return jsonify({
        'success': False,
        'message': message
    }), code

def paginate_query(query, page=1, per_page=10):
    """分页查询"""
    try:
        page = int(page) if page else 1
        per_page = int(per_page) if per_page else 10
        per_page = min(per_page, 100)  # 限制最大每页数量

        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return {
            'items': [item.to_dict() for item in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': paginated.has_next,
            'has_prev': paginated.has_prev
        }
    except Exception as e:
        current_app.logger.error(f"分页查询失败: {str(e)}")
        return {
            'items': [],
            'total': 0,
            'pages': 0,
            'current_page': 1,
            'per_page': per_page,
            'has_next': False,
            'has_prev': False
        }