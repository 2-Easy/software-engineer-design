from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import Match, MatchRegistration, Account, Transaction, User, db
from utils.auth import require_auth, log_action, success_response, error_response, paginate_query
from datetime import datetime, date
from decimal import Decimal

match_bp = Blueprint('match', __name__, url_prefix='/api/match')

@match_bp.route('/list', methods=['GET'])
def get_matches():
    """获取比赛列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')

        # 构建查询
        query = Match.query

        if status:
            query = query.filter(Match.status == status)
        else:
            # 默认显示即将开始和报名中的比赛
            query = query.filter(Match.status.in_(['upcoming', 'registration']))

        query = query.order_by(Match.match_date.desc())

        # 分页查询
        result = paginate_query(query, page, per_page)

        return success_response(result)

    except Exception as e:
        return error_response(f'获取比赛列表失败: {str(e)}')

@match_bp.route('/<int:match_id>', methods=['GET'])
def get_match_detail(match_id):
    """获取比赛详情"""
    try:
        match = Match.query.get(match_id)
        if not match:
            return error_response('比赛不存在', 404)

        # 获取报名统计
        registration_stats = db.session.query(
            MatchRegistration.group_name,
            db.func.count(MatchRegistration.id).label('count')
        ).filter(
            MatchRegistration.match_id == match_id,
            MatchRegistration.payment_status == 'paid'
        ).group_by(MatchRegistration.group_name).all()

        stats = {}
        for stat in registration_stats:
            stats[stat.group_name] = stat.count

        match_info = match.to_dict()
        match_info['registration_stats'] = stats

        return success_response(match_info)

    except Exception as e:
        return error_response(f'获取比赛详情失败: {str(e)}')

@match_bp.route('/create', methods=['POST'])
@require_auth(['campus_admin', 'super_admin'])
def create_match(current_user):
    """创建比赛"""
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = ['name', 'match_date', 'registration_end', 'registration_fee', 'campus_id']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'{field} 为必填项')

        # 验证日期格式和逻辑
        match_date_str = data['match_date']
        match_time_str = data.get('match_time', '09:00')
        registration_end_str = data['registration_end']

        # 解析比赛日期
        match_date = datetime.strptime(match_date_str, '%Y-%m-%d').date()

        # 构建完整的比赛日期时间
        match_datetime = datetime.strptime(f"{match_date_str} {match_time_str}", '%Y-%m-%d %H:%M')

        # 解析报名截止日期
        registration_end = datetime.strptime(registration_end_str, '%Y-%m-%d').date()
        registration_end_datetime = datetime.combine(registration_end, datetime.min.time().replace(hour=23, minute=59))

        # 验证日期逻辑
        if registration_end >= match_date:
            return error_response('报名截止日期必须早于比赛日期')

        # 创建比赛
        match = Match(
            name=data['name'],
            campus_id=data['campus_id'],
            match_date=match_date,
            match_time=match_time_str,
            registration_start=datetime.now(),  # 立即开始报名
            registration_end=registration_end_datetime,
            registration_fee=float(data['registration_fee']),
            max_participants=data.get('max_participants'),
            match_type=data.get('match_type', 'singles'),
            description=data.get('description'),
            prize_info=data.get('prize_info'),
            status='registration'  # 创建后立即开放报名
        )

        db.session.add(match)
        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'create_match',
                  f'创建比赛: {data["name"]}, 日期: {match_date}',
                  request.remote_addr)

        return success_response(match.to_dict(), '比赛创建成功')

    except ValueError as e:
        return error_response(f'日期格式错误: {str(e)}')
    except Exception as e:
        db.session.rollback()
        return error_response(f'创建比赛失败: {str(e)}')

@match_bp.route('/<int:match_id>/register', methods=['POST'])
@require_auth(['student'])
def register_match(current_user, match_id):
    """学员报名比赛"""
    try:
        data = request.get_json()
        group_name = data.get('group_name')

        if not group_name or group_name not in ['group_a', 'group_b', 'group_c']:
            return error_response('请选择有效的比赛分组')

        # 验证比赛是否存在
        match = Match.query.get(match_id)
        if not match:
            return error_response('比赛不存在', 404)

        # 检查比赛状态
        if match.status != 'registration':
            return error_response('比赛不在报名期间')

        # 检查报名时间
        now = datetime.now()
        if now < match.registration_start or now > match.registration_end:
            return error_response('不在报名时间范围内')

        # 检查是否已报名
        existing_registration = MatchRegistration.query.filter_by(
            match_id=match_id,
            student_id=current_user.id
        ).first()

        if existing_registration:
            return error_response('您已报名该比赛')

        # 检查账户余额
        account = Account.query.filter_by(user_id=current_user.id).first()
        if not account or account.balance < match.registration_fee:
            return error_response(f'账户余额不足，需要{match.registration_fee}元报名费')

        # 扣费
        account.balance -= match.registration_fee
        account.updated_at = datetime.utcnow()

        # 记录交易
        transaction = Transaction(
            user_id=current_user.id,
            transaction_type='withdraw',
            amount=match.registration_fee,
            payment_method='system',
            description=f'比赛报名费 - {match.name}',
            status='completed'
        )
        db.session.add(transaction)

        # 创建报名记录
        registration = MatchRegistration(
            match_id=match_id,
            student_id=current_user.id,
            group_name=group_name,
            payment_status='paid'
        )
        db.session.add(registration)
        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'register_match',
                  f'报名比赛: {match.name}, 分组: {group_name}',
                  request.remote_addr)

        return success_response(registration.to_dict(), '报名成功')

    except Exception as e:
        db.session.rollback()
        return error_response(f'报名失败: {str(e)}')

@match_bp.route('/<int:match_id>/registrations', methods=['GET'])
@require_auth(['campus_admin', 'super_admin'])
def get_match_registrations(current_user, match_id):
    """获取比赛报名名单"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        group_name = request.args.get('group')

        # 构建查询
        query = MatchRegistration.query.filter_by(match_id=match_id)

        if group_name:
            query = query.filter(MatchRegistration.group_name == group_name)

        query = query.order_by(MatchRegistration.registration_time.desc())

        # 分页查询
        result = paginate_query(query, page, per_page)

        return success_response(result)

    except Exception as e:
        return error_response(f'获取报名名单失败: {str(e)}')

