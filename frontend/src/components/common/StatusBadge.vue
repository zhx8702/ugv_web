<template>
  <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg border"
    :class="statusClass"
  >
    <span class="text-lg">{{ icon }}</span>
    <span class="text-sm font-mono">{{ value }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: String,
  value: String,
  status: {
    type: String,
    default: 'good',
    validator: (value) => ['good', 'warning', 'danger'].includes(value)
  }
})

const statusClass = computed(() => {
  const classes = {
    good: 'border-success/30 bg-success/10 text-success',
    warning: 'border-warning/30 bg-warning/10 text-warning',
    danger: 'border-danger/30 bg-danger/10 text-danger'
  }
  return classes[props.status]
})
</script>
