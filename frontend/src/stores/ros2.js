/**
 * ROS2 Bridge State Store
 *
 * Polls /api/ros2/status to track ROS2 connection state.
 */
import { defineStore } from 'pinia'
import { ref, onUnmounted } from 'vue'
import api from '@/services/api'

export const useROS2Store = defineStore('ros2', () => {
  const enabled = ref(false)
  const connected = ref(false)
  const host = ref('')
  const port = ref(0)
  const videoPort = ref(8080)
  const publishers = ref(0)
  const subscribers = ref(0)

  let pollTimer = null

  async function fetchStatus() {
    try {
      const data = await api.get('/ros2/status')
      enabled.value = data.enabled || false
      connected.value = data.connected || false
      host.value = data.host || ''
      port.value = data.port || 0
      publishers.value = data.publishers || 0
      subscribers.value = data.subscribers || 0
    } catch {
      enabled.value = false
      connected.value = false
    }
  }

  async function reconnect() {
    try {
      const data = await api.post('/ros2/reconnect')
      connected.value = data.connected || false
    } catch {
      connected.value = false
    }
  }

  function startPolling(interval = 5000) {
    if (pollTimer) return
    fetchStatus()
    pollTimer = setInterval(fetchStatus, interval)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return {
    enabled,
    connected,
    host,
    port,
    videoPort,
    publishers,
    subscribers,
    fetchStatus,
    reconnect,
    startPolling,
    stopPolling,
  }
})
