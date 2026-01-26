<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="confirmState.visible" class="confirm-overlay" @click.self="handleCancel">
        <div class="confirm-dialog" :class="confirmState.type">
          <!-- Header -->
          <div class="dialog-header">
            <div class="header-icon" :class="confirmState.type">
              <svg v-if="confirmState.type === 'warning'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              <svg v-else-if="confirmState.type === 'danger'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="15" y1="9" x2="9" y2="15" />
                <line x1="9" y1="9" x2="15" y2="15" />
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="16" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12.01" y2="8" />
              </svg>
            </div>
            <h3 class="dialog-title">{{ confirmState.title }}</h3>
          </div>

          <!-- Content -->
          <div class="dialog-content">
            <p>{{ confirmState.message }}</p>
          </div>

          <!-- Actions -->
          <div class="dialog-actions">
            <button class="btn btn-outline" @click="handleCancel">
              {{ confirmState.cancelText }}
            </button>
            <button class="btn" :class="confirmButtonClass" @click="handleConfirm">
              {{ confirmState.confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useConfirm } from '@/composables/useConfirm'

const { confirmState, handleConfirm, handleCancel } = useConfirm()

const confirmButtonClass = computed(() => {
  const classes = {
    warning: 'btn-warning',
    danger: 'btn-danger',
    info: 'btn-primary'
  }
  return classes[confirmState.value.type] || 'btn-primary'
})
</script>

<style scoped>
.confirm-overlay {
  @apply fixed inset-0 z-50 flex items-center justify-center p-4;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
}

.confirm-dialog {
  @apply relative w-full max-w-md overflow-hidden;
  background: linear-gradient(135deg, rgba(10, 22, 40, 0.98) 0%, rgba(3, 7, 18, 0.99) 100%);
  border: 1px solid rgba(0, 240, 255, 0.2);
  clip-path: polygon(16px 0, 100% 0, 100% calc(100% - 16px), calc(100% - 16px) 100%, 0 100%, 0 16px);
}

.confirm-dialog::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(0, 240, 255, 0.6), transparent);
}

.confirm-dialog.warning::before {
  background: linear-gradient(90deg, transparent, rgba(255, 170, 0, 0.6), transparent);
}

.confirm-dialog.danger::before {
  background: linear-gradient(90deg, transparent, rgba(255, 68, 68, 0.6), transparent);
}

.dialog-header {
  @apply flex items-center gap-3 px-6 py-4;
  background: rgba(0, 240, 255, 0.03);
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.header-icon {
  @apply w-8 h-8 text-primary;
}

.header-icon.warning {
  @apply text-warning;
}

.header-icon.danger {
  @apply text-danger;
}

.dialog-title {
  @apply text-lg font-orbitron font-semibold tracking-wider text-dark-text-primary uppercase;
}

.dialog-content {
  @apply px-6 py-5;
}

.dialog-content p {
  @apply text-sm font-mono text-dark-text-secondary leading-relaxed;
}

.dialog-actions {
  @apply flex justify-end gap-3 px-6 py-4;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(0, 240, 255, 0.1);
}

.btn-warning {
  @apply bg-warning/20 text-warning border-warning/50;
}

.btn-warning:hover {
  @apply bg-warning/30 border-warning;
}

/* Transition */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-active .confirm-dialog,
.modal-leave-active .confirm-dialog {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .confirm-dialog,
.modal-leave-to .confirm-dialog {
  transform: scale(0.9) translateY(-20px);
  opacity: 0;
}
</style>
