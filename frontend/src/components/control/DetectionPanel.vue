<template>
  <div class="detection-panel">
    <!-- CV Mode Selector (合并后的统一选择器) -->
    <div class="form-group">
      <label class="form-label">CV Mode</label>
      <div class="cv-modes">
        <button
          v-for="mode in cvModes"
          :key="mode.value"
          @click="selectMode(mode.value)"
          :class="[
            'cv-btn',
            detectionType === mode.value ? 'active' : ''
          ]"
        >
          <span class="cv-icon">{{ mode.icon }}</span>
          <span class="cv-label">{{ mode.label }}</span>
        </button>
      </div>
    </div>

    <!-- Detection Results -->
    <div v-if="detections.length > 0" class="detection-results">
      <div class="results-header">
        <span class="results-title">Detected: {{ detections.length }} objects</span>
      </div>
      <div class="results-list">
        <div
          v-for="detection in detections"
          :key="detection.id"
          class="detection-badge"
        >
          <div class="badge-icon">🎯</div>
          <div class="badge-content">
            <div class="badge-label">{{ detection.label }}</div>
            <div class="badge-confidence">
              <div class="confidence-bar">
                <div
                  class="confidence-fill"
                  :style="{ width: `${detection.confidence}%` }"
                ></div>
              </div>
              <span class="confidence-text">{{ detection.confidence }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- No Detections -->
    <div v-else-if="detectionType !== 'none'" class="no-detections">
      <span class="no-detections-icon">👁️</span>
      <p class="no-detections-text">Searching...</p>
    </div>

    <!-- Detection Reaction -->
    <div class="form-group">
      <label class="form-label">When Detected</label>
      <div class="reaction-buttons">
        <button
          v-for="reaction in reactions"
          :key="reaction.value"
          @click="setReaction(reaction.value)"
          :class="[
            'reaction-btn',
            detectionReaction === reaction.value ? 'active' : ''
          ]"
        >
          {{ reaction.icon }} {{ reaction.label }}
        </button>
      </div>
    </div>

    <!-- Tracking Controls -->
    <div class="tracking-controls">
      <button
        @click="toggleTracking"
        :class="[
          'btn flex-1',
          tracking ? 'btn-danger' : 'btn-outline'
        ]"
      >
        {{ tracking ? '🔓 Unlock' : '🔒 Lock' }}
      </button>
      <button
        @click="toggleAutoDrive"
        :class="[
          'btn flex-1',
          autoDrive ? 'btn-primary' : 'btn-outline'
        ]"
      >
        🚗 Auto Drive
      </button>
    </div>

    <!-- Stats -->
    <div v-if="detectionType !== 'none'" class="detection-stats">
      <div class="stat-item">
        <span class="stat-label">Mode:</span>
        <span class="stat-value">{{ currentDetectionMode?.label }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Status:</span>
        <span :class="['stat-value', detections.length > 0 ? 'text-success' : '']">
          {{ detections.length > 0 ? 'Active' : 'Scanning' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useControlStore } from '@/stores/control'

const controlStore = useControlStore()
const {
  detectionType,
  detectionReaction,
  tracking,
  autoDrive,
  detections
} = storeToRefs(controlStore)

const { setDetectionMode, toggleTracking, toggleAutoDrive } = controlStore

// 合并后的CV模式列表（移除重复，统一管理）
const cvModes = [
  { value: 'none', label: 'OFF', icon: '⭕' },
  { value: 'motion', label: 'Motion', icon: '🏃' },
  { value: 'faces', label: 'Face', icon: '👤' },
  { value: 'objects', label: 'Objects', icon: '📦' },
  { value: 'color', label: 'Color', icon: '🎨' },
  { value: 'hand', label: 'Hand', icon: '✋' },
  { value: 'mp_face', label: 'MP Face', icon: '😊' },
  { value: 'mp_pose', label: 'Pose', icon: '🤸' }
]

// Reactions
const reactions = [
  { value: 'none', label: 'None', icon: '⭕' },
  { value: 'capture', label: 'Capture', icon: '📷' },
  { value: 'record', label: 'Record', icon: '⏺' }
]

// Computed
const currentDetectionMode = computed(() => {
  return cvModes.find(m => m.value === detectionType.value)
})

// Methods
const selectMode = (mode) => {
  setDetectionMode(mode)
}

const setReaction = (reaction) => {
  detectionReaction.value = reaction
}
</script>

<style scoped>
.detection-panel {
  @apply space-y-4;
}

.form-group {
  @apply space-y-2;
}

.form-label {
  @apply block text-xs text-dark-text-secondary font-medium;
}

.form-select {
  @apply w-full px-3 py-2 rounded text-sm;
  @apply bg-dark-bg-tertiary border border-dark-border;
  @apply text-dark-text-primary;
  @apply transition-colors cursor-pointer;
}

.form-select:focus {
  @apply outline-none ring-1 ring-primary border-primary;
}

.cv-modes {
  @apply grid grid-cols-4 gap-2;
}

.cv-btn {
  @apply flex flex-col items-center justify-center gap-1 p-2.5 rounded;
  @apply bg-dark-bg-secondary border border-dark-border;
  @apply transition-all cursor-pointer;
}

.cv-btn:hover {
  @apply border-primary/50;
  background: rgba(0, 240, 255, 0.05);
}

.cv-btn.active {
  @apply border-primary;
  background: rgba(0, 240, 255, 0.15);
  box-shadow: 0 0 12px rgba(0, 240, 255, 0.3), inset 0 0 8px rgba(0, 240, 255, 0.1);
}

.cv-btn.active .cv-icon,
.cv-btn.active .cv-label {
  @apply text-primary;
  text-shadow: 0 0 8px rgba(0, 240, 255, 0.5);
}

.cv-icon {
  @apply text-lg;
}

.cv-label {
  @apply text-xs font-medium;
}

.detection-results {
  @apply bg-dark-bg-tertiary rounded-lg p-3 space-y-2;
}

.results-header {
  @apply flex items-center justify-between;
}

.results-title {
  @apply text-sm font-medium text-dark-text-secondary;
}

.results-list {
  @apply space-y-2;
}

.detection-badge {
  @apply flex items-center gap-3 p-2 bg-dark-bg-secondary rounded;
}

.badge-icon {
  @apply text-xl;
}

.badge-content {
  @apply flex-1 space-y-1;
}

.badge-label {
  @apply text-sm font-medium text-dark-text-primary;
}

.badge-confidence {
  @apply flex items-center gap-2;
}

.confidence-bar {
  @apply flex-1 h-1.5 bg-dark-bg-primary rounded-full overflow-hidden;
}

.confidence-fill {
  @apply h-full bg-success;
  transition: width 0.3s ease;
}

.confidence-text {
  @apply text-xs text-dark-text-secondary font-mono;
}

.no-detections {
  @apply flex items-center justify-center gap-4 py-6 px-6;
  @apply bg-dark-bg-tertiary rounded-lg;
}

.no-detections-icon {
  @apply text-5xl opacity-60;
}

.no-detections-text {
  @apply text-xl text-dark-text-secondary;
}

.reaction-buttons {
  @apply flex gap-2;
}

.reaction-btn {
  @apply flex-1 px-3 py-2 rounded text-sm;
  @apply bg-dark-bg-secondary border border-dark-border;
  @apply transition-all cursor-pointer;
}

.reaction-btn:hover {
  @apply border-primary/50;
  background: rgba(0, 240, 255, 0.05);
}

.reaction-btn.active {
  @apply border-primary text-primary;
  background: rgba(0, 240, 255, 0.15);
  box-shadow: 0 0 8px rgba(0, 240, 255, 0.2);
}

.tracking-controls {
  @apply flex gap-2;
}

.tracking-controls .btn {
  @apply text-sm py-2;
}

.detection-stats {
  @apply grid grid-cols-2 gap-2 text-sm;
}

.stat-item {
  @apply flex justify-between items-center;
  @apply py-2 px-3 bg-dark-bg-tertiary rounded;
}

.stat-label {
  @apply text-dark-text-secondary;
}

.stat-value {
  @apply font-mono text-dark-text-primary;
}

.stat-value.text-success {
  @apply text-green-500;
}
</style>
