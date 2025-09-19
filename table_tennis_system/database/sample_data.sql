-- 示例数据插入脚本
USE table_tennis_db;

-- 插入校区数据
INSERT INTO campus (name, address, contact_person, contact_phone, contact_email, campus_type) VALUES
('中心校区', '北京市朝阳区体育路100号', '张主任', '13800138000', 'center@ttms.com', 'center'),
('东城分校', '北京市东城区建国门大街50号', '李经理', '13800138001', 'dongcheng@ttms.com', 'branch'),
('西城分校', '北京市西城区西单大街25号', '王经理', '13800138002', 'xicheng@ttms.com', 'branch');

-- 插入用户数据
-- 密码都是 123456，经过bcrypt加密
INSERT INTO users (username, password, real_name, gender, age, phone, email, user_type, campus_id, status) VALUES
-- 超级管理员
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO.1dNhPa', '系统管理员', 'male', 35, '13800138888', 'admin@ttms.com', 'super_admin', 1, 'active'),

-- 校区管理员
('campus_admin1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO.1dNhPa', '张主任', 'male', 40, '13800138000', 'center@ttms.com', 'campus_admin', 1, 'active'),
('campus_admin2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO.1dNhPa', '李经理', 'female', 38, '13800138001', 'dongcheng@ttms.com', 'campus_admin', 2, 'active'),

-- 教练
('coach1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO.1dNhPa', '刘教练', 'male', 28, '13800139001', 'coach1@ttms.com', 'coach', 1, 'active'),
('coach2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO.1dNhPa', '陈教练', 'female', 26, '13800139002', 'coach2@ttms.com', 'coach', 1, 'active'),
('coach3', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO.1dNhPa', '王教练', 'male', 32, '13800139003', 'coach3@ttms.com', 'coach', 2, 'active'),

-- 学员
('student1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO.1dNhPa', '小明', 'male', 16, '13800140001', 'student1@ttms.com', 'student', 1, 'active'),
('student2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO.1dNhPa', '小红', 'female', 15, '13800140002', 'student2@ttms.com', 'student', 1, 'active'),
('student3', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO.1dNhPa', '小张', 'male', 17, '13800140003', 'student3@ttms.com', 'student', 2, 'active'),
('student4', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO.1dNhPa', '小李', 'female', 16, '13800140004', 'student4@ttms.com', 'student', 2, 'active');

-- 设置校区管理员
UPDATE campus SET manager_id = 2 WHERE id = 1;
UPDATE campus SET manager_id = 3 WHERE id = 2;
UPDATE campus SET manager_id = 2 WHERE id = 3;

-- 插入教练信息
INSERT INTO coach_profiles (user_id, coach_level, hourly_rate, achievements, max_students, current_students) VALUES
(4, 'senior', 200.00, '2020年全国乒乓球锦标赛季军，2019年世界乒乓球锦标赛参赛选手', 20, 2),
(5, 'intermediate', 150.00, '2021年省级乒乓球比赛冠军，专业教练员证书', 20, 2),
(6, 'junior', 80.00, '乒乓球国家二级运动员，3年教学经验', 20, 1);

-- 插入球台数据
INSERT INTO tables (table_number, campus_id, status) VALUES
('1号台', 1, 'available'),
('2号台', 1, 'available'),
('3号台', 1, 'available'),
('4号台', 1, 'available'),
('1号台', 2, 'available'),
('2号台', 2, 'available'),
('3号台', 2, 'available'),
('1号台', 3, 'available'),
('2号台', 3, 'available');

-- 插入师生关系
INSERT INTO coach_student_relations (student_id, coach_id, approve_time, status) VALUES
(7, 4, NOW(), 'approved'),
(8, 4, NOW(), 'approved'),
(8, 5, NOW(), 'approved'),
(9, 5, NOW(), 'approved'),
(10, 6, NOW(), 'approved');

-- 更新教练当前学员数
UPDATE coach_profiles SET current_students = 2 WHERE user_id = 4;
UPDATE coach_profiles SET current_students = 2 WHERE user_id = 5;
UPDATE coach_profiles SET current_students = 1 WHERE user_id = 6;

-- 插入账户数据
INSERT INTO accounts (user_id, balance) VALUES
(7, 500.00),
(8, 800.00),
(9, 300.00),
(10, 600.00);

-- 插入一些预约记录
INSERT INTO bookings (student_id, coach_id, campus_id, table_id, booking_date, start_time, end_time, lesson_fee, status, confirm_time) VALUES
(7, 4, 1, 1, CURDATE() + INTERVAL 1 DAY, '09:00:00', '10:00:00', 200.00, 'confirmed', NOW()),
(8, 4, 1, 2, CURDATE() + INTERVAL 1 DAY, '10:00:00', '11:00:00', 200.00, 'confirmed', NOW()),
(8, 5, 1, 3, CURDATE() + INTERVAL 2 DAY, '14:00:00', '15:00:00', 150.00, 'pending', NULL),
(9, 5, 2, 5, CURDATE() + INTERVAL 3 DAY, '16:00:00', '17:00:00', 150.00, 'confirmed', NOW());

-- 插入交易记录
INSERT INTO transactions (user_id, transaction_type, amount, payment_method, description) VALUES
(7, 'deposit', 500.00, 'wechat', '账户充值'),
(8, 'deposit', 800.00, 'alipay', '账户充值'),
(9, 'deposit', 300.00, 'offline', '现金充值'),
(10, 'deposit', 600.00, 'wechat', '账户充值'),
(7, 'withdraw', 200.00, 'system', '课时费扣除'),
(8, 'withdraw', 200.00, 'system', '课时费扣除');

-- 插入比赛数据
INSERT INTO matches (name, match_date, registration_start, registration_end, registration_fee, status) VALUES
('2025年1月月赛', '2025-01-28', '2025-01-01 00:00:00', '2025-01-25 23:59:59', 30.00, 'registration'),
('2025年2月月赛', '2025-02-25', '2025-02-01 00:00:00', '2025-02-22 23:59:59', 30.00, 'upcoming');

-- 插入比赛报名记录
INSERT INTO match_registrations (match_id, student_id, group_name, payment_status) VALUES
(1, 7, 'group_a', 'paid'),
(1, 8, 'group_a', 'paid'),
(1, 9, 'group_b', 'paid');

-- 插入一些评价记录
INSERT INTO evaluations (booking_id, evaluator_id, evaluated_id, evaluation_type, content, rating) VALUES
(1, 7, 4, 'student_to_coach', '刘教练教学很认真，技术指导很到位，进步很大！', 5),
(1, 4, 7, 'coach_to_student', '小明学习态度很好，基本功扎实，继续加油！', 4);

-- 插入系统日志
INSERT INTO system_logs (user_id, action, description, ip_address) VALUES
(1, 'login', '管理员登录系统', '127.0.0.1'),
(7, 'register', '学员注册', '127.0.0.1'),
(4, 'create_booking', '创建课程预约', '127.0.0.1');