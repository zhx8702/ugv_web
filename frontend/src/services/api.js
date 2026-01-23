import axios from 'axios'
import { useToast } from '@/composables/useToast'

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

// 系统相关API
export const getSystemStatus = () => api.get('/system/status')
export const getSystemStats = () => api.get('/system/stats')
export const rebootSystem = () => api.post('/system/reboot')

// OTA 更新相关 API
export const getVersion = () => api.get('/system/version')
export const checkUpdate = () => api.get('/system/check-update')
export const doUpdate = () => api.post('/system/update', {}, { timeout: 120000 })
export const restartService = () => api.post('/system/restart-service')

// 媒体相关API
export const getPhotos = () => api.get('/media/photos')
export const getVideos = () => api.get('/media/videos')
export const deletePhoto = (id) => api.delete(`/media/photos/${id}`)
export const deleteVideo = (id) => api.delete(`/media/videos/${id}`)
export const getMediaStats = () => api.get('/media/storage')

// 设置相关API
export const getSettings = () => api.get('/settings')
export const updateSettings = (settings) => api.put('/settings', settings)

// 视频相关API
export const capturePhoto = () => api.post('/video/capture')
export const startRecording = () => api.post('/video/recording/start')
export const stopRecording = () => api.post('/video/recording/stop')
export const setVideoZoom = (rate) => api.post('/video/zoom', { rate })
export const getVideoStatus = () => api.get('/video/status')

// 命令发送（通过WebSocket更合适，这里作为备用）
export const sendCommand = (code, val1 = 0, val2 = 0) => {
  return api.post('/command', { code, val1, val2 })
}

export const sendJsonCommand = (command) => {
  return api.post('/control/json_command', command)
}

// 灯光控制API
export const setLights = (base, head) => api.post('/control/light', { base, head })
export const getLightStatus = () => api.get('/control/light/status')

// 电机锁定API
export const lockMotor = () => api.post('/control/motor/lock')
export const unlockMotor = () => api.post('/control/motor/unlock')

// 舵机配置API
export const setServoId = (oldId, newId) => api.post('/control/servo/id', { old_id: oldId, new_id: newId })
export const setServoTorque = (id, lock) => api.post('/control/servo/torque', { id, lock })
export const setServoMid = (id) => api.post('/control/servo/mid', { id })
export const releaseServo = (id) => api.post('/control/servo/release', id ? { id } : {})

// CV检测相关API
export const getCVStatus = () => api.get('/cv/status')
export const setCVMode = (mode) => api.post('/cv/mode', { mode })
export const setCVMotionLock = (locked) => api.post('/cv/motion-lock', { locked })

// 语音相关API
export const getAudioFiles = (category) => {
  const params = category ? { category } : {}
  return api.get('/audio/files', { params })
}

export const playAudioFile = (file) => api.post('/audio/play', { file })

export const playRandomAudio = (category, force = false) => {
  return api.post('/audio/play-random', { category, force })
}

export const speakText = (text) => api.post('/audio/speak', { text })

export const stopAudio = () => api.post('/audio/stop')

export const getAudioVolume = () => api.get('/audio/volume')

export const setAudioVolume = (volume) => api.post('/audio/volume', { volume })

export const getAudioStatus = () => api.get('/audio/status')

export default api
