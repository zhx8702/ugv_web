import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getMediaStats } from '@/services/api'

export const useSystemStore = defineStore('system', () => {
  // 状态
  const cpuUsage = ref(45)
  const ramUsage = ref(62)
  const temperature = ref(52)
  const voltage = ref(11.8)
  const rssi = ref(-45)
  const fps = ref(30)
  const cpuHistory = ref([])
  const ramHistory = ref([])

  // 媒体统计
  const photoCount = ref(0)
  const videoCount = ref(0)
  const picturesSize = ref(0)  // bytes
  const videosSize = ref(0)    // bytes

  // Mock 模式
  const mockMode = ref(true)
  let mockInterval = null

  // 计算属性
  const systemStatus = computed(() => {
    if (temperature.value > 70) return 'critical'
    if (temperature.value > 60) return 'warning'
    return 'good'
  })

  const batteryStatus = computed(() => {
    if (voltage.value < 10.8) return 'critical'
    if (voltage.value < 11.2) return 'warning'
    return 'good'
  })

  // 平滑系数 (0-1, 越小越平滑)
  const smoothingFactor = 0.3

  // 平滑函数
  function smooth(oldVal, newVal) {
    return oldVal + (newVal - oldVal) * smoothingFactor
  }

  // 方法
  function updateStats(data) {
    // 收到真实数据时，停止 mock 模式
    if (mockMode.value) {
      stopMockMode()
    }

    // Update values with smoothing, keeping previous valid values if new value is 0 or undefined
    if (data[106] !== undefined && data[106] !== 0) {
      cpuUsage.value = smooth(cpuUsage.value, data[106])
    }
    if (data[108] !== undefined && data[108] !== 0) {
      ramUsage.value = smooth(ramUsage.value, data[108])
    }
    if (data[107] !== undefined && data[107] !== 0) {
      temperature.value = smooth(temperature.value, data[107])
    }
    if (data[112] !== undefined && data[112] !== 0) {
      voltage.value = smooth(voltage.value, data[112])
    }
    // For RSSI, 0 is invalid (valid range is negative), keep previous value
    if (data[111] !== undefined && data[111] !== 0) {
      rssi.value = Math.round(smooth(rssi.value, data[111]))
    }
    // For FPS, 0 means no stream, keep previous value if streaming
    if (data[113] !== undefined && data[113] > 0) {
      fps.value = smooth(fps.value, data[113])
    }
    if (data[104] !== undefined) picturesSize.value = data[104]
    if (data[105] !== undefined) videosSize.value = data[105]

    // 更新历史数据（保留最近50个点）
    cpuHistory.value.push(Math.round(cpuUsage.value))
    ramHistory.value.push(Math.round(ramUsage.value))

    if (cpuHistory.value.length > 50) {
      cpuHistory.value.shift()
      ramHistory.value.shift()
    }
  }

  // 更新媒体计数
  function updateMediaCount(photos, videos) {
    photoCount.value = photos
    videoCount.value = videos
  }

  // 从后端获取媒体计数
  async function fetchMediaCount() {
    try {
      const data = await getMediaStats()
      if (data) {
        photoCount.value = data.photos_count || 0
        videoCount.value = data.videos_count || 0
        picturesSize.value = data.photos_size || 0
        videosSize.value = data.videos_size || 0
      }
    } catch (error) {
      console.error('Failed to fetch media stats:', error)
    }
  }

  // Mock 数据生成
  function generateMockData() {
    // 模拟 CPU 使用率波动 (30-70%)
    const cpuBase = 45
    const cpuVariation = Math.sin(Date.now() / 2000) * 15 + (Math.random() - 0.5) * 10
    cpuUsage.value = Math.max(15, Math.min(85, cpuBase + cpuVariation))

    // 模拟 RAM 使用率 (50-75%)
    const ramBase = 62
    const ramVariation = Math.sin(Date.now() / 3000) * 8 + (Math.random() - 0.5) * 5
    ramUsage.value = Math.max(40, Math.min(80, ramBase + ramVariation))

    // 模拟温度 (45-58°C)
    const tempBase = 52
    const tempVariation = Math.sin(Date.now() / 5000) * 5 + (Math.random() - 0.5) * 3
    temperature.value = Math.max(40, Math.min(65, tempBase + tempVariation))

    // 模拟电压 (11.2-12.2V)
    const voltBase = 11.8
    const voltVariation = Math.sin(Date.now() / 10000) * 0.3 + (Math.random() - 0.5) * 0.1
    voltage.value = Math.max(10.8, Math.min(12.4, voltBase + voltVariation))

    // 模拟信号强度 (-30 to -60 dBm)
    const rssiBase = -45
    const rssiVariation = (Math.random() - 0.5) * 10
    rssi.value = Math.round(Math.max(-65, Math.min(-25, rssiBase + rssiVariation)))

    // 模拟 FPS (25-32)
    fps.value = Math.round(28 + (Math.random() - 0.5) * 6)

    // 更新历史数据
    cpuHistory.value.push(Math.round(cpuUsage.value))
    ramHistory.value.push(Math.round(ramUsage.value))

    if (cpuHistory.value.length > 50) {
      cpuHistory.value.shift()
      ramHistory.value.shift()
    }
  }

  // 初始化历史数据
  function initMockHistory() {
    cpuHistory.value = []
    ramHistory.value = []
    for (let i = 0; i < 30; i++) {
      cpuHistory.value.push(Math.round(40 + Math.random() * 25))
      ramHistory.value.push(Math.round(55 + Math.random() * 20))
    }
    // 模拟媒体计数
    photoCount.value = Math.round(5 + Math.random() * 20)
    videoCount.value = Math.round(2 + Math.random() * 8)
  }

  function startMockMode() {
    if (mockInterval) return
    mockMode.value = true
    initMockHistory()
    generateMockData()
    mockInterval = setInterval(generateMockData, 1000)
  }

  function stopMockMode() {
    mockMode.value = false
    if (mockInterval) {
      clearInterval(mockInterval)
      mockInterval = null
    }
  }

  function startMonitoring() {
    // 在没有真实连接时启动 Mock 模式
    startMockMode()
  }

  function stopMonitoring() {
    stopMockMode()
  }

  return {
    cpuUsage,
    ramUsage,
    temperature,
    voltage,
    rssi,
    fps,
    cpuHistory,
    ramHistory,
    photoCount,
    videoCount,
    picturesSize,
    videosSize,
    systemStatus,
    batteryStatus,
    mockMode,
    updateStats,
    updateMediaCount,
    fetchMediaCount,
    startMonitoring,
    stopMonitoring,
    startMockMode,
    stopMockMode
  }
})
