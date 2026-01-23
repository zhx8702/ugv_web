<template>
  <div class="mobile-status-bar">
    <div class="status-left">
      <span class="status-item">
        <span class="status-label">FPS</span>
        <span class="status-value">{{ fps.toFixed(0) }}</span>
      </span>
      <span class="status-item">
        <span class="status-label">LAT</span>
        <span class="status-value">{{ latency }}ms</span>
      </span>
      <span class="status-item">
        <span class="status-label">VOLT</span>
        <span class="status-value" :class="voltageClass">{{ voltage.toFixed(1) }}V</span>
      </span>
    </div>

    <div class="status-right">
      <span class="status-item">
        <span class="connection-indicator" :class="{ connected }"></span>
      </span>
      <span class="status-item" v-if="motorLocked">
        <svg class="lock-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="11" width="18" height="11" rx="2" />
          <path d="M7 11V7a5 5 0 0 1 10 0v4" />
        </svg>
      </span>
      <span class="status-item time">
        {{ currentTime }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  fps: {
    type: Number,
    default: 0
  },
  latency: {
    type: Number,
    default: 0
  },
  voltage: {
    type: Number,
    default: 0
  },
  connected: {
    type: Boolean,
    default: false
  },
  motorLocked: {
    type: Boolean,
    default: false
  },
  currentTime: {
    type: String,
    default: '--:--:--'
  }
})

const voltageClass = computed(() => {
  if (props.voltage < 6.5) return 'danger'
  if (props.voltage < 7.0) return 'warning'
  return ''
})
</script>

<style scoped>
.mobile-status-bar {
  @apply absolute top-0 left-0 right-0 flex items-center justify-between py-1 px-3;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.4) 70%, transparent 100%);
  z-index: 20;
  pointer-events: none;
}

.status-left,
.status-right {
  @apply flex items-center gap-3;
}

.status-item {
  @apply flex items-center gap-1;
}

.status-label {
  @apply text-[8px] font-orbitron tracking-wider text-dark-text-tertiary uppercase;
}

.status-value {
  @apply text-[11px] font-mono font-bold text-primary;
  text-shadow: 0 0 6px rgba(0, 240, 255, 0.5);
}

.status-value.warning {
  @apply text-accent;
  text-shadow: 0 0 6px rgba(255, 160, 0, 0.5);
}

.status-value.danger {
  @apply text-danger;
  text-shadow: 0 0 6px rgba(255, 0, 64, 0.5);
  animation: blink 1s ease-in-out infinite;
}

.connection-indicator {
  @apply w-2 h-2 rounded-full bg-danger;
  box-shadow: 0 0 6px rgba(255, 0, 64, 0.5);
}

.connection-indicator.connected {
  @apply bg-secondary;
  box-shadow: 0 0 6px rgba(0, 255, 136, 0.5);
}

.lock-icon {
  @apply w-3.5 h-3.5 text-danger;
  animation: pulse 1.5s ease-in-out infinite;
}

.time {
  @apply text-[10px] font-mono text-primary/80;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
