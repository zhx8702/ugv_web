<template>
  <div class="angle-display-item">
    <div class="angle-header">
      <span class="angle-icon">{{ icon }}</span>
      <span class="angle-label">{{ label }}</span>
      <span class="value-number" :class="valueClass">{{ displayValue }}°</span>
    </div>
    <div class="value-bar">
      <div class="bar-track"></div>
      <div class="bar-center"></div>
      <!-- 双向填充：从中心向两边 -->
      <div
        class="bar-fill"
        :class="fillClass"
        :style="fillStyle"
      ></div>
      <div class="bar-indicator" :style="{ left: `${indicatorPos}%` }"></div>
    </div>
    <div class="bar-labels">
      <span>{{ min }}°</span>
      <span class="center-label">0°</span>
      <span>{{ max }}°</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: Number,
    required: true
  },
  min: {
    type: Number,
    default: -90
  },
  max: {
    type: Number,
    default: 90
  },
  icon: {
    type: String,
    default: '•'
  }
})

const displayValue = computed(() => {
  const v = Math.round(props.value)
  return v > 0 ? `+${v}` : v
})

const valueClass = computed(() => {
  if (props.value > 0) return 'positive'
  if (props.value < 0) return 'negative'
  return 'zero'
})

const fillClass = computed(() => {
  return props.value >= 0 ? 'positive' : 'negative'
})

// 指示器位置 (0-100%)
const indicatorPos = computed(() => {
  const range = props.max - props.min
  return ((props.value - props.min) / range) * 100
})

// 双向填充样式
const fillStyle = computed(() => {
  const range = props.max - props.min
  const centerPercent = (0 - props.min) / range * 100
  const valuePercent = indicatorPos.value

  if (props.value >= 0) {
    // 正值：从中心向右
    return {
      left: `${centerPercent}%`,
      width: `${valuePercent - centerPercent}%`
    }
  } else {
    // 负值：从值位置向右到中心
    return {
      left: `${valuePercent}%`,
      width: `${centerPercent - valuePercent}%`
    }
  }
})
</script>

<style scoped>
.angle-display-item {
  @apply bg-dark-bg-tertiary/50 rounded-lg p-2.5;
  border: 1px solid rgba(0, 240, 255, 0.1);
}

.angle-header {
  @apply flex items-center gap-2 mb-2;
}

.angle-icon {
  @apply text-base text-primary/70;
}

.angle-label {
  @apply text-[10px] font-orbitron text-dark-text-tertiary tracking-wider uppercase;
}

.value-number {
  @apply ml-auto text-base font-mono font-bold;
  min-width: 48px;
  text-align: right;
}

.value-number.positive { @apply text-secondary; }
.value-number.negative { @apply text-warning; }
.value-number.zero { @apply text-primary; }

.value-bar {
  @apply relative h-2 rounded-full overflow-hidden;
}

.bar-track {
  @apply absolute inset-0;
  background: rgba(0, 240, 255, 0.08);
}

.bar-center {
  @apply absolute top-0 bottom-0 w-0.5;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 240, 255, 0.4);
}

.bar-fill {
  @apply absolute top-0 h-full;
  transition: left 0.15s ease-out, width 0.15s ease-out;
}

.bar-fill.positive {
  background: linear-gradient(90deg, rgba(0, 240, 255, 0.3) 0%, rgba(0, 255, 136, 0.6) 100%);
}

.bar-fill.negative {
  background: linear-gradient(90deg, rgba(255, 200, 0, 0.6) 0%, rgba(0, 240, 255, 0.3) 100%);
}

.bar-indicator {
  @apply absolute top-0 bottom-0 w-1 rounded-full;
  transform: translateX(-50%);
  background: #00f0ff;
  box-shadow: 0 0 6px rgba(0, 240, 255, 0.8);
  transition: left 0.15s ease-out;
}

.bar-labels {
  @apply flex justify-between mt-1;
}

.bar-labels span {
  @apply text-[8px] font-mono text-dark-text-tertiary/50;
}

.bar-labels .center-label {
  @apply text-primary/60;
}
</style>
