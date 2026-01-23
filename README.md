# UGV Rover Web Control System

基于 Waveshare UGV Rover 的现代化 Web 控制系统。

## 特性

- **现代技术栈**: Vue 3 + Flask + WebSocket
- **响应式设计**: 支持桌面、平板、手机
- **低延迟视频**: MJPEG + WebRTC 双模式
- **AI 视觉**: 人脸检测、物体识别、手势控制
- **OTA 升级**: 支持远程自动更新

## 项目结构

```
web-control/
├── frontend/                # Vue 3 前端
│   ├── src/
│   └── package.json
├── backend/                 # Flask 后端
│   ├── app/                 # 应用代码
│   ├── deploy/              # 部署文件
│   ├── scripts/             # OTA 脚本
│   └── static/              # 前端构建产物
└── .github/workflows/       # CI/CD
```

## 快速开始

### 开发环境

**前端开发：**
```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:3080
```

**后端开发：**
```bash
cd backend
uv sync
uv run python run.py
# 访问 http://localhost:5080
```

### 树莓派部署

**方式一：一键部署（推荐）**

```bash
# 1. 克隆仓库
git clone https://github.com/zhx8702/ugv_web.git /home/ws/web-control

# 2. 运行安装脚本
cd /home/ws/web-control/backend
chmod +x deploy/install.sh
sudo ./deploy/install.sh

# 3. 编辑配置
nano .env

# 4. 启动服务
sudo systemctl start ugv-web
```

**方式二：手动部署**

```bash
# 安装依赖
sudo apt-get update
sudo apt-get install -y python3 git curl

# 安装 uv（树莓派用 pipx）
sudo apt install -y pipx
pipx install uv
pipx ensurepath
source ~/.bashrc

# 克隆仓库
git clone https://github.com/zhx8702/ugv_web.git /home/ws/web-control

# 设置后端
cd /home/ws/web-control/backend
uv sync
cp .env.example .env

# 安装服务
sudo cp deploy/ugv-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ugv-web
sudo systemctl start ugv-web
```

访问 `http://树莓派IP:5080` 即可使用。

## 前端构建

前端由 **GitHub Actions 自动构建**，无需在树莓派上安装 Node.js。

每次 push 到 main 分支时，CI 会自动：
1. 构建前端
2. 提交到 `backend/static/` 目录

如需手动构建：
```bash
cd frontend
npm install
npm run build  # 输出到 ../backend/static/
```

## OTA 升级

系统支持通过 Git Pull 进行远程更新。

**手动更新：**
```bash
sudo /home/ws/web-control/backend/scripts/ota_git_pull.sh
```

**通过 Web API 更新：**
```bash
curl -X POST http://localhost:5080/api/ota/perform-update
```

**自动更新（可选）：**
```bash
# 安装 cron 任务，每天凌晨 2 点自动更新
sudo cp deploy/ota-check.cron /etc/cron.d/ugv-ota
```

详见 [OTA 文档](./backend/OTA_INTEGRATION.md)

## 配置

编辑 `backend/.env` 文件：

```bash
# 服务端口
PORT=5080

# 串口（留空自动检测）
UART_PORT=

# 模拟模式（开发环境）
MOCK_MODE=false
```

## 服务管理

```bash
# 查看状态
sudo systemctl status ugv-web

# 查看日志
sudo journalctl -u ugv-web -f

# 重启服务
sudo systemctl restart ugv-web
```

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3, Vite, Tailwind CSS, ECharts |
| 后端 | Flask, Flask-SocketIO, OpenCV |
| 部署 | systemd, GitHub Actions |

## 许可证

GPL-3.0
