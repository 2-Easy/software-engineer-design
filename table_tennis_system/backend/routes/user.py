from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import User, CoachProfile, Campus, CoachStudentRelation, db
from utils.auth import require_auth, log_action, success_response, error_response, paginate_query
from datetime import datetime

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/campus', methods=['GET'])
def get_campus_list():
    """获取校区列表"""
    try:
        campus_list = Campus.query.all()
        return success_response([campus.to_dict() for campus in campus_list])
    except Exception as e:
        return error_response(f'获取校区列表失败: {str(e)}')

@user_bp.route('/coaches', methods=['GET'])
def get_coaches():
    """获取教练列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        campus_id = request.args.get('campus_id', type=int)
        name = request.args.get('name')
        gender = request.args.get('gender')
        coach_level = request.args.get('coach_level')

        # 构建查询
        query = db.session.query(User).join(CoachProfile).filter(
            User.user_type == 'coach',
            User.status == 'active'
        )

        if campus_id:
            query = query.filter(User.campus_id == campus_id)
        if name:
            query = query.filter(User.real_name.like(f'%{name}%'))
        if gender:
            query = query.filter(User.gender == gender)
        if coach_level:
            query = query.filter(CoachProfile.coach_level == coach_level)

        # 分页查询
        result = paginate_query(query, page, per_page)

        # 添加教练详细信息
        for item in result['items']:
            user = User.query.get(item['id'])
            if user and user.coach_profile:
                item['coach_profile'] = user.coach_profile.to_dict()

        return success_response(result)

    except Exception as e:
        return error_response(f'获取教练列表失败: {str(e)}')

@user_bp.route('/coaches/<int:coach_id>', methods=['GET'])
def get_coach_detail(coach_id):
    """获取教练详情"""
    try:
        user = User.query.filter_by(id=coach_id, user_type='coach').first()
        if not user:
            return error_response('教练不存在', 404)

        coach_info = user.to_dict()
        if user.coach_profile:
            coach_info['coach_profile'] = user.coach_profile.to_dict()

        return success_response(coach_info)

    except Exception as e:
        return error_response(f'获取教练详情失败: {str(e)}')

@user_bp.route('/students', methods=['GET'])
@require_auth(['campus_admin', 'super_admin'])
def get_students(current_user):
    """获取学员列表（管理员权限）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        campus_id = request.args.get('campus_id', type=int)
        name = request.args.get('name')

        # 构建查询
        query = User.query.filter(User.user_type == 'student')

        # 校区管理员只能看到自己校区的学员
        if current_user.user_type == 'campus_admin':
            query = query.filter(User.campus_id == current_user.campus_id)
        elif campus_id:
            query = query.filter(User.campus_id == campus_id)

        if name:
            query = query.filter(User.real_name.like(f'%{name}%'))

        # 分页查询
        result = paginate_query(query, page, per_page)

        return success_response(result)

    except Exception as e:
        return error_response(f'获取学员列表失败: {str(e)}')

@user_bp.route('/campus', methods=['POST'])
@require_auth(['super_admin'])
def create_campus(current_user):
    """创建校区（超级管理员）"""
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = ['name', 'address']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'{field} 为必填项')

        # 检查校区名称是否已存在
        existing_campus = Campus.query.filter_by(name=data['name']).first()
        if existing_campus:
            return error_response('校区名称已存在')

        # 创建校区
        campus = Campus(
            name=data['name'],
            address=data['address'],
            contact_person=data.get('contact_person'),
            contact_phone=data.get('contact_phone'),
            contact_email=data.get('contact_email'),
            campus_type=data.get('campus_type', 'branch'),
            manager_id=data.get('manager_id')
        )

        db.session.add(campus)
        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'create_campus', f'创建校区: {campus.name}', request.remote_addr)

        return success_response(campus.to_dict(), '校区创建成功')

    except Exception as e:
        db.session.rollback()
        return error_response(f'创建校区失败: {str(e)}')

@user_bp.route('/campus/<int:campus_id>', methods=['PUT'])
@require_auth(['super_admin'])
def update_campus(current_user, campus_id):
    """更新校区信息（超级管理员）"""
    try:
        campus = Campus.query.get(campus_id)
        if not campus:
            return error_response('校区不存在', 404)

        data = request.get_json()

        # 可更新的字段
        updatable_fields = ['name', 'address', 'contact_person', 'contact_phone',
                           'contact_email', 'campus_type', 'manager_id']

        for field in updatable_fields:
            if field in data:
                # 检查校区名称唯一性
                if field == 'name' and data[field] != campus.name:
                    existing_campus = Campus.query.filter_by(name=data[field]).first()
                    if existing_campus:
                        return error_response('校区名称已存在')

                setattr(campus, field, data[field])

        campus.updated_at = datetime.utcnow()
        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'update_campus', f'更新校区: {campus.name}', request.remote_addr)

        return success_response(campus.to_dict(), '校区信息更新成功')

    except Exception as e:
        db.session.rollback()
        return error_response(f'更新校区失败: {str(e)}')

