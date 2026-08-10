<template>
  <div class="slam-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-title">
        <div class="title-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
        </div>
        <div>
          <h1 class="title-text">SLAM MAPPING</h1>
          <p class="title-sub">// SIMULTANEOUS LOCALIZATION & MAPPING</p>
        </div>
      </div>
      <div class="header-status" :class="statusClass">
        <span class="status-dot"></span>
        <span>{{ slamStatusText }}</span>
      </div>
    </div>

    <div class="slam-content">
      <!-- Left: Map Canvas -->
      <div class="slam-map-area">
        <SlamMapPanel
          ref="slamMapRef"
          :navMode="navMode"
          @goal-set="onGoalSet"
        />
      </div>

      <!-- Right: Control Panel -->
      <div class="slam-sidebar">
        <!-- ROS2 Connection -->
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">ROS2 CONNECTION</span>
            <span :class="['panel-badge', ros2Store.connected ? 'badge-ok' : 'badge-err']">
              {{ ros2Store.connected ? 'ONLINE' : 'OFFLINE' }}
            </span>
          </div>
          <div class="panel-content">
            <div class="info-row">
              <span class="info-label">Bridge</span>
              <span class="info-value">{{ ros2Store.host }}:{{ ros2Store.port }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Topics</span>
              <span class="info-value">{{ ros2Store.subscribers?.length || 0 }} sub</span>
            </div>
          </div>
        </div>

        <!-- SLAM Control -->
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">SLAM CONTROL</span>
            <span class="panel-badge">{{ slamAlgorithm.toUpperCase() }}</span>
          </div>
          <div class="panel-content">
            <!-- Algorithm Selection -->
            <div class="control-group">
              <span class="section-label">Algorithm</span>
              <div class="algo-select">
                <button
                  v-for="algo in algorithms"
                  :key="algo.value"
                  :class="['algo-btn', { active: slamAlgorithm === algo.value }]"
                  @click="slamAlgorithm = algo.value"
                  :disabled="slamRunning"
                >
                  {{ algo.label }}
                </button>
              </div>
            </div>

            <!-- Start/Stop -->
            <div class="control-group">
              <span class="section-label">Mapping</span>
              <div class="action-buttons">
                <button
                  v-if="!slamRunning"
                  class="btn btn-primary btn-full"
                  @click="startSlam"
                  :disabled="starting"
                >
                  <svg viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
                    <polygon points="5 3 19 12 5 21 5 3" />
                  </svg>
                  <span>{{ starting ? 'Starting...' : 'Start Mapping' }}</span>
                </button>
                <button
                  v-else
                  class="btn btn-danger btn-full"
                  @click="stopSlam"
                  :disabled="stopping"
                >
                  <svg viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
                    <rect x="6" y="6" width="12" height="12" rx="1" />
                  </svg>
                  <span>{{ stopping ? 'Stopping...' : 'Stop Mapping' }}</span>
                </button>
              </div>
            </div>

            <!-- Save Map -->
            <div class="control-group">
              <span class="section-label">Save Map</span>
              <div class="save-row">
                <input
                  v-model="mapName"
                  class="map-name-input"
                  placeholder="map_name"
                  :disabled="!slamRunning"
                />
                <button
                  class="btn btn-accent"
                  @click="saveMap"
                  :disabled="!slamRunning || saving || !mapName.trim()"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                    <polyline points="17 21 17 13 7 13 7 21" />
                    <polyline points="7 3 7 8 15 8" />
                  </svg>
                  <span>{{ saving ? 'Saving...' : 'Save' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Navigation Mode Toggle -->
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">MAP MODE</span>
            <span :class="['panel-badge', navMode ? 'badge-warn' : '']">
              {{ navMode ? 'NAV MODE' : 'VIEW MODE' }}
            </span>
          </div>
          <div class="panel-content">
            <button
              :class="['btn btn-full', navMode ? 'btn-warning' : 'btn-secondary']"
              @click="navMode = !navMode"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
                <circle cx="12" cy="12" r="10" />
                <line x1="22" y1="12" x2="18" y2="12" />
                <line x1="6" y1="12" x2="2" y2="12" />
                <line x1="12" y1="6" x2="12" y2="2" />
                <line x1="12" y1="22" x2="12" y2="18" />
              </svg>
              <span>{{ navMode ? 'Disable Nav Mode' : 'Enable Nav Mode' }}</span>
            </button>
            <p class="nav-hint" v-if="navMode">Click on the map to set a navigation goal</p>
          </div>
        </div>

        <!-- Navigation Control Panel -->
        <NavControlPanel
          ref="navControlRef"
          :robotPose="robotPose"
          @navigate="onNavGoalNavigate"
          @cancel="onNavCancel"
        />

        <!-- Robot Pose -->
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">ROBOT POSE</span>
          </div>
          <div class="panel-content">
            <div class="pose-grid">
              <div class="pose-item">
                <span class="pose-label">X</span>
                <span class="pose-value">{{ robotPose.x.toFixed(3) }}</span>
                <span class="pose-unit">m</span>
              </div>
              <div class="pose-item">
                <span class="pose-label">Y</span>
                <span class="pose-value">{{ robotPose.y.toFixed(3) }}</span>
                <span class="pose-unit">m</span>
              </div>
              <div class="pose-item">
                <span class="pose-label">&theta;</span>
                <span class="pose-value">{{ robotPose.theta.toFixed(1) }}</span>
                <span class="pose-unit">&deg;</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import SlamMapPanel from '@/components/slam/SlamMapPanel.vue'
import NavControlPanel from '@/components/slam/NavControlPanel.vue'
import { useROS2Store } from '@/stores/ros2'
import { useToast } from '@/composables/useToast'
import { startSlamMapping, stopSlamMapping, saveSlamMap } from '@/services/api'

const ros2Store = useROS2Store()
const toast = useToast()

// Refs
const slamMapRef = ref(null)
const navControlRef = ref(null)

// State
const slamRunning = ref(false)
const slamAlgorithm = ref('cartographer')
const starting = ref(false)
const stopping = ref(false)
const saving = ref(false)
const mapName = ref('my_map')
const navMode = ref(false)
const lastGoal = ref(null)

// Robot pose (mirrors SlamMapPanel's internal state for sidebar display)
const robotPose = reactive({ x: 0, y: 0, theta: 0 })

const algorithms = [
  { value: 'cartographer', label: 'Cartographer' },
  { value: 'gmapping', label: 'GMapping' },
]

// Computed
const slamStatusText = computed(() => {
  if (!ros2Store.connected) return 'NO ROS2'
  if (slamRunning.value) return 'MAPPING'
  return 'IDLE'
})

const statusClass = computed(() => {
  if (!ros2Store.connected) return 'status-offline'
  if (slamRunning.value) return 'status-active'
  return 'status-idle'
})

// Actions
async function startSlam() {
  starting.value = true
  try {
    await startSlamMapping(slamAlgorithm.value)
    slamRunning.value = true
    toast.success(`SLAM started (${slamAlgorithm.value})`)
  } catch (e) {
    toast.error('Failed to start SLAM: ' + (e.response?.data?.error || e.message))
  } finally {
    starting.value = false
  }
}

async function stopSlam() {
  stopping.value = true
  try {
    await stopSlamMapping()
    slamRunning.value = false
    toast.success('SLAM stopped')
  } catch (e) {
    toast.error('Failed to stop SLAM')
  } finally {
    stopping.value = false
  }
}

async function saveMap() {
  saving.value = true
  try {
    await saveSlamMap(mapName.value)
    toast.success(`Map saved: ${mapName.value}`)
  } catch (e) {
    toast.error('Failed to save map')
  } finally {
    saving.value = false
  }
}

function onGoalSet(goal) {
  lastGoal.value = goal
  // Forward map click goal to NavControlPanel for publishing
  if (navControlRef.value) {
    navControlRef.value.setGoalFromMap(goal)
  }
}

function onNavGoalNavigate(goal) {
  lastGoal.value = goal
}

function onNavCancel() {
  lastGoal.value = null
}

// Poll robot pose from the map panel
let poseInterval = null

onMounted(() => {
  ros2Store.startPolling()
  poseInterval = setInterval(() => {
    if (slamMapRef.value?.robotPose) {
      const p = slamMapRef.value.robotPose
      robotPose.x = p.x
      robotPose.y = p.y
      robotPose.theta = p.theta
    }
  }, 500)
})

onUnmounted(() => {
  ros2Store.stopPolling()
  if (poseInterval) clearInterval(poseInterval)
})
</script>

<style scoped>
.slam-page {
  @apply max-w-[1400px] mx-auto;
}

/* Page Header */
.page-header {
  @apply flex items-center justify-between mb-6 pb-4;
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.header-title {
  @apply flex items-center gap-4;
}

.title-icon {
  @apply w-12 h-12 p-2.5;
  @apply text-primary;
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid rgba(0, 240, 255, 0.2);
  clip-path: polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px);
}

.title-text {
  @apply text-xl font-orbitron font-bold text-dark-text-primary tracking-wider;
}

.title-sub {
  @apply text-xs font-mono text-dark-text-tertiary mt-1;
}

.header-status {
  @apply flex items-center gap-2 px-4 py-2 text-xs font-mono;
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.1);
  clip-path: polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px);
}

.status-dot {
  @apply w-2 h-2 rounded-full;
}

.status-idle {
  @apply text-dark-text-tertiary;
}
.status-idle .status-dot {
  @apply bg-dark-text-tertiary;
}

.status-active {
  @apply text-secondary;
}
.status-active .status-dot {
  @apply bg-secondary;
  box-shadow: 0 0 8px rgba(0, 255, 136, 0.6);
  animation: pulse 1s infinite;
}

.status-offline {
  @apply text-danger;
}
.status-offline .status-dot {
  @apply bg-danger;
  box-shadow: 0 0 8px rgba(255, 0, 64, 0.6);
  animation: pulse 0.5s infinite;
}

/* Content Layout */
.slam-content {
  @apply grid gap-6;
  grid-template-columns: 1fr 320px;
  height: calc(100vh - 180px);
}

@media (max-width: 1024px) {
  .slam-content {
    grid-template-columns: 1fr;
    height: auto;
  }
}

.slam-map-area {
  @apply min-h-[400px];
}

.slam-sidebar {
  @apply flex flex-col gap-4 overflow-y-auto;
}

/* Panel Styles */
.panel {
  background: rgba(3, 7, 18, 0.8);
  border: 1px solid rgba(0, 240, 255, 0.1);
  clip-path: polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px);
}

