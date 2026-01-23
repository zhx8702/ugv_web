<template>
  <div class="dashboard" :class="{ 'mobile-mode': isMobile, 'landscape-mode': isLandscape }">
    <!-- Mobile Layout (auto-rotates in portrait mode) -->
    <div v-if="isMobile" class="mobile-cockpit" :class="{ 'force-landscape': !isLandscape }">
      <!-- Left: Movement Control -->
      <div class="mobile-control-panel left-panel">
        <MobileJoystick />
      </div>

      <!-- Center: Video with overlay controls -->
      <div class="mobile-video-container">
        <VideoStream />
        <!-- Top status bar -->
        <div class="mobile-status-bar">
          <span class="status-item">
            <span class="status-label">FPS</span>
            <span class="status-value">{{ systemStore.fps.toFixed(0) }}</span>
          </span>
          <span class="status-item">
            <span class="status-label">LAT</span>
            <span class="status-value">{{ latency }}ms</span>
          </span>
          <span class="status-item">
            <span class="status-label">VOLT</span>
            <span class="status-value">{{ systemStore.voltage.toFixed(1) }}V</span>
          </span>
        </div>
        <!-- Bottom action bar -->
        <div class="mobile-action-bar">
          <button class="mobile-action-btn" @click="captureSnapshot" title="Snapshot">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </button>
          <button class="mobile-action-btn" @click="toggleMobileFullscreen" title="Fullscreen">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
            </svg>
          </button>
          <button
            class="mobile-action-btn"
            :class="{ active: controlStore.motorLocked }"
            @click="controlStore.toggleMotorLock"
            title="Motor Lock"
          >
            <svg v-if="controlStore.motorLocked" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0 1 9.9-1" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Right: PT Control -->
      <div class="mobile-control-panel right-panel">
        <MobilePTControl />
      </div>
    </div>

    <!-- Desktop Layout (unchanged) -->
    <template v-if="!isMobile">
    <!-- Page Header -->
    <div class="dashboard-header">
      <div class="header-left">
        <div class="header-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="3" y="3" width="7" height="9" rx="1" />
            <rect x="14" y="3" width="7" height="5" rx="1" />
            <rect x="14" y="12" width="7" height="9" rx="1" />
            <rect x="3" y="16" width="7" height="5" rx="1" />
          </svg>
        </div>
        <div class="header-text">
          <h1 class="header-title">COMMAND CENTER</h1>
          <div class="header-subtitle">
            <span class="prefix">//</span>
            REAL-TIME TACTICAL OVERVIEW
            <span class="timestamp">{{ currentTime }}</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <div class="quick-stat">
          <span class="stat-label">FPS</span>
          <span class="stat-value">{{ systemStore.fps.toFixed(1) }}</span>
        </div>
        <div class="quick-stat">
          <span class="stat-label">LATENCY</span>
          <span class="stat-value">{{ latency }}ms</span>
        </div>
      </div>
    </div>

    <!-- Main Cockpit Layout: Left Control + Video + Right Control -->
    <div class="cockpit-layout">
      <!-- Left: Movement Control -->
      <div class="panel control-panel side-control left-control">
        <div class="panel-header compact">
          <div class="panel-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v8M8 12h8" />
            </svg>
          </div>
          <h3 class="panel-title">MOVEMENT</h3>
        </div>
        <div class="panel-content">
          <VirtualJoystick />
        </div>
      </div>

      <!-- Center: Video Panel -->
      <div class="panel video-panel">
        <div class="panel-header">
          <div class="panel-icon pulse-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 7l-7 5 7 5V7z" />
              <rect x="1" y="5" width="15" height="14" rx="2" />
            </svg>
          </div>
          <h2 class="panel-title">LIVE FEED</h2>
          <div class="panel-badge recording" v-if="isRecording">
            <span class="rec-dot"></span>
            REC
          </div>
          <div class="panel-actions">
            <button class="action-btn" title="Snapshot" @click="captureSnapshot">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <path d="M21 15l-5-5L5 21" />
              </svg>
            </button>
            <button class="action-btn" title="Fullscreen" @click="toggleFullscreen">
              <svg v-if="!isFullscreen" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3" />
              </svg>
            </button>
          </div>
        </div>
        <div class="panel-content">
          <VideoStream />
        </div>
      </div>

      <!-- Right: Pan-Tilt Control -->
      <div class="panel control-panel side-control right-control">
        <div class="panel-header compact">
          <div class="panel-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
            </svg>
          </div>
          <h3 class="panel-title">PAN-TILT</h3>
        </div>
        <div class="panel-content">
          <PTControl />
        </div>
      </div>
    </div>

    <!-- Secondary Controls Row: (Throttle + Lighting) | System | AI Detection -->
    <div class="secondary-grid">
      <!-- Combined: Throttle + Lighting -->
      <div class="panel control-panel combined-panel">
        <!-- Throttle Section -->
        <div class="combined-section">
          <div class="section-header">
            <div class="panel-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
              </svg>
            </div>
            <h3 class="section-title">THROTTLE</h3>
            <!-- Motor Lock Button -->
            <button
              class="motor-lock-btn"
              :class="{ locked: controlStore.motorLocked }"
              @click="controlStore.toggleMotorLock"
              :title="controlStore.motorLocked ? 'Unlock Motors' : 'Lock Motors'"
            >
              <svg v-if="controlStore.motorLocked" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 9.9-1" />
              </svg>
            </button>
          </div>
          <div class="section-content">
            <SpeedControl />
          </div>
        </div>
        <!-- Divider -->
        <div class="section-divider"></div>
        <!-- Lighting Section -->
        <div class="combined-section">
          <div class="section-header">
            <div class="panel-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18h6" />
                <path d="M10 22h4" />
                <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14" />
              </svg>
            </div>
            <h3 class="section-title">LIGHTING</h3>
          </div>
          <div class="section-content">
            <LightingPanel />
          </div>
        </div>
      </div>

      <!-- System Monitor -->
      <div class="panel monitor-panel">
        <div class="panel-header compact">
          <div class="panel-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <h3 class="panel-title">SYSTEM</h3>
          <div class="panel-badge online">OK</div>
        </div>
        <div class="panel-content compact">
          <SystemMonitor />
        </div>
      </div>

      <!-- AI Detection -->
      <div class="panel monitor-panel ai-detection-panel">
        <div class="panel-header compact">
          <div class="panel-icon ai-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a10 10 0 1 0 10 10" />
              <path d="M12 2v10l7-7" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </div>
          <h3 class="panel-title">AI DETECTION</h3>
          <div class="panel-badge ai">ON</div>
        </div>
        <div class="panel-content compact ai-detection-content">
          <DetectionPanel />
        </div>
      </div>
    </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useSystemStore } from '@/stores/system'
