<template>
  <div class="mobile-action-bar">
    <!-- 拍照按钮 -->
    <button
      class="action-btn"
      @touchstart.prevent="onSnapshot"
      title="Snapshot"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    </button>

    <!-- 录像按钮 -->
    <button
      class="action-btn"
      :class="{ active: isRecording }"
      @touchstart.prevent="onToggleRecording"
      title="Recording"
    >
      <svg v-if="!isRecording" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" />
        <circle cx="12" cy="12" r="3" fill="currentColor" />
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" />
        <rect x="9" y="9" width="6" height="6" fill="currentColor" />
      </svg>
      <span v-if="isRecording" class="rec-indicator"></span>
    </button>

    <!-- 灯光按钮 -->
    <button
      class="action-btn"
      :class="{ active: lightOn }"
      @touchstart.prevent="onToggleLight"
      title="Light"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 18h6" />
        <path d="M10 22h4" />
        <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14" />
      </svg>
    </button>

    <!-- 电机锁定按钮 -->
    <button
      class="action-btn"
      :class="{ locked: motorLocked }"
      @touchstart.prevent="onToggleMotorLock"
      title="Motor Lock"
    >
      <svg v-if="motorLocked" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="11" width="18" height="11" rx="2" />
        <path d="M7 11V7a5 5 0 0 1 10 0v4" />
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="11" width="18" height="11" rx="2" />
        <path d="M7 11V7a5 5 0 0 1 9.9-1" />
      </svg>
    </button>

    <!-- 全屏按钮 -->
    <button
      class="action-btn"
      @touchstart.prevent="onToggleFullscreen"
      title="Fullscreen"
    >
      <svg v-if="!isFullscreen" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3" />
      </svg>
    </button>
  </div>
</template>

<script setup>
defineProps({
  isRecording: {
    type: Boolean,
    default: false
  },
  lightOn: {
    type: Boolean,
    default: false
  },
  motorLocked: {
    type: Boolean,
    default: false
  },
  isFullscreen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'snapshot',
  'toggle-recording',
  'toggle-light',
  'toggle-motor-lock',
  'toggle-fullscreen'
])

function onSnapshot() {
  emit('snapshot')
}

function onToggleRecording() {
  emit('toggle-recording')
}

function onToggleLight() {
  emit('toggle-light')
}

function onToggleMotorLock() {
  emit('toggle-motor-lock')
}

function onToggleFullscreen() {
  emit('toggle-fullscreen')
}
</script>

<style scoped>
.mobile-action-bar {
  @apply absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-2;
  z-index: 20;
}

.action-btn {
  @apply w-11 h-11 flex items-center justify-center rounded-xl relative;
  @apply text-dark-text-secondary transition-all duration-150;
  background: rgba(0, 0, 0, 0.7);
  border: 1px solid rgba(0, 240, 255, 0.3);
  backdrop-filter: blur(8px);
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}

.action-btn svg {
  @apply w-5 h-5;
}

.action-btn:active {
  @apply text-primary;
  background: rgba(0, 240, 255, 0.25);
  transform: scale(0.92);
  border-color: rgba(0, 240, 255, 0.6);
}

.action-btn.active {
  @apply text-secondary border-secondary;
  background: rgba(0, 255, 136, 0.2);
}

.action-btn.locked {
  @apply text-danger border-danger;
  background: rgba(255, 0, 64, 0.2);
  animation: pulse 1.5s ease-in-out infinite;
}

.rec-indicator {
  @apply absolute -top-1 -right-1 w-2 h-2 bg-danger rounded-full;
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* 小屏幕适配 */
@media (max-height: 400px) {
  .action-btn {
    @apply w-9 h-9;
  }

  .action-btn svg {
    @apply w-4 h-4;
  }

  .mobile-action-bar {
    @apply gap-1.5 bottom-2;
  }
}
</style>
