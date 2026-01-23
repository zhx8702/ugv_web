#!/bin/bash
################################################################################
# OTA升级脚本 - Git Pull方式
# 用于UGV Rover Web Control系统的自动更新
#
# 使用方法:
#   sudo ./ota_git_pull.sh
#
# 作者: Claude Code
# 日期: 2026-01-21
################################################################################

set -e  # 遇到错误立即退出

# ============================================================================
# 配置变量
# ============================================================================

REPO_DIR="/home/ws/web-control"
BACKUP_DIR="/home/ws/web-control-backups"
VERSION_FILE="$REPO_DIR/.version"
SERVICE_NAME="ugv-web"
LOG_FILE="/var/log/ota-update.log"

# Git配置
GIT_REMOTE="origin"
GIT_BRANCH="main"

# 构建配置
# 如果前端由 GitHub Actions 构建，设为 false 跳过本地构建
BUILD_FRONTEND_LOCALLY=${BUILD_FRONTEND_LOCALLY:-false}

# 健康检查配置
HEALTH_CHECK_URL="http://localhost:5080/api/system/health"
HEALTH_CHECK_TIMEOUT=10

# ============================================================================
# 日志函数
# ============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1" | tee -a "$LOG_FILE"
}

# ============================================================================
# 检查函数
# ============================================================================

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Please run as root (use sudo)"
        exit 1
    fi
}

check_network() {
    log "Checking network connectivity..."
    if ! ping -c 1 -W 5 github.com &> /dev/null; then
        if ! ping -c 1 -W 5 gitee.com &> /dev/null; then
            log_error "Network unreachable"
            exit 1
        fi
    fi
    log_success "Network OK"
}

check_repo() {
    log "Checking repository..."
    if [ ! -d "$REPO_DIR/.git" ]; then
        log_error "Not a git repository: $REPO_DIR"
        exit 1
    fi
    log_success "Repository OK"
}

# ============================================================================
# 备份函数
# ============================================================================

backup_current() {
    local current_version=$(cat "$VERSION_FILE" 2>/dev/null || echo "unknown")
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local backup_name="backup-$current_version-$timestamp"
    local backup_path="$BACKUP_DIR/$backup_name"

    log "Backing up current version to: $backup_path"

    mkdir -p "$BACKUP_DIR"
    cp -r "$REPO_DIR" "$backup_path"

    log_success "Backup created: $backup_path"
    echo "$backup_path"
}

cleanup_old_backups() {
    log "Cleaning up old backups (keeping latest 5)..."
    cd "$BACKUP_DIR"
    ls -t | tail -n +6 | xargs rm -rf 2>/dev/null || true
    log_success "Cleanup complete"
}

# ============================================================================
# Git操作函数
# ============================================================================

check_updates() {
    log "Checking for updates..."
    cd "$REPO_DIR"

    git fetch "$GIT_REMOTE" 2>&1 | tee -a "$LOG_FILE"

    local LOCAL=$(git rev-parse @)
    local REMOTE=$(git rev-parse @{u})

    if [ "$LOCAL" = "$REMOTE" ]; then
        log_success "Already up to date"
        return 1
    else
        log "Updates available: $LOCAL -> $REMOTE"
        return 0
    fi
}

pull_updates() {
    log "Pulling updates from $GIT_REMOTE/$GIT_BRANCH..."
    cd "$REPO_DIR"

    git pull "$GIT_REMOTE" "$GIT_BRANCH" 2>&1 | tee -a "$LOG_FILE"

    local new_version=$(git describe --tags --always)
    echo "$new_version" > "$VERSION_FILE"

    log_success "Updates pulled successfully"
    echo "$new_version"
}

# ============================================================================
# 依赖安装函数
# ============================================================================

install_backend_deps() {
    log "Installing backend dependencies..."
    cd "$REPO_DIR/backend"

    if [ ! -f "pyproject.toml" ]; then
        log "No pyproject.toml found, skipping"
        return 0
    fi

    # 使用 uv 安装依赖
    uv sync 2>&1 | tee -a "$LOG_FILE"

    log_success "Backend dependencies installed"
}