import { useControlStore } from '@/stores/control'
import { useWebSocket } from '@/composables/useWebSocket'
import VirtualJoystick from '@/components/control/VirtualJoystick.vue'
import PTControl from '@/components/control/PTControl.vue'
import SpeedControl from '@/components/control/SpeedControl.vue'
import VideoStream from '@/components/control/VideoStream.vue'
import DetectionPanel from '@/components/control/DetectionPanel.vue'
import MobileJoystick from '@/components/control/MobileJoystick.vue'
import MobilePTControl from '@/components/control/MobilePTControl.vue'
import SystemMonitor from '@/components/monitoring/SystemMonitor.vue'
import LightingPanel from '@/components/control/LightingPanel.vue'

const systemStore = useSystemStore()
const controlStore = useControlStore()
const { latency } = useWebSocket()

const currentTime = ref('')
const isRecording = ref(false)
const isFullscreen = ref(false)

// Mobile detection
const screenWidth = ref(window.innerWidth)
const screenHeight = ref(window.innerHeight)

const isMobile = computed(() => {
  // Detect mobile by touch capability and screen size
  const hasTouchScreen = 'ontouchstart' in window || navigator.maxTouchPoints > 0
  const isSmallScreen = Math.min(screenWidth.value, screenHeight.value) < 768
  return hasTouchScreen && isSmallScreen
})

