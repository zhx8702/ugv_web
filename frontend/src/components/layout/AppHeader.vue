<template>
  <header class="header">
    <!-- Animated top border -->
    <div class="header-border"></div>

    <div class="header-content">
      <!-- Logo Section -->
      <div class="logo-section">
        <div class="logo-container">
          <div class="logo-icon">
            <svg viewBox="0 0 40 40" class="w-full h-full">
              <!-- Hexagon background -->
              <polygon
                points="20,2 37,11 37,29 20,38 3,29 3,11"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                class="text-primary"
              />
              <!-- Inner tech pattern -->
              <circle cx="20" cy="20" r="8" fill="none" stroke="currentColor" stroke-width="1" class="text-primary/50" />
              <circle cx="20" cy="20" r="3" fill="currentColor" class="text-primary animate-pulse" />
              <!-- Corner accents -->
              <line x1="20" y1="2" x2="20" y2="8" stroke="currentColor" stroke-width="1" class="text-primary/70" />
              <line x1="20" y1="32" x2="20" y2="38" stroke="currentColor" stroke-width="1" class="text-primary/70" />
            </svg>
          </div>
          <div class="logo-text">
            <h1 class="logo-title">UGV ROVER</h1>
            <div class="logo-subtitle">
              <span class="subtitle-prefix">//</span>
              TACTICAL CONTROL
              <span class="status-indicator">
                <span :class="['status-dot', connected ? 'status-dot-online' : 'status-dot-offline']"></span>
                <span :class="connected ? 'text-secondary' : 'text-danger'">
                  {{ connected ? 'LINKED' : 'OFFLINE' }}
                </span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- System Status -->
      <div class="status-section">
        <div class="status-item" :class="batteryStatusClass">
          <div class="status-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
              <rect x="2" y="7" width="18" height="10" rx="2" />
              <line x1="22" y1="11" x2="22" y2="13" />
              <rect :x="4" :y="9" :width="batteryWidth" height="6" fill="currentColor" rx="1" />
            </svg>
          </div>
          <div class="status-data">
            <span class="status-value">{{ voltage.toFixed(1) }}</span>
            <span class="status-unit">V</span>
          </div>
        </div>

        <div class="status-divider"></div>

        <div class="status-item" :class="tempStatusClass">
          <div class="status-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
              <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z" />
            </svg>
          </div>
          <div class="status-data">
            <span class="status-value">{{ temperature.toFixed(1) }}</span>
            <span class="status-unit">°C</span>
          </div>
        </div>

        <div class="status-divider"></div>

        <div class="status-item status-good">
          <div class="status-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
              <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </div>
          <div class="status-data">
            <span class="status-value">{{ rssi }}</span>
            <span class="status-unit">dBm</span>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="nav-section">
        <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
          <div class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="9" rx="1" />
              <rect x="14" y="3" width="7" height="5" rx="1" />
              <rect x="14" y="12" width="7" height="9" rx="1" />
              <rect x="3" y="16" width="7" height="5" rx="1" />
            </svg>
          </div>
          <span class="nav-label">DASHBOARD</span>
        </router-link>

        <router-link to="/voice" class="nav-item" :class="{ active: $route.path === '/voice' }">
          <div class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
          </div>
          <span class="nav-label">VOICE</span>
        </router-link>

        <router-link to="/photos" class="nav-item" :class="{ active: $route.path === '/photos' }">
          <div class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <path d="M21 15l-5-5L5 21" />
            </svg>
          </div>
          <span class="nav-label">PHOTOS</span>
        </router-link>

        <router-link to="/videos" class="nav-item" :class="{ active: $route.path === '/videos' }">
          <div class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="23 7 16 12 23 17 23 7" />
              <rect x="1" y="5" width="15" height="14" rx="2" />
            </svg>
          </div>
          <span class="nav-label">VIDEOS</span>
        </router-link>

        <router-link to="/slam" class="nav-item" :class="{ active: $route.path === '/slam' }">
          <div class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
              <circle cx="12" cy="10" r="3" />
            </svg>
          </div>
          <span class="nav-label">SLAM</span>
        </router-link>

        <router-link to="/tracking" class="nav-item" :class="{ active: $route.path === '/tracking' }">
          <div class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </div>
          <span class="nav-label">TRACK</span>
        </router-link>

        <router-link to="/settings" class="nav-item" :class="{ active: $route.path === '/settings' }">
          <div class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
          </div>
          <span class="nav-label">CONFIG</span>
        </router-link>
      </nav>
    </div>

    <!-- Animated bottom border -->
    <div class="header-border-bottom"></div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useSystemStore } from '@/stores/system'
import { useWebSocket } from '@/composables/useWebSocket'

const systemStore = useSystemStore()
const { voltage, temperature, rssi, systemStatus, batteryStatus } = storeToRefs(systemStore)
const { connected } = useWebSocket()

