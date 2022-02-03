#!/usr/bin/env sh
docker build -t mysqltest .
docker-compose up -d
echo "数据库已启动..."

