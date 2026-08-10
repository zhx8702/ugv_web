<template>
  <div class="tracking-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-title">
        <div class="title-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </div>
        <div>
          <h1 class="title-text">VISION TRACKING</h1>
          <p class="title-sub">// APRILTAG DETECTION & TRACKING</p>
        </div>
      </div>
      <div class="header-status" :class="statusClass">
        <span class="status-dot"></span>
        <span>{{ trackingStatusText }}</span>
      </div>
    </div>

    <div class="tracking-content">
      <!-- Left: Video Feed -->
      <div class="tracking-video-area">
        <div class="video-wrapper">
          <img
            v-if="ros2Store.connected"
            :src="videoUrl"
            class="video-feed"
            alt="ROS2 Camera"
            @error="onVideoError"
          />
          <div v-else class="video-placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-16 h-16 text-dark-text-tertiary/30">
              <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            <p class="text-dark-text-tertiary text-sm mt-2">Connect to ROS2 for camera feed</p>
          </div>

          <!-- Detection overlay info -->
          <div v-if="detections.length > 0" class="detection-overlay">
            <div v-for="det in detections" :key="det.id" class="detection-tag">
              <span class="tag-id">TAG #{{ det.id }}</span>
              <span class="tag-dist">{{ det.distance.toFixed(2) }}m</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Control Panel -->
      <div class="tracking-sidebar">
        <!-- Tracking Control -->
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">TRACKING CONTROL</span>
            <span :class="['panel-badge', trackingActive ? 'badge-ok' : 'badge-err']">
              {{ trackingActive ? 'ACTIVE' : 'INACTIVE' }}
            </span>
          </div>
          <div class="panel-content">
            <!-- Mode Selection -->
            <div class="control-group">
              <span class="section-label">Tracking Mode</span>
              <div class="mode-select">
                <button
                  v-for="mode in trackingModes"
                  :key="mode.value"
                  :class="['mode-btn', { active: trackingMode === mode.value }]"
                  @click="trackingMode = mode.value"
                  :disabled="trackingActive"
                >
                  {{ mode.label }}
                </button>
              </div>
            </div>

            <!-- Target Tag ID -->
            <div class="control-group">
              <span class="section-label">Target Tag ID</span>
              <div class="tag-id-row">
                <input
                  v-model.number="targetTagId"
                  class="tag-input"
                  type="number"
                  min="0"
                  max="100"
                  :disabled="trackingActive"
                />
                <span class="tag-hint">AprilTag ID to track</span>
              </div>
            </div>

            <!-- Start/Stop -->
            <div class="control-group">
              <div class="action-buttons">
                <button
                  v-if="!trackingActive"
                  class="btn btn-primary btn-full"
                  @click="startTracking"
                  :disabled="starting"
                >
                  <svg viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
                    <polygon points="5 3 19 12 5 21 5 3" />
                  </svg>
                  <span>{{ starting ? 'Starting...' : 'Start Tracking' }}</span>
                </button>
                <button
                  v-else
                  class="btn btn-danger btn-full"
                  @click="stopTracking"
                  :disabled="stopping"
                >
                  <svg viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
                    <rect x="6" y="6" width="12" height="12" rx="1" />
                  </svg>
                  <span>{{ stopping ? 'Stopping...' : 'Stop Tracking' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Detections -->
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">DETECTIONS</span>
            <span class="panel-badge">{{ detections.length }}</span>
          </div>
          <div class="panel-content">
            <div v-if="detections.length === 0" class="empty-state">
              <span class="text-dark-text-tertiary text-xs">No tags detected</span>
            </div>
            <div v-else class="detection-list">
              <div
                v-for="det in detections"
                :key="det.id"
                :class="['det-item', { tracked: det.id === targetTagId }]"
              >
                <div class="det-header">
                  <span class="det-id">TAG #{{ det.id }}</span>
                  <span v-if="det.id === targetTagId" class="det-tracked">TRACKING</span>
                </div>
                <div class="det-info">
                  <span>Dist: {{ det.distance.toFixed(2) }}m</span>
                  <span>X: {{ det.x.toFixed(2) }}</span>
                  <span>Y: {{ det.y.toFixed(2) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Behavior Actions -->
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">BEHAVIOR</span>
          </div>
          <div class="panel-content">
            <span class="section-label">Quick Actions</span>
            <div class="behavior-grid">
              <button class="behavior-btn" @click="sendBehavior('follow')" :disabled="!ros2Store.connected">
                Follow Tag
              </button>
              <button class="behavior-btn" @click="sendBehavior('patrol')" :disabled="!ros2Store.connected">
                Patrol
              </button>
              <button class="behavior-btn" @click="sendBehavior('return_home')" :disabled="!ros2Store.connected">
                Return Home
              </button>
              <button class="behavior-btn danger" @click="sendBehavior('stop')" :disabled="!ros2Store.connected">
                E-Stop
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useROS2Store } from '@/stores/ros2'
import { useRosbridge } from '@/composables/useRosbridge'
import { useToast } from '@/composables/useToast'
import {
  startVisionTracking,
  stopVisionTracking,
  sendBehaviorAction,
} from '@/services/api'

const ros2Store = useROS2Store()
const { rosConnected, subscribe, publish, connect } = useRosbridge()
const toast = useToast()

// State
const trackingActive = ref(false)
const trackingMode = ref('simple')
const targetTagId = ref(0)
const starting = ref(false)
const stopping = ref(false)
const detections = ref([])

const trackingModes = [
  { value: 'manual', label: 'Manual' },
  { value: 'simple', label: 'Simple' },
  { value: 'nav', label: 'Nav Track' },
]

const videoUrl = computed(() => {
  const host = window.location.hostname
  return `http://${host}:${ros2Store.videoPort || 8080}/stream?topic=/camera/image_raw&type=mjpeg&quality=70`
})

const trackingStatusText = computed(() => {
  if (!ros2Store.connected) return 'NO ROS2'
  if (trackingActive.value) return 'TRACKING'
  return 'IDLE'
})

const statusClass = computed(() => {
  if (!ros2Store.connected) return 'status-offline'
  if (trackingActive.value) return 'status-active'
  return 'status-idle'
})

// Subscriptions
let detectionSub = null

function setupDetectionSubscription() {
  if (!rosConnected.value) return
  detectionSub = subscribe('/apriltag/detections', 'apriltag_msgs/AprilTagDetectionArray', (msg) => {
    detections.value = (msg.detections || []).map(d => ({
      id: d.id?.[0] ?? d.id ?? 0,
      distance: Math.sqrt(
        (d.pose?.pose?.pose?.position?.x || 0) ** 2 +
        (d.pose?.pose?.pose?.position?.y || 0) ** 2 +
        (d.pose?.pose?.pose?.position?.z || 0) ** 2
      ),
      x: d.pose?.pose?.pose?.position?.x || 0,
      y: d.pose?.pose?.pose?.position?.y || 0,
    }))
  }, 500)
}

// Actions
async function startTracking() {
  starting.value = true
  try {
    await startVisionTracking(trackingMode.value, targetTagId.value)
    trackingActive.value = true
    toast.success(`Tracking started (${trackingMode.value})`)
  } catch (e) {
    toast.error('Failed to start tracking')
  } finally {
    starting.value = false
  }
}

async function stopTracking() {
  stopping.value = true
  try {
    await stopVisionTracking()
    trackingActive.value = false
    toast.success('Tracking stopped')
  } catch (e) {
    toast.error('Failed to stop tracking')
  } finally {
    stopping.value = false
  }
}

async function sendBehavior(action) {
  try {
    await sendBehaviorAction(action)
    toast.success(`Behavior: ${action}`)
  } catch (e) {
    toast.error(`Behavior failed: ${action}`)
  }
}

function onVideoError() {
  // Silently handle video load errors
}

onMounted(() => {
  ros2Store.startPolling()
  connect(window.location.hostname, ros2Store.port || 5001)
  // Delay subscription setup until rosbridge connects
  const checkInterval = setInterval(() => {
    if (rosConnected.value && !detectionSub) {
      setupDetectionSubscription()
      clearInterval(checkInterval)
    }
  }, 1000)
  // Cleanup after 30s if never connected
  setTimeout(() => clearInterval(checkInterval), 30000)
})

onUnmounted(() => {
  ros2Store.stopPolling()
  if (detectionSub) {
    detectionSub.unsubscribe()
    detectionSub = null
  }
})
</script>

<style scoped>
.tracking-page {
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
}

/* Content Layout */
.tracking-content {
  @apply grid gap-6;
  grid-template-columns: 1fr 340px;
  height: calc(100vh - 180px);
}

@media (max-width: 1024px) {
  .tracking-content {
    grid-template-columns: 1fr;
    height: auto;
  }
}

.tracking-video-area {
  @apply min-h-[300px];
}

.video-wrapper {
  @apply relative w-full h-full;
  background: #0a0f14;
  border: 1px solid rgba(0, 240, 255, 0.2);
  min-height: 300px;
}

.video-feed {
  @apply w-full h-full object-contain;
}

.video-placeholder {
  @apply absolute inset-0 flex flex-col items-center justify-center;
}

.detection-overlay {
  @apply absolute top-3 left-3 flex flex-col gap-1;
}

.detection-tag {
  @apply flex items-center gap-2 px-2 py-1 text-xs font-mono;
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid rgba(0, 255, 136, 0.4);
}

.tag-id {
  @apply text-secondary font-bold;
}

.tag-dist {
  @apply text-dark-text-secondary;
}

.tracking-sidebar {
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

.panel-content {
  @apply p-4;
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

.mode-select {
  @apply flex gap-2;
}

.mode-btn {
  @apply flex-1 py-2 text-xs font-mono;
  @apply text-dark-text-tertiary bg-dark-bg-tertiary/30;
  @apply border border-transparent;
  @apply transition-all duration-150;
}

.mode-btn:hover:not(:disabled) {
  @apply text-dark-text-secondary;
}

.mode-btn.active {
  @apply text-primary bg-primary/10;
  border-color: rgba(0, 240, 255, 0.3);
}

.mode-btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}

/* Tag ID input */
.tag-id-row {
  @apply flex items-center gap-3;
}

.tag-input {
  @apply w-20 px-3 py-2 text-sm font-mono text-center;
  @apply text-dark-text-primary bg-dark-bg-tertiary/50;
  @apply border border-dark-border;
  @apply focus:border-primary focus:outline-none;
}

.tag-input:disabled {
  @apply opacity-50;
}

.tag-hint {
  @apply text-[10px] font-mono text-dark-text-tertiary;
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

/* Detections */
.empty-state {
  @apply flex items-center justify-center py-4;
}

.detection-list {
  @apply flex flex-col gap-2;
}

.det-item {
  @apply px-3 py-2;
  background: rgba(0, 240, 255, 0.03);
  border: 1px solid rgba(0, 240, 255, 0.08);
}

.det-item.tracked {
  border-color: rgba(0, 255, 136, 0.3);
  background: rgba(0, 255, 136, 0.05);
}

.det-header {
  @apply flex items-center justify-between mb-1;
}

.det-id {
  @apply text-xs font-orbitron font-bold text-primary;
}

.det-tracked {
  @apply text-[10px] font-mono text-secondary px-1;
  border: 1px solid rgba(0, 255, 136, 0.3);
}

.det-info {
  @apply flex gap-3 text-[11px] font-mono text-dark-text-tertiary;
}

/* Behavior */
.behavior-grid {
  @apply grid grid-cols-2 gap-2;
}

.behavior-btn {
  @apply py-2 px-3 text-xs font-mono;
  @apply text-dark-text-secondary bg-dark-bg-tertiary/30;
  @apply border border-dark-border;
  @apply transition-all duration-150;
}

.behavior-btn:hover:not(:disabled) {
  @apply text-primary border-primary/50;
  background: rgba(0, 240, 255, 0.05);
}

.behavior-btn:disabled {
  @apply opacity-30 cursor-not-allowed;
}

.behavior-btn.danger {
  @apply text-danger border-danger/30;
}

.behavior-btn.danger:hover:not(:disabled) {
  @apply border-danger bg-danger/10;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