const batteryWidth = computed(() => {
  const minV = 6.0
  const maxV = 8.4
  const percent = Math.max(0, Math.min(100, ((voltage.value - minV) / (maxV - minV)) * 100))
  return (percent / 100) * 14
})

const batteryStatusClass = computed(() => {
  if (batteryStatus.value === 'critical') return 'status-danger'
  if (batteryStatus.value === 'warning') return 'status-warning'
  return 'status-good'
})

const tempStatusClass = computed(() => {
  if (systemStatus.value === 'critical') return 'status-danger'
  if (systemStatus.value === 'warning') return 'status-warning'
  return 'status-good'
})
</script>

<style scoped>
.header {
  @apply sticky top-0 z-50;
  background: linear-gradient(180deg, rgba(3, 7, 18, 0.98) 0%, rgba(10, 22, 40, 0.95) 100%);
  backdrop-filter: blur(12px);
}

.header-border {
  @apply h-[2px] w-full;
  background: linear-gradient(90deg,
    transparent 0%,
    var(--cyber-cyan) 20%,
    var(--cyber-cyan) 80%,
    transparent 100%
  );
  opacity: 0.8;
}

.header-border-bottom {
  @apply h-px w-full;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(0, 240, 255, 0.3) 50%,
    transparent 100%
  );
}

.header-content {
  @apply container mx-auto px-6 h-16 flex items-center justify-between;
}

/* Logo Section */
.logo-section {
  @apply flex items-center;
}

.logo-container {
  @apply flex items-center gap-3;
}

.logo-icon {
  @apply w-10 h-10 relative;
  filter: drop-shadow(0 0 8px rgba(0, 240, 255, 0.5));
}

.logo-text {
  @apply flex flex-col;
}

.logo-title {
  @apply text-lg font-orbitron font-bold tracking-widest text-dark-text-primary;
  text-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
}

.logo-subtitle {
  @apply text-[10px] font-mono tracking-wider text-dark-text-tertiary flex items-center gap-2;
}

.subtitle-prefix {
  @apply text-primary;
}

.status-indicator {
  @apply flex items-center gap-1.5 ml-2 px-2 py-0.5;
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.1);
  clip-path: polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px);
}

/* Status Section */
.status-section {
  @apply hidden md:flex items-center gap-4 px-4 py-2;
  background: rgba(0, 240, 255, 0.03);
  border: 1px solid rgba(0, 240, 255, 0.1);
  clip-path: polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px);
}

.status-item {
  @apply flex items-center gap-2 px-3 py-1;
}

.status-icon {
  @apply w-4 h-4 opacity-70;
}

.status-data {
  @apply font-mono text-sm;
}

.status-value {
  @apply font-bold;
}

.status-unit {
  @apply text-xs opacity-60 ml-0.5;
}

.status-divider {
  @apply w-px h-6 bg-dark-border;
}

.status-good {
  @apply text-secondary;
}

.status-good .status-icon {
  filter: drop-shadow(0 0 4px rgba(0, 255, 136, 0.5));
}

.status-warning {
  @apply text-warning;
}

.status-warning .status-icon {
  filter: drop-shadow(0 0 4px rgba(255, 255, 0, 0.5));
  animation: pulse 1s infinite;
}

.status-danger {
  @apply text-danger;
}

.status-danger .status-icon {
  filter: drop-shadow(0 0 4px rgba(255, 0, 64, 0.5));
  animation: pulse 0.5s infinite;
}

/* Navigation Section */
.nav-section {
  @apply flex items-center gap-1;
}

.nav-item {
  @apply relative flex flex-col items-center gap-1 px-4 py-2;
  @apply text-dark-text-tertiary transition-all duration-200;
}

.nav-item::before {
  content: '';
  @apply absolute inset-0 opacity-0 transition-opacity duration-200;
  background: linear-gradient(180deg, rgba(0, 240, 255, 0.1) 0%, transparent 100%);
}

.nav-item:hover {
  @apply text-primary;
}

.nav-item:hover::before {
  @apply opacity-100;
}

.nav-item.active {
  @apply text-primary;
}

.nav-item.active::before {
  @apply opacity-100;
}

.nav-item.active::after {
  content: '';
  @apply absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-[2px];
  background: var(--cyber-cyan);
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.8);
}

.nav-icon {
  @apply w-5 h-5;
}

.nav-label {
  @apply text-[10px] font-orbitron tracking-wider;
}

/* Status Dot */
.status-dot {
  @apply w-1.5 h-1.5 rounded-full;
}

.status-dot-online {
  @apply bg-secondary;
  box-shadow: 0 0 6px rgba(0, 255, 136, 0.8);
}

.status-dot-offline {
  @apply bg-danger;
  box-shadow: 0 0 6px rgba(255, 0, 64, 0.8);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