@user_bp.route('/campus/<int:campus_id>', methods=['DELETE'])
@require_auth(['super_admin'])
def delete_campus(current_user, campus_id):
    """删除校区（超级管理员）"""
    try:
        campus = Campus.query.get(campus_id)
        if not campus:
            return error_response('校区不存在', 404)

        # 检查是否有关联的用户
        users_count = User.query.filter_by(campus_id=campus_id).count()
        if users_count > 0:
            return error_response(f'该校区还有 {users_count} 个用户，无法删除')

        campus_name = campus.name
        db.session.delete(campus)
        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'delete_campus', f'删除校区: {campus_name}', request.remote_addr)

        return success_response(message='校区删除成功')

    except Exception as e:
        db.session.rollback()
        return error_response(f'删除校区失败: {str(e)}')

@user_bp.route('/coach-applications', methods=['GET'])
@require_auth(['campus_admin', 'super_admin'])
def get_coach_applications(current_user):
    """获取教练申请列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # 构建查询
        query = User.query.filter(
            User.user_type == 'coach',
            User.status == 'pending'
        )

        # 校区管理员只能看到自己校区的申请
        if current_user.user_type == 'campus_admin':
            query = query.filter(User.campus_id == current_user.campus_id)

        # 分页查询
        result = paginate_query(query, page, per_page)

        # 添加教练详细信息
        for item in result['items']:
            user = User.query.get(item['id'])
            if user and user.coach_profile:
                item['coach_profile'] = user.coach_profile.to_dict()

        return success_response(result)

    except Exception as e:
        return error_response(f'获取教练申请失败: {str(e)}')

@user_bp.route('/coach-applications/<int:user_id>/approve', methods=['POST'])
@require_auth(['campus_admin', 'super_admin'])
def approve_coach_application(current_user, user_id):
    """审核教练申请"""
    try:
        data = request.get_json()
        approve = data.get('approve', True)
        reason = data.get('reason', '')

        user = User.query.get(user_id)
        if not user or user.user_type != 'coach':
            return error_response('教练申请不存在', 404)

        # 检查权限
        if current_user.user_type == 'campus_admin' and user.campus_id != current_user.campus_id:
            return error_response('权限不足', 403)

        if approve:
            user.status = 'active'
            # 更新教练级别和收费标准
            if user.coach_profile and 'coach_level' in data:
                user.coach_profile.coach_level = data['coach_level']
                hourly_rates = {'senior': 200, 'intermediate': 150, 'junior': 80}
                user.coach_profile.hourly_rate = hourly_rates[data['coach_level']]

            message = '教练申请已通过'
            action_desc = f'审核通过教练申请: {user.username}'
        else:
            user.status = 'inactive'
            message = f'教练申请已拒绝: {reason}'
            action_desc = f'拒绝教练申请: {user.username}, 原因: {reason}'

        user.updated_at = datetime.utcnow()
        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'approve_coach', action_desc, request.remote_addr)

        return success_response(message=message)

    except Exception as e:
        db.session.rollback()
        return error_response(f'审核失败: {str(e)}')

@user_bp.route('/relations', methods=['GET'])
@require_auth(['student', 'coach'])
def get_user_relations(current_user):
    """获取用户的师生关系"""
    try:
        if current_user.user_type == 'student':
            relations = CoachStudentRelation.query.filter_by(
                student_id=current_user.id,
                status='approved'
            ).all()
        else:  # coach
            relations = CoachStudentRelation.query.filter_by(
                coach_id=current_user.id,
                status='approved'
            ).all()

        return success_response([relation.to_dict() for relation in relations])

    except Exception as e:
        return error_response(f'获取师生关系失败: {str(e)}')

@user_bp.route('/choose-coach', methods=['POST'])
@require_auth(['student'])
def choose_coach(current_user):
    """学员选择教练"""
    try:
        data = request.get_json()
        coach_id = data.get('coach_id')

        if not coach_id:
            return error_response('教练ID不能为空')

        # 验证教练是否存在且激活
        coach = User.query.filter_by(
            id=coach_id,
            user_type='coach',
            status='active'
        ).first()
        if not coach:
            return error_response('教练不存在或未激活')

        # 检查是否已经选择过该教练
        existing_relation = CoachStudentRelation.query.filter_by(
            student_id=current_user.id,
            coach_id=coach_id
        ).first()
        if existing_relation:
            if existing_relation.status == 'approved':
                return error_response('已经选择过该教练')
            elif existing_relation.status == 'pending':
                return error_response('申请正在审核中')

        # 检查学员选择教练数量限制（最多2个）
        student_relations_count = CoachStudentRelation.query.filter_by(
            student_id=current_user.id,
            status='approved'
        ).count()
        if student_relations_count >= 2:
            return error_response('最多只能选择2个教练')

        # 检查教练学员数量限制（最多20个）
        coach_relations_count = CoachStudentRelation.query.filter_by(
            coach_id=coach_id,
            status='approved'
        ).count()
        if coach_relations_count >= 20:
            return error_response('该教练学员数量已满')

        # 创建师生关系申请
        relation = CoachStudentRelation(
            student_id=current_user.id,
            coach_id=coach_id,
            status='pending'
        )
        db.session.add(relation)
        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'choose_coach', f'申请选择教练: {coach.username}', request.remote_addr)

        return success_response(relation.to_dict(), '选择教练申请已提交')

    except Exception as e:
        db.session.rollback()
        return error_response(f'选择教练失败: {str(e)}')

@user_bp.route('/student-applications', methods=['GET'])
@require_auth(['coach'])
def get_coach_student_applications(current_user):
    """教练查看学员申请"""
    try:
        applications = CoachStudentRelation.query.filter_by(
            coach_id=current_user.id,
            status='pending'
        ).all()

        return success_response([app.to_dict() for app in applications])

    except Exception as e:
        return error_response(f'获取学员申请失败: {str(e)}')

@user_bp.route('/student-applications/<int:relation_id>/approve', methods=['POST'])
@require_auth(['coach'])
def approve_student_application(current_user, relation_id):
    """教练审核学员申请"""
    try:
        data = request.get_json()
        approve = data.get('approve', True)
        reason = data.get('reason', '')

        relation = CoachStudentRelation.query.filter_by(
            id=relation_id,
            coach_id=current_user.id,
            status='pending'
        ).first()

        if not relation:
            return error_response('申请不存在', 404)

        if approve:
            # 再次检查数量限制
            coach_relations_count = CoachStudentRelation.query.filter_by(
                coach_id=current_user.id,
                status='approved'
            ).count()
            if coach_relations_count >= 20:
                return error_response('学员数量已满，无法接收更多学员')

            relation.status = 'approved'
            relation.approve_time = datetime.utcnow()

            # 更新教练当前学员数
            if current_user.coach_profile:
                current_user.coach_profile.current_students += 1

            message = '学员申请已通过'
        else:
            relation.status = 'rejected'
            message = f'学员申请已拒绝: {reason}'

        db.session.commit()

        # 记录日志
        action_desc = f'审核学员申请: {relation.student.username}, 结果: {"通过" if approve else "拒绝"}'
        log_action(current_user.id, 'approve_student', action_desc, request.remote_addr)

        return success_response(message=message)

    except Exception as e:
        db.session.rollback()
        return error_response(f'审核失败: {str(e)}')

@user_bp.route('/my-students', methods=['GET'])
@require_auth(['coach'])
def get_my_students(current_user):
    """教练查看自己的学员列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # 查询已通过审核的师生关系
        relations = CoachStudentRelation.query.filter_by(
            coach_id=current_user.id,
            status='approved'
        ).all()

        # 格式化返回数据
        students_data = []
        for relation in relations:
            if relation.student:
                student_info = relation.student.to_dict()
                student_info['relation_info'] = {
                    'id': relation.id,
                    'apply_time': relation.apply_time.isoformat() if relation.apply_time else None,
                    'approve_time': relation.approve_time.isoformat() if relation.approve_time else None,
                    'status': relation.status
                }
                students_data.append(student_info)

        # 手动分页
        total = len(students_data)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_data = students_data[start:end]

        result = {
            'items': paginated_data,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'current_page': page,
            'per_page': per_page,
            'has_next': end < total,
            'has_prev': page > 1
        }

        return success_response(result)

    except Exception as e:
        return error_response(f'获取学员列表失败: {str(e)}')