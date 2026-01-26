import { ref } from 'vue'

const confirmState = ref({
  visible: false,
  title: '',
  message: '',
  confirmText: 'CONFIRM',
  cancelText: 'CANCEL',
  type: 'warning', // 'warning' | 'danger' | 'info'
  resolve: null
})

export function useConfirm() {
  function confirm(options) {
    return new Promise((resolve) => {
      if (typeof options === 'string') {
        options = { message: options }
      }

      confirmState.value = {
        visible: true,
        title: options.title || 'Confirm',
        message: options.message || 'Are you sure?',
        confirmText: options.confirmText || 'CONFIRM',
        cancelText: options.cancelText || 'CANCEL',
        type: options.type || 'warning',
        resolve
      }
    })
  }

  function handleConfirm() {
    confirmState.value.visible = false
    if (confirmState.value.resolve) {
      confirmState.value.resolve(true)
    }
  }

  function handleCancel() {
    confirmState.value.visible = false
    if (confirmState.value.resolve) {
      confirmState.value.resolve(false)
    }
  }

  return {
    confirmState,
    confirm,
    handleConfirm,
    handleCancel
  }
}