build_frontend() {
    # 检查是否需要本地构建
    if [ "$BUILD_FRONTEND_LOCALLY" != "true" ]; then
        log "Frontend build skipped (pre-built by GitHub Actions)"
        return 0
    fi

    log "Building frontend locally..."
    cd "$REPO_DIR/frontend"

    if [ ! -f "package.json" ]; then
        log "No package.json found, skipping frontend build"
        return 0
    fi

    # 安装依赖
    npm install 2>&1 | tee -a "$LOG_FILE"

    # 构建
    npm run build 2>&1 | tee -a "$LOG_FILE"

    log_success "Frontend built successfully"
}

# ============================================================================
# 服务管理函数
# ============================================================================

stop_service() {
    log "Stopping service: $SERVICE_NAME..."
    systemctl stop "$SERVICE_NAME" 2>&1 | tee -a "$LOG_FILE" || true
    sleep 2
    log_success "Service stopped"
}

start_service() {
    log "Starting service: $SERVICE_NAME..."
    systemctl start "$SERVICE_NAME" 2>&1 | tee -a "$LOG_FILE"
    sleep 5
    log_success "Service started"
}

restart_service() {
    stop_service
    start_service
}

# ============================================================================
# 健康检查函数
# ============================================================================

health_check() {
    log "Performing health check..."

    # 检查systemd状态
    if ! systemctl is-active --quiet "$SERVICE_NAME"; then
        log_error "Service is not running"
        return 1
    fi

    # HTTP健康检查
    local response=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$HEALTH_CHECK_TIMEOUT" "$HEALTH_CHECK_URL" 2>/dev/null || echo "000")

    if [ "$response" = "200" ]; then
        log_success "Health check passed (HTTP $response)"
        return 0
    else
        log_error "Health check failed (HTTP $response)"
        return 1
    fi
}

# ============================================================================
# 回滚函数
# ============================================================================

rollback() {
    local backup_path=$1

    log_error "Rolling back to: $backup_path"

    # 停止服务
    systemctl stop "$SERVICE_NAME" 2>&1 | tee -a "$LOG_FILE" || true

    # 删除当前版本
    cd /
    rm -rf "${REPO_DIR:?}"/* 2>&1 | tee -a "$LOG_FILE"

    # 恢复备份
    cp -r "$backup_path"/* "$REPO_DIR/" 2>&1 | tee -a "$LOG_FILE"

    # 重启服务
    systemctl start "$SERVICE_NAME" 2>&1 | tee -a "$LOG_FILE"

    log_success "Rollback completed"
}

# ============================================================================
# 主函数
# ============================================================================

main() {
    log "=========================================="
    log "OTA Update Started"
    log "=========================================="

    # 1. 前置检查
    check_root
    check_network
    check_repo

    # 2. 检查更新
    if ! check_updates; then
        log "No updates needed. Exiting."
        exit 0
    fi

    # 3. 备份当前版本
    BACKUP_PATH=$(backup_current)

    # 4. 停止服务
    stop_service

    # 5. 拉取更新
    NEW_VERSION=$(pull_updates)
    log "Updated to version: $NEW_VERSION"

    # 6. 安装依赖
    install_backend_deps || {
        log_error "Failed to install backend dependencies"
        rollback "$BACKUP_PATH"
        exit 1
    }

    # 7. 构建前端（如果需要）
    if [ -d "$REPO_DIR/frontend" ]; then
        build_frontend || {
            log_error "Failed to build frontend"
            rollback "$BACKUP_PATH"
            exit 1
        }
    fi

    # 8. 重启服务
    start_service || {
        log_error "Failed to start service"
        rollback "$BACKUP_PATH"
        exit 1
    }

    # 9. 健康检查
    if health_check; then
        log_success "Update completed successfully!"
        log "Version: $NEW_VERSION"

        # 清理旧备份
        cleanup_old_backups

        log "=========================================="
        log "OTA Update Completed"
        log "=========================================="
        exit 0
    else
        log_error "Health check failed after update"
        rollback "$BACKUP_PATH"
        exit 1
    fi
}

# ============================================================================
# 执行主函数
# ============================================================================

main "$@"
