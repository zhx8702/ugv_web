# OTA升级系统集成文档

> 完成时间: 2026-01-21
> 状态: ✅ 已完成

## 📋 概述

基于Git Pull的OTA（Over-The-Air）升级系统已成功实现，支持内网环境下的安全自动更新。

## 🎯 实现内容

### 1. 新增文件

```
backend/
├── scripts/
│   └── ota_git_pull.sh      ✅ NEW - OTA升级脚本（400+行）
│
├── app/services/
│   └── ota_service.py       ✅ NEW - OTA服务（300+行）
│
├── app/api/
│   └── ota.py               ✅ NEW - OTA API端点（7个）
│
└── deploy/
    ├── ugv-web.service      ✅ NEW - Systemd服务文件
    ├── ota-check.cron       ✅ NEW - Cron定时任务
    └── install.sh           ✅ NEW - 一键部署脚本
```

### 2. 核心功能

#### OTA升级脚本 (ota_git_pull.sh)

**功能特性:**
- ✅ Git Pull自动更新
- ✅ 自动备份当前版本
- ✅ 依赖安装（backend + frontend）
- ✅ 服务管理（停止/启动）
- ✅ 健康检查
- ✅ 失败自动回滚
- ✅ 日志记录
- ✅ 清理旧备份（保留最近5个）

**执行流程:**
```
1. 检查网络连接
2. 检查Git更新
3. 备份当前版本
4. 停止服务
5. 拉取更新
6. 安装依赖
7. 构建前端
8. 启动服务
9. 健康检查
10. 成功 ✅ 或 回滚 ❌
```

#### OTA服务 (ota_service.py)

**主要方法:**
- `check_update()` - 检查是否有更新
- `perform_update()` - 执行OTA升级
- `get_update_log()` - 获取commit历史
- `get_backups()` - 获取备份列表
- `rollback()` - 回滚到指定备份
- `get_current_version()` - 获取当前版本

## 📡 API端点

### 1. 获取当前版本

```
GET /api/ota/version
```

**返回:**
```json
{
  "version": "v2.0.0-abc123"
}
```

### 2. 检查更新

```
GET /api/ota/check-update
```

**返回:**
```json
{
  "has_update": true,
  "current_version": "v2.0.0",
  "latest_version": "v2.0.1",
  "commits_behind": 5,
  "error": null
}
```

### 3. 获取更新日志

```
GET /api/ota/update-log?limit=10
```

**返回:**
```json
{
  "commits": [
    {
      "hash": "abc123",
      "author": "Author Name",
      "date": "2 days ago",
      "message": "Add new feature"
    }
  ]
}
```

### 4. 执行OTA更新

```
POST /api/ota/perform-update
```

**返回:**
```json
{
  "success": true,
  "message": "Update started"
}
```

**WebSocket进度通知:**
```javascript
socket.on('ota_progress', (data) => {
  // data = {
  //   step: 'pull',
  //   progress: 50,
  //   message: 'Pulling updates...'
  // }
});
```

### 5. 获取备份列表

```
GET /api/ota/backups
```

**返回:**
```json
{
  "backups": [
    {
      "name": "backup-v2.0.0-20260121-143045",
      "version": "v2.0.0",
      "date": "20260121",
      "time": "143045",
      "size": 150
    }
  ]
}
```

### 6. 回滚

```
POST /api/ota/rollback
```

**请求:**
```json
{
  "backup_name": "backup-v2.0.0-20260121-143045"
}
```

**返回:**
```json
{
  "success": true,
  "message": "Rolled back to backup-v2.0.0-20260121-143045"
}
```

### 7. 获取状态

```
GET /api/ota/status
```

**返回:**
```json
{
  "updating": false,
  "current_version": "v2.0.0",
  "repo_dir": "/home/pi/web-control",
  "service_name": "ugv-web"
}
```

## 🚀 部署步骤

### 方法 1: 一键部署脚本（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/web-control.git
cd web-control

# 2. 运行安装脚本
cd backend
chmod +x deploy/install.sh
sudo ./deploy/install.sh

# 3. 编辑配置
nano .env

# 4. 启动服务
sudo systemctl start ugv-web
sudo systemctl status ugv-web
```

### 方法 2: 手动部署

```bash
# 1. 安装系统依赖
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git curl ffmpeg v4l-utils

# 2. 创建目录
sudo mkdir -p /home/pi/web-control
sudo mkdir -p /home/pi/web-control-backups

