from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import Account, Transaction, User, db
from utils.auth import require_auth, log_action, success_response, error_response, paginate_query
from datetime import datetime
from decimal import Decimal

payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

@payment_bp.route('/account', methods=['GET'])
@require_auth(['student'])
def get_account_info(current_user):
    """获取账户信息"""
    try:
        account = Account.query.filter_by(user_id=current_user.id).first()
        if not account:
            # 如果账户不存在，创建一个
            account = Account(user_id=current_user.id, balance=0.00)
            db.session.add(account)
            db.session.commit()

        return success_response(account.to_dict())

    except Exception as e:
        return error_response(f'获取账户信息失败: {str(e)}')

@payment_bp.route('/deposit', methods=['POST'])
@require_auth(['student'])
def deposit(current_user):
    """账户充值"""
    try:
        data = request.get_json()
        amount = data.get('amount')
        payment_method = data.get('payment_method', 'offline')

        if not amount or amount <= 0:
            return error_response('充值金额必须大于0')

        amount = Decimal(str(amount))

        # 获取或创建账户
        account = Account.query.filter_by(user_id=current_user.id).first()
        if not account:
            account = Account(user_id=current_user.id, balance=0.00)
            db.session.add(account)
            db.session.flush()

        # 模拟支付处理（在实际项目中这里会调用第三方支付API）
        if payment_method in ['wechat', 'alipay']:
            # 模拟在线支付成功
            payment_status = 'completed'
            description = f'{payment_method}充值'
        else:
            # 线下支付需要管理员确认
            payment_status = 'completed'  # 简化处理，直接成功
            description = '线下充值'

        # 更新账户余额
        account.balance += amount
        account.updated_at = datetime.utcnow()

        # 记录交易
        transaction = Transaction(
            user_id=current_user.id,
            transaction_type='deposit',
            amount=amount,
            payment_method=payment_method,
            status=payment_status,
            description=description
        )
        db.session.add(transaction)
        db.session.commit()

        # 记录日志
        log_action(current_user.id, 'deposit',
                  f'账户充值: {amount}元, 支付方式: {payment_method}',
                  request.remote_addr)

        return success_response({
            'transaction_id': transaction.id,
            'new_balance': float(account.balance)
        }, '充值成功')

    except Exception as e:
        db.session.rollback()
        return error_response(f'充值失败: {str(e)}')

@payment_bp.route('/transactions', methods=['GET'])
@require_auth(['student'])
def get_transactions(current_user):
    """获取交易记录"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        transaction_type = request.args.get('type')

        # 构建查询
        query = Transaction.query.filter_by(user_id=current_user.id)

        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)

        query = query.order_by(Transaction.created_at.desc())

        # 分页查询
        result = paginate_query(query, page, per_page)

        return success_response(result)

    except Exception as e:
        return error_response(f'获取交易记录失败: {str(e)}')

@payment_bp.route('/statistics', methods=['GET'])
@require_auth(['campus_admin', 'super_admin'])
def get_payment_statistics(current_user):
    """获取收费统计（管理员）"""
    try:
        # 获取统计数据
        stats = {}

        # 总收入
        total_income = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter(
            Transaction.transaction_type == 'deposit',
            Transaction.status == 'completed'
        ).scalar() or 0

        # 总支出（课时费）
        total_expense = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter(
            Transaction.transaction_type == 'withdraw',
            Transaction.status == 'completed'
        ).scalar() or 0

        # 今日收入
        today = datetime.now().date()
        today_income = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter(
            Transaction.transaction_type == 'deposit',
            Transaction.status == 'completed',
            db.func.date(Transaction.created_at) == today
        ).scalar() or 0

        # 本月收入
        this_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_income = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter(
            Transaction.transaction_type == 'deposit',
            Transaction.status == 'completed',
            Transaction.created_at >= this_month_start
        ).scalar() or 0

        stats = {
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'net_income': float(total_income - total_expense),
            'today_income': float(today_income),
            'this_month_income': float(this_month_income)
        }

        return success_response(stats)

    except Exception as e:
        return error_response(f'获取统计数据失败: {str(e)}')

@payment_bp.route('/admin/transactions', methods=['GET'])
@require_auth(['campus_admin', 'super_admin'])
def get_all_transactions(current_user):
    """获取所有交易记录（管理员）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        transaction_type = request.args.get('type')
        user_id = request.args.get('user_id', type=int)

        # 构建查询
        query = Transaction.query

        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)

        if user_id:
            query = query.filter(Transaction.user_id == user_id)

        # 校区管理员只能看到自己校区的交易
        if current_user.user_type == 'campus_admin':
            query = query.join(User).filter(User.campus_id == current_user.campus_id)

        query = query.order_by(Transaction.created_at.desc())

        # 分页查询
        result = paginate_query(query, page, per_page)

        # 添加用户信息
        for item in result['items']:
            transaction = Transaction.query.get(item['id'])
            if transaction and transaction.user:
                item['user'] = {
                    'id': transaction.user.id,
                    'username': transaction.user.username,
                    'real_name': transaction.user.real_name
                }

        return success_response(result)

    except Exception as e:
        return error_response(f'获取交易记录失败: {str(e)}')