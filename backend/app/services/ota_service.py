"""
OTA Upgrade Service
OTA升级服务 - 支持Git Pull方式的自动更新
"""
import subprocess
import logging
import json
import threading
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class OTAService:
    """
    OTA升级服务
    通过Git Pull方式实现系统更新
    """

    def __init__(self, config=None):
        """
        初始化OTA服务

        Args:
            config: 配置字典，包含:
                - repo_dir: Git仓库路径
                - backup_dir: 备份目录路径
                - service_name: systemd服务名称
                - script_path: OTA脚本路径
                - git_remote: Git远程仓库名
                - git_branch: Git分支名
        """
        self.config = config or {}

        # 路径配置
        self.repo_dir = Path(self.config.get('repo_dir', '/home/ws/web-control'))
        self.backup_dir = Path(self.config.get('backup_dir', '/home/ws/web-control-backups'))
        self.version_file = self.repo_dir / '.version'

        # 服务配置
        self.service_name = self.config.get('service_name', 'ugv-web')
        self.script_path = self.config.get(
            'script_path',
            self.repo_dir / 'backend/scripts/ota_git_pull.sh'
        )

        # Git配置
        self.git_remote = self.config.get('git_remote', 'origin')
        self.git_branch = self.config.get('git_branch', 'main')

        # 状态
        self.updating = False
        self.update_thread = None
        self.update_callback = None

    def get_current_version(self):
        """
        获取当前版本

        Returns:
            str: 当前版本号，如果无法读取返回 'unknown'
        """
        try:
            if self.version_file.exists():
                return self.version_file.read_text().strip()
            else:
                # 尝试从git获取
                result = subprocess.run(
                    ['git', 'describe', '--tags', '--always'],
                    cwd=self.repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.version_file.write_text(version)
                    return version
        except Exception as e:
            logger.error(f'Failed to get current version: {e}')

        return 'unknown'

    def get_version_info(self):
        """
        获取完整的版本信息

        Returns:
            dict: 包含版本、git信息、最后更新时间等
        """
        version = self.get_current_version()
        git_hash = None
        git_branch = None
        last_update = None

        try:
            # 获取当前 commit hash
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_hash = result.stdout.strip()

            # 获取当前分支
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_branch = result.stdout.strip()

            # 获取最后 commit 时间
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%ci'],
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                last_update = result.stdout.strip()

        except Exception as e:
            logger.error(f'Failed to get git info: {e}')

        return {
            'version': version,
            'sbc_version': version.lstrip('v').split('-')[0] if version != 'unknown' else '0.0.0',
            'git_hash': git_hash,
            'git_branch': git_branch,
            'last_update': last_update
        }

    def check_update(self):
        """
        检查是否有更新

        Returns:
            dict: {
                'has_update': bool,
                'current_version': str,
                'latest_version': str|None,
                'commits_behind': int,
                'error': str|None
            }
        """
        try:
            current_version = self.get_current_version()

            # Fetch远程更新
            subprocess.run(
                ['git', 'fetch', self.git_remote],
                cwd=self.repo_dir,
                capture_output=True,
                timeout=30
            )

            # 获取本地和远程的commit哈希
            local_result = subprocess.run(
                ['git', 'rev-parse', '@'],
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                timeout=5
            )

            remote_result = subprocess.run(
                ['git', 'rev-parse', f'@{{u}}'],
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                timeout=5
            )

            if local_result.returncode != 0 or remote_result.returncode != 0:
                return {
                    'has_update': False,
                    'current_version': current_version,
                    'error': 'Failed to check remote version'
                }

            local_commit = local_result.stdout.strip()
            remote_commit = remote_result.stdout.strip()

            has_update = local_commit != remote_commit

            # 获取落后的commit数量
            commits_behind = 0
            if has_update:
                count_result = subprocess.run(
                    ['git', 'rev-list', '--count', f'{local_commit}..{remote_commit}'],
                    cwd=self.repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if count_result.returncode == 0:
                    commits_behind = int(count_result.stdout.strip())

            return {
                'has_update': has_update,
                'current_version': current_version,
                'latest_version': remote_commit[:8] if has_update else current_version,
                'commits_behind': commits_behind,
                'error': None
            }

        except subprocess.TimeoutExpired:
            logger.error('Check update timeout')
            return {
                'has_update': False,
                'current_version': self.get_current_version(),
                'error': 'Timeout'
            }
        except Exception as e:
            logger.error(f'Check update failed: {e}')
            return {
                'has_update': False,
                'current_version': self.get_current_version(),
                'error': str(e)
            }

    def get_update_log(self, limit=10):
        """
        获取更新日志（最近的commits）

        Args:
            limit: 获取commit数量

        Returns:
            list: Commit历史列表
        """
        try:
            result = subprocess.run(
                [
                    'git', 'log',
                    f'-{limit}',
                    '--pretty=format:%h|%an|%ar|%s'
                ],
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return []

            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    hash, author, date, message = line.split('|', 3)
                    commits.append({
                        'hash': hash,
                        'author': author,
                        'date': date,
                        'message': message
                    })

            return commits

        except Exception as e:
            logger.error(f'Failed to get update log: {e}')
            return []

    def perform_update(self, progress_callback=None):
        """
        执行OTA更新（异步）

        Args:
            progress_callback: 进度回调函数 callback(step, progress, message)

        Returns:
            bool: 是否成功启动更新线程
        """
        if self.updating:
            logger.warning('Update already in progress')
            return False

        self.updating = True
        self.update_callback = progress_callback

        # 在后台线程执行
        self.update_thread = threading.Thread(
            target=self._run_update_script,
            daemon=True
        )
        self.update_thread.start()

        return True

    def _run_update_script(self):
        """运行OTA更新脚本（内部方法）"""
        try:
            logger.info('Starting OTA update...')

            if self.update_callback:
                self.update_callback('prepare', 0, 'Preparing update...')

            # 检查脚本是否存在
            if not self.script_path.exists():
                logger.error(f'OTA script not found: {self.script_path}')
                if self.update_callback:
                    self.update_callback('error', 0, 'OTA script not found')
                self.updating = False
                return

            # 执行脚本
            process = subprocess.Popen(
                ['sudo', 'bash', str(self.script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # 实时读取输出
            step_map = {
                'Checking': ('check', 10, 'Checking for updates...'),
                'Backing up': ('backup', 20, 'Backing up current version...'),
                'Stopping': ('stop', 30, 'Stopping service...'),
                'Pulling': ('pull', 50, 'Pulling updates...'),
                'Installing': ('install', 70, 'Installing dependencies...'),
                'Building': ('build', 80, 'Building frontend...'),
                'Starting': ('start', 90, 'Starting service...'),
                'Health check': ('verify', 95, 'Verifying update...'),
                'Update completed': ('done', 100, 'Update completed!'),
                'ERROR': ('error', 0, 'Update failed')
            }

            for line in process.stdout:
                line = line.strip()
                logger.info(f'OTA: {line}')

                # 解析进度
                if self.update_callback:
                    for keyword, (step, progress, message) in step_map.items():
                        if keyword in line:
                            self.update_callback(step, progress, message)
                            break

            # 等待完成
            process.wait()

            if process.returncode == 0:
                logger.info('OTA update completed successfully')
                if self.update_callback:
                    self.update_callback('done', 100, 'Update completed!')
            else:
                logger.error(f'OTA update failed with code {process.returncode}')
                if self.update_callback:
                    self.update_callback('error', 0, f'Update failed (code {process.returncode})')

        except Exception as e:
            logger.error(f'OTA update error: {e}')
            if self.update_callback:
                self.update_callback('error', 0, f'Update error: {str(e)}')

        finally:
            self.updating = False

    def get_backups(self):
        """
        获取备份列表

        Returns:
            list: 备份信息列表
        """
        try:
            if not self.backup_dir.exists():
                return []

            backups = []
            for backup in sorted(self.backup_dir.glob('backup-*'), reverse=True):
                try:
                    # 解析备份名称: backup-v2.0.0-20260121-143045
                    parts = backup.name.split('-')
                    if len(parts) >= 3:
                        version = parts[1]
                        date = parts[2]
                        time_part = parts[3] if len(parts) > 3 else ''

                        backups.append({
                            'name': backup.name,
                            'path': str(backup),
                            'version': version,
                            'date': date,
                            'time': time_part,
                            'size': self._get_dir_size(backup)
                        })
                except Exception as e:
                    logger.warning(f'Failed to parse backup {backup}: {e}')

            return backups

        except Exception as e:
            logger.error(f'Failed to get backups: {e}')
            return []

    def _get_dir_size(self, path):
        """获取目录大小（MB）"""
        try:
            result = subprocess.run(
                ['du', '-sm', str(path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                size_mb = int(result.stdout.split()[0])
                return size_mb
        except:
            pass
        return 0

    def rollback(self, backup_name):
        """
        回滚到指定备份

        Args:
            backup_name: 备份名称

        Returns:
            dict: 回滚结果
        """
        try:
            backup_path = self.backup_dir / backup_name

            if not backup_path.exists():
                return {
                    'success': False,
                    'error': 'Backup not found'
                }

            logger.info(f'Rolling back to: {backup_path}')

            # 停止服务
            subprocess.run(['sudo', 'systemctl', 'stop', self.service_name], timeout=10)

            # 删除当前版本
            subprocess.run(['sudo', 'rm', '-rf', f'{self.repo_dir}/*'], timeout=30)

            # 恢复备份
            subprocess.run(['sudo', 'cp', '-r', f'{backup_path}/*', f'{self.repo_dir}/'], timeout=60)

            # 启动服务
            subprocess.run(['sudo', 'systemctl', 'start', self.service_name], timeout=10)

            logger.info('Rollback completed')

            return {
                'success': True,
                'message': f'Rolled back to {backup_name}'
            }

        except Exception as e:
            logger.error(f'Rollback failed: {e}')
            return {
                'success': False,
                'error': str(e)
            }

    def get_status(self):
        """获取OTA状态"""
        return {
            'updating': self.updating,
            'current_version': self.get_current_version(),
            'repo_dir': str(self.repo_dir),
            'service_name': self.service_name
        }


# 全局单例实例
_ota_service_instance = None


def get_ota_service(config=None):
    """
    获取OTAService单例实例

    Args:
        config: 配置字典

    Returns:
        OTAService实例
    """
    global _ota_service_instance
    if _ota_service_instance is None:
        _ota_service_instance = OTAService(config)
    return _ota_service_instance


def init_ota_service(app_config):
    """
    从Flask配置初始化OTAService

    Args:
        app_config: Flask app.config对象
    """
    config = {
        'repo_dir': app_config.get('OTA_REPO_DIR', '/home/ws/web-control'),
        'backup_dir': app_config.get('OTA_BACKUP_DIR', '/home/ws/web-control-backups'),
        'service_name': app_config.get('OTA_SERVICE_NAME', 'ugv-web'),
        'git_remote': app_config.get('OTA_GIT_REMOTE', 'origin'),
        'git_branch': app_config.get('OTA_GIT_BRANCH', 'main')
    }
    return get_ota_service(config)