const isLandscape = computed(() => {
  return screenWidth.value > screenHeight.value
})

let timeInterval = null

// Snapshot function
function captureSnapshot() {
  controlStore.capturePhoto()
}

// Fullscreen function (Desktop)
function toggleFullscreen() {
  const panel = document.querySelector('.video-panel')
  if (!panel) return

  if (!document.fullscreenElement) {
    panel.requestFullscreen().then(() => {
      isFullscreen.value = true
    }).catch(err => {
      console.error('Fullscreen error:', err)
    })
  } else {
    document.exitFullscreen().then(() => {
      isFullscreen.value = false
    })
  }
}

// Fullscreen function (Mobile) - fullscreen the entire cockpit
function toggleMobileFullscreen() {
  const cockpit = document.querySelector('.mobile-cockpit')
  if (!cockpit) return

  if (!document.fullscreenElement) {
    cockpit.requestFullscreen().catch(err => {
      console.error('Mobile fullscreen error:', err)
    })
  } else {
    document.exitFullscreen()
  }
}

// Handle screen resize
function handleResize() {
  screenWidth.value = window.innerWidth
  screenHeight.value = window.innerHeight
}

// Listen for fullscreen changes
function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard {
  @apply p-6 min-h-screen;
  animation: fadeIn 0.5s ease-out;
}

/* Dashboard Header */
.dashboard-header {
  @apply flex items-center justify-between mb-6 pb-4;
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.header-left {
  @apply flex items-center gap-4;
}

.header-icon {
  @apply w-10 h-10 text-primary;
  filter: drop-shadow(0 0 8px rgba(0, 240, 255, 0.5));
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
  filter: drop-shadow(0 0 15px rgba(0, 240, 255, 0.3));
}

.header-subtitle {
  @apply text-xs font-mono text-dark-text-tertiary flex items-center gap-3;
}

.header-subtitle .prefix {
  @apply text-primary;
}

.timestamp {
  @apply px-2 py-0.5 bg-dark-bg-tertiary/50 text-primary font-mono;
  clip-path: polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px);
}

.header-right {
  @apply flex items-center gap-6;
}

.quick-stat {
  @apply flex flex-col items-center;
}

.stat-label {
  @apply text-[10px] font-orbitron text-dark-text-tertiary tracking-wider;
}

.stat-value {
  @apply text-lg font-mono font-bold text-primary;
  text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
}

/* Cockpit Layout: 3-column grid */
.cockpit-layout {
  @apply grid gap-4 mb-4;
  grid-template-columns: 1fr;
}

@media (min-width: 1024px) {
  .cockpit-layout {
    grid-template-columns: 280px 1fr 280px;
    align-items: stretch;
  }
}

@media (min-width: 1280px) {
  .cockpit-layout {
    grid-template-columns: 320px 1fr 320px;
  }
}

/* Side Control Panels */
.side-control {
  @apply flex flex-col;
}

.side-control .panel-content {
  @apply flex-1 flex items-center justify-center p-4;
  min-height: 280px;
}

@media (max-width: 1023px) {
  .cockpit-layout {
    grid-template-columns: 1fr 1fr;
  }

  .cockpit-layout .video-panel {
    grid-column: 1 / -1;
    order: -1;
  }
}

/* Video Panel */
.video-panel {
  @apply flex flex-col;
}

.video-panel .panel-content {
  @apply p-0 flex-1;
  min-height: 400px;
}

/* Panel Base Styles */
.panel {
  @apply relative overflow-hidden;
  background: linear-gradient(135deg, rgba(10, 22, 40, 0.9) 0%, rgba(3, 7, 18, 0.95) 100%);
  border: 1px solid rgba(0, 240, 255, 0.15);
  clip-path: polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px);
  transition: all 0.3s ease;
}

.panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 240, 255, 0.5), transparent);
}

.panel:hover {
  border-color: rgba(0, 240, 255, 0.3);
  box-shadow: 0 0 30px rgba(0, 240, 255, 0.1), inset 0 0 30px rgba(0, 240, 255, 0.02);
}

.panel-header {
  @apply flex items-center gap-3 px-5 py-3;
  background: rgba(0, 240, 255, 0.03);
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.panel-icon {
  @apply w-5 h-5 text-primary;
}

.pulse-icon {
  animation: pulse 2s ease-in-out infinite;
}

.ai-icon {
  animation: spin 4s linear infinite;
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

.panel-badge.recording {
  @apply bg-danger/20 text-danger border border-danger/30 flex items-center gap-1.5;
}

.panel-badge.ai {
  @apply bg-primary/20 text-primary border border-primary/30;
}

.rec-dot {
  @apply w-2 h-2 bg-danger rounded-full;
  animation: pulse 1s ease-in-out infinite;
}

.panel-actions {
  @apply flex items-center gap-2;
}

.action-btn {
  @apply w-8 h-8 flex items-center justify-center text-dark-text-tertiary rounded;
  @apply transition-all duration-200 hover:text-primary hover:bg-primary/10;
}

.action-btn svg {
  @apply w-4 h-4;
}

.panel-content {
  @apply p-5;
}

/* Secondary Grid: 3 columns */
.secondary-grid {
  @apply grid gap-4 mb-4;
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .secondary-grid {
    grid-template-columns: repeat(3, 1fr);
    align-items: stretch;
  }

  .secondary-grid > .panel {
    @apply flex flex-col;
    height:650px;
  }

  .secondary-grid > .panel > .panel-content {
    @apply flex-1 overflow-y-auto;
  }
}

.control-panel .panel-content {
  @apply p-4;
}

/* Combined Panel: Throttle + Lighting in one column */
.combined-panel {
  @apply flex flex-col;
}

.combined-section {
  @apply flex-1;
}

.section-header {
  @apply flex items-center gap-3 px-4 py-2;
  background: rgba(0, 240, 255, 0.03);
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.section-title {
  @apply flex-1 text-xs font-orbitron font-semibold tracking-wider text-dark-text-primary uppercase;
}

.section-content {
  @apply p-3;
}

.section-divider {
  @apply mx-3;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 240, 255, 0.2), transparent);
}

/* AI Detection Panel scrollbar styling */
.ai-detection-content {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 240, 255, 0.3) transparent;
}

.ai-detection-content::-webkit-scrollbar {
  width: 4px;
}

.ai-detection-content::-webkit-scrollbar-track {
  background: transparent;
}

.ai-detection-content::-webkit-scrollbar-thumb {
  background: rgba(0, 240, 255, 0.3);
  border-radius: 2px;
}

/* Compact panel header */
.panel-header.compact {
  @apply px-4 py-2;
}

.panel-content.compact {
  @apply p-3;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Motor Lock Button */
.motor-lock-btn {
  @apply w-8 h-8 flex items-center justify-center rounded;
  @apply text-dark-text-tertiary border border-dark-border;
  @apply transition-all duration-200;
}

.motor-lock-btn svg {
  @apply w-4 h-4;
}

.motor-lock-btn:hover {
  @apply text-primary border-primary/50;
}

.motor-lock-btn.locked {
  @apply text-danger border-danger bg-danger/10;
  animation: pulse 1.5s ease-in-out infinite;
}

/* ========================================
   MOBILE LAYOUT STYLES
   ======================================== */

/* Mobile mode base - prevent scrolling and fullscreen */
.dashboard.mobile-mode {
  @apply p-0 overflow-hidden fixed inset-0;
  height: 100vh;
  height: 100dvh;
  width: 100vw;
  width: 100dvw;
  touch-action: none;
  overscroll-behavior: none;
  -webkit-overflow-scrolling: none;
}

/* Mobile Cockpit Layout */
.mobile-cockpit {
  @apply flex items-stretch;
  height: 100%;
  width: 100%;
  background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 100%);
  touch-action: manipulation;
  user-select: none;
  -webkit-user-select: none;
}

