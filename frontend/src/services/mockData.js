/**
 * Mock Data for GitHub Pages Demo
 * 用于 GitHub Pages 静态展示的模拟数据
 */

// 系统状态
export const systemStatus = {
  cpu: 32,
  ram: 58,
  temperature: 45,
  voltage: 11.8,
  fps: 30,
  rssi: -52,
  timestamp: Date.now()
}

export const systemStats = {
  cpu_history: [28, 32, 35, 30, 32, 38, 42, 35, 32, 30],
  ram_history: [55, 56, 58, 57, 58, 59, 58, 57, 58, 58],
  temp_history: [42, 43, 44, 45, 44, 45, 46, 45, 44, 45],
  voltage_history: [11.9, 11.8, 11.8, 11.9, 11.8, 11.7, 11.8, 11.8, 11.9, 11.8]
}

// OTA 版本
export const otaVersion = {
  version: 'v2.0.0-demo',
  sbc_version: '0.93',
  git_hash: 'abc1234',
  git_branch: 'main',
  last_update: new Date().toISOString()
}

export const otaCheckUpdate = {
  has_update: false,
  current_version: 'v2.0.0-demo',
  latest_version: 'v2.0.0-demo',
  commits_behind: 0,
  changelog: []
}

// 设置
export const settings = {
  base_config: {
    robot_name: 'UGV Rover Demo',
    main_type: 2,
    module_type: 0,
    sbc_version: '0.93'
  },
  args_config: {
    max_speed: 1.3,
    slow_speed: 0.2,
    mid_rate: 0.66
  },
  video: {
    default_quality: 20,
    default_res_w: 640,
    default_res_h: 480,
    stream_type: 'mjpeg'
  },
  user_preferences: {
    speed_mode: 'mid',
    head_light: 'off',
    base_light: false,
    zoom_level: 1,
    detection_type: 'none',
    keyboard_control: true,
    vibration: false
  }
}

// 媒体
export const photos = [
  { id: 1, filename: 'photo_001.jpg', timestamp: '2024-01-20 14:30:00', size: 245000 },
  { id: 2, filename: 'photo_002.jpg', timestamp: '2024-01-20 15:45:00', size: 312000 },
  { id: 3, filename: 'photo_003.jpg', timestamp: '2024-01-21 09:15:00', size: 287000 }
]

export const videos = [
  { id: 1, filename: 'video_001.mp4', timestamp: '2024-01-20 14:32:00', size: 15200000, duration: 45 },
  { id: 2, filename: 'video_002.mp4', timestamp: '2024-01-21 10:20:00', size: 28500000, duration: 92 }
]

export const mediaStorage = {
  total: 32000000000,
  used: 4500000000,
  free: 27500000000,
  photos_count: 3,
  videos_count: 2
}

// CV 状态
export const cvStatus = {
  mode: 10301,
  mode_name: 'None',
  motion_lock: false,
  tracking: false,
  target: null
}

// 音频
export const audioFiles = {
  categories: ['robot_started', 'photo_taken', 'recording_started'],
  files: [
    { name: 'startup.wav', category: 'robot_started' },
    { name: 'shutter.wav', category: 'photo_taken' }
  ]
}

export const audioStatus = {
  playing: false,
  volume: 0.5,
  current_file: null
}

// 视频状态
export const videoStatus = {
  streaming: true,
  recording: false,
  width: 640,
  height: 480,
  fps: 30,
  quality: 20
}

// 通用成功响应
export const successResponse = { success: true }

// Mock 延迟模拟网络请求
export const mockDelay = (data, delay = 100) => {
  return new Promise(resolve => setTimeout(() => resolve(data), delay))
}
