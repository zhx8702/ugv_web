import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useSystemStore } from '@/stores/system'
import { useControlStore } from '@/stores/control'
import { useWebSocket } from '@/composables/useWebSocket'

export function useDashboard() {
  const systemStore = useSystemStore()
  const controlStore = useControlStore()
  const { latency, connected } = useWebSocket()

  // 时间显示
  const currentTime = ref('')
  let timeInterval = null

  function updateTime() {
    const now = new Date()
    currentTime.value = now.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  function startTimeUpdater() {
    updateTime()
    timeInterval = setInterval(updateTime, 1000)
  }

  function stopTimeUpdater() {
    if (timeInterval) {
      clearInterval(timeInterval)
      timeInterval = null
    }
  }

  // 全屏状态
  const isFullscreen = ref(false)

  function handleFullscreenChange() {
    isFullscreen.value = !!document.fullscreenElement
  }

  // 桌面版全屏 - 针对视频面板
  function toggleFullscreen(selector = '.video-panel') {
    const element = document.querySelector(selector)
    if (!element) return

    if (!document.fullscreenElement) {
      element.requestFullscreen().then(() => {
        isFullscreen.value = true
      }).catch(err => {
        console.error('Fullscreen error:', err)
      })
    } else {
      document.exitFullscreen().then(() => {
        isFullscreen.value = false
      })
    }
  }

  // 移动端全屏 - 针对整个 cockpit
  function toggleMobileFullscreen(selector = '.mobile-cockpit') {
    const element = document.querySelector(selector)
    if (!element) return

    if (!document.fullscreenElement) {
      element.requestFullscreen().catch(err => {
        console.error('Mobile fullscreen error:', err)
      })
    } else {
      document.exitFullscreen()
    }
  }

  // 录像状态 (使用 store 中的 recording 状态)
  const isRecording = computed(() => controlStore.recording)

  function toggleRecording() {
    controlStore.toggleRecord()
  }

  // 拍照
  function captureSnapshot() {
    controlStore.capturePhoto()
  }

  // 状态数据 (供状态栏使用)
  const statusData = computed(() => ({
    fps: systemStore.fps,
    latency: latency.value,
    voltage: systemStore.voltage,
    temperature: systemStore.temperature,
    motorLocked: controlStore.motorLocked,
    connected: connected.value,
    cpuUsage: systemStore.cpuUsage,
    memoryUsage: systemStore.memoryUsage
  }))

  // 生命周期
  onMounted(() => {
    startTimeUpdater()
    document.addEventListener('fullscreenchange', handleFullscreenChange)
  })

  onUnmounted(() => {
    stopTimeUpdater()
    document.removeEventListener('fullscreenchange', handleFullscreenChange)
  })

  return {
    // Stores
    systemStore,
    controlStore,

    // WebSocket
    latency,
    connected,

    // 时间
    currentTime,

    // 全屏
    isFullscreen,
    toggleFullscreen,
    toggleMobileFullscreen,

    // 录像
    isRecording,
    toggleRecording,

    // 拍照
    captureSnapshot,

    // 状态数据
    statusData
  }
}
