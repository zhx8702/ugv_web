import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  sendCommand as sendApiCommand,
  sendJsonCommand as sendApiJsonCommand,
  capturePhoto as apiCapturePhoto,
  startRecording,
  stopRecording,
  setVideoZoom,
  setLights as apiSetLights,
  lockMotor as apiLockMotor,
  unlockMotor as apiUnlockMotor,
  getCVStatus
} from '@/services/api'
import { useWebSocket } from '@/composables/useWebSocket'
import { useSystemStore } from '@/stores/system'

export const useControlStore = defineStore('control', () => {
  const { sendCommand, sendJsonCommand, connected } = useWebSocket()

  // 速度控制
  const speedMode = ref('mid')
  const speedValue = ref(0.66)

  // 云台控制
  const panAngle = ref(0)
  const tiltAngle = ref(0)
  const ptSteady = ref(false)
  const ptAhead = ref(false)

  // 灯光控制
  const headLight = ref('off')
  const baseLight = ref(false)

  // 电机锁定
  const motorLocked = ref(false)

  // 检测设置
  const detectionType = ref('none')
  const detectionReaction = ref('none')
  const tracking = ref(false)
  const autoDrive = ref(false)

  // AI功能（已合并到 detectionType）
  const detections = ref([])

  // 视频设置
  const zoomLevel = ref(1)
  const recording = ref(false)
  const recordTime = ref('00:00')
  let recordTimer = null
  let recordSeconds = 0

  // 检测轮询
  let detectionPollTimer = null

  // 方法
  function setSpeed(mode) {
    speedMode.value = mode
    const speedMap = {
      slow: 0.2,
      mid: 0.66,
      fast: 1.3
    }
    speedValue.value = speedMap[mode] || 0.66
  }

  function moveRover(leftSpeed, rightSpeed) {
    const cmd = {
      T: 1, // cmd_movition_ctrl
      L: leftSpeed * speedValue.value,
      R: rightSpeed * speedValue.value
    }
    // Use WebSocket if connected, fallback to API
    if (connected.value) {
      sendJsonCommand(cmd)
    } else {
      sendApiJsonCommand(cmd)
    }
  }

  function stopRover() {
    moveRover(0, 0)
  }

  function movePT(pan, tilt) {
    // 更新本地状态并限制范围
    panAngle.value = Math.max(-90, Math.min(90, panAngle.value + pan))
    tiltAngle.value = Math.max(-60, Math.min(60, tiltAngle.value + tilt))

    const cmd = {
      T: 133, // cmd_gimbal_ctrl
      X: panAngle.value,
      Y: tiltAngle.value,
      SPD: 200,  // 速度
      ACC: 10    // 加速度
    }
    if (connected.value) {
      sendJsonCommand(cmd)
    } else {
      sendApiJsonCommand(cmd)
    }
  }

  function centerPT() {
    const cmd = {
      T: 133,
      X: 0,
      Y: 0,
      SPD: 200,  // 速度
      ACC: 10    // 加速度
    }
    if (connected.value) {
      sendJsonCommand(cmd)
    } else {
      sendApiJsonCommand(cmd)
    }
    panAngle.value = 0
    tiltAngle.value = 0
  }

  function setDetectionMode(type) {
    detectionType.value = type
    // 发送命令到后端（合并后的统一映射）
    const typeMap = {
      none: 10301,    // cv_none
      motion: 10302,  // cv_moti
      faces: 10303,   // cv_face (OpenCV)
      objects: 10304, // cv_objs
      color: 10305,   // cv_clor
      hand: 10306,    // mp_hand
      auto: 10307,    // cv_auto
      mp_face: 10308, // mp_face (MediaPipe)
      mp_pose: 10309  // mp_pose
    }
    if (typeMap[type]) {
      if (connected.value) {
        sendCommand(typeMap[type])
      } else {
        sendApiCommand(typeMap[type])
      }
    }
    // 启动或停止检测轮询
    if (type !== 'none') {
      startDetectionPolling()
    } else {
      stopDetectionPolling()
    }
  }

  function toggleTracking() {
    tracking.value = !tracking.value
    const code = tracking.value ? 10501 : 10502 // mc_lock / mc_unlo
    if (connected.value) {
      sendCommand(code)
    } else {
      sendApiCommand(code)
    }
  }

  function toggleAutoDrive() {
    autoDrive.value = !autoDrive.value
    if (connected.value) {
      sendCommand(10307) // cv_auto
    } else {
      sendApiCommand(10307)
    }
  }

  function setHeadLight(mode) {
    // mode: 'off', 'auto', 'on'
    headLight.value = mode
    const headPwm = mode === 'off' ? 0 : (mode === 'on' ? 255 : 128)
    const basePwm = baseLight.value ? 255 : 0

    const cmd = {
      T: 132, // cmd_light_ctrl
      IO4: basePwm,
      IO5: headPwm
    }
    if (connected.value) {
      sendJsonCommand(cmd)
    } else {
      apiSetLights(basePwm, headPwm)
    }
  }

  function setBaseLight(on) {
    baseLight.value = on
    const basePwm = on ? 255 : 0
    const headPwm = headLight.value === 'off' ? 0 : (headLight.value === 'on' ? 255 : 128)

    const cmd = {
      T: 132, // cmd_light_ctrl
      IO4: basePwm,
      IO5: headPwm
    }
    if (connected.value) {
      sendJsonCommand(cmd)
    } else {
      apiSetLights(basePwm, headPwm)
    }
  }

  function toggleBaseLight() {
    setBaseLight(!baseLight.value)
  }

  function cycleHeadLight() {
    // Cycle through: off -> auto -> on -> off
    const modes = ['off', 'auto', 'on']
    const currentIndex = modes.indexOf(headLight.value)
    const nextIndex = (currentIndex + 1) % modes.length
    setHeadLight(modes[nextIndex])
  }

  // 电机锁定控制
  async function toggleMotorLock() {
    try {
      if (motorLocked.value) {
        await apiUnlockMotor()
        motorLocked.value = false
      } else {
        await apiLockMotor()
        motorLocked.value = true
      }
    } catch (e) {
      console.error('Toggle motor lock failed:', e)
    }
  }

  async function lockMotor() {
    try {
      await apiLockMotor()
      motorLocked.value = true
    } catch (e) {
      console.error('Lock motor failed:', e)
    }
  }

  async function unlockMotor() {
    try {
      await apiUnlockMotor()
      motorLocked.value = false
    } catch (e) {
      console.error('Unlock motor failed:', e)
    }
  }

  async function setZoom(level) {
    zoomLevel.value = level
    try {
      await setVideoZoom(level)
    } catch (e) {
      console.error('Set zoom failed:', e)
    }
  }

  async function capturePhoto() {
    try {
      await apiCapturePhoto()
      // 更新媒体计数
      const systemStore = useSystemStore()
      systemStore.fetchMediaCount()
    } catch (e) {
      console.error('Capture photo failed:', e)
    }
  }

  // 开始录制
  async function startRecord() {
    if (recording.value) return
    try {
      await startRecording()
      recording.value = true
      // 启动计时器
      recordSeconds = 0
      recordTime.value = '00:00'
      recordTimer = setInterval(() => {
        recordSeconds++
        const mins = Math.floor(recordSeconds / 60).toString().padStart(2, '0')
        const secs = (recordSeconds % 60).toString().padStart(2, '0')
        recordTime.value = `${mins}:${secs}`
      }, 1000)
    } catch (e) {
      console.error('Start record failed:', e)
    }
  }

  // 停止录制
  async function stopRecord() {
    if (!recording.value) return
    try {
      await stopRecording()
      recording.value = false
      // 停止计时器
      if (recordTimer) {
        clearInterval(recordTimer)
        recordTimer = null
      }
      recordSeconds = 0
      recordTime.value = '00:00'
      // 更新媒体计数
      const systemStore = useSystemStore()
      systemStore.fetchMediaCount()
    } catch (e) {
      console.error('Stop record failed:', e)
    }
  }

  // 切换录制
  async function toggleRecord() {
    if (recording.value) {
      await stopRecord()
    } else {
      await startRecord()
    }
  }

  // 获取CV检测状态
  async function fetchDetections() {
    try {
      const status = await getCVStatus()
      if (status && status.detections) {
        detections.value = status.detections
      }
    } catch (e) {
      // 静默失败，避免频繁报错
    }
  }

  // 启动检测轮询
  function startDetectionPolling() {
    if (detectionPollTimer) return
    // 每500ms轮询一次检测结果
    detectionPollTimer = setInterval(fetchDetections, 500)
  }

  // 停止检测轮询
  function stopDetectionPolling() {
    if (detectionPollTimer) {
      clearInterval(detectionPollTimer)
      detectionPollTimer = null
    }
    detections.value = []
  }

  return {
    speedMode,
    speedValue,
    panAngle,
    tiltAngle,
    ptSteady,
    ptAhead,
    headLight,
    baseLight,
    motorLocked,
    detectionType,
    detectionReaction,
    tracking,
    autoDrive,
    detections,
    zoomLevel,
    recording,
    recordTime,
    setSpeed,
    moveRover,
    stopRover,
    movePT,
    centerPT,
    setDetectionMode,
    toggleTracking,
    toggleAutoDrive,
    setZoom,
    capturePhoto,
    startRecord,
    stopRecord,
    toggleRecord,
    setHeadLight,
    setBaseLight,
    toggleBaseLight,
    cycleHeadLight,
    toggleMotorLock,
    lockMotor,
    unlockMotor,
    startDetectionPolling,
    stopDetectionPolling,
    fetchDetections
  }
})
