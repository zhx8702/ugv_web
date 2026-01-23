#!/bin/bash
################################################################################
# UGV Rover Web Control 部署脚本
#
# 使用方法:
#   sudo ./install.sh
#
# 作者: Claude Code
# 更新: 2026-01-23
################################################################################

set -e

echo "=========================================="
echo "UGV Rover Web Control - Installation"
echo "=========================================="

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (use sudo)"
    exit 1
fi

# 变量
INSTALL_DIR="/home/pi/web-control"
BACKEND_DIR="$INSTALL_DIR/backend"
SERVICE_NAME="ugv-web"
CURRENT_USER=${SUDO_USER:-pi}

echo "Installing to: $INSTALL_DIR"
echo "Service name: $SERVICE_NAME"
echo "User: $CURRENT_USER"
echo ""

# 1. 安装系统依赖
echo "📦 Installing system dependencies..."
apt-get update
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    ffmpeg \
    v4l-utils

# 2. 创建目录
echo "📁 Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR-backups"
mkdir -p /var/log/ota

# 3. 安装 uv（如果没有）
echo "🐍 Setting up Python environment..."
if ! command -v uv &> /dev/null; then
    echo "Installing uv via pipx..."
    apt-get install -y pipx
    sudo -u $CURRENT_USER pipx install uv
    sudo -u $CURRENT_USER pipx ensurepath
    export PATH="/home/$CURRENT_USER/.local/bin:$PATH"
fi

# 4. 安装 Python 依赖
cd "$BACKEND_DIR"
echo "Installing Python dependencies with uv..."
uv sync

# 4. 创建配置文件
echo "⚙️  Creating configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env file. Please edit it with your settings."
fi

# 5. 设置权限
echo "🔐 Setting permissions..."
chown -R $CURRENT_USER:$CURRENT_USER "$INSTALL_DIR"
chown -R $CURRENT_USER:$CURRENT_USER "$INSTALL_DIR-backups"

# 将用户添加到必要的组
usermod -a -G video $CURRENT_USER
usermod -a -G dialout $CURRENT_USER

# 6. 安装systemd服务
echo "🔧 Installing systemd service..."
cp "$BACKEND_DIR/deploy/ugv-web.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME

# 7. 安装OTA脚本
echo "🔄 Installing OTA scripts..."
chmod +x "$BACKEND_DIR/scripts/ota_git_pull.sh"

# 8. 安装Cron任务（可选）
read -p "Install automatic OTA updates (runs daily at 2 AM)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cp "$BACKEND_DIR/deploy/ota-check.cron" /etc/cron.d/ugv-ota
    echo "✅ Automatic OTA updates installed"
fi

# 9. 创建版本文件
echo "📝 Creating version file..."
cd "$INSTALL_DIR"
git describe --tags --always > .version 2>/dev/null || echo "dev" > .version

echo ""
echo "=========================================="
echo "✅ Installation completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit configuration: nano $BACKEND_DIR/.env"
echo "  2. Start service: sudo systemctl start $SERVICE_NAME"
echo "  3. Check status: sudo systemctl status $SERVICE_NAME"
echo "  4. View logs: sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Access web interface at: http://$(hostname -I | awk '{print $1}'):5080"
echo ""
