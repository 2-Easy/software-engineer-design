from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum

db = SQLAlchemy()

# 枚举类定义
class UserType(Enum):
    STUDENT = 'student'
    COACH = 'coach'
    CAMPUS_ADMIN = 'campus_admin'
    SUPER_ADMIN = 'super_admin'

class Gender(Enum):
    MALE = 'male'
    FEMALE = 'female'

class UserStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    PENDING = 'pending'

class CoachLevel(Enum):
    SENIOR = 'senior'
    INTERMEDIATE = 'intermediate'
    JUNIOR = 'junior'

class RelationStatus(Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    TERMINATED = 'terminated'

class BookingStatus(Enum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'

# 用户模型
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    user_type = db.Column(db.String(20), nullable=False)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    campus = db.relationship('Campus', foreign_keys=[campus_id], backref='users')
    coach_profile = db.relationship('CoachProfile', backref='user', uselist=False)
    account = db.relationship('Account', backref='user', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'gender': self.gender,
            'age': self.age,
            'phone': self.phone,
            'email': self.email,
            'user_type': self.user_type,
            'campus_id': self.campus_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# 校区模型
class Campus(db.Model):
    __tablename__ = 'campus'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    contact_person = db.Column(db.String(50))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(100))
    campus_type = db.Column(db.Enum('center', 'branch'), default='branch')
    # manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id', use_alter=True, name='fk_campus_manager_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    manager = db.relationship('User', foreign_keys=[manager_id])

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'campus_type': self.campus_type,
            'manager_id': self.manager_id
        }

# 教练信息模型
class CoachProfile(db.Model):
    __tablename__ = 'coach_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    coach_level = db.Column(db.String(20), nullable=False)
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=False)
    photo_url = db.Column(db.String(255))
    achievements = db.Column(db.Text)
    max_students = db.Column(db.Integer, default=20)
    current_students = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'coach_level': self.coach_level,
            'hourly_rate': float(self.hourly_rate),
            'photo_url': self.photo_url,
            'achievements': self.achievements,
            'max_students': self.max_students,
            'current_students': self.current_students,
            'user': self.user.to_dict() if self.user else None
        }

# 师生关系模型
class CoachStudentRelation(db.Model):
    __tablename__ = 'coach_student_relations'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    apply_time = db.Column(db.DateTime, default=datetime.utcnow)
    approve_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    student = db.relationship('User', foreign_keys=[student_id])
    coach = db.relationship('User', foreign_keys=[coach_id])

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'coach_id': self.coach_id,
            'apply_time': self.apply_time.isoformat() if self.apply_time else None,
            'approve_time': self.approve_time.isoformat() if self.approve_time else None,
            'status': self.status,
            'student': self.student.to_dict() if self.student else None,
            'coach': self.coach.to_dict() if self.coach else None
        }

# 球台模型
class Table(db.Model):
    __tablename__ = 'tables'

    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.String(10), nullable=False)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    status = db.Column(db.Enum('available', 'maintenance', 'occupied'), default='available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    campus = db.relationship('Campus', backref='tables')

    def to_dict(self):
        return {
            'id': self.id,
            'table_number': self.table_number,
            'campus_id': self.campus_id,
            'status': self.status,
            'campus': self.campus.to_dict() if self.campus else None
        }

# 预约模型
class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'))
    booking_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    lesson_fee = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirm_time = db.Column(db.DateTime)

    # 关系
    student = db.relationship('User', foreign_keys=[student_id])
    coach = db.relationship('User', foreign_keys=[coach_id])
    campus = db.relationship('Campus', backref='bookings')
    table = db.relationship('Table', backref='bookings')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'coach_id': self.coach_id,
            'campus_id': self.campus_id,
            'table_id': self.table_id,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'lesson_fee': float(self.lesson_fee),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'confirm_time': self.confirm_time.isoformat() if self.confirm_time else None,
            'student': self.student.to_dict() if self.student else None,
            'coach': self.coach.to_dict() if self.coach else None,
            'table': self.table.to_dict() if self.table else None
        }

# 账户模型
class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'balance': float(self.balance),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# 交易记录模型
class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_type = db.Column(db.Enum('deposit', 'withdraw', 'refund'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.Enum('wechat', 'alipay', 'offline', 'system'), default='system')
    status = db.Column(db.Enum('pending', 'completed', 'failed'), default='completed')
    description = db.Column(db.String(255))
    related_booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    user = db.relationship('User', backref='transactions')
    related_booking = db.relationship('Booking', backref='transactions')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'transaction_type': self.transaction_type,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'status': self.status,
            'description': self.description,
            'related_booking_id': self.related_booking_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# 比赛模型
class Match(db.Model):
    __tablename__ = 'matches'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    match_date = db.Column(db.Date, nullable=False)
    registration_start = db.Column(db.DateTime, nullable=False)
    registration_end = db.Column(db.DateTime, nullable=False)
    registration_fee = db.Column(db.Numeric(10, 2), default=30.00)
    status = db.Column(db.Enum('upcoming', 'registration', 'ongoing', 'completed'), default='upcoming')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'match_date': self.match_date.isoformat() if self.match_date else None,
            'registration_start': self.registration_start.isoformat() if self.registration_start else None,
            'registration_end': self.registration_end.isoformat() if self.registration_end else None,
            'registration_fee': float(self.registration_fee),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# 比赛报名模型
class MatchRegistration(db.Model):
    __tablename__ = 'match_registrations'

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_name = db.Column(db.Enum('group_a', 'group_b', 'group_c'), nullable=False)
    registration_time = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.Enum('pending', 'paid'), default='pending')

    # 关系
    match = db.relationship('Match', backref='registrations')
    student = db.relationship('User', backref='match_registrations')

    def to_dict(self):
        return {
            'id': self.id,
            'match_id': self.match_id,
            'student_id': self.student_id,
            'group_name': self.group_name,
            'registration_time': self.registration_time.isoformat() if self.registration_time else None,
            'payment_status': self.payment_status,
            'match': self.match.to_dict() if self.match else None,
            'student': self.student.to_dict() if self.student else None
        }

# 评价模型
class Evaluation(db.Model):
    __tablename__ = 'evaluations'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    evaluated_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    evaluation_type = db.Column(db.Enum('student_to_coach', 'coach_to_student'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    booking = db.relationship('Booking', backref='evaluations')
    evaluator = db.relationship('User', foreign_keys=[evaluator_id])
    evaluated = db.relationship('User', foreign_keys=[evaluated_id])

    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'evaluator_id': self.evaluator_id,
            'evaluated_id': self.evaluated_id,
            'evaluation_type': self.evaluation_type,
            'content': self.content,
            'rating': self.rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'evaluator': self.evaluator.to_dict() if self.evaluator else None,
            'evaluated': self.evaluated.to_dict() if self.evaluated else None
        }

# 系统日志模型
class SystemLog(db.Model):
    __tablename__ = 'system_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    user = db.relationship('User', backref='system_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'description': self.description,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user': self.user.to_dict() if self.user else None
        }