.panel-header {
  @apply flex items-center justify-between px-4 py-3;
  background: rgba(0, 240, 255, 0.05);
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.panel-title {
  @apply text-xs font-orbitron font-semibold text-primary tracking-wider;
}

.panel-badge {
  @apply text-[10px] font-mono px-2 py-0.5;
  @apply text-secondary bg-secondary/10;
  border: 1px solid rgba(0, 255, 136, 0.3);
}

.badge-ok {
  @apply text-secondary bg-secondary/10;
  border-color: rgba(0, 255, 136, 0.3);
}

.badge-err {
  @apply text-danger bg-danger/10;
  border-color: rgba(255, 0, 64, 0.3);
}

.badge-warn {
  @apply text-warning bg-warning/10;
  border-color: rgba(255, 255, 0, 0.3);
}

.panel-content {
  @apply p-4;
}

/* Info rows */
.info-row {
  @apply flex items-center justify-between py-1;
}

.info-label {
  @apply text-[11px] font-mono text-dark-text-tertiary uppercase tracking-wider;
}

.info-value {
  @apply text-sm font-mono text-dark-text-secondary;
}

/* Control groups */
.control-group {
  @apply mb-4;
}
.control-group:last-child {
  @apply mb-0;
}

.section-label {
  @apply block text-[10px] font-mono text-dark-text-tertiary mb-2 uppercase tracking-wider;
}

.algo-select {
  @apply flex gap-2;
}

.algo-btn {
  @apply flex-1 py-2 text-xs font-mono;
  @apply text-dark-text-tertiary bg-dark-bg-tertiary/30;
  @apply border border-transparent;
  @apply transition-all duration-150;
}

.algo-btn:hover:not(:disabled) {
  @apply text-dark-text-secondary;
}

.algo-btn.active {
  @apply text-primary bg-primary/10;
  border-color: rgba(0, 240, 255, 0.3);
}

.algo-btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}

