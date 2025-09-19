from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import Booking, Table, CoachStudentRelation, Account, Transaction, User, db
from utils.auth import require_auth, log_action, success_response, error_response, paginate_query
from datetime import datetime, date, time, timedelta
from sqlalchemy import and_, or_

booking_bp = Blueprint('booking', __name__, url_prefix='/api/booking')

@booking_bp.route('/tables', methods=['GET'])
@require_auth(['student', 'coach'])
def get_available_tables(current_user):
    """获取可用球台"""
    try:
        campus_id = request.args.get('campus_id', type=int)
        booking_date = request.args.get('date')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

        if not all([campus_id, booking_date, start_time, end_time]):
            return error_response('校区、日期和时间段为必填项')

        # 获取所有球台
        all_tables = Table.query.filter_by(
            campus_id=campus_id,
            status='available'
        ).all()

        # 检查时间段冲突的预约
        occupied_tables = db.session.query(Booking.table_id).filter(
            and_(
                Booking.booking_date == booking_date,
                Booking.status.in_(['pending', 'confirmed']),
                or_(
                    and_(Booking.start_time <= start_time, Booking.end_time > start_time),
                    and_(Booking.start_time < end_time, Booking.end_time >= end_time),
                    and_(Booking.start_time >= start_time, Booking.end_time <= end_time)
                )
            )
        ).all()

        occupied_table_ids = [table[0] for table in occupied_tables if table[0]]

        # 过滤可用球台
        available_tables = [
            table for table in all_tables
            if table.id not in occupied_table_ids
        ]

        return success_response([table.to_dict() for table in available_tables])

    except Exception as e:
        return error_response(f'获取可用球台失败: {str(e)}')

@booking_bp.route('/schedule/<int:coach_id>', methods=['GET'])
@require_auth(['student', 'coach'])
def get_coach_schedule(current_user, coach_id):
    """获取教练课表"""
    try:
        start_date = request.args.get('start_date', date.today().isoformat())
        end_date = request.args.get('end_date', (date.today() + timedelta(days=7)).isoformat())

        # 获取教练的预约记录
        bookings = Booking.query.filter(
            and_(
                Booking.coach_id == coach_id,
                Booking.booking_date >= start_date,
                Booking.booking_date <= end_date,
                Booking.status.in_(['pending', 'confirmed'])
            )
        ).order_by(Booking.booking_date, Booking.start_time).all()

        # 按日期组织课表
        schedule = {}
        current_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

        while current_date <= end_date_obj:
            date_str = current_date.isoformat()
            schedule[date_str] = []

            # 添加该日期的预约
            for booking in bookings:
                if booking.booking_date == current_date:
                    schedule[date_str].append({
                        'booking_id': booking.id,
                        'start_time': booking.start_time.isoformat(),
                        'end_time': booking.end_time.isoformat(),
                        'status': booking.status,
                        'student_name': booking.student.real_name if booking.student else None,
                        'table_number': booking.table.table_number if booking.table else None
                    })

            current_date += timedelta(days=1)

        return success_response({
            'coach_id': coach_id,
            'schedule': schedule
        })

    except Exception as e:
        return error_response(f'获取教练课表失败: {str(e)}')

