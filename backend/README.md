# Web Control Backend

Flask 后端 API，支持 WebSocket 实时通信、WebRTC 视频流。

> 部署说明请查看 [项目 README](../README.md)

## 开发

### Windows

```powershell
# 安装 uv（如果还没安装）
irm https://astral.sh/uv/install.ps1 | iex
# 或: pip install uv

# 创建虚拟环境并安装依赖
uv venv
uv pip install -e .

# 启动开发服务器
.venv\Scripts\python run.py
```

> Windows 下自动启用模拟模式，无需连接真实硬件。

### Linux / macOS

```bash
# 安装依赖
uv sync

# 启动开发服务器
uv run python run.py
```

服务器运行在 http://localhost:5080

## 可选依赖

| 依赖组 | 用途 | 平台 |
|--------|------|------|
| `mediapipe` | 手势/人脸/姿态检测 | x86/macOS |
| `rpi` | 树莓派 CSI 摄像头 | 树莓派 |
| `oak` | OAK 深度摄像头 | 全平台 |
| `dev` | 测试工具 | 全平台 |

```bash
uv sync --extra rpi           # 树莓派
uv sync --extra mediapipe     # x86 开发机
```

## 项目结构

```
backend/
├── app/
│   ├── __init__.py          # Flask 应用工厂
│   ├── api/                  # API 路由
│   ├── services/             # 业务逻辑
│   └── websocket/            # WebSocket 处理
├── deploy/                   # 部署文件
├── scripts/                  # OTA 脚本
├── config.py                 # 配置管理
├── pyproject.toml            # 依赖配置
└── run.py                    # 入口文件
```

## API 端点

### 系统 `/api/system`

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/status` | 系统状态 |
| GET | `/health` | 健康检查 |
| GET | `/info` | 系统信息 |

### 控制 `/api/control`

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/command` | 发送命令 |
| POST | `/move` | 移动控制 |
| POST | `/stop` | 停止 |

### 视频 `/api/video`

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/stream` | MJPEG 流 |
| POST | `/webrtc/offer` | WebRTC 信令 |
| POST | `/capture` | 拍照 |

### OTA `/api/ota`

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/version` | 当前版本 |
| GET | `/check-update` | 检查更新 |
| POST | `/perform-update` | 执行更新 |

详见 [OTA_INTEGRATION.md](./OTA_INTEGRATION.md)

## 常用命令

```bash
uv add package-name      # 添加依赖
uv add --dev pytest      # 添加开发依赖
uv lock --upgrade        # 更新依赖
uv tree                  # 查看依赖树
uv run pytest            # 运行测试
```
