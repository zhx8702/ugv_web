<template>
  <div class="mobile-dashboard" :class="{ 'force-landscape': !isLandscape }">
    <div class="mobile-cockpit">
      <!-- 左侧面板: 摇杆 + 速度 -->
      <div class="control-panel left-panel">
        <div class="panel-content">
          <!-- 速度档位 -->
          <div class="speed-section">
            <button
              v-for="mode in speedModes"
              :key="mode.value"
              class="speed-btn"
              :class="{ active: controlStore.speedMode === mode.value }"
              @touchstart.prevent="setSpeed(mode.value)"
            >
              <span class="speed-icon">{{ mode.icon }}</span>
            </button>
          </div>

          <!-- 摇杆区域 -->
          <div class="joystick-wrapper">
            <MobileJoystick />
          </div>

          <!-- 电机锁定 -->
          <button
            class="lock-btn"
            :class="{ locked: controlStore.motorLocked }"
            @touchstart.prevent="controlStore.toggleMotorLock"
          >
            <svg v-if="controlStore.motorLocked" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0 1 9.9-1" />
            </svg>
            <span class="lock-label">{{ controlStore.motorLocked ? 'LOCKED' : 'UNLOCK' }}</span>
          </button>
        </div>
      </div>

      <!-- 中间: 视频流 -->
      <div class="video-container">
        <VideoStream />

        <!-- 底部快捷操作 -->
        <div class="action-overlay">
          <button class="action-btn" @touchstart.prevent="captureSnapshot">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </button>
          <button class="action-btn" :class="{ active: isRecording }" @touchstart.prevent="toggleRecording">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <circle v-if="!isRecording" cx="12" cy="12" r="3" fill="currentColor" />
              <rect v-else x="9" y="9" width="6" height="6" fill="currentColor" />
            </svg>
          </button>
          <button
            class="action-btn"
            :class="{ active: controlStore.headLight !== 'off' }"
            @touchstart.prevent="controlStore.cycleHeadLight"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18h6M10 22h4" />
              <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14" />
            </svg>
          </button>
          <button class="action-btn" @touchstart.prevent="handleFullscreen">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
            </svg>
          </button>
        </div>
      </div>

      <!-- 右侧面板: PT控制 + 功能 -->
      <div class="control-panel right-panel">
        <div class="panel-content">
          <!-- PT 控制 -->
          <div class="pt-wrapper">
            <MobilePTControl />
          </div>

          <!-- 底部灯光快捷 -->
          <div class="light-section">
            <button
              class="light-btn"
              :class="{ active: controlStore.baseLight }"
              @touchstart.prevent="controlStore.toggleBaseLight"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="5" />
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
              </svg>
              <span>BASE</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 切换模式 (移到左上角) -->
    <button class="switch-btn" @touchstart.prevent="switchToDesktop">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <path d="M8 21h8M12 17v4" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useDashboard } from '@/composables/useDashboard'
import { useDeviceDetection } from '@/composables/useDeviceDetection'
import MobileJoystick from '@/components/control/MobileJoystick.vue'
import MobilePTControl from '@/components/control/MobilePTControl.vue'
import VideoStream from '@/components/control/VideoStream.vue'

const {
  controlStore,
  isRecording,
  toggleRecording,
  captureSnapshot,
  toggleMobileFullscreen
} = useDashboard()

const { isLandscape, forceDesktop } = useDeviceDetection()

// 速度档位
const speedModes = [
  { value: 'slow', icon: '🐢' },
  { value: 'mid', icon: '🚶' },
  { value: 'fast', icon: '🏃' }
]

function setSpeed(mode) {
  controlStore.setSpeed(mode)
}

function handleFullscreen() {
  toggleMobileFullscreen('.mobile-cockpit')
}

function switchToDesktop() {
  forceDesktop()
}

// 禁用默认触摸行为
function preventDefaultTouch(e) {
  if (e.target.closest('.mobile-dashboard')) {
    e.preventDefault()
  }
}

// Wake Lock
let wakeLock = null

async function requestWakeLock() {
  try {
    if ('wakeLock' in navigator) {
      wakeLock = await navigator.wakeLock.request('screen')
    }
  } catch (err) {
    console.log('Wake Lock not supported:', err)
  }
}

function releaseWakeLock() {
  if (wakeLock) {
    wakeLock.release()
    wakeLock = null
  }
}

onMounted(() => {
  document.addEventListener('touchmove', preventDefaultTouch, { passive: false })
  requestWakeLock()
})

onUnmounted(() => {
  document.removeEventListener('touchmove', preventDefaultTouch)
  releaseWakeLock()
})
</script>

<style scoped>
.mobile-dashboard {
  @apply fixed inset-0 overflow-hidden;
  background: #080810;
  touch-action: none;
  user-select: none;
  -webkit-user-select: none;
  -webkit-touch-callout: none;
}

/* 强制横屏 */
.mobile-dashboard.force-landscape {
  transform: rotate(90deg);
  transform-origin: center center;
  width: 100vh;
  width: 100dvh;
  height: 100vw;
  height: 100dvw;
  position: fixed;
  top: 50%;
  left: 50%;
  margin-top: calc(-50vw);
  margin-left: calc(-50vh);
}

