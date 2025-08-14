#!/bin/bash

# 配置项
CONTAINER_NAME="ljwx-mysql"
DB_NAME="lj-06"
MYSQL_USER="root"
MYSQL_PASSWORD="123456"
TABLE_NAME="t_user_health_data_202506"
SOURCE_TABLE="t_user_health_data"

echo "👉 检查 MySQL 容器是否运行中..."
docker ps | grep $CONTAINER_NAME > /dev/null
if [ $? -ne 0 ]; then
  echo "❌ 容器 $CONTAINER_NAME 没有运行，请先启动 MySQL 容器。"
  exit 1
fi

echo "✅ MySQL 容器已运行，准备连接数据库 $DB_NAME"

# 检查表是否存在
CHECK_CMD="USE $DB_NAME; SHOW TABLES LIKE '$TABLE_NAME';"
CREATE_CMD="USE $DB_NAME; CREATE TABLE $TABLE_NAME LIKE $SOURCE_TABLE;"

echo "🔍 正在检查是否存在表：$TABLE_NAME ..."
TABLE_EXISTS=$(docker exec -i $CONTAINER_NAME mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -e "$CHECK_CMD" | grep "$TABLE_NAME")

if [ "$TABLE_EXISTS" != "" ]; then
  echo "✅ 表 $TABLE_NAME 已存在，无需创建。"
else
  echo "⚠️ 表 $TABLE_NAME 不存在，准备创建..."
  docker exec -i $CONTAINER_NAME mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -e "$CREATE_CMD"
  if [ $? -eq 0 ]; then
    echo "🎉 表 $TABLE_NAME 创建成功（结构已复制自 $SOURCE_TABLE）"
  else
    echo "❌ 表创建失败，请检查容器状态、数据库权限或表名是否正确。"
  fi
fi