/* Force landscape mode when device is in portrait */
.mobile-cockpit.force-landscape {
  /* Rotate the entire cockpit 90 degrees */
  transform: rotate(90deg);
  transform-origin: center center;
  /* Swap width and height - use viewport units */
  width: 100vh;
  width: 100dvh;
  height: 100vw;
  height: 100dvw;
  /* Center the rotated element */
  position: fixed;
  top: 50%;
  left: 50%;
  margin-top: calc(-50vw);
  margin-left: calc(-50vh);
  overflow: hidden;
}

/* Mobile Control Panels (Left & Right) */
.mobile-control-panel {
  @apply flex items-center justify-center p-2;
  width: 140px;
  min-width: 140px;
  flex-shrink: 0;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(0, 240, 255, 0.15);
}

/* Adjust panel sizes in forced landscape (portrait device) */
.force-landscape .mobile-control-panel {
  width: 120px;
  min-width: 120px;
}

.mobile-control-panel.left-panel {
  border-right: 1px solid rgba(0, 240, 255, 0.2);
}

.mobile-control-panel.right-panel {
  border-left: 1px solid rgba(0, 240, 255, 0.2);
}

/* Mobile Video Container (Center) */
.mobile-video-container {
  @apply flex-1 relative;
  min-width: 0; /* Allow flex shrinking */
}

.mobile-video-container :deep(.video-stream) {
  @apply h-full;
}

.mobile-video-container :deep(.video-container) {
  @apply h-full;
  aspect-ratio: auto;
}

/* Mobile Status Bar (Top overlay on video) */
.mobile-status-bar {
  @apply absolute top-0 left-0 right-0 flex items-center justify-center gap-4 py-1 px-3;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.7) 0%, transparent 100%);
  z-index: 20;
}

.status-item {
  @apply flex items-center gap-1;
}

.status-label {
  @apply text-[8px] font-orbitron tracking-wider text-dark-text-tertiary;
}

.status-value {
  @apply text-[10px] font-mono font-bold text-primary;
  text-shadow: 0 0 6px rgba(0, 240, 255, 0.5);
}

/* Mobile Action Bar (Bottom overlay on video) */
.mobile-action-bar {
  @apply absolute bottom-2 left-1/2 -translate-x-1/2 flex items-center gap-2;
  z-index: 20;
}

.mobile-action-btn {
  @apply w-10 h-10 flex items-center justify-center rounded-lg;
  @apply text-dark-text-secondary transition-all duration-200;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(0, 240, 255, 0.3);
  backdrop-filter: blur(4px);
  -webkit-tap-highlight-color: transparent;
}

.mobile-action-btn svg {
  @apply w-5 h-5;
}

.mobile-action-btn:active {
  @apply text-primary;
  background: rgba(0, 240, 255, 0.2);
  transform: scale(0.95);
}

.mobile-action-btn.active {
  @apply text-danger border-danger;
  background: rgba(255, 0, 64, 0.2);
}

/* Very small screens (iPhone SE landscape, etc.) */
@media (max-height: 400px) and (orientation: landscape) {
  .mobile-control-panel {
    width: 100px;
    min-width: 100px;
    padding: 4px;
  }

  .mobile-status-bar {
    padding: 2px 8px;
  }

  .mobile-action-btn {
    @apply w-8 h-8;
  }

  .mobile-action-btn svg {
    @apply w-4 h-4;
  }
}

/* Hide desktop-only elements in mobile mode */
.mobile-mode .dashboard-header,
.mobile-mode .secondary-grid {
  @apply hidden;
}

/* Mobile fullscreen adjustments */
.mobile-cockpit:fullscreen {
  background: #000;
}

.mobile-cockpit:fullscreen .mobile-control-panel {
  background: rgba(0, 0, 0, 0.6);
}
</style>
