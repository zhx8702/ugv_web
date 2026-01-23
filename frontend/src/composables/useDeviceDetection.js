import { ref, computed, onMounted, onUnmounted } from 'vue'

const STORAGE_KEY = 'device-preference'

// 全局状态 (单例)
const screenWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1920)
const screenHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 1080)
const userPreference = ref(null) // null = auto, 'desktop', 'mobile'

// 从 localStorage 恢复用户偏好
if (typeof window !== 'undefined') {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'desktop' || saved === 'mobile') {
    userPreference.value = saved
  }
}

export function useDeviceDetection() {
  // 检测是否有触摸能力
  const hasTouchScreen = computed(() => {
    if (typeof window === 'undefined') return false
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0
  })

  // 检测小屏幕 (短边 < 768px)
  const isSmallScreen = computed(() => {
    return Math.min(screenWidth.value, screenHeight.value) < 768
  })

  // 自动检测：触摸 + 小屏幕 = 移动设备
  const autoDetectedMobile = computed(() => {
    return hasTouchScreen.value && isSmallScreen.value
  })

  // 最终判断：考虑用户偏好
  const isMobile = computed(() => {
    if (userPreference.value === 'desktop') return false
    if (userPreference.value === 'mobile') return true
    return autoDetectedMobile.value
  })

  // 横屏检测
  const isLandscape = computed(() => {
    return screenWidth.value > screenHeight.value
  })

  // 设备类型
  const deviceType = computed(() => {
    if (isMobile.value) return 'mobile'
    return 'desktop'
  })

  // 是否有用户手动覆盖
  const hasUserOverride = computed(() => {
    return userPreference.value !== null
  })

  // 强制使用桌面版
  function forceDesktop() {
    userPreference.value = 'desktop'
    localStorage.setItem(STORAGE_KEY, 'desktop')
  }

  // 强制使用移动版
  function forceMobile() {
    userPreference.value = 'mobile'
    localStorage.setItem(STORAGE_KEY, 'mobile')
  }

  // 重置为自动检测
  function resetToAuto() {
    userPreference.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  // 切换模式 (用于UI按钮)
  function toggleMode() {
    if (isMobile.value) {
      forceDesktop()
    } else {
      forceMobile()
    }
  }

  // 屏幕尺寸变化处理
  function handleResize() {
    screenWidth.value = window.innerWidth
    screenHeight.value = window.innerHeight
  }

  // 生命周期管理
  let resizeListener = null

  onMounted(() => {
    if (typeof window !== 'undefined' && !resizeListener) {
      resizeListener = handleResize
      window.addEventListener('resize', resizeListener)
    }
  })

  onUnmounted(() => {
    // 注意：不移除监听器，因为可能有其他组件在使用
    // 这是一个单例模式，监听器应该一直存在
  })

  return {
    // 状态
    isMobile,
    isLandscape,
    deviceType,
    hasTouchScreen,
    isSmallScreen,
    hasUserOverride,
    screenWidth,
    screenHeight,

    // 操作
    forceDesktop,
    forceMobile,
    resetToAuto,
    toggleMode
  }
}
