<template>
  <div class="speed-slider-container">
    <div class="speed-label">SPEED</div>
    <div class="slider-wrapper">
      <input
        type="range"
        :value="speedValue"
        :min="0.1"
        :max="2.0"
        :step="0.1"
        class="speed-slider"
        @input="handleInput"
        @touchstart.stop
        @touchmove.stop
      />
      <div class="slider-track">
        <div
          class="slider-fill"
          :style="{ width: `${fillPercent}%` }"
        ></div>
      </div>
    </div>
    <div class="speed-value">
      {{ speedValue.toFixed(1) }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useControlStore } from '@/stores/control'

const controlStore = useControlStore()
const { speedValue } = storeToRefs(controlStore)

const fillPercent = computed(() => {
  return ((speedValue.value - 0.1) / (2.0 - 0.1)) * 100
})

function handleInput(e) {
  const value = parseFloat(e.target.value)
  controlStore.speedValue = value
  controlStore.speedMode = 'custom'
}
</script>

<style scoped>
.speed-slider-container {
  @apply flex items-center gap-2 px-2;
  touch-action: none;
}

.speed-label {
  @apply text-[9px] font-orbitron tracking-wider text-dark-text-tertiary;
}

.slider-wrapper {
  @apply relative flex-1 h-6 flex items-center;
}

.speed-slider {
  @apply absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10;
  touch-action: pan-x;
}

.slider-track {
  @apply w-full h-1.5 rounded-full overflow-hidden;
  background: rgba(0, 240, 255, 0.15);
}

.slider-fill {
  @apply h-full rounded-full transition-all duration-100;
  background: linear-gradient(90deg, #00f0ff 0%, #0080ff 100%);
  box-shadow: 0 0 8px rgba(0, 240, 255, 0.5);
}

.speed-value {
  @apply min-w-[2rem] text-sm font-mono font-bold text-primary text-right;
  text-shadow: 0 0 6px rgba(0, 240, 255, 0.4);
}

/* 确保滑块在触摸设备上响应良好 */
.speed-slider::-webkit-slider-thumb {
  @apply appearance-none w-5 h-5 rounded-full;
  @apply bg-primary cursor-pointer;
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.6);
}

.speed-slider::-moz-range-thumb {
  @apply w-5 h-5 rounded-full border-0;
  @apply bg-primary cursor-pointer;
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.6);
}
</style>
