#!/usr/bin/env sh
docker build -t mysqltest .
docker-compose up -d
echo "数据库已启动..."
pip install -r ./requirements.txt
python3 ./main.py
