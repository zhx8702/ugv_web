import axios from 'axios'
import { useToast } from '@/composables/useToast'
import * as mock from './mockData'

// 检测是否为 Mock 模式（GitHub Pages 或手动设置）
export const isMockMode = import.meta.env.VITE_MOCK === 'true' ||
  window.location.hostname.includes('github.io') ||
  window.location.hostname.includes('localhost') && import.meta.env.VITE_MOCK === 'true'

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL || window.location.origin}/api`,
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    const toast = useToast()
    toast.error(error.message || 'Request failed')
    return Promise.reject(error)
  }
)

// ============ 系统相关 API ============
export const getSystemStatus = () => {
  if (isMockMode) return mock.mockDelay({ ...mock.systemStatus, timestamp: Date.now() })
  return api.get('/system/status')
}

export const getSystemStats = () => {
  if (isMockMode) return mock.mockDelay(mock.systemStats)
  return api.get('/system/stats')
}

export const rebootSystem = () => {
  if (isMockMode) return mock.mockDelay(mock.successResponse, 500)
  return api.post('/system/reboot')
}

// ============ OTA 更新相关 API ============
export const getVersion = () => {
  if (isMockMode) return mock.mockDelay(mock.otaVersion)
  return api.get('/ota/version')
}

export const checkUpdate = () => {
  if (isMockMode) return mock.mockDelay(mock.otaCheckUpdate, 800)
  return api.get('/ota/check-update')
}

export const doUpdate = () => {
  if (isMockMode) return mock.mockDelay(mock.successResponse, 2000)
  return api.post('/ota/perform-update', {}, { timeout: 120000 })
}

export const restartService = () => {
  if (isMockMode) return mock.mockDelay(mock.successResponse, 500)
  return api.post('/system/restart-service')
}

// ============ 媒体相关 API ============
export const getPhotos = () => {
  if (isMockMode) return mock.mockDelay(mock.photos)
  return api.get('/media/photos')
}

export const getVideos = () => {
  if (isMockMode) return mock.mockDelay(mock.videos)
  return api.get('/media/videos')
}

export const deletePhoto = (id) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.delete(`/media/photos/${id}`)
}

export const deleteVideo = (id) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.delete(`/media/videos/${id}`)
}

export const getMediaStats = () => {
  if (isMockMode) return mock.mockDelay(mock.mediaStorage)
  return api.get('/media/storage')
}

// ============ 设置相关 API ============
export const getSettings = () => {
  if (isMockMode) return mock.mockDelay(mock.settings)
  return api.get('/settings')
}

export const updateSettings = (settings) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.put('/settings', settings)
}

// ============ 视频相关 API ============
export const capturePhoto = () => {
  if (isMockMode) return mock.mockDelay(mock.successResponse, 300)
  return api.post('/video/capture')
}

export const startRecording = () => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/video/recording/start')
}

export const stopRecording = () => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/video/recording/stop')
}

export const setVideoZoom = (rate) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/video/zoom', { rate })
}

export const getVideoStatus = () => {
  if (isMockMode) return mock.mockDelay(mock.videoStatus)
  return api.get('/video/status')
}

// ============ 命令发送 ============
export const sendCommand = (code, val1 = 0, val2 = 0) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/command', { code, val1, val2 })
}

export const sendJsonCommand = (command) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/control/json_command', command)
}

// ============ 灯光控制 API ============
export const setLights = (base, head) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/control/light', { base, head })
}

export const getLightStatus = () => {
  if (isMockMode) return mock.mockDelay({ base: false, head: 'off' })
  return api.get('/control/light/status')
}

// ============ 电机锁定 API ============
export const lockMotor = () => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/control/motor/lock')
}

export const unlockMotor = () => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/control/motor/unlock')
}

// ============ 舵机配置 API ============
export const setServoId = (oldId, newId) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/control/servo/id', { old_id: oldId, new_id: newId })
}

export const setServoTorque = (id, lock) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/control/servo/torque', { id, lock })
}

export const setServoMid = (id) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/control/servo/mid', { id })
}

export const releaseServo = (id) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/control/servo/release', id ? { id } : {})
}

// ============ CV 检测相关 API ============
export const getCVStatus = () => {
  if (isMockMode) return mock.mockDelay(mock.cvStatus)
  return api.get('/cv/status')
}

export const setCVMode = (mode) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/cv/mode', { mode })
}

export const setCVMotionLock = (locked) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/cv/motion-lock', { locked })
}

// ============ 语音相关 API ============
export const getAudioFiles = (category) => {
  if (isMockMode) return mock.mockDelay(mock.audioFiles)
  const params = category ? { category } : {}
  return api.get('/audio/files', { params })
}

export const playAudioFile = (file) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/audio/play', { file })
}

export const playRandomAudio = (category, force = false) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/audio/play-random', { category, force })
}

export const speakText = (text) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/audio/speak', { text })
}

export const stopAudio = () => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/audio/stop')
}

export const getAudioVolume = () => {
  if (isMockMode) return mock.mockDelay({ volume: 0.5 })
  return api.get('/audio/volume')
}

export const setAudioVolume = (volume) => {
  if (isMockMode) return mock.mockDelay(mock.successResponse)
  return api.post('/audio/volume', { volume })
}

export const getAudioStatus = () => {
  if (isMockMode) return mock.mockDelay(mock.audioStatus)
  return api.get('/audio/status')
}

export default api
