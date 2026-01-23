<template>
  <div class="settings-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        </div>
        <div class="header-text">
          <h1 class="header-title">SYSTEM CONFIG</h1>
          <div class="header-subtitle">
            <span class="prefix">//</span>
            ADVANCED PARAMETER SETTINGS
          </div>
        </div>
      </div>
      <div class="header-status" v-if="settingsStore.loading">
        <span class="loading-indicator"></span>
        SYNCING...
      </div>
    </div>

    <!-- Settings Grid -->
    <div class="settings-grid">
      <!-- Robot Configuration -->
      <div class="settings-panel" :style="{ animationDelay: '0ms' }">
        <div class="panel-header">
          <div class="panel-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="10" rx="2" />
              <circle cx="12" cy="5" r="2" />
              <path d="M12 7v4" />
              <line x1="8" y1="16" x2="8" y2="16" />
              <line x1="16" y1="16" x2="16" y2="16" />
            </svg>
          </div>
          <h2 class="panel-title">UNIT PROFILE</h2>
        </div>
        <div class="panel-content">
          <div class="form-group">
            <label class="form-label">DESIGNATION</label>
            <input type="text" v-model="settingsStore.settings.robotName" class="input w-full" />
          </div>
          <div class="form-group">
            <label class="form-label">CHASSIS TYPE</label>
            <select v-model="settingsStore.settings.robotType" class="input w-full">
              <option :value="1">RaspRover</option>
              <option :value="2">UGV Rover</option>
              <option :value="3">UGV Beast</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">MODULE CONFIG</label>
            <select v-model="settingsStore.settings.moduleType" class="input w-full">
              <option :value="0">Camera PT</option>
              <option :value="1">RoArm-M2</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Video Settings -->
      <div class="settings-panel" :style="{ animationDelay: '100ms' }">
        <div class="panel-header">
          <div class="panel-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="23 7 16 12 23 17 23 7" />
              <rect x="1" y="5" width="15" height="14" rx="2" />
            </svg>
          </div>
          <h2 class="panel-title">VIDEO PARAMS</h2>
        </div>
        <div class="panel-content">
          <div class="form-group">
            <label class="form-label">RESOLUTION</label>
            <select v-model="settingsStore.settings.resolution" class="input w-full">
              <option value="480p">640x480 (480p)</option>
              <option value="720p">1280x720 (720p)</option>
              <option value="1080p">1920x1080 (1080p)</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">QUALITY: {{ settingsStore.settings.quality }}%</label>
            <div class="slider-container">
              <input type="range" v-model="settingsStore.settings.quality" min="10" max="100" class="w-full" />
              <div class="slider-labels">
                <span>LOW</span>
                <span>HIGH</span>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">STREAM PROTOCOL</label>
            <div class="radio-group">
              <label class="radio-item" :class="{ active: settingsStore.settings.streamType === 'mjpeg' }">
                <input type="radio" v-model="settingsStore.settings.streamType" value="mjpeg" />
                <span class="radio-label">MJPEG</span>
              </label>
              <label class="radio-item" :class="{ active: settingsStore.settings.streamType === 'webrtc' }">
                <input type="radio" v-model="settingsStore.settings.streamType" value="webrtc" />
                <span class="radio-label">WebRTC</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Control Settings -->
      <div class="settings-panel" :style="{ animationDelay: '200ms' }">
        <div class="panel-header">
          <div class="panel-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v8M8 12h8" />
            </svg>
          </div>
          <h2 class="panel-title">CONTROL PARAMS</h2>
        </div>
        <div class="panel-content">
          <div class="form-row">
            <div class="form-group flex-1">
              <label class="form-label">MAX SPEED (m/s)</label>
              <input type="number" v-model="settingsStore.settings.maxSpeed" step="0.1" class="input w-full" />
            </div>
            <div class="form-group flex-1">
              <label class="form-label">SLOW SPEED (m/s)</label>
              <input type="number" v-model="settingsStore.settings.slowSpeed" step="0.1" class="input w-full" />
            </div>
          </div>
          <div class="form-group">
            <label class="toggle-item">
              <input type="checkbox" v-model="settingsStore.preferences.keyboardControl" />
              <span class="toggle-switch"></span>
              <span class="toggle-label">KEYBOARD CONTROL</span>
            </label>
          </div>
          <div class="form-group">
            <label class="toggle-item">
              <input type="checkbox" v-model="settingsStore.preferences.vibration" />
              <span class="toggle-switch"></span>
              <span class="toggle-label">HAPTIC FEEDBACK</span>
            </label>
          </div>
        </div>
      </div>

      <!-- System Information -->
      <div class="settings-panel" :style="{ animationDelay: '300ms' }">
        <div class="panel-header">
          <div class="panel-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
            </svg>
          </div>
          <h2 class="panel-title">SYSTEM INFO</h2>
          <div class="panel-badge" :class="settingsStore.synced ? 'online' : 'warning'">
            {{ settingsStore.synced ? 'SYNCED' : 'NOT SYNCED' }}
          </div>
        </div>
        <div class="panel-content">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">FIRMWARE</span>
              <span class="info-value">v{{ settingsStore.settings.sbcVersion }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">PLATFORM</span>
              <span class="info-value">Raspberry Pi</span>
            </div>
            <div class="info-item">
              <span class="info-label">ROBOT TYPE</span>
              <span class="info-value">{{ robotTypeName }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">MODULE</span>
              <span class="info-value">{{ moduleTypeName }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">LAST SYNC</span>
              <span class="info-value">{{ settingsStore.formattedLastSync }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">STATUS</span>
              <span class="info-value status-online">OPERATIONAL</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Servo Configuration -->
      <div class="settings-panel" :style="{ animationDelay: '400ms' }">
        <div class="panel-header">
          <div class="panel-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
            </svg>
          </div>
          <h2 class="panel-title">SERVO CONFIG</h2>
          <div class="panel-badge" :class="servoReleased ? 'warning' : 'online'">
            {{ servoReleased ? 'RELEASED' : 'LOCKED' }}
          </div>
        </div>
        <div class="panel-content">
          <!-- Servo ID Settings -->
          <div class="servo-section">
            <div class="section-title">SERVO ID ASSIGNMENT</div>
            <div class="form-row">
              <div class="form-group flex-1">
                <label class="form-label">PAN SERVO ID</label>
                <input type="number" v-model="servo.panId" min="1" max="253" class="input w-full" />
              </div>
              <div class="form-group flex-1">
                <label class="form-label">TILT SERVO ID</label>
                <input type="number" v-model="servo.tiltId" min="1" max="253" class="input w-full" />
              </div>
            </div>
          </div>

          <!-- Servo Actions -->
          <div class="servo-section">
            <div class="section-title">SERVO ACTIONS</div>
            <div class="servo-actions">
              <button class="servo-btn" @click="setServoMid(1)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="2" x2="12" y2="22" />
                  <polyline points="19 12 12 5 5 12" />
                </svg>
                SET PAN MID
              </button>
              <button class="servo-btn" @click="setServoMid(2)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="2" x2="12" y2="22" />
                  <polyline points="19 12 12 5 5 12" />
                </svg>
                SET TILT MID
              </button>
              <button class="servo-btn release" :class="{ active: servoReleased }" @click="toggleServoRelease">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 9.9-1" />
                </svg>
                {{ servoReleased ? 'LOCK SERVOS' : 'RELEASE SERVOS' }}
              </button>
            </div>
          </div>

          <!-- Advanced: Change Servo ID -->
          <div class="servo-section">
            <div class="section-title">ADVANCED: CHANGE SERVO ID</div>
            <div class="form-row">
              <div class="form-group flex-1">
                <label class="form-label">OLD ID</label>
                <input type="number" v-model="servo.oldId" min="1" max="253" class="input w-full" />
              </div>
              <div class="form-group flex-1">
                <label class="form-label">NEW ID</label>
                <input type="number" v-model="servo.newId" min="1" max="253" class="input w-full" />
              </div>
              <button class="btn btn-outline change-id-btn" @click="changeServoId">
                CHANGE
              </button>
            </div>
            <div class="warning-text">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              Only one servo should be connected when changing ID
            </div>
          </div>
        </div>
      </div>

      <!-- User Preferences -->
      <div class="settings-panel" :style="{ animationDelay: '500ms' }">
        <div class="panel-header">
          <div class="panel-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
          <h2 class="panel-title">USER PREFERENCES</h2>
          <div class="panel-badge online">SAVED ON SERVER</div>
        </div>
        <div class="panel-content">
          <div class="form-group">
            <label class="form-label">DEFAULT SPEED MODE</label>
            <div class="radio-group triple">
              <label class="radio-item" :class="{ active: settingsStore.preferences.speedMode === 'slow' }">
                <input type="radio" v-model="settingsStore.preferences.speedMode" value="slow" />
                <span class="radio-label">SLOW</span>
              </label>
              <label class="radio-item" :class="{ active: settingsStore.preferences.speedMode === 'mid' }">
                <input type="radio" v-model="settingsStore.preferences.speedMode" value="mid" />
                <span class="radio-label">MEDIUM</span>
              </label>
              <label class="radio-item" :class="{ active: settingsStore.preferences.speedMode === 'fast' }">
                <input type="radio" v-model="settingsStore.preferences.speedMode" value="fast" />
                <span class="radio-label">FAST</span>
              </label>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">DEFAULT HEAD LIGHT</label>
            <div class="radio-group triple">
              <label class="radio-item" :class="{ active: settingsStore.preferences.headLight === 'off' }">
                <input type="radio" v-model="settingsStore.preferences.headLight" value="off" />
                <span class="radio-label">OFF</span>
              </label>
              <label class="radio-item" :class="{ active: settingsStore.preferences.headLight === 'auto' }">
                <input type="radio" v-model="settingsStore.preferences.headLight" value="auto" />
                <span class="radio-label">AUTO</span>
              </label>
              <label class="radio-item" :class="{ active: settingsStore.preferences.headLight === 'on' }">
                <input type="radio" v-model="settingsStore.preferences.headLight" value="on" />
                <span class="radio-label">ON</span>
              </label>
            </div>
          </div>
          <div class="form-group">
            <label class="toggle-item">
              <input type="checkbox" v-model="settingsStore.preferences.baseLight" />
              <span class="toggle-switch"></span>
              <span class="toggle-label">DEFAULT BASE LIGHT ON</span>
            </label>
          </div>
        </div>
      </div>

      <!-- OTA Update -->
      <div class="settings-panel" :style="{ animationDelay: '600ms' }">
        <div class="panel-header">
          <div class="panel-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          </div>
          <h2 class="panel-title">OTA UPDATE</h2>
          <div class="panel-badge" :class="updateStatus.hasUpdate ? 'warning' : 'online'">
            {{ updateStatus.hasUpdate ? 'UPDATE AVAILABLE' : 'UP TO DATE' }}
          </div>
        </div>
        <div class="panel-content">
          <!-- Version Info -->
          <div class="version-info">
            <div class="version-row">
              <span class="version-label">CURRENT VERSION</span>
              <span class="version-value">v{{ versionInfo.sbc_version || '0.93' }}</span>
            </div>
            <div class="version-row" v-if="versionInfo.git_hash">
              <span class="version-label">GIT COMMIT</span>
              <span class="version-value mono">{{ versionInfo.git_hash }}</span>
            </div>
            <div class="version-row" v-if="versionInfo.git_branch">
              <span class="version-label">BRANCH</span>
              <span class="version-value mono">{{ versionInfo.git_branch }}</span>
            </div>
            <div class="version-row" v-if="versionInfo.last_update">
              <span class="version-label">LAST UPDATE</span>
              <span class="version-value mono">{{ formatDate(versionInfo.last_update) }}</span>
            </div>
          </div>

          <!-- Update Status -->
          <div class="update-status" v-if="updateStatus.hasUpdate">
            <div class="update-badge">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              {{ updateStatus.commits_behind }} commit(s) behind
            </div>
            <div class="changelog" v-if="updateStatus.changelog && updateStatus.changelog.length">
              <div class="changelog-title">CHANGELOG</div>
              <div class="changelog-item" v-for="(log, idx) in updateStatus.changelog" :key="idx">
                {{ log }}
              </div>
            </div>
          </div>

          <!-- Update Actions -->
          <div class="update-actions">
            <button
              class="btn btn-outline"
              @click="handleCheckUpdate"
              :disabled="checkingUpdate"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4" :class="{ spinning: checkingUpdate }">
                <polyline points="23 4 23 10 17 10" />
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
              </svg>
              {{ checkingUpdate ? 'CHECKING...' : 'CHECK UPDATE' }}
            </button>
            <button
              class="btn btn-primary"
              @click="handleDoUpdate"
              :disabled="!updateStatus.hasUpdate || updating"
              v-if="updateStatus.hasUpdate"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              {{ updating ? 'UPDATING...' : 'INSTALL UPDATE' }}
            </button>
          </div>

          <!-- Update Progress -->
          <div class="update-progress" v-if="updating">
            <div class="progress-bar">
              <div class="progress-fill"></div>
            </div>
            <div class="progress-text">Downloading and applying update...</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Actions Panel -->
    <div class="actions-panel">
      <div class="actions-left">
        <button class="btn btn-primary" @click="saveSettings" :disabled="settingsStore.loading">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
            <polyline points="17 21 17 13 7 13 7 21" />
            <polyline points="7 3 7 8 15 8" />
          </svg>
          {{ settingsStore.loading ? 'SAVING...' : 'SAVE CONFIG' }}
        </button>
        <button class="btn btn-outline" @click="resetSettings">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
            <path d="M3 3v5h5" />
          </svg>
          RESET DEFAULTS
        </button>
        <button class="btn btn-outline" @click="refreshConfig">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
          REFRESH
        </button>
      </div>
      <div class="actions-right">
        <button class="btn btn-outline" @click="exportConfig">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          EXPORT
        </button>
        <button class="btn btn-outline" @click="triggerImport">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          IMPORT
        </button>
        <input type="file" ref="fileInput" @change="handleImport" accept=".json" style="display: none" />
        <button class="btn btn-danger" @click="rebootSystem">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
            <path d="M18.36 6.64a9 9 0 1 1-12.73 0" />
            <line x1="12" y1="2" x2="12" y2="12" />
          </svg>
          REBOOT
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useToast } from '@/composables/useToast'
import {
  setServoId as apiSetServoId,
  setServoMid as apiSetServoMid,
  setServoTorque,
  releaseServo as apiReleaseServo,
  getVersion,
  checkUpdate,
  doUpdate,
  restartService
} from '@/services/api'

const settingsStore = useSettingsStore()
const toast = useToast()

const servo = ref({
  panId: 1,
  tiltId: 2,
  oldId: 1,
  newId: 1
})

const servoReleased = ref(false)
const fileInput = ref(null)

// OTA 更新状态
const versionInfo = ref({})
const updateStatus = ref({ hasUpdate: false, commits_behind: 0, changelog: [] })
const checkingUpdate = ref(false)
const updating = ref(false)

// 计算属性
const robotTypeName = computed(() => {
  const types = { 1: 'RaspRover', 2: 'UGV Rover', 3: 'UGV Beast' }
  return types[settingsStore.settings.robotType] || 'Unknown'
})

const moduleTypeName = computed(() => {
  const types = { 0: 'Camera PT', 1: 'RoArm-M2' }
  return types[settingsStore.settings.moduleType] || 'None'
})

// 保存设置
async function saveSettings() {
  const success = await settingsStore.saveConfig()
  if (success) {
    toast.success('Configuration saved successfully')
  } else {
    toast.error('Failed to save configuration')
  }
}

// 重置设置
async function resetSettings() {
  if (confirm('Are you sure you want to reset all settings to defaults?')) {
    await settingsStore.resetToDefaults()
    toast.info('Settings reset to defaults')
  }
}

// 刷新配置
async function refreshConfig() {
  await settingsStore.fetchConfig()
  toast.info('Configuration refreshed')
}

// 导出配置
function exportConfig() {
  settingsStore.exportConfig()
  toast.success('Configuration exported')
}

// 触发导入
function triggerImport() {
  fileInput.value?.click()
}

// 处理导入
async function handleImport(e) {
  const file = e.target.files?.[0]
  if (!file) return

  try {
    await settingsStore.importConfig(file)
    toast.success('Configuration imported successfully')
  } catch (err) {
    toast.error('Failed to import configuration')
  }

  // 清除文件输入
  e.target.value = ''
}

// 重启系统
async function rebootSystem() {
  if (confirm('Are you sure you want to reboot the system?')) {
    const success = await settingsStore.rebootSystem()
    if (success) {
      toast.info('System is rebooting...')
    } else {
      toast.error('Failed to reboot system')
    }
  }
}

// Servo control functions
async function setServoMid(id) {
  try {
    await apiSetServoMid(id)
    toast.success(`Servo ${id} mid position set`)
  } catch (e) {
    toast.error('Set servo mid failed')
  }
}

async function toggleServoRelease() {
  try {
    if (servoReleased.value) {
      // Lock servos
      await setServoTorque(servo.value.panId, true)
      await setServoTorque(servo.value.tiltId, true)
      servoReleased.value = false
      toast.info('Servos locked')
    } else {
      // Release servos
      await apiReleaseServo()
      servoReleased.value = true
      toast.info('Servos released')
    }
  } catch (e) {
    toast.error('Toggle servo release failed')
  }
}

async function changeServoId() {
  if (servo.value.oldId === servo.value.newId) {
    toast.warning('Old ID and new ID are the same')
    return
  }
  try {
    await apiSetServoId(servo.value.oldId, servo.value.newId)
    toast.success(`Servo ID changed: ${servo.value.oldId} -> ${servo.value.newId}`)
  } catch (e) {
    toast.error('Change servo ID failed')
  }
}

// OTA 更新方法
async function fetchVersionInfo() {
  try {
    const info = await getVersion()
    versionInfo.value = info
  } catch (e) {
    console.error('Failed to fetch version info:', e)
  }
}

async function handleCheckUpdate() {
  checkingUpdate.value = true
  try {
    const result = await checkUpdate()
    updateStatus.value = {
      hasUpdate: result.has_update || false,
      commits_behind: result.commits_behind || 0,
      changelog: result.changelog || []
    }
    if (result.has_update) {
      toast.info(`${result.commits_behind} update(s) available`)
    } else {
      toast.success('Already up to date')
    }
  } catch (e) {
    toast.error('Failed to check updates')
  } finally {
    checkingUpdate.value = false
  }
}

async function handleDoUpdate() {
  if (!confirm('Are you sure you want to install the update? The service will restart after update.')) {
    return
  }

  updating.value = true
  try {
    const result = await doUpdate()
    if (result.success) {
      toast.success('Update completed! Restarting service...')
      // 尝试重启服务
      try {
        await restartService()
      } catch (e) {
        // 服务重启可能会断开连接，这是正常的
      }
      // 提示用户刷新页面
      setTimeout(() => {
        if (confirm('Update installed. Refresh page to see changes?')) {
          window.location.reload()
        }
      }, 2000)
    } else {
      toast.error(result.message || 'Update failed')
    }
  } catch (e) {
    toast.error('Update failed: ' + (e.message || 'Unknown error'))
  } finally {
    updating.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return dateStr
  }
}

onMounted(() => {
  settingsStore.fetchConfig()
  fetchVersionInfo()
})
</script>

<style scoped>
.settings-page {
  @apply p-6 min-h-screen;
  animation: fadeIn 0.5s ease-out;
}

/* Page Header */
.page-header {
  @apply flex items-center justify-between mb-6 pb-4;
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.header-left {
  @apply flex items-center gap-4;
}

.header-icon {
  @apply w-10 h-10 text-primary;
  filter: drop-shadow(0 0 8px rgba(0, 240, 255, 0.5));
  animation: spin 10s linear infinite;
}

.header-text {
  @apply flex flex-col;
}

.header-title {
  @apply text-2xl font-orbitron font-bold tracking-widest;
  background: linear-gradient(135deg, #00f0ff 0%, #0080ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-subtitle {
  @apply text-xs font-mono text-dark-text-tertiary flex items-center gap-2;
}

.header-subtitle .prefix {
  @apply text-primary;
}

.header-status {
  @apply flex items-center gap-2 text-xs font-orbitron text-primary;
}

.loading-indicator {
  @apply w-2 h-2 rounded-full bg-primary;
  animation: pulse 1s ease-in-out infinite;
}

/* Settings Grid */
.settings-grid {
  @apply grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6;
}

/* Settings Panel */
.settings-panel {
  @apply relative overflow-hidden;
  background: linear-gradient(135deg, rgba(10, 22, 40, 0.9) 0%, rgba(3, 7, 18, 0.95) 100%);
  border: 1px solid rgba(0, 240, 255, 0.15);
  clip-path: polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px);
  animation: slideUp 0.5s ease-out both;
}

.settings-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 240, 255, 0.5), transparent);
}

.panel-header {
  @apply flex items-center gap-3 px-5 py-3;
  background: rgba(0, 240, 255, 0.03);
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.panel-icon {
  @apply w-5 h-5 text-primary;
}

.panel-title {
  @apply flex-1 text-sm font-orbitron font-semibold tracking-wider text-dark-text-primary uppercase;
}

.panel-badge {
  @apply px-2 py-0.5 text-[10px] font-orbitron font-medium tracking-wider rounded-sm;
}

.panel-badge.online {
  @apply bg-secondary/20 text-secondary border border-secondary/30;
}

.panel-content {
  @apply p-5 space-y-4;
}

/* Form Elements */
.form-group {
  @apply space-y-2;
}

.form-row {
  @apply flex gap-4;
}

.form-label {
  @apply block text-[10px] font-orbitron tracking-wider text-dark-text-tertiary uppercase;
}

/* Slider */
.slider-container {
  @apply space-y-1;
}

.slider-labels {
  @apply flex justify-between text-[10px] font-mono text-dark-text-tertiary;
}

/* Radio Group */
.radio-group {
  @apply flex gap-2;
}

.radio-group.triple {
  @apply grid grid-cols-3 gap-2;
}

.radio-item {
  @apply flex-1 relative cursor-pointer;
}

.radio-item input {
  @apply absolute opacity-0;
}

.radio-label {
  @apply block text-center py-2 px-4 font-orbitron text-xs tracking-wider;
  @apply text-dark-text-tertiary border border-dark-border;
  @apply transition-all duration-200;
  clip-path: polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px);
}

.radio-item.active .radio-label {
  @apply text-primary border-primary bg-primary/10;
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
}

/* Toggle Switch */
.toggle-item {
  @apply flex items-center gap-3 cursor-pointer;
}

.toggle-item input {
  @apply hidden;
}

.toggle-switch {
  @apply relative w-12 h-6 rounded-full transition-all duration-200;
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid rgba(0, 240, 255, 0.3);
}

.toggle-switch::after {
  content: '';
  @apply absolute top-1 left-1 w-4 h-4 rounded-full transition-all duration-200;
  background: var(--dark-bg);
  border: 1px solid rgba(0, 240, 255, 0.5);
}

.toggle-item input:checked + .toggle-switch {
  background: var(--cyber-cyan);
  border-color: var(--cyber-cyan);
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
}

.toggle-item input:checked + .toggle-switch::after {
  @apply left-6;
  background: var(--dark-bg);
  border-color: var(--dark-bg);
}

.toggle-label {
  @apply text-sm font-mono text-dark-text-primary;
}

/* Info Grid */
.info-grid {
  @apply grid grid-cols-2 gap-4;
}

.info-item {
  @apply flex flex-col gap-1;
}

.info-label {
  @apply text-[10px] font-orbitron tracking-wider text-dark-text-tertiary uppercase;
}

.info-value {
  @apply text-sm font-mono text-dark-text-primary;
}

.info-value.status-online {
  @apply text-secondary;
  text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
}

/* Actions Panel */
.actions-panel {
  @apply flex items-center justify-between p-5 flex-wrap gap-4;
  background: linear-gradient(135deg, rgba(10, 22, 40, 0.9) 0%, rgba(3, 7, 18, 0.95) 100%);
  border: 1px solid rgba(0, 240, 255, 0.15);
  clip-path: polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px);
}

