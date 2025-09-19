#!/bin/bash

# 数据库初始化脚本
# 使用方法: ./init.sh [mysql_password]

echo "🚀 初始化乒乓球培训管理系统数据库..."

# 获取MySQL密码
MYSQL_PASSWORD=${1:-""}
if [ -z "$MYSQL_PASSWORD" ]; then
    echo "请输入MySQL root密码:"
    read -s MYSQL_PASSWORD
fi

# 检查MySQL是否运行
if ! command -v mysql &> /dev/null; then
    echo "❌ MySQL未安装或未在PATH中找到"
    echo "请先安装MySQL: brew install mysql"
    exit 1
fi

# 测试MySQL连接
mysql -u root -p$MYSQL_PASSWORD -e "SELECT 1;" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ MySQL连接失败，请检查密码"
    exit 1
fi

echo "✅ MySQL连接成功"

# 创建数据库和表结构
echo "📊 创建数据库结构..."
mysql -u root -p$MYSQL_PASSWORD < schema.sql
if [ $? -eq 0 ]; then
    echo "✅ 数据库结构创建成功"
else
    echo "❌ 数据库结构创建失败"
    exit 1
fi

# 插入示例数据
echo "📝 插入示例数据..."
mysql -u root -p$MYSQL_PASSWORD < sample_data.sql
if [ $? -eq 0 ]; then
    echo "✅ 示例数据插入成功"
else
    echo "❌ 示例数据插入失败"
    exit 1
fi

echo "🎉 数据库初始化完成！"
echo ""
echo "📋 测试账号信息："
echo "管理员: admin / 123456"
echo "教练: coach1 / 123456"
echo "学员: student1 / 123456"
echo ""
echo "🔗 数据库连接信息："
echo "Host: localhost"
echo "Port: 3306"
echo "Database: table_tennis_db"
echo "Username: root"