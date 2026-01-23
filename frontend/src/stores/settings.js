import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

// 默认配置
const defaultSettings = {
  // 机器人基础配置
  robotName: 'UGV Rover',
  robotType: 2,
  moduleType: 0,
  sbcVersion: '0.93',

  // 视频配置
  resolution: '720p',
  resWidth: 1280,
  resHeight: 720,
  quality: 20,
  streamType: 'mjpeg',

  // 速度配置
  maxSpeed: 1.3,
  slowSpeed: 0.2,
  midRate: 0.66,

  // 舵机配置
  panServoId: 1,
  tiltServoId: 2
}

const defaultPreferences = {
  speedMode: 'mid',
  headLight: 'off',
  baseLight: false,
  zoomLevel: 1,
  detectionType: 'none',
  keyboardControl: true,
  vibration: false
}

export const useSettingsStore = defineStore('settings', () => {
  // 设置状态
  const settings = ref({ ...defaultSettings })
  const preferences = ref({ ...defaultPreferences })
  const loading = ref(false)
  const synced = ref(false)
  const lastSyncTime = ref(null)

  // 解析分辨率字符串
  function parseResolution(res) {
    const map = {
      '480p': { w: 640, h: 480 },
      '720p': { w: 1280, h: 720 },
      '1080p': { w: 1920, h: 1080 }
    }
    return map[res] || map['480p']
  }

  // 根据宽高获取分辨率标签
  function getResolutionLabel(w, h) {
    if (w >= 1920) return '1080p'
    if (w >= 1280) return '720p'
    return '480p'
  }

  // 从后端加载配置
  async function fetchConfig() {
    loading.value = true
    try {
      const config = await api.get('/settings')

      if (config) {
        // 映射后端配置到前端
        if (config.base_config) {
          settings.value.robotName = config.base_config.robot_name || defaultSettings.robotName
          settings.value.robotType = config.base_config.main_type || defaultSettings.robotType
          settings.value.moduleType = config.base_config.module_type || defaultSettings.moduleType
          settings.value.sbcVersion = config.base_config.sbc_version || defaultSettings.sbcVersion
        }

        if (config.args_config) {
          settings.value.maxSpeed = config.args_config.max_speed || defaultSettings.maxSpeed
          settings.value.slowSpeed = config.args_config.slow_speed || defaultSettings.slowSpeed
          settings.value.midRate = config.args_config.mid_rate || defaultSettings.midRate
        }

        if (config.video) {
          settings.value.quality = config.video.default_quality || defaultSettings.quality
          settings.value.resWidth = config.video.default_res_w || defaultSettings.resWidth
          settings.value.resHeight = config.video.default_res_h || defaultSettings.resHeight
          settings.value.resolution = getResolutionLabel(settings.value.resWidth, settings.value.resHeight)
          settings.value.streamType = config.video.stream_type || defaultSettings.streamType
        }

        // 加载用户偏好
        if (config.user_preferences) {
          preferences.value = {
            speedMode: config.user_preferences.speed_mode || defaultPreferences.speedMode,
            headLight: config.user_preferences.head_light || defaultPreferences.headLight,
            baseLight: config.user_preferences.base_light || defaultPreferences.baseLight,
            zoomLevel: config.user_preferences.zoom_level || defaultPreferences.zoomLevel,
            detectionType: config.user_preferences.detection_type || defaultPreferences.detectionType,
            keyboardControl: config.user_preferences.keyboard_control !== undefined
              ? config.user_preferences.keyboard_control
              : defaultPreferences.keyboardControl,
            vibration: config.user_preferences.vibration || defaultPreferences.vibration
          }
        }

        synced.value = true
        lastSyncTime.value = new Date()
      }

      return config
    } catch (e) {
      console.error('Failed to fetch config:', e)
      return null
    } finally {
      loading.value = false
    }
  }

  // 保存配置到后端
  async function saveConfig() {
    loading.value = true
    try {
      const { w, h } = parseResolution(settings.value.resolution)

      const configData = {
        base_config: {
          robot_name: settings.value.robotName,
          main_type: parseInt(settings.value.robotType),
          module_type: parseInt(settings.value.moduleType)
        },
        args_config: {
          max_speed: parseFloat(settings.value.maxSpeed),
          slow_speed: parseFloat(settings.value.slowSpeed),
          mid_rate: parseFloat(settings.value.midRate)
        },
        video: {
          default_quality: parseInt(settings.value.quality),
          default_res_w: w,
          default_res_h: h,
          stream_type: settings.value.streamType
        },
        user_preferences: {
          speed_mode: preferences.value.speedMode,
          head_light: preferences.value.headLight,
          base_light: preferences.value.baseLight,
          zoom_level: preferences.value.zoomLevel,
          detection_type: preferences.value.detectionType,
          keyboard_control: preferences.value.keyboardControl,
          vibration: preferences.value.vibration
        }
      }

      const result = await api.put('/settings', configData)

      if (result && result.success) {
        lastSyncTime.value = new Date()
        synced.value = true
        return true
      }
      return false
    } catch (e) {
      console.error('Failed to save config:', e)
      return false
    } finally {
      loading.value = false
    }
  }

  // 仅保存用户偏好
  async function savePreferences() {
    try {
      const prefsData = {
        speed_mode: preferences.value.speedMode,
        head_light: preferences.value.headLight,
        base_light: preferences.value.baseLight,
        zoom_level: preferences.value.zoomLevel,
        detection_type: preferences.value.detectionType,
        keyboard_control: preferences.value.keyboardControl,
        vibration: preferences.value.vibration
      }

      const result = await api.put('/settings/preferences', prefsData)
      return result && result.success
    } catch (e) {
      console.error('Failed to save preferences:', e)
      return false
    }
  }

  // 更新单个偏好并保存
  async function updatePreference(key, value) {
    if (preferences.value.hasOwnProperty(key)) {
      preferences.value[key] = value
      // 延迟保存，避免频繁请求
      debouncePreferencesSave()
    }
  }

  // 防抖保存
  let saveTimer = null
  function debouncePreferencesSave() {
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => {
      savePreferences()
    }, 1000)
  }

  // 重置为默认值
  async function resetToDefaults() {
    settings.value = { ...defaultSettings }
    preferences.value = { ...defaultPreferences }
    await saveConfig()
  }

  // 导出配置
  function exportConfig() {
    const exportData = {
      settings: settings.value,
      preferences: preferences.value,
      exportedAt: new Date().toISOString()
    }
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ugv-config-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // 导入配置
  async function importConfig(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = async (e) => {
        try {
          const imported = JSON.parse(e.target.result)
          if (imported.settings) {
            settings.value = { ...defaultSettings, ...imported.settings }
          }
          if (imported.preferences) {
            preferences.value = { ...defaultPreferences, ...imported.preferences }
          }
          await saveConfig()
          resolve(true)
        } catch (err) {
          reject(err)
        }
      }
      reader.onerror = reject
      reader.readAsText(file)
    })
  }

  // 重启系统
  async function rebootSystem() {
    try {
      await api.post('/system/reboot')
      return true
    } catch (e) {
      console.error('Failed to reboot:', e)
      return false
    }
  }

  // 计算属性
  const formattedLastSync = computed(() => {
    if (!lastSyncTime.value) return 'Never'
    return lastSyncTime.value.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  })

  const speedMap = computed(() => ({
    slow: settings.value.slowSpeed,
    mid: settings.value.maxSpeed * settings.value.midRate,
    fast: settings.value.maxSpeed
  }))

  // 初始化
  function init() {
    fetchConfig()
  }

  return {
    settings,
    preferences,
    loading,
    synced,
    lastSyncTime,
    formattedLastSync,
    speedMap,
    init,
    fetchConfig,
    saveConfig,
    savePreferences,
    updatePreference,
    resetToDefaults,
    exportConfig,
    importConfig,
    rebootSystem
  }
})
