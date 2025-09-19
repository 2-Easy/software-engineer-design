-- 创建数据库
USE table_tennis_db;

-- 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    real_name VARCHAR(50) NOT NULL,
    gender ENUM('male', 'female') DEFAULT NULL,
    age INT DEFAULT NULL,
    phone VARCHAR(20) DEFAULT NULL,
    email VARCHAR(100) DEFAULT NULL,
    user_type ENUM('student', 'coach', 'campus_admin', 'super_admin') NOT NULL,
    campus_id INT DEFAULT NULL,
    status ENUM('active', 'inactive', 'pending') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_user_type (user_type),
    INDEX idx_campus_id (campus_id)
);

-- 校区表
CREATE TABLE campus (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) DEFAULT NULL,
    contact_person VARCHAR(50) DEFAULT NULL,
    contact_phone VARCHAR(20) DEFAULT NULL,
    contact_email VARCHAR(100) DEFAULT NULL,
    campus_type ENUM('center', 'branch') DEFAULT 'branch',
    manager_id INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_manager_id (manager_id)
);

-- 教练信息表
CREATE TABLE coach_profiles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    coach_level ENUM('senior', 'intermediate', 'junior') NOT NULL,
    hourly_rate DECIMAL(10,2) NOT NULL,
    photo_url VARCHAR(255) DEFAULT NULL,
    achievements TEXT DEFAULT NULL,
    max_students INT DEFAULT 20,
    current_students INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_coach_level (coach_level)
);

-- 师生关系表
CREATE TABLE coach_student_relations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    coach_id INT NOT NULL,
    apply_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approve_time TIMESTAMP NULL DEFAULT NULL,
    status ENUM('pending', 'approved', 'rejected', 'terminated') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (coach_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_relation (student_id, coach_id),
    INDEX idx_student_id (student_id),
    INDEX idx_coach_id (coach_id),
    INDEX idx_status (status)
);

-- 球台表
CREATE TABLE tables (
    id INT PRIMARY KEY AUTO_INCREMENT,
    table_number VARCHAR(10) NOT NULL,
    campus_id INT NOT NULL,
    status ENUM('available', 'maintenance', 'occupied') DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campus_id) REFERENCES campus(id) ON DELETE CASCADE,
    INDEX idx_campus_id (campus_id),
    INDEX idx_status (status)
);

-- 预约表
CREATE TABLE bookings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    coach_id INT NOT NULL,
    campus_id INT NOT NULL,
    table_id INT DEFAULT NULL,
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    lesson_fee DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'confirmed', 'cancelled', 'completed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirm_time TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (coach_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (campus_id) REFERENCES campus(id) ON DELETE CASCADE,
    FOREIGN KEY (table_id) REFERENCES tables(id) ON DELETE SET NULL,
    INDEX idx_student_id (student_id),
    INDEX idx_coach_id (coach_id),
    INDEX idx_booking_date (booking_date),
    INDEX idx_status (status)
);

-- 账户表
CREATE TABLE accounts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    balance DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);

-- 交易记录表
CREATE TABLE transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    transaction_type ENUM('deposit', 'withdraw', 'refund') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method ENUM('wechat', 'alipay', 'offline', 'system') DEFAULT 'system',
    status ENUM('pending', 'completed', 'failed') DEFAULT 'completed',
    description VARCHAR(255) DEFAULT NULL,
    related_booking_id INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (related_booking_id) REFERENCES bookings(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_created_at (created_at)
);

-- 比赛表
CREATE TABLE matches (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    match_date DATE NOT NULL,
    registration_start TIMESTAMP NOT NULL,
    registration_end TIMESTAMP NOT NULL,
    registration_fee DECIMAL(10,2) DEFAULT 30.00,
    status ENUM('upcoming', 'registration', 'ongoing', 'completed') DEFAULT 'upcoming',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_match_date (match_date),
    INDEX idx_status (status)
);

-- 比赛报名表
CREATE TABLE match_registrations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    match_id INT NOT NULL,
    student_id INT NOT NULL,
    group_name ENUM('group_a', 'group_b', 'group_c') NOT NULL,
    registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_status ENUM('pending', 'paid') DEFAULT 'pending',
    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_registration (match_id, student_id),
    INDEX idx_match_id (match_id),
    INDEX idx_student_id (student_id)
);

-- 评价表
CREATE TABLE evaluations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    booking_id INT NOT NULL,
    evaluator_id INT NOT NULL,
    evaluated_id INT NOT NULL,
    evaluation_type ENUM('student_to_coach', 'coach_to_student') NOT NULL,
    content TEXT NOT NULL,
    rating INT DEFAULT NULL CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (evaluator_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (evaluated_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_booking_id (booking_id),
    INDEX idx_evaluator_id (evaluator_id),
    INDEX idx_evaluated_id (evaluated_id)
);

-- 取消预约限制表
CREATE TABLE cancellation_limits (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    cancellation_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_month (user_id, year_month),
    INDEX idx_user_id (user_id),
    INDEX idx_year_month (year_month)
);

-- 系统日志表
CREATE TABLE system_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT DEFAULT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT DEFAULT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
);

-- 添加外键约束
ALTER TABLE users ADD FOREIGN KEY (campus_id) REFERENCES campus(id) ON DELETE SET NULL;
ALTER TABLE campus ADD FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE SET NULL;