@booking_bp.route('/create', methods=['POST'])
@require_auth(['student'])
def create_booking(current_user):
    """创建课程预约"""
    try:
        data = request.get_json()
        coach_id = data.get('coach_id')
        booking_date = data.get('date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        table_id = data.get('table_id')

        # 验证必填字段
        if not all([coach_id, booking_date, start_time, end_time]):
            return error_response('教练、日期、开始时间和结束时间为必填项')

        # 验证师生关系
        relation = CoachStudentRelation.query.filter_by(
            student_id=current_user.id,
            coach_id=coach_id,
            status='approved'
        ).first()
        if not relation:
            return error_response('您还未选择该教练，请先建立师生关系')

        # 验证预约日期（不能是过去日期）
        booking_date_obj = datetime.strptime(booking_date, '%Y-%m-%d').date()
        if booking_date_obj <= date.today():
            return error_response('预约日期不能是今天或过去日期')

        # 验证时间格式
        start_time_obj = datetime.strptime(start_time, '%H:%M:%S').time()
        end_time_obj = datetime.strptime(end_time, '%H:%M:%S').time()

        if start_time_obj >= end_time_obj:
            return error_response('结束时间必须晚于开始时间')

        # 计算课时费
        coach = User.query.get(coach_id)
        if not coach or not coach.coach_profile:
            return error_response('教练信息不存在')

        # 计算时长（小时）
        start_datetime = datetime.combine(date.today(), start_time_obj)
        end_datetime = datetime.combine(date.today(), end_time_obj)
        duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
        lesson_fee = float(coach.coach_profile.hourly_rate) * duration_hours

        # 检查账户余额
        account = Account.query.filter_by(user_id=current_user.id).first()
        if not account or account.balance < lesson_fee:
            return error_response(f'账户余额不足，需要{lesson_fee}元，当前余额{account.balance if account else 0}元')

        # 检查时间冲突
        existing_booking = Booking.query.filter(
            and_(
                or_(Booking.student_id == current_user.id, Booking.coach_id == coach_id),
                Booking.booking_date == booking_date,
                Booking.status.in_(['pending', 'confirmed']),
                or_(
                    and_(Booking.start_time <= start_time_obj, Booking.end_time > start_time_obj),
                    and_(Booking.start_time < end_time_obj, Booking.end_time >= end_time_obj),
                    and_(Booking.start_time >= start_time_obj, Booking.end_time <= end_time_obj)
                )
            )
        ).first()

        if existing_booking:
            return error_response('该时间段已有预约冲突')

        # 验证球台可用性
        if table_id:
            table = Table.query.get(table_id)
            if not table:
                return error_response('球台不存在')

            table_conflict = Booking.query.filter(
                and_(
                    Booking.table_id == table_id,
                    Booking.booking_date == booking_date,
                    Booking.status.in_(['pending', 'confirmed']),
                    or_(
                        and_(Booking.start_time <= start_time_obj, Booking.end_time > start_time_obj),
                        and_(Booking.start_time < end_time_obj, Booking.end_time >= end_time_obj),
                        and_(Booking.start_time >= start_time_obj, Booking.end_time <= end_time_obj)
                    )
                )
            ).first()

            if table_conflict:
                return error_response('该球台在此时间段已被占用')

        # 创建预约
        booking = Booking(
            student_id=current_user.id,
            coach_id=coach_id,
            campus_id=coach.campus_id,
            table_id=table_id,
            booking_date=booking_date_obj,
            start_time=start_time_obj,
            end_time=end_time_obj,
            lesson_fee=lesson_fee,
            status='pending'
        )

        db.session.add(booking)
        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'create_booking',
                  f'创建预约: 教练{coach.real_name}, 日期{booking_date}, 时间{start_time}-{end_time}',
                  request.remote_addr)

        return success_response(booking.to_dict(), '预约申请已提交，等待教练确认')

    except Exception as e:
        db.session.rollback()
        return error_response(f'创建预约失败: {str(e)}')

@booking_bp.route('/<int:booking_id>/confirm', methods=['POST'])
@require_auth(['coach'])
def confirm_booking(current_user, booking_id):
    """确认预约"""
    try:
        data = request.get_json()
        confirm = data.get('confirm', True)
        reason = data.get('reason', '')

        booking = Booking.query.filter_by(
            id=booking_id,
            coach_id=current_user.id,
            status='pending'
        ).first()

        if not booking:
            return error_response('预约不存在或已处理', 404)

        if confirm:
            # 确认预约，扣除学员账户余额
            account = Account.query.filter_by(user_id=booking.student_id).first()
            if not account or account.balance < booking.lesson_fee:
                return error_response('学员账户余额不足，无法确认预约')

            # 扣费
            account.balance -= booking.lesson_fee
            account.updated_at = datetime.utcnow()

            # 记录交易
            transaction = Transaction(
                user_id=booking.student_id,
                transaction_type='withdraw',
                amount=booking.lesson_fee,
                payment_method='system',
                description=f'课时费扣除 - 教练: {current_user.real_name}',
                related_booking_id=booking.id
            )
            db.session.add(transaction)

            booking.status = 'confirmed'
            booking.confirm_time = datetime.utcnow()
            message = '预约已确认'
        else:
            booking.status = 'cancelled'
            message = f'预约已拒绝: {reason}'

        db.session.commit()

        # 记录日志
        action_desc = f'{"确认" if confirm else "拒绝"}预约: 学员{booking.student.real_name}, 原因: {reason if not confirm else "无"}'
        log_action(current_user.id, 'confirm_booking', action_desc, request.remote_addr)

        return success_response(message=message)

    except Exception as e:
        db.session.rollback()
        return error_response(f'确认预约失败: {str(e)}')