.actions-left,
.actions-right {
  @apply flex items-center gap-3 flex-wrap;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Servo Config Panel */
.servo-section {
  @apply space-y-3 pb-4;
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.servo-section:last-child {
  @apply pb-0;
  border-bottom: none;
}

.section-title {
  @apply text-[10px] font-orbitron tracking-wider text-primary uppercase;
}

.servo-actions {
  @apply grid grid-cols-3 gap-2;
}

.servo-btn {
  @apply flex flex-col items-center justify-center gap-1 py-3 px-2;
  @apply text-[10px] font-orbitron tracking-wider;
  @apply text-dark-text-tertiary border border-dark-border;
  @apply transition-all duration-200;
  clip-path: polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px);
}

.servo-btn svg {
  @apply w-5 h-5;
}

.servo-btn:hover {
  @apply text-primary border-primary/50 bg-primary/5;
}

.servo-btn.release {
  @apply text-warning border-warning/30;
}

.servo-btn.release:hover {
  @apply bg-warning/10 border-warning;
}

.servo-btn.release.active {
  @apply text-secondary border-secondary bg-secondary/10;
}

.change-id-btn {
  @apply self-end mb-2;
}

.warning-text {
  @apply flex items-center gap-2 mt-2 p-2;
  @apply text-[10px] font-mono text-warning;
  @apply bg-warning/5 border border-warning/20 rounded;
}

.warning-text svg {
  @apply w-4 h-4 flex-shrink-0;
}

.panel-badge.warning {
  @apply bg-warning/20 text-warning border border-warning/30;
}

/* OTA Update Styles */
.version-info {
  @apply space-y-2 p-3 rounded;
  background: rgba(0, 240, 255, 0.03);
  border: 1px solid rgba(0, 240, 255, 0.1);
}

.version-row {
  @apply flex justify-between items-center;
}

.version-label {
  @apply text-[10px] font-orbitron tracking-wider text-dark-text-tertiary uppercase;
}

.version-value {
  @apply text-sm text-dark-text-primary;
}

.version-value.mono {
  @apply font-mono text-primary;
}

.update-status {
  @apply mt-4 space-y-3;
}

.update-badge {
  @apply flex items-center gap-2 px-3 py-2 rounded;
  @apply text-sm font-mono text-warning;
  @apply bg-warning/10 border border-warning/30;
}

.update-badge svg {
  @apply w-4 h-4;
}

.changelog {
  @apply p-3 rounded space-y-1;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 240, 255, 0.1);
}

.changelog-title {
  @apply text-[10px] font-orbitron tracking-wider text-primary uppercase mb-2;
}

.changelog-item {
  @apply text-xs font-mono text-dark-text-secondary;
  @apply pl-3 border-l-2 border-primary/30;
}

.update-actions {
  @apply flex gap-3 mt-4;
}

.update-progress {
  @apply mt-4 space-y-2;
}

.progress-bar {
  @apply h-1 w-full rounded-full overflow-hidden;
  background: rgba(0, 240, 255, 0.1);
}

.progress-fill {
  @apply h-full rounded-full;
  width: 100%;
  background: linear-gradient(90deg, var(--cyber-cyan), var(--cyber-blue));
  animation: progressPulse 1.5s ease-in-out infinite;
}

.progress-text {
  @apply text-xs font-mono text-dark-text-tertiary text-center;
}

@keyframes progressPulse {
  0%, 100% { opacity: 0.5; transform: translateX(-100%); }
  50% { opacity: 1; transform: translateX(0); }
}

.spinning {
  animation: spin 1s linear infinite;
}
</style>
