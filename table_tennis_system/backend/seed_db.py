
import datetime
from app import create_app
from models import db, User, Campus, CoachProfile, Table, CoachStudentRelation, Account, Booking, Transaction, Match, MatchRegistration, Evaluation, SystemLog
from utils.auth import hash_password

def seed_database():
    """
    Seeds the database with initial data.
    This script will drop all existing tables and recreate them.
    """
    app = create_app()
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()

        print("Seeding database...")

        try:
            # --- Create Campuses ---
            campus1 = Campus(name='中心校区', address='北京市朝阳区体育路100号', contact_person='张主任', contact_phone='13800138000', contact_email='center@ttms.com', campus_type='center')
            campus2 = Campus(name='东城分校', address='北京市东城区建国门大街50号', contact_person='李经理', contact_phone='13800138001', contact_email='dongcheng@ttms.com', campus_type='branch')
            campus3 = Campus(name='西城分校', address='北京市西城区西单大街25号', contact_person='王经理', contact_phone='13800138002', contact_email='xicheng@ttms.com', campus_type='branch')
            db.session.add_all([campus1, campus2, campus3])
            db.session.commit()

            # --- Create Users ---
            # All users will have the same password: '123456'
            password = '123456'
            hashed_pwd = hash_password(password)

            # Super Admin
            admin = User(username='admin', password=hashed_pwd, real_name='系统管理员', gender='male', age=35, phone='13800138888', email='admin@ttms.com', user_type='super_admin', campus_id=campus1.id, status='active')
            
            # Campus Admins
            campus_admin1 = User(username='campus_admin1', password=hashed_pwd, real_name='张主任', gender='male', age=40, phone='13800138000', email='center@ttms.com', user_type='campus_admin', campus_id=campus1.id, status='active')
            campus_admin2 = User(username='campus_admin2', password=hashed_pwd, real_name='李经理', gender='female', age=38, phone='13800138001', email='dongcheng@ttms.com', user_type='campus_admin', campus_id=campus2.id, status='active')

            # Coaches
            coach1 = User(username='coach1', password=hashed_pwd, real_name='刘教练', gender='male', age=28, phone='13800139001', email='coach1@ttms.com', user_type='coach', campus_id=campus1.id, status='active')
            coach2 = User(username='coach2', password=hashed_pwd, real_name='陈教练', gender='female', age=26, phone='13800139002', email='coach2@ttms.com', user_type='coach', campus_id=campus1.id, status='active')
            coach3 = User(username='coach3', password=hashed_pwd, real_name='王教练', gender='male', age=32, phone='13800139003', email='coach3@ttms.com', user_type='coach', campus_id=campus2.id, status='active')

            # Students
            student1 = User(username='student1', password=hashed_pwd, real_name='小明', gender='male', age=16, phone='13800140001', email='student1@ttms.com', user_type='student', campus_id=campus1.id, status='active')
            student2 = User(username='student2', password=hashed_pwd, real_name='小红', gender='female', age=15, phone='13800140002', email='student2@ttms.com', user_type='student', campus_id=campus1.id, status='active')
            student3 = User(username='student3', password=hashed_pwd, real_name='小张', gender='male', age=17, phone='13800140003', email='student3@ttms.com', user_type='student', campus_id=campus2.id, status='active')
            student4 = User(username='student4', password=hashed_pwd, real_name='小李', gender='female', age=16, phone='13800140004', email='student4@ttms.com', user_type='student', campus_id=campus2.id, status='active')
            
            db.session.add_all([admin, campus_admin1, campus_admin2, coach1, coach2, coach3, student1, student2, student3, student4])
            db.session.commit()

            # --- Set Campus Managers ---
            campus1.manager_id = campus_admin1.id
            campus2.manager_id = campus_admin2.id
            campus3.manager_id = campus_admin1.id # As per sample_data
            db.session.commit()

            # --- Create Coach Profiles ---
            cp1 = CoachProfile(user_id=coach1.id, coach_level='senior', hourly_rate=200.00, achievements='2020年全国乒乓球锦标赛季军，2019年世界乒乓球锦标赛参赛选手', max_students=20, current_students=2)
            cp2 = CoachProfile(user_id=coach2.id, coach_level='intermediate', hourly_rate=150.00, achievements='2021年省级乒乓球比赛冠军，专业教练员证书', max_students=20, current_students=2)
            cp3 = CoachProfile(user_id=coach3.id, coach_level='junior', hourly_rate=80.00, achievements='乒乓球国家二级运动员，3年教学经验', max_students=20, current_students=1)
            db.session.add_all([cp1, cp2, cp3])

            # --- Create Student Accounts ---
            acc1 = Account(user_id=student1.id, balance=500.00)
            acc2 = Account(user_id=student2.id, balance=800.00)
            acc3 = Account(user_id=student3.id, balance=300.00)
            acc4 = Account(user_id=student4.id, balance=600.00)
            db.session.add_all([acc1, acc2, acc3, acc4])
            
            # --- Create Tables ---
            tables_campus1 = [Table(table_number=f'{i}号台', campus_id=campus1.id) for i in range(1, 5)]
            tables_campus2 = [Table(table_number=f'{i}号台', campus_id=campus2.id) for i in range(1, 4)]
            tables_campus3 = [Table(table_number=f'{i}号台', campus_id=campus3.id) for i in range(1, 3)]
            db.session.add_all(tables_campus1 + tables_campus2 + tables_campus3)

            db.session.commit()

            print("Database seeded successfully!")

        except Exception as e:
            print(f"An error occurred during seeding: {e}")
            db.session.rollback()

if __name__ == '__main__':
    seed_database()