/* Buttons */
.action-buttons {
  @apply flex gap-2;
}

.btn {
  @apply flex items-center justify-center gap-2 px-4 py-2;
  @apply text-sm font-orbitron font-medium;
  @apply transition-all duration-200;
  clip-path: polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px);
}

.btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}

.btn-full {
  @apply w-full;
}

.btn-primary {
  @apply text-dark-bg-primary bg-primary;
}
.btn-primary:hover:not(:disabled) {
  @apply bg-primary/80;
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.4);
}

.btn-danger {
  @apply text-white bg-danger;
}
.btn-danger:hover:not(:disabled) {
  @apply bg-danger/80;
  box-shadow: 0 0 20px rgba(255, 0, 64, 0.4);
}

.btn-accent {
  @apply text-dark-bg-primary bg-secondary;
}
.btn-accent:hover:not(:disabled) {
  @apply bg-secondary/80;
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.4);
}

.btn-secondary {
  @apply text-dark-text-secondary bg-dark-bg-tertiary border border-dark-border;
}
.btn-secondary:hover:not(:disabled) {
  @apply border-primary/50 text-primary;
}

.btn-warning {
  @apply text-dark-bg-primary bg-warning;
}
.btn-warning:hover:not(:disabled) {
  @apply bg-warning/80;
  box-shadow: 0 0 20px rgba(255, 255, 0, 0.4);
}

/* Save row */
.save-row {
  @apply flex gap-2;
}

.map-name-input {
  @apply flex-1 px-3 py-2 text-sm font-mono;
  @apply text-dark-text-primary bg-dark-bg-tertiary/50;
  @apply border border-dark-border;
  @apply focus:border-primary focus:outline-none;
  @apply placeholder:text-dark-text-tertiary/50;
}

.map-name-input:disabled {
  @apply opacity-50;
}

/* Navigation */
.nav-hint {
  @apply mt-3 text-xs font-mono text-warning/80 text-center;
}

.goal-info {
  @apply mt-3 flex items-center justify-between;
}

.goal-value {
  @apply text-danger;
}

/* Robot Pose */
.pose-grid {
  @apply grid grid-cols-3 gap-3;
}

.pose-item {
  @apply flex flex-col items-center gap-1 py-2;
  background: rgba(0, 240, 255, 0.03);
  border: 1px solid rgba(0, 240, 255, 0.08);
}

.pose-label {
  @apply text-[10px] font-mono text-dark-text-tertiary uppercase;
}

.pose-value {
  @apply text-lg font-mono font-bold text-primary;
}

.pose-unit {
  @apply text-[10px] font-mono text-dark-text-tertiary;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
