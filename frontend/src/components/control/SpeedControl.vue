<template>
  <div class="speed-control">
    <!-- Speed Mode Selector with integrated indicator -->
    <div class="mode-selector">
      <div class="mode-track">
        <div
          class="mode-highlight"
          :style="{ transform: `translateX(${activeIndex * 100}%)` }"
        ></div>
      </div>
      <button
        v-for="mode in speedModes"
        :key="mode.value"
        @click="setSpeed(mode.value)"
        :class="['mode-button', { active: speedMode === mode.value }]"
      >
        <span class="mode-icon">{{ mode.icon }}</span>
        <span class="mode-label">{{ mode.label }}</span>
        <span class="mode-speed">{{ mode.speed }} m/s</span>
      </button>
    </div>

    <!-- Compact Speed Display -->
    <div class="speed-display">
      <div class="speed-bar">
        <div
          class="speed-bar-fill"
          :style="{ width: `${(speedValue / 2.0) * 100}%` }"
        ></div>
        <div class="speed-bar-marks">
          <span v-for="i in 5" :key="i" class="mark"></span>
        </div>
      </div>
      <div class="speed-readout">
        <span class="speed-value">{{ currentSpeedDisplay }}</span>
        <span class="speed-unit">m/s</span>
      </div>
    </div>

    <!-- Custom Speed (collapsible) -->
    <div class="custom-section">
      <button @click="showAdvanced = !showAdvanced" class="custom-toggle">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          :class="{ rotated: showAdvanced }"
        >
          <path d="M19 9l-7 7-7-7" />
        </svg>
        <span>Custom</span>
      </button>
      <Transition name="slide">
        <div v-if="showAdvanced" class="custom-speed">
          <input
            type="range"
            v-model.number="customSpeed"
            :min="0.1"
            :max="2.0"
            :step="0.05"
            class="speed-slider"
            @input="handleCustomSpeed"
          />
          <div class="slider-labels">
            <span>0.1</span>
            <span>2.0</span>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useControlStore } from '@/stores/control'

const controlStore = useControlStore()
const { speedMode, speedValue } = storeToRefs(controlStore)

// Local state
const showAdvanced = ref(false)
const customSpeed = ref(0.66)

// Speed modes configuration
const speedModes = [
  { value: 'slow', label: 'Slow', icon: '🐌', speed: 0.2 },
  { value: 'mid', label: 'Medium', icon: '🚶', speed: 0.66 },
  { value: 'fast', label: 'Fast', icon: '🏃', speed: 1.3 }
]

// Computed
const activeIndex = computed(() => {
  const index = speedModes.findIndex(mode => mode.value === speedMode.value)
  return index >= 0 ? index : 0
})

const currentSpeedDisplay = computed(() => {
  return speedValue.value.toFixed(2)
})

// Methods
const setSpeed = (mode) => {
  controlStore.setSpeed(mode)
  showAdvanced.value = false
}

const handleCustomSpeed = () => {
  controlStore.speedValue = customSpeed.value
  controlStore.speedMode = 'custom'
}
</script>

<style scoped>
.speed-control {
  @apply flex flex-col gap-4;
}

/* Mode Selector with sliding highlight */
.mode-selector {
  @apply relative flex;
  @apply bg-dark-bg-tertiary rounded-lg p-1;
}

.mode-track {
  @apply absolute inset-1;
  pointer-events: none;
}

.mode-highlight {
  @apply absolute top-0 left-0 h-full rounded-md;
  width: calc(100% / 3);
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.2) 0%, rgba(0, 240, 255, 0.1) 100%);
  border: 1px solid rgba(0, 240, 255, 0.4);
  box-shadow: 0 0 12px rgba(0, 240, 255, 0.3), inset 0 0 8px rgba(0, 240, 255, 0.1);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.mode-button {
  @apply relative flex-1 flex flex-col items-center gap-0.5;
  @apply py-2.5 px-2 rounded-md z-10;
  @apply text-dark-text-secondary;
  @apply transition-colors duration-200;
}

.mode-button:hover {
  @apply text-dark-text-primary;
}

.mode-button.active {
  @apply text-primary;
}

.mode-button.active .mode-label {
  @apply text-primary font-semibold;
}

.mode-icon {
  @apply text-xl leading-none;
}

.mode-label {
  @apply text-xs font-medium transition-all duration-200;
}

.mode-speed {
  @apply text-[10px] font-mono opacity-60;
}

/* Compact Speed Display */
.speed-display {
  @apply flex items-center gap-3;
}

.speed-bar {
  @apply relative flex-1 h-2 rounded-full overflow-hidden;
  @apply bg-dark-bg-tertiary;
}

.speed-bar-fill {
  @apply absolute inset-y-0 left-0 rounded-full;
  background: linear-gradient(90deg, #00f0ff 0%, #0080ff 100%);
  box-shadow: 0 0 8px rgba(0, 240, 255, 0.5);
  transition: width 0.3s ease;
}

.speed-bar-marks {
  @apply absolute inset-0 flex justify-between items-center px-1;
}

.speed-bar-marks .mark {
  @apply w-px h-1 bg-dark-bg-secondary opacity-50;
}

.speed-readout {
  @apply flex items-baseline gap-1 min-w-[4.5rem] justify-end;
}

.speed-value {
  @apply text-xl font-mono font-bold text-primary;
  text-shadow: 0 0 8px rgba(0, 240, 255, 0.4);
}

.speed-unit {
  @apply text-xs text-dark-text-tertiary;
}

/* Custom Section */
.custom-section {
  @apply border-t border-dark-border pt-3;
}

.custom-toggle {
  @apply flex items-center gap-2 text-xs text-dark-text-tertiary;
  @apply hover:text-dark-text-secondary transition-colors;
}

.custom-toggle svg {
  @apply w-3 h-3 transition-transform duration-200;
}

.custom-toggle svg.rotated {
  @apply rotate-180;
}

.custom-speed {
  @apply mt-3 space-y-2;
}

.speed-slider {
  @apply w-full h-1.5 rounded-full appearance-none;
  @apply bg-dark-bg-tertiary;
  @apply cursor-pointer;
}

.speed-slider::-webkit-slider-thumb {
  @apply appearance-none w-3.5 h-3.5 rounded-full;
  @apply bg-primary cursor-pointer;
  box-shadow: 0 0 6px rgba(0, 240, 255, 0.5);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.speed-slider::-webkit-slider-thumb:hover {
  @apply scale-125;
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.7);
}

.speed-slider::-moz-range-thumb {
  @apply w-3.5 h-3.5 rounded-full border-0;
  @apply bg-primary cursor-pointer;
}

.slider-labels {
  @apply flex justify-between text-[10px] text-dark-text-tertiary font-mono;
}

/* Slide transition */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
