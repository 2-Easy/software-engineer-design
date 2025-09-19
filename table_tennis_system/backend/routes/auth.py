from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, CoachProfile, Account, Campus, db
from utils.auth import hash_password, check_password, validate_email, validate_phone, validate_password, log_action, success_response, error_response
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = ['username', 'password', 'real_name', 'user_type', 'campus_id']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'{field} 为必填项')

        username = data['username']
        password = data['password']
        real_name = data['real_name']
        user_type = data['user_type']
        campus_id = data['campus_id']

        # 验证用户名唯一性
        if User.query.filter_by(username=username).first():
            return error_response('用户名已存在')

        # 验证密码强度
        is_valid, message = validate_password(password)
        if not is_valid:
            return error_response(message)

        # 验证邮箱格式
        email = data.get('email')
        if email and not validate_email(email):
            return error_response('邮箱格式不正确')

        # 验证手机号格式
        phone = data.get('phone')
        if phone and not validate_phone(phone):
            return error_response('手机号格式不正确')

        # 验证校区是否存在
        campus = Campus.query.get(campus_id)
        if not campus:
            return error_response('校区不存在')

        # 创建用户
        user = User(
            username=username,
            password=hash_password(password),
            real_name=real_name,
            gender=data.get('gender'),
            age=data.get('age'),
            phone=phone,
            email=email,
            user_type=user_type,
            campus_id=campus_id,
            status='pending' if user_type == 'coach' else 'active'
        )

        db.session.add(user)
        db.session.flush()  # 获取用户ID

        # 如果是教练，创建教练信息
        if user_type == 'coach':
            coach_level = data.get('coach_level', 'junior')
            hourly_rates = {'senior': 200, 'intermediate': 150, 'junior': 80}

            coach_profile = CoachProfile(
                user_id=user.id,
                coach_level=coach_level,
                hourly_rate=hourly_rates[coach_level],
                achievements=data.get('achievements', ''),
                photo_url=data.get('photo_url')
            )
            db.session.add(coach_profile)

        # 为学员创建账户
        if user_type == 'student':
            account = Account(user_id=user.id, balance=0.00)
            db.session.add(account)

        db.session.commit()

        # 记录日志
        log_action(user.id, 'register', f'用户注册: {username}', request.remote_addr)

        return success_response({
            'user_id': user.id,
            'username': username,
            'status': user.status
        }, '注册成功' if user_type != 'coach' else '注册申请已提交，等待审核')

    except Exception as e:
        db.session.rollback()
        return error_response(f'注册失败: {str(e)}')

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return error_response('用户名和密码不能为空')

        # 查找用户
        user = User.query.filter_by(username=username).first()
        if not user:
            return error_response('用户名或密码错误')

        # 验证密码
        if not check_password(password, user.password):
            return error_response('用户名或密码错误')

        # 检查用户状态
        if user.status == 'inactive':
            return error_response('账户已被禁用')
        elif user.status == 'pending':
            return error_response('账户等待审核中')

        # 创建访问令牌
        access_token = create_access_token(identity=user.id)

        # 记录登录日志
        log_action(user.id, 'login', f'用户登录: {username}', request.remote_addr)

        # 获取用户详细信息
        user_info = user.to_dict()
        if user.user_type == 'coach' and user.coach_profile:
            user_info['coach_profile'] = user.coach_profile.to_dict()
        if user.user_type == 'student' and user.account:
            user_info['account'] = user.account.to_dict()

        return success_response({
            'access_token': access_token,
            'user': user_info
        }, '登录成功')

    except Exception as e:
        return error_response(f'登录失败: {str(e)}')

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if user:
            # 记录登出日志
            log_action(user.id, 'logout', f'用户登出: {user.username}', request.remote_addr)

        return success_response(message='登出成功')

    except Exception as e:
        return error_response(f'登出失败: {str(e)}')

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取用户信息"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return error_response('用户不存在', 404)

        user_info = user.to_dict()
        if user.user_type == 'coach' and user.coach_profile:
            user_info['coach_profile'] = user.coach_profile.to_dict()
        if user.user_type == 'student' and user.account:
            user_info['account'] = user.account.to_dict()

        return success_response(user_info)

    except Exception as e:
        return error_response(f'获取用户信息失败: {str(e)}')

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户信息"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return error_response('用户不存在', 404)

        data = request.get_json()

        # 可更新的字段
        updatable_fields = ['real_name', 'gender', 'age', 'phone', 'email']

        for field in updatable_fields:
            if field in data:
                if field == 'email' and data[field] and not validate_email(data[field]):
                    return error_response('邮箱格式不正确')
                if field == 'phone' and data[field] and not validate_phone(data[field]):
                    return error_response('手机号格式不正确')

                setattr(user, field, data[field])

        user.updated_at = datetime.utcnow()
        db.session.commit()

        # 记录日志
        log_action(user.id, 'update_profile', '更新个人信息', request.remote_addr)

        return success_response(user.to_dict(), '个人信息更新成功')

    except Exception as e:
        db.session.rollback()
        return error_response(f'更新失败: {str(e)}')

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """修改密码"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return error_response('用户不存在', 404)

        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not old_password or not new_password:
            return error_response('原密码和新密码不能为空')

        # 验证原密码
        if not check_password(old_password, user.password):
            return error_response('原密码错误')

        # 验证新密码强度
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return error_response(message)

        # 更新密码
        user.password = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()

        # 记录日志
        log_action(user.id, 'change_password', '修改密码', request.remote_addr)

        return success_response(message='密码修改成功')

    except Exception as e:
        db.session.rollback()
        return error_response(f'密码修改失败: {str(e)}')