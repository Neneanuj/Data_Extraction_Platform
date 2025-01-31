#!/bin/bash -x  # -x 启用调试模式，会输出详细执行日志
echo "=== 脚本开始执行 ==="

set -euxo pipefail  # 添加 -x 用于调试


sudo -i

# 1. 更新系统并安装依赖
sudo apt-get update 
sudo apt-get install -y python3 python3-venv python3-pip curl unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install



# 2. 从 S3 下载应用
aws s3 cp s3://bigdata-project1-storage/webapp.zip /tmp/webapp.zip || {
    echo "ERROR: Failed to download webapp.zip from S3"
    exit 1
}

# 3. 创建应用目录并解压
mkdir -p /opt/myapp
chown $TARGET_USER:$TARGET_USER /opt/myapp
unzip -o /tmp/webapp.zip -d /opt/myapp || {
    echo "ERROR: Failed to unzip webapp.zip"
    exit 1
}

# 4. 安装 Python 依赖
python3 -m venv /opt/myapp/venv
/opt/myapp/venv/bin/pip install --upgrade pip
if [ -f "/opt/myapp/requirements.txt" ]; then
    /opt/myapp/venv/bin/pip install -r /opt/myapp/requirements.txt
else
    echo "WARN: requirements.txt not found"
fi

# 5. 验证应用目录存在
APP_DIR="/opt/myapp/webapp/backend/src/api"
if [ ! -d "$APP_DIR" ]; then
    echo "ERROR: App directory $APP_DIR not found"
    exit 1
fi

# 6. 创建 Systemd 服务
tee /etc/systemd/system/myapp.service > /dev/null <<EOF
[Unit]
Description=My FastAPI App
After=network.target

[Service]
Type=simple
User=$TARGET_USER
WorkingDirectory=$APP_DIR
ExecStart=/opt/myapp/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 7. 启动服务
systemctl daemon-reload
systemctl enable myapp.service
systemctl start myapp.service

echo "Setup completed. Check service status: systemctl status myapp.service"
