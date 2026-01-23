import { ref } from 'vue'

const toasts = ref([])
let idCounter = 0

export function useToast() {
  function addToast(type, message, options = {}) {
    const id = ++idCounter
    const toast = {
      id,
      type,
      message,
      icon: options.icon,
      duration: options.duration || 3000,
      action: options.action
    }

    toasts.value.push(toast)

    if (toast.duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, toast.duration)
    }

    return id
  }

  function removeToast(id) {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  function success(message, options = {}) {
    return addToast('success', message, {
      icon: '✅',
      ...options
    })
  }

  function error(message, options = {}) {
    return addToast('error', message, {
      icon: '❌',
      duration: 5000,
      ...options
    })
  }

  function warning(message, options = {}) {
    return addToast('warning', message, {
      icon: '⚠️',
      ...options
    })
  }

  function info(message, options = {}) {
    return addToast('info', message, {
      icon: 'ℹ️',
      ...options
    })
  }

  return {
    toasts,
    success,
    error,
    warning,
    info,
    removeToast
  }
}
