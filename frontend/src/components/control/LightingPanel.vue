<template>
  <div class="lighting-controls">
    <!-- Head Light -->
    <div class="light-group">
      <div class="light-label">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="light-icon">
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
        <span>HEAD LIGHT</span>
      </div>
      <div class="light-modes">
        <button
          v-for="mode in headModes"
          :key="mode.value"
          class="mode-btn"
          :class="{ active: headLight === mode.value }"
          @click="setHeadLight(mode.value)"
        >
          {{ mode.label }}
        </button>
      </div>
    </div>

    <!-- Base Light -->
    <div class="light-group">
      <div class="light-label">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="light-icon">
          <path d="M9 18h6" />
          <path d="M10 22h4" />
          <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14" />
        </svg>
        <span>BASE LIGHT</span>
      </div>
      <div class="light-toggle">
        <button
          class="toggle-btn"
          :class="{ active: baseLight }"
          @click="toggleBaseLight"
        >
          <span class="toggle-indicator"></span>
          <span class="toggle-text">{{ baseLight ? 'ON' : 'OFF' }}</span>
        </button>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions">
      <button class="action-btn all-on" @click="setAllLights(true)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
        </svg>
        ALL ON
      </button>
      <button class="action-btn all-off" @click="setAllLights(false)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
        </svg>
        ALL OFF
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useControlStore } from '@/stores/control'
import { storeToRefs } from 'pinia'

const controlStore = useControlStore()
const { headLight, baseLight } = storeToRefs(controlStore)
const { setHeadLight, toggleBaseLight, setBaseLight } = controlStore

const headModes = [
  { value: 'off', label: 'OFF' },
  { value: 'auto', label: 'AUTO' },
  { value: 'on', label: 'ON' }
]

function setAllLights(on) {
  setHeadLight(on ? 'on' : 'off')
  setBaseLight(on)
}
</script>

<style scoped>
.lighting-controls {
  @apply space-y-4;
}

.light-group {
  @apply space-y-2;
}

.light-label {
  @apply flex items-center gap-2 text-[10px] font-orbitron tracking-wider text-dark-text-tertiary uppercase;
}

.light-icon {
  @apply w-4 h-4 text-primary;
}

.light-modes {
  @apply flex gap-2;
}

.mode-btn {
  @apply flex-1 py-2 px-3 text-xs font-orbitron tracking-wider;
  @apply text-dark-text-tertiary border border-dark-border;
  @apply transition-all duration-200;
  clip-path: polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px);
}

.mode-btn:hover {
  @apply text-dark-text-secondary border-primary/50;
}

.mode-btn.active {
  @apply text-primary border-primary bg-primary/10;
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
}

.light-toggle {
  @apply flex;
}

.toggle-btn {
  @apply flex-1 flex items-center justify-center gap-3 py-2 px-4;
  @apply text-dark-text-tertiary border border-dark-border;
  @apply transition-all duration-200;
  clip-path: polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px);
}

.toggle-btn:hover {
  @apply border-primary/50;
}

.toggle-btn.active {
  @apply text-secondary border-secondary bg-secondary/10;
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.2);
}

.toggle-indicator {
  @apply w-3 h-3 rounded-full bg-dark-text-tertiary;
  @apply transition-all duration-200;
}

.toggle-btn.active .toggle-indicator {
  @apply bg-secondary;
  box-shadow: 0 0 8px rgba(0, 255, 136, 0.6);
}

.toggle-text {
  @apply text-xs font-orbitron tracking-wider;
}

.quick-actions {
  @apply flex gap-2 pt-2;
  border-top: 1px solid rgba(0, 240, 255, 0.1);
}

.action-btn {
  @apply flex-1 flex items-center justify-center gap-2 py-2 px-3;
  @apply text-[10px] font-orbitron tracking-wider;
  @apply border transition-all duration-200;
  clip-path: polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px);
}

.action-btn svg {
  @apply w-3 h-3;
}

.action-btn.all-on {
  @apply text-secondary border-secondary/30 bg-secondary/5;
}

.action-btn.all-on:hover {
  @apply bg-secondary/20 border-secondary;
}

.action-btn.all-off {
  @apply text-dark-text-tertiary border-dark-border bg-dark-bg-tertiary/30;
}

.action-btn.all-off:hover {
  @apply text-danger border-danger/50 bg-danger/10;
}
</style>