@booking_bp.route('/<int:booking_id>/cancel', methods=['POST'])
@require_auth(['student', 'coach'])
def cancel_booking(current_user, booking_id):
    """取消预约"""
    try:
        data = request.get_json()
        reason = data.get('reason', '用户取消')

        # 查找预约
        query_filter = {'id': booking_id, 'status': 'confirmed'}
        if current_user.user_type == 'student':
            query_filter['student_id'] = current_user.id
        else:
            query_filter['coach_id'] = current_user.id

        booking = Booking.query.filter_by(**query_filter).first()

        if not booking:
            return error_response('预约不存在或无权限操作', 404)

        # 检查取消时间限制（24小时前）
        booking_datetime = datetime.combine(booking.booking_date, booking.start_time)
        current_datetime = datetime.now()
        time_diff = booking_datetime - current_datetime

        if time_diff.total_seconds() < 24 * 3600:  # 24小时
            return error_response('预约开始前24小时内无法取消')

        # TODO: 检查当月取消次数限制（暂时跳过）

        # 取消预约
        booking.status = 'cancelled'

        # 退费
        account = Account.query.filter_by(user_id=booking.student_id).first()
        if account:
            account.balance += booking.lesson_fee
            account.updated_at = datetime.utcnow()

            # 记录退费交易
            transaction = Transaction(
                user_id=booking.student_id,
                transaction_type='refund',
                amount=booking.lesson_fee,
                payment_method='system',
                description=f'预约取消退费 - 教练: {booking.coach.real_name}',
                related_booking_id=booking.id
            )
            db.session.add(transaction)

        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'cancel_booking',
                  f'取消预约: {booking.student.real_name} - {booking.coach.real_name}, 原因: {reason}',
                  request.remote_addr)

        return success_response(message='预约已取消，课时费已退回')

    except Exception as e:
        db.session.rollback()
        return error_response(f'取消预约失败: {str(e)}')

@booking_bp.route('/my-bookings', methods=['GET'])
@require_auth(['student', 'coach'])
def get_my_bookings(current_user):
    """获取我的预约记录"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 构建查询
        if current_user.user_type == 'student':
            query = Booking.query.filter_by(student_id=current_user.id)
        else:
            query = Booking.query.filter_by(coach_id=current_user.id)

        if status:
            query = query.filter(Booking.status == status)

        # 日期范围筛选
        if start_date:
            query = query.filter(Booking.booking_date >= start_date)
        if end_date:
            query = query.filter(Booking.booking_date <= end_date)

        query = query.order_by(Booking.booking_date.desc(), Booking.start_time.desc())

        # 分页查询
        result = paginate_query(query, page, per_page)

        return success_response(result)

    except Exception as e:
        return error_response(f'获取预约记录失败: {str(e)}')

@booking_bp.route('/pending', methods=['GET'])
@require_auth(['coach'])
def get_pending_bookings(current_user):
    """获取待确认的预约"""
    try:
        bookings = Booking.query.filter_by(
            coach_id=current_user.id,
            status='pending'
        ).order_by(Booking.created_at.desc()).all()

        return success_response([booking.to_dict() for booking in bookings])

    except Exception as e:
        return error_response(f'获取待确认预约失败: {str(e)}')

@booking_bp.route('/<int:booking_id>/complete', methods=['POST'])
@require_auth(['coach'])
def complete_booking(current_user, booking_id):
    """完成预约"""
    try:
        booking = Booking.query.filter_by(
            id=booking_id,
            coach_id=current_user.id,
            status='confirmed'
        ).first()

        if not booking:
            return error_response('预约不存在或无权限操作', 404)

        # 标记预约为已完成
        booking.status = 'completed'
        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'complete_booking',
                  f'完成预约: 学员{booking.student.real_name}, 日期{booking.booking_date}',
                  request.remote_addr)

        return success_response(message='预约已标记为完成')

    except Exception as e:
        db.session.rollback()
        return error_response(f'完成预约失败: {str(e)}')

@booking_bp.route('/admin/all-bookings', methods=['GET'])
@require_auth(['campus_admin', 'super_admin'])
def get_all_bookings_admin(current_user):
    """管理员获取所有预约记录"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        campus_id = request.args.get('campus_id', type=int)
        date = request.args.get('date')

        # 构建查询
        query = Booking.query

        # 校区管理员只能看到自己校区的预约
        if current_user.user_type == 'campus_admin':
            query = query.filter(Booking.campus_id == current_user.campus_id)
        elif campus_id:
            query = query.filter(Booking.campus_id == campus_id)

        if status:
            query = query.filter(Booking.status == status)

        if date:
            query = query.filter(Booking.booking_date == date)

        query = query.order_by(Booking.created_at.desc())

        # 分页查询
        result = paginate_query(query, page, per_page)

        return success_response(result)

    except Exception as e:
        return error_response(f'获取预约列表失败: {str(e)}')

