<template>
  <button
    class="direction-button"
    @mousedown="handlePress"
    @touchstart="handlePress"
    @mouseup="handleRelease"
    @touchend="handleRelease"
    @mouseleave="handleRelease"
  >
    <span class="direction-icon">{{ direction }}</span>
  </button>
</template>

<script setup>
const props = defineProps({
  direction: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['press', 'release'])

let pressInterval = null

const handlePress = (e) => {
  e.preventDefault()
  emit('press')

  // Continuous press
  pressInterval = setInterval(() => {
    emit('press')
  }, 100)
}

const handleRelease = () => {
  if (pressInterval) {
    clearInterval(pressInterval)
    pressInterval = null
  }
  emit('release')
}
</script>

<style scoped>
.direction-button {
  @apply flex items-center justify-center;
  @apply bg-dark-bg-secondary hover:bg-dark-bg-tertiary active:bg-primary;
  @apply border border-dark-border hover:border-primary;
  @apply rounded-lg transition-all;
  @apply select-none touch-none;
}

.direction-icon {
  @apply text-xl text-dark-text-primary;
}

.direction-button:active .direction-icon {
  @apply text-white;
}
</style>
