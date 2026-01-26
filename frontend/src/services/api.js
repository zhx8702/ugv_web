import axios from 'axios'
import { useToast } from '@/composables/useToast'
import * as mock from './mockData'

// ============ Mock 模式检测 ============
const checkMockMode = () => {
  if (import.meta.env.VITE_MOCK === 'true') return true
  if (typeof window !== 'undefined' && window.location.hostname.includes('github.io')) return true
  return false
}
export const isMockMode = checkMockMode()

// ============ Mock 数据映射表 ============
const mockMap = {
  // 系统
  'GET /system/status': () => ({ ...mock.systemStatus, timestamp: Date.now() }),
  'GET /system/stats': mock.systemStats,
  'POST /system/reboot': { data: mock.successResponse, delay: 500 },
  'POST /system/restart-service': { data: mock.successResponse, delay: 500 },

  // OTA
  'GET /ota/version': mock.otaVersion,
  'GET /ota/check-update': { data: mock.otaCheckUpdate, delay: 800 },
  'POST /ota/perform-update': { data: mock.successResponse, delay: 2000 },

  // 媒体
  'GET /media/photos': mock.photos,
  'GET /media/videos': mock.videos,
  'DELETE /media/photos': mock.successResponse,
  'DELETE /media/videos': mock.successResponse,
  'GET /media/storage': mock.mediaStorage,

  // 设置
  'GET /settings': mock.settings,
  'PUT /settings': mock.successResponse,
  'PUT /settings/preferences': mock.successResponse,

  // 视频
  'POST /video/capture': { data: mock.successResponse, delay: 300 },
  'POST /video/recording/start': mock.successResponse,
  'POST /video/recording/stop': mock.successResponse,
  'POST /video/zoom': mock.successResponse,
  'GET /video/status': mock.videoStatus,

  // 控制
  'POST /command': mock.successResponse,
  'POST /control/json_command': mock.successResponse,
  'POST /control/light': mock.successResponse,
  'GET /control/light/status': { base: false, head: 'off' },
  'POST /control/motor/lock': mock.successResponse,
  'POST /control/motor/unlock': mock.successResponse,
  'POST /control/servo/id': mock.successResponse,
  'POST /control/servo/torque': mock.successResponse,
  'POST /control/servo/mid': mock.successResponse,
  'POST /control/servo/release': mock.successResponse,

  // CV
  'GET /cv/status': mock.cvStatus,
  'POST /cv/mode': mock.successResponse,
  'POST /cv/motion-lock': mock.successResponse,

  // 音频
  'GET /audio/files': mock.audioFiles,
  'POST /audio/play': mock.successResponse,
  'POST /audio/play-random': mock.successResponse,
  'POST /audio/speak': mock.successResponse,
  'POST /audio/stop': mock.successResponse,
  'GET /audio/volume': { volume: 0.5 },
  'POST /audio/volume': mock.successResponse,
  'GET /audio/status': mock.audioStatus
}

// ============ Axios 实例 ============
const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL || window.location.origin}/api`,
  timeout: 10000
})

api.interceptors.request.use(config => config, error => Promise.reject(error))

api.interceptors.response.use(
  response => response.data,
  error => {
    const toast = useToast()
    toast.error(error.message || 'Request failed')
    return Promise.reject(error)
  }
)

// ============ 统一请求函数 ============
const request = (method, url, data, config) => {
  if (isMockMode) {
    // 尝试精确匹配，然后尝试路径前缀匹配（用于带参数的路径如 /media/photos/123）
    const key = `${method.toUpperCase()} ${url}`
    let mockConfig = mockMap[key]

    // 如果没有精确匹配，尝试前缀匹配
    if (!mockConfig) {
      const baseUrl = url.replace(/\/[^/]+$/, '') // 移除最后一段路径
      mockConfig = mockMap[`${method.toUpperCase()} ${baseUrl}`]
    }

    if (mockConfig) {
      const { data: mockData, delay = 100 } = mockConfig.data !== undefined ? mockConfig : { data: mockConfig }
      const result = typeof mockData === 'function' ? mockData(data) : mockData
      return mock.mockDelay(result, delay)
    }
  }

  const axiosConfig = { method, url, ...config }
  if (data && ['post', 'put', 'patch'].includes(method)) {
    axiosConfig.data = data
  }
  return api.request(axiosConfig)
}

// ============ 系统相关 API ============
export const getSystemStatus = () => request('get', '/system/status')
export const getSystemStats = () => request('get', '/system/stats')
export const rebootSystem = () => request('post', '/system/reboot')
export const restartService = () => request('post', '/system/restart-service')

// ============ OTA 更新相关 API ============
export const getVersion = () => request('get', '/ota/version')
export const checkUpdate = () => request('get', '/ota/check-update')
export const doUpdate = () => request('post', '/ota/perform-update', {}, { timeout: 120000 })

// ============ 媒体相关 API ============
export const getPhotos = () => request('get', '/media/photos')
export const getVideos = () => request('get', '/media/videos')
export const deletePhoto = (id) => request('delete', `/media/photos/${id}`)
export const deleteVideo = (id) => request('delete', `/media/videos/${id}`)
export const getMediaStats = () => request('get', '/media/storage')

// ============ 设置相关 API ============
export const getSettings = () => request('get', '/settings')
export const updateSettings = (settings) => request('put', '/settings', settings)
export const updatePreferences = (preferences) => request('put', '/settings/preferences', preferences)

// ============ 视频相关 API ============
export const capturePhoto = () => request('post', '/video/capture')
export const startRecording = () => request('post', '/video/recording/start')
export const stopRecording = () => request('post', '/video/recording/stop')
export const setVideoZoom = (rate) => request('post', '/video/zoom', { rate })
export const getVideoStatus = () => request('get', '/video/status')

// ============ 命令发送 ============
export const sendCommand = (code, val1 = 0, val2 = 0) => request('post', '/command', { code, val1, val2 })
export const sendJsonCommand = (command) => request('post', '/control/json_command', command)

// ============ 灯光控制 API ============
export const setLights = (base, head) => request('post', '/control/light', { base, head })
export const getLightStatus = () => request('get', '/control/light/status')

// ============ 电机锁定 API ============
export const lockMotor = () => request('post', '/control/motor/lock')
export const unlockMotor = () => request('post', '/control/motor/unlock')

// ============ 舵机配置 API ============
export const setServoId = (oldId, newId) => request('post', '/control/servo/id', { old_id: oldId, new_id: newId })
export const setServoTorque = (id, lock) => request('post', '/control/servo/torque', { id, lock })
export const setServoMid = (id) => request('post', '/control/servo/mid', { id })
export const releaseServo = (id) => request('post', '/control/servo/release', id ? { id } : {})

// ============ CV 检测相关 API ============
export const getCVStatus = () => request('get', '/cv/status')
export const setCVMode = (mode) => request('post', '/cv/mode', { mode })
export const setCVMotionLock = (locked) => request('post', '/cv/motion-lock', { locked })

// ============ 语音相关 API ============
export const getAudioFiles = (category) => request('get', '/audio/files', null, { params: category ? { category } : {} })
export const playAudioFile = (file) => request('post', '/audio/play', { file })
export const playRandomAudio = (category, force = false) => request('post', '/audio/play-random', { category, force })
export const speakText = (text) => request('post', '/audio/speak', { text })
export const stopAudio = () => request('post', '/audio/stop')
export const getAudioVolume = () => request('get', '/audio/volume')
export const setAudioVolume = (volume) => request('post', '/audio/volume', { volume })
export const getAudioStatus = () => request('get', '/audio/status')

export default api