.mobile-cockpit {
  @apply flex h-full w-full;
}

/* ============ 控制面板通用 ============ */
.control-panel {
  width: 150px;
  min-width: 150px;
  flex-shrink: 0;
  background: rgba(0, 10, 20, 0.95);
  border: 1px solid rgba(0, 240, 255, 0.1);
}

.left-panel {
  border-right: 1px solid rgba(0, 240, 255, 0.15);
}

.right-panel {
  border-left: 1px solid rgba(0, 240, 255, 0.15);
}

.panel-content {
  @apply flex flex-col h-full p-2;
  gap: 6px;
}

/* ============ 左侧：速度 + 摇杆 + 锁定 ============ */
.speed-section {
  @apply flex justify-center gap-1;
}

.speed-btn {
  @apply w-10 h-8 flex items-center justify-center rounded;
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.15);
  transition: all 0.15s;
  -webkit-tap-highlight-color: transparent;
}

.speed-btn .speed-icon {
  font-size: 16px;
}

.speed-btn.active {
  background: rgba(0, 240, 255, 0.2);
  border-color: rgba(0, 240, 255, 0.5);
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
}

.joystick-wrapper {
  @apply flex-1 min-h-0;
}

.lock-btn {
  @apply flex items-center justify-center gap-2 py-2 rounded;
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.15);
  color: rgba(255, 255, 255, 0.5);
  transition: all 0.15s;
  -webkit-tap-highlight-color: transparent;
}

.lock-btn svg {
  @apply w-5 h-5;
}

.lock-btn .lock-label {
  @apply text-[9px] font-orbitron tracking-wider;
}

.lock-btn.locked {
  background: rgba(255, 0, 64, 0.15);
  border-color: rgba(255, 0, 64, 0.5);
  color: #ff4040;
  animation: pulse 1.5s ease-in-out infinite;
}

/* ============ 中间：视频 ============ */
.video-container {
  @apply flex-1 relative;
  min-width: 0;
  background: #000;
}

.video-container :deep(.video-stream) {
  @apply h-full w-full;
}

.video-container :deep(.video-container) {
  @apply h-full w-full flex items-center justify-center;
  aspect-ratio: auto;
}

.video-container :deep(.video-container img),
.video-container :deep(.video-container video) {
  @apply max-h-full max-w-full;
  object-fit: contain;
}

/* 操作栏 */
.action-overlay {
  @apply absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5;
  z-index: 10;
}

.action-btn {
  @apply w-9 h-9 flex items-center justify-center rounded-lg;
  @apply text-white/60 transition-all duration-150;
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(4px);
  -webkit-tap-highlight-color: transparent;
}

.action-btn svg {
  @apply w-4 h-4;
}

.action-btn:active {
  @apply text-primary;
  background: rgba(0, 240, 255, 0.2);
  transform: scale(0.92);
}

.action-btn.active {
  @apply text-secondary border-secondary;
  background: rgba(0, 255, 136, 0.15);
}

/* ============ 右侧：PT控制 + 灯光 ============ */
.pt-wrapper {
  @apply flex-1 min-h-0;
}

.light-section {
  @apply flex justify-center;
}

.light-btn {
  @apply flex flex-col items-center gap-1 px-4 py-2 rounded;
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.15);
  color: rgba(255, 255, 255, 0.4);
  transition: all 0.15s;
  -webkit-tap-highlight-color: transparent;
}

.light-btn svg {
  @apply w-5 h-5;
}

.light-btn span {
  @apply text-[8px] font-orbitron tracking-wider;
}

.light-btn.active {
  background: rgba(255, 200, 0, 0.15);
  border-color: rgba(255, 200, 0, 0.5);
  color: #ffc800;
}

/* ============ 切换按钮 ============ */
.switch-btn {
  @apply absolute top-1 left-1 w-7 h-7 flex items-center justify-center rounded;
  @apply text-white/30 transition-all;
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 20;
  -webkit-tap-highlight-color: transparent;
}

.switch-btn svg {
  @apply w-3.5 h-3.5;
}

.switch-btn:active {
  @apply text-primary;
  background: rgba(0, 240, 255, 0.2);
}

/* ============ 动画 ============ */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* ============ 小屏幕适配 ============ */
@media (max-height: 380px) {
  .control-panel {
    width: 130px;
    min-width: 130px;
  }

  .panel-content {
    padding: 4px;
    gap: 4px;
  }

  .speed-btn {
    @apply w-9 h-7;
  }

  .speed-btn .speed-icon {
    font-size: 14px;
  }

  .action-btn {
    @apply w-9 h-9;
  }

  .action-btn svg {
    @apply w-4 h-4;
  }

  .lock-btn svg {
    @apply w-4 h-4;
  }

  .lock-btn .lock-label {
    @apply text-[8px];
  }

  .light-btn svg {
    @apply w-4 h-4;
  }
}

/* 强制横屏下的适配 */
.force-landscape .control-panel {
  width: 140px;
  min-width: 140px;
}
</style>