@match_bp.route('/my-registrations', methods=['GET'])
@require_auth(['student'])
def get_my_registrations(current_user):
    """获取我的报名记录"""
    try:
        registrations = MatchRegistration.query.filter_by(
            student_id=current_user.id
        ).order_by(MatchRegistration.registration_time.desc()).all()

        return success_response([reg.to_dict() for reg in registrations])

    except Exception as e:
        return error_response(f'获取报名记录失败: {str(e)}')

@match_bp.route('/<int:match_id>/schedule', methods=['POST'])
@require_auth(['campus_admin', 'super_admin'])
def generate_match_schedule(current_user, match_id):
    """生成比赛赛程"""
    try:
        match = Match.query.get(match_id)
        if not match:
            return error_response('比赛不存在', 404)

        # 获取各组报名人员
        registrations = MatchRegistration.query.filter_by(
            match_id=match_id,
            payment_status='paid'
        ).all()

        if not registrations:
            return error_response('暂无报名人员')

        # 按组别统计
        groups = {}
        for reg in registrations:
            group = reg.group_name
            if group not in groups:
                groups[group] = []
            groups[group].append(reg)

        # 生成赛程安排
        schedule = {}
        for group_name, participants in groups.items():
            participant_count = len(participants)

            if participant_count <= 6:
                # 全循环赛制
                schedule[group_name] = generate_round_robin_schedule(participants)
            else:
                # 分小组+交叉淘汰
                schedule[group_name] = generate_group_elimination_schedule(participants)

        # 更新比赛状态
        match.status = 'ongoing'
        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'generate_schedule',
                  f'生成比赛赛程: {match.name}',
                  request.remote_addr)

        return success_response({
            'match_id': match_id,
            'schedule': schedule
        }, '赛程生成成功')

    except Exception as e:
        db.session.rollback()
        return error_response(f'生成赛程失败: {str(e)}')

def generate_round_robin_schedule(participants):
    """生成全循环赛程"""
    schedule = []
    n = len(participants)

    if n < 2:
        return schedule

    # 简化的全循环算法
    for i in range(n):
        for j in range(i + 1, n):
            match_info = {
                'round': len(schedule) + 1,
                'player1': participants[i].student.real_name,
                'player2': participants[j].student.real_name,
                'player1_id': participants[i].student_id,
                'player2_id': participants[j].student_id
            }
            schedule.append(match_info)

    return schedule

