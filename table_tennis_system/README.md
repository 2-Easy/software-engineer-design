# 乒乓球培训管理系统
# Table Tennis Training Management System

一个基于 Flask + MySQL 的乒乓球培训管理系统，支持学员选课、教练管理、比赛组织等功能。

## 系统功能

### 用户角色
- **学员 (Student)**: 选择教练、预约课程、参加比赛、管理账户
- **教练 (Coach)**: 管理学员、确认预约、查看收入统计
- **校区管理员 (Campus Admin)**: 管理本校区用户、预约、比赛
- **超级管理员 (Super Admin)**: 全系统管理权限

### 主要功能
- 用户注册登录、角色管理
- 师生关系管理（学员选择教练）
- 课程预约系统（时间、球台管理）
- 比赛管理系统（报名、赛程、奖金）
- 账户系统（充值、扣费、交易记录）
- 校区管理（多校区支持）
- 统计报表（收入、预约数据等）

## 技术栈

### 后端
- **Python 3.8+**
- **Flask** - Web框架
- **Flask-SQLAlchemy** - ORM
- **Flask-JWT-Extended** - JWT认证
- **MySQL 8.0** - 数据库
- **bcrypt** - 密码加密

### 前端
- **HTML5 + CSS3**
- **Bootstrap 5** - UI框架
- **JavaScript (ES6+)**
- **Axios** - HTTP客户端

## 环境要求

- Python 3.8 或更高版本
- MySQL 8.0 或更高版本
- Node.js (可选，用于前端包管理)

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/table_tennis_system.git
cd table_tennis_system
```

### 2. 安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 数据库配置

#### 3.1 安装 MySQL
- macOS: `brew install mysql`
- Ubuntu: `sudo apt-get install mysql-server`
- Windows: 下载 MySQL 安装包

#### 3.2 启动 MySQL 服务
```bash
# macOS
brew services start mysql

# Ubuntu
sudo service mysql start

# 或者直接启动
mysqld --console
```

#### 3.3 创建数据库
```bash
mysql -u root -p
```

在 MySQL 命令行中执行：
```sql
CREATE DATABASE table_tennis_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;
```

#### 3.4 配置数据库连接
编辑 `backend/config.py` 文件，修改数据库连接信息：

```python
# 数据库配置
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:your_password@localhost:3306/table_tennis_db'
```

### 4. 初始化数据库

```bash
cd backend
python init_db.py
```

这将创建所有必要的数据表并插入初始数据。

### 5. 启动后端服务

```bash
cd backend
python app.py
```

后端服务将在 `http://localhost:5001` 启动。

### 6. 启动前端服务

打开新的终端窗口：

```bash
cd frontend
# 使用 Python 内置服务器
python -m http.server 8000

# 或者使用 Node.js serve (需要先安装: npm install -g serve)
# serve . -p 8000
```

前端服务将在 `http://localhost:8000` 启动。

### 7. 访问系统

在浏览器中访问 `http://localhost:8000`

## 默认账户

系统初始化后会创建以下测试账户：

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| admin | admin123 | 超级管理员 | 系统管理员 |
| coach1 | coach123 | 教练 | 测试教练1 |
| coach2 | coach123 | 教练 | 测试教练2 |
| student1 | student123 | 学员 | 测试学员1 |
| student2 | student123 | 学员 | 测试学员2 |

## 项目结构

```
table_tennis_system/
├── backend/                 # 后端代码
│   ├── app.py              # Flask 应用主文件
│   ├── config.py           # 配置文件
│   ├── init_db.py          # 数据库初始化脚本
│   ├── requirements.txt    # Python 依赖
│   ├── models/             # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py         # 用户模型
│   │   ├── booking.py      # 预约模型
│   │   ├── match.py        # 比赛模型
│   │   └── account.py      # 账户模型
│   ├── routes/             # 路由处理
│   │   ├── __init__.py
│   │   ├── auth.py         # 认证路由
│   │   ├── user.py         # 用户管理
│   │   ├── booking.py      # 预约管理
│   │   ├── match.py        # 比赛管理
│   │   └── account.py      # 账户管理
│   └── utils/              # 工具函数
│       ├── __init__.py
│       └── auth.py         # 认证工具
├── frontend/               # 前端代码
│   ├── index.html          # 登录页面
│   ├── assets/             # 静态资源
│   │   ├── css/
│   │   └── js/
│   └── pages/              # 页面文件
│       ├── student/        # 学员页面
│       ├── coach/          # 教练页面
│       └── admin/          # 管理员页面
└── README.md               # 项目说明
```

## API 接口文档

### 认证接口
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/logout` - 用户登出

### 用户管理
- `GET /api/user/coaches` - 获取教练列表
- `GET /api/user/students` - 获取学员列表（管理员）
- `POST /api/user/choose-coach` - 学员选择教练

### 预约管理
- `GET /api/booking/tables` - 获取可用球台
- `POST /api/booking/create` - 创建预约
- `GET /api/booking/my-bookings` - 获取我的预约
- `POST /api/booking/{id}/confirm` - 确认预约

### 比赛管理
- `GET /api/match/list` - 获取比赛列表
- `POST /api/match/create` - 创建比赛（管理员）
- `POST /api/match/{id}/register` - 报名比赛

详细 API 文档请参考各路由文件中的注释。

## 配置说明

### 数据库配置 (config.py)
```python
# 数据库连接
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@host:port/database'

# JWT 配置
JWT_SECRET_KEY = 'your-secret-key'
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
```

### 前端配置 (frontend/assets/js/common.js)
```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:5001/api',  // 后端 API 地址
    TOKEN_KEY: 'authToken',
    USER_KEY: 'currentUser'
};
```

## 部署到生产环境

### 1. 使用 Gunicorn 部署后端
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

### 2. 使用 Nginx 部署前端
配置 Nginx 代理静态文件和 API 请求。

### 3. 环境变量配置
```bash
export FLASK_ENV=production
export DATABASE_URL=mysql+pymysql://user:pass@host:port/db
export JWT_SECRET_KEY=your-production-secret-key
```

## 常见问题

### Q: 数据库连接失败
A: 检查 MySQL 服务是否启动，数据库连接配置是否正确。

### Q: 前端无法访问后端 API
A: 检查后端服务是否启动，CORS 配置是否正确。

### Q: 登录后页面跳转异常
A: 检查用户角色配置，确保路由权限设置正确。

## 开发指南

### 添加新功能
1. 在 `models/` 中定义数据模型
2. 在 `routes/` 中添加 API 路由
3. 在 `frontend/` 中添加前端页面
4. 更新数据库迁移脚本

### 代码规范
- Python: 遵循 PEP 8 规范
- JavaScript: 使用 ES6+ 语法
- 数据库: 使用 Snake_case 命名

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题请联系项目维护者。