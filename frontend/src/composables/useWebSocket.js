import { ref } from 'vue'
import { io } from 'socket.io-client'
import { useSystemStore } from '@/stores/system'
import { useToast } from '@/composables/useToast'

let socket = null
const connected = ref(false)
const latency = ref(0)
let pingInterval = null
let pingStartTime = 0

export function useWebSocket() {
  const systemStore = useSystemStore()
  const toast = useToast()

  function startPing() {
    if (pingInterval) return
    // 每3秒测量一次延迟
    pingInterval = setInterval(() => {
      if (socket && connected.value) {
        pingStartTime = Date.now()
        socket.emit('ping')
      }
    }, 3000)
    // 立即测量一次
    if (socket && connected.value) {
      pingStartTime = Date.now()
      socket.emit('ping')
    }
  }

  function stopPing() {
    if (pingInterval) {
      clearInterval(pingInterval)
      pingInterval = null
    }
  }

  function connect() {
    if (socket) return

    // Connect to backend server
    // Use current origin if served from same server, otherwise use env variable
    const backendUrl = import.meta.env.VITE_API_URL || window.location.origin
    socket = io(backendUrl, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity,  // Never stop trying to reconnect
      timeout: 20000,  // Longer timeout for slow networks
      forceNew: false
    })

    socket.on('connect', () => {
      connected.value = true
      toast.success('Connected to rover')
      console.log('WebSocket connected')
      startPing()
    })

    socket.on('disconnect', () => {
      connected.value = false
      latency.value = 0
      stopPing()
      toast.warning('Disconnected from rover')
      console.log('WebSocket disconnected')
    })

    socket.on('pong', () => {
      if (pingStartTime > 0) {
        latency.value = Date.now() - pingStartTime
        pingStartTime = 0
      }
    })

    socket.on('feedback', (data) => {
      systemStore.updateStats(data)
    })

    socket.on('config', (config) => {
      console.log('Received config:', config)
    })

    socket.on('audio_list', (audioList) => {
      console.log('Received audio list:', audioList)
    })

    socket.on('error', (error) => {
      console.error('WebSocket error:', error)
      toast.error(error.message || 'WebSocket error')
    })
  }

  function disconnect() {
    stopPing()
    if (socket) {
      socket.disconnect()
      socket = null
      connected.value = false
      latency.value = 0
    }
  }

  function emit(event, data) {
    if (socket && connected.value) {
      socket.emit(event, data)
    } else {
      console.warn('WebSocket not connected, cannot emit:', event)
    }
  }

  function sendCommand(code, val1 = 0, val2 = 0) {
    emit('cmd_input', { code, val1, val2 })
  }

  function sendJsonCommand(command) {
    emit('json_cmd', command)
  }

  // 注意：不要在这里添加 onUnmounted 钩子
  // WebSocket 连接是全局单例，应该只在 App.vue 中管理连接的生命周期
  // 如果在这里添加 onUnmounted，会导致任何使用此 composable 的组件卸载时断开全局连接

  return {
    socket,
    connected,
    latency,
    connect,
    disconnect,
    emit,
    sendCommand,
    sendJsonCommand
  }
}
