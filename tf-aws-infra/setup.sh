#!/bin/bash -x  # Enable debug mode (-x) to print executed commands
echo "=== Script Execution Started ==="

set -euxo pipefail  # Enable strict error handling

# Switch to root user
sudo -i

# ------------------------------
# 1. Update System and Install Dependencies
# ------------------------------

sudo apt-get update 
sudo apt-get install -y python3 python3-venv python3-pip curl unzip

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify AWS CLI installation
aws --version

# ------------------------------
# 2. Download Web Application from S3
# ------------------------------

aws s3 cp s3://bigdata-project1-storage/webapp.zip /tmp/webapp.zip || {
    echo "ERROR: Failed to download webapp.zip from S3"
    exit 1
}

# ------------------------------
# 3. Create Application Directory and Extract Files
# ------------------------------

mkdir -p /opt/myapp
chown $TARGET_USER:$TARGET_USER /opt/myapp

# Unzip web application files
unzip -o /tmp/webapp.zip -d /opt/myapp || {
    echo "ERROR: Failed to unzip webapp.zip"
    exit 1
}

# ------------------------------
# 4. Set Up Python Virtual Environment and Install Dependencies
# ------------------------------

python3 -m venv /opt/myapp/venv
/opt/myapp/venv/bin/pip install --upgrade pip

# Install dependencies from requirements.txt
if [ -f "/opt/myapp/requirements.txt" ]; then
    /opt/myapp/venv/bin/pip install -r /opt/myapp/requirements.txt
else
    echo "WARNING: requirements.txt not found"
fi

# ------------------------------
# 5. Verify Application Directory
# ------------------------------

APP_DIR="/opt/myapp/webapp/backend/src/api"
if [ ! -d "$APP_DIR" ]; then
    echo "ERROR: Application directory $APP_DIR not found"
    exit 1
fi

# ------------------------------
# 6. Create Systemd Service File
# ------------------------------

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

# ------------------------------
# 7. Start the Application Service
# ------------------------------

systemctl daemon-reload
systemctl enable myapp.service
systemctl start myapp.service

echo "Setup completed. Check service status: systemctl status myapp.service"
