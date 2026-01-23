<template>
  <div class="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
    <TransitionGroup name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast"
        :class="toastClass(toast.type)"
      >
        <div class="flex items-start gap-3">
          <span class="text-2xl">{{ toast.icon }}</span>
          <div class="flex-1">
            <p class="text-sm">{{ toast.message }}</p>
            <button
              v-if="toast.action"
              @click="toast.action.onClick"
              class="mt-2 text-xs text-primary hover:underline"
            >
              {{ toast.action.label }}
            </button>
          </div>
          <button
            @click="removeToast(toast.id)"
            class="text-dark-text-tertiary hover:text-dark-text-primary"
          >
            ✕
          </button>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useToast } from '@/composables/useToast'

const { toasts, removeToast } = useToast()

function toastClass(type) {
  const classes = {
    success: 'border-success/30',
    error: 'border-danger/30',
    warning: 'border-warning/30',
    info: 'border-primary/30'
  }
  return classes[type] || ''
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.toast-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