def generate_group_elimination_schedule(participants):
    """生成分组+淘汰赛程"""
    # 简化实现：分为多个小组，每组最多6人
    groups = []
    group_size = 6
    total_participants = len(participants)

    for i in range(0, total_participants, group_size):
        group = participants[i:i + group_size]
        groups.append(group)

    schedule = {
        'groups': [],
        'elimination': []
    }

    # 小组赛
    for idx, group in enumerate(groups):
        group_schedule = generate_round_robin_schedule(group)
        schedule['groups'].append({
            'group_name': f'小组{idx + 1}',
            'matches': group_schedule
        })

    return schedule

@match_bp.route('/admin/all-matches', methods=['GET'])
@require_auth(['campus_admin', 'super_admin'])
def get_all_matches_admin(current_user):
    """管理员获取所有比赛记录"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        campus_id = request.args.get('campus_id', type=int)
        date = request.args.get('date')

        # 构建查询
        query = Match.query

        # 校区管理员只能看到自己校区的比赛
        if current_user.user_type == 'campus_admin':
            query = query.filter(Match.campus_id == current_user.campus_id)
        elif campus_id:
            query = query.filter(Match.campus_id == campus_id)

        if status:
            query = query.filter(Match.status == status)

        if date:
            query = query.filter(Match.match_date == date)

        query = query.order_by(Match.created_at.desc())

        # 分页查询
        result = paginate_query(query, page, per_page)

        return success_response(result)

    except Exception as e:
        return error_response(f'获取比赛列表失败: {str(e)}')

@match_bp.route('/<int:match_id>/start', methods=['POST'])
@require_auth(['campus_admin', 'super_admin'])
def start_match_admin(current_user, match_id):
    """管理员开始比赛"""
    try:
        match = Match.query.get(match_id)
        if not match:
            return error_response('比赛不存在', 404)

        # 检查权限
        if current_user.user_type == 'campus_admin' and match.campus_id != current_user.campus_id:
            return error_response('权限不足', 403)

        if match.status != 'registration' and match.status != 'upcoming':
            return error_response('只能开始报名中或即将开始的比赛')

        match.status = 'ongoing'
        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'start_match',
                  f'管理员开始比赛: {match.name}',
                  request.remote_addr)

        return success_response(message='比赛已开始')

    except Exception as e:
        db.session.rollback()
        return error_response(f'开始比赛失败: {str(e)}')

@match_bp.route('/<int:match_id>/cancel', methods=['POST'])
@require_auth(['campus_admin', 'super_admin'])
def cancel_match_admin(current_user, match_id):
    """管理员取消比赛"""
    try:
        data = request.get_json()
        reason = data.get('reason', '管理员取消')

        match = Match.query.get(match_id)
        if not match:
            return error_response('比赛不存在', 404)

        # 检查权限
        if current_user.user_type == 'campus_admin' and match.campus_id != current_user.campus_id:
            return error_response('权限不足', 403)

        if match.status == 'cancelled':
            return error_response('比赛已被取消')

        # 退费给已报名的学员
        registrations = MatchRegistration.query.filter_by(
            match_id=match_id,
            payment_status='paid'
        ).all()

        for registration in registrations:
            # 退还报名费
            account = Account.query.filter_by(user_id=registration.student_id).first()
            if account:
                account.balance += match.registration_fee
                account.updated_at = datetime.utcnow()

                # 记录退费交易
                transaction = Transaction(
                    user_id=registration.student_id,
                    transaction_type='refund',
                    amount=match.registration_fee,
                    payment_method='system',
                    description=f'比赛取消退费 - {match.name} (管理员取消)',
                    status='completed'
                )
                db.session.add(transaction)

            # 更新报名状态
            registration.payment_status = 'refunded'

        match.status = 'cancelled'
        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'cancel_match',
                  f'管理员取消比赛: {match.name}, 原因: {reason}',
                  request.remote_addr)

        return success_response(message='比赛已取消，报名费已退还')

    except Exception as e:
        db.session.rollback()
        return error_response(f'取消比赛失败: {str(e)}')