@booking_bp.route('/<int:booking_id>/approve', methods=['POST'])
@require_auth(['campus_admin', 'super_admin'])
def approve_booking_admin(current_user, booking_id):
    """管理员确认预约"""
    try:
        booking = Booking.query.get(booking_id)
        if not booking:
            return error_response('预约不存在', 404)

        # 检查权限
        if current_user.user_type == 'campus_admin' and booking.campus_id != current_user.campus_id:
            return error_response('权限不足', 403)

        if booking.status != 'pending':
            return error_response('只能确认待处理的预约')

        # 检查学员账户余额
        account = Account.query.filter_by(user_id=booking.student_id).first()
        if not account or account.balance < booking.lesson_fee:
            return error_response('学员账户余额不足，无法确认预约')

        # 扣费
        account.balance -= booking.lesson_fee
        account.updated_at = datetime.utcnow()

        # 记录交易
        transaction = Transaction(
            user_id=booking.student_id,
            transaction_type='withdraw',
            amount=booking.lesson_fee,
            payment_method='system',
            description=f'课时费扣除 - 教练: {booking.coach.real_name} (管理员确认)',
            related_booking_id=booking.id
        )
        db.session.add(transaction)

        booking.status = 'confirmed'
        booking.confirm_time = datetime.utcnow()

        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'admin_approve_booking',
                  f'管理员确认预约: 学员{booking.student.real_name} - 教练{booking.coach.real_name}',
                  request.remote_addr)

        return success_response(message='预约已确认')

    except Exception as e:
        db.session.rollback()
        return error_response(f'确认预约失败: {str(e)}')

@booking_bp.route('/<int:booking_id>/admin-cancel', methods=['POST'])
@require_auth(['campus_admin', 'super_admin'])
def cancel_booking_admin(current_user, booking_id):
    """管理员取消预约"""
    try:
        data = request.get_json()
        reason = data.get('reason', '管理员取消')

        booking = Booking.query.get(booking_id)
        if not booking:
            return error_response('预约不存在', 404)

        # 检查权限
        if current_user.user_type == 'campus_admin' and booking.campus_id != current_user.campus_id:
            return error_response('权限不足', 403)

        if booking.status == 'cancelled':
            return error_response('预约已被取消')

        # 退费（如果已经扣费）
        if booking.status == 'confirmed':
            account = Account.query.filter_by(user_id=booking.student_id).first()
            if account:
                account.balance += booking.lesson_fee
                account.updated_at = datetime.utcnow()

                # 记录退费交易
                transaction = Transaction(
                    user_id=booking.student_id,
                    transaction_type='refund',
                    amount=booking.lesson_fee,
                    payment_method='system',
                    description=f'预约取消退费 - 教练: {booking.coach.real_name} (管理员取消)',
                    related_booking_id=booking.id
                )
                db.session.add(transaction)

        booking.status = 'cancelled'
        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'admin_cancel_booking',
                  f'管理员取消预约: 学员{booking.student.real_name} - 教练{booking.coach.real_name}, 原因: {reason}',
                  request.remote_addr)

        return success_response(message='预约已取消，费用已退回')

    except Exception as e:
        db.session.rollback()
        return error_response(f'取消预约失败: {str(e)}')