# 3. 克隆仓库
git clone https://github.com/yourusername/web-control.git /home/pi/web-control

# 4. 安装 uv 并设置依赖
sudo apt install -y pipx
pipx install uv
pipx ensurepath
source ~/.bashrc
cd /home/pi/web-control/backend
uv sync

# 6. 配置
cp .env.example .env
nano .env

# 7. 安装systemd服务
sudo cp deploy/ugv-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ugv-web
sudo systemctl start ugv-web

# 8. 安装OTA脚本
chmod +x scripts/ota_git_pull.sh

# 9. （可选）安装自动更新
sudo cp deploy/ota-check.cron /etc/cron.d/ugv-ota
```

## ⚙️ 配置

### 环境变量

在 `.env` 文件中添加（如果需要自定义）：

```bash
# OTA配置（可选，使用默认值即可）
OTA_REPO_DIR=/home/pi/web-control
OTA_BACKUP_DIR=/home/pi/web-control-backups
OTA_SERVICE_NAME=ugv-web
OTA_GIT_REMOTE=origin
OTA_GIT_BRANCH=main
```

### Systemd服务

见 `deploy/ugv-web.service`

### Cron自动更新（可选）

```cron
# 每天凌晨2点自动检查并更新
0 2 * * * root /home/pi/web-control/backend/scripts/ota_git_pull.sh >> /var/log/ota-auto.log 2>&1
```

## 🔧 使用方法

### 手动OTA升级

```bash
# 方法1: 使用脚本
sudo /home/pi/web-control/backend/scripts/ota_git_pull.sh

# 方法2: 使用API
curl -X POST http://localhost:5080/api/ota/perform-update
```

### 前端集成示例

```vue
<!-- frontend/src/views/Settings.vue -->
<template>
  <div class="ota-panel">
    <h2>系统更新</h2>

    <!-- 当前版本 -->
    <div class="current-version">
      <p>当前版本: {{ currentVersion }}</p>
    </div>

    <!-- 检查更新 -->
    <button @click="checkUpdate" :disabled="checking">
      {{ checking ? '检查中...' : '检查更新' }}
    </button>

    <!-- 更新信息 -->
    <div v-if="updateInfo.has_update" class="update-available">
      <h3>🎉 发现新版本</h3>
      <p>最新版本: {{ updateInfo.latest_version }}</p>
      <p>落后 {{ updateInfo.commits_behind }} 个提交</p>

      <!-- 更新日志 -->
      <div class="changelog">
        <h4>更新内容:</h4>
        <ul>
          <li v-for="commit in commits" :key="commit.hash">
            <strong>{{ commit.hash }}</strong> - {{ commit.message }}
            <br>
            <small>{{ commit.author }} · {{ commit.date }}</small>
          </li>
        </ul>
      </div>

      <button @click="performUpdate" :disabled="updating">
        {{ updating ? '更新中...' : '立即更新' }}
      </button>
    </div>

    <div v-else-if="!checking">
      <p>✅ 已是最新版本</p>
    </div>

    <!-- 更新进度 -->
    <div v-if="updating" class="update-progress">
      <h3>{{ progress.message }}</h3>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progress.progress + '%' }"></div>
      </div>
      <p>{{ progress.step }} - {{ progress.progress }}%</p>
    </div>

    <!-- 备份列表 -->
    <div class="backups">
      <h3>备份版本</h3>
      <div v-for="backup in backups" :key="backup.name" class="backup-item">
        <span>{{ backup.version }} ({{ backup.date }})</span>
        <span>{{ backup.size }} MB</span>
        <button @click="rollbackTo(backup.name)">回滚</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'
import api from '@/services/api'

const currentVersion = ref('unknown')
const checking = ref(false)
const updating = ref(false)
const updateInfo = ref({})
const commits = ref([])
const backups = ref([])
const progress = ref({ step: '', progress: 0, message: '' })

const { socket } = useWebSocket()

onMounted(() => {
  loadVersion()
  loadBackups()

  // 监听WebSocket进度
  socket.on('ota_progress', (data) => {
    progress.value = data
  })
})

async function loadVersion() {
  const res = await api.get('/api/ota/version')
  currentVersion.value = res.data.version
}

async function checkUpdate() {
  checking.value = true
  try {
    const res = await api.get('/api/ota/check-update')
    updateInfo.value = res.data

    if (res.data.has_update) {
      // 获取更新日志
      const logRes = await api.get('/api/ota/update-log')
      commits.value = logRes.data.commits
    }
  } finally {
    checking.value = false
  }
}

async function performUpdate() {
  if (!confirm('确定要更新吗? 更新期间服务将暂时不可用。')) {
    return
  }

  updating.value = true
  try {
    await api.post('/api/ota/perform-update')
  } catch (error) {
    alert('启动更新失败: ' + error.message)
    updating.value = false
  }
}

async function loadBackups() {
  const res = await api.get('/api/ota/backups')
  backups.value = res.data.backups
}

async function rollbackTo(backupName) {
  if (!confirm(`确定要回滚到 ${backupName}?`)) {
    return
  }

  try {
    await api.post('/api/ota/rollback', { backup_name: backupName })
    alert('回滚成功! 系统将重启...')
    setTimeout(() => location.reload(), 3000)
  } catch (error) {
    alert('回滚失败: ' + error.message)
  }
}
</script>
```

## 🔍 故障排查

### 问题1: 权限错误

**错误:**
```
Permission denied: cannot write to /home/pi/web-control
```

**解决:**
```bash
sudo chown -R pi:pi /home/pi/web-control
sudo chown -R pi:pi /home/pi/web-control-backups
```

### 问题2: Git无法pull

**错误:**
```
fatal: could not read Username for 'https://github.com'
```

**解决:**
```bash
# 使用SSH方式
cd /home/pi/web-control
git remote set-url origin git@github.com:username/web-control.git

# 或配置credential helper
git config --global credential.helper store
```

### 问题3: 服务启动失败

**检查:**
```bash
sudo systemctl status ugv-web
sudo journalctl -u ugv-web -n 50
```

**解决:**
```bash
# 检查虚拟环境
cd /home/pi/web-control/backend
source .venv/bin/activate
python run.py  # 手动测试

# 检查依赖
uv sync
```

### 问题4: 健康检查失败

**检查:**
```bash
curl http://localhost:5080/api/system/health
```

**解决:**
```bash
# 检查端口占用
sudo netstat -tulpn | grep 5080

# 检查防火墙
sudo ufw status
```

## 🧪 测试

### 测试OTA脚本（本地）

```bash
# 设置测试环境变量
export REPO_DIR="$(pwd)"
export BACKUP_DIR="/tmp/test-backups"

# 运行脚本
sudo bash backend/scripts/ota_git_pull.sh
```

### 测试API

```bash
# 检查更新
curl http://localhost:5080/api/ota/check-update

# 获取版本
curl http://localhost:5080/api/ota/version

# 获取备份
curl http://localhost:5080/api/ota/backups
```

## 📝 安全考虑

### 1. 备份策略
- ✅ 每次更新前自动备份
- ✅ 保留最近5个备份
- ✅ 更新失败自动回滚

### 2. 权限管理
- ✅ 脚本需要root权限
- ✅ 服务以pi用户运行
- ✅ 日志文件权限控制

### 3. 网络安全
- ✅ ZeroTier内网连接
- ✅ Git SSH认证
- ✅ 无需公网暴露

## 🎯 与原需求对比

| 功能 | 需求 | 实现 | 状态 |
|------|------|------|------|
| **内网OTA** | ZeroTier | ✅ Git Pull | 完成 |
| **自动备份** | 必须 | ✅ | 完成 |
| **失败回滚** | 必须 | ✅ | 完成 |
| **健康检查** | 必须 | ✅ | 完成 |
| **前端UI** | 建议 | ✅ 示例 | 完成 |
| **定时更新** | 可选 | ✅ Cron | 完成 |
| **WebSocket进度** | 建议 | ✅ | 完成 |

## 🎉 总结

### ✅ 已完成

- [x] OTA升级脚本（400+行）
- [x] OTA服务（300+行）
- [x] OTA API（7个端点）
- [x] Systemd服务文件
- [x] 一键部署脚本
- [x] Cron定时任务
- [x] 前端UI示例
- [x] 完整文档

### 🚀 就绪状态

- ✅ **可以部署到树莓派**
- ✅ **支持Git Pull更新**
- ✅ **自动备份和回滚**
- ✅ **Web界面控制**
- ✅ **ZeroTier内网兼容**

---

**集成完成**: 2026-01-21
**代码行数**: 700+ 行
**API端点**: 7个
**测试状态**: ✅ 脚本可用
**部署就绪**: ✅ 生产可用
