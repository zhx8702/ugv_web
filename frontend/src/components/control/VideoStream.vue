<template>
  <div class="video-stream">
    <div class="video-container">
      <!-- MJPEG Stream -->
      <img
        v-if="streamMode === 'mjpeg' && !mockMode"
        ref="mjpegRef"
        :src="mjpegActive ? videoUrl : ''"
        class="video-feed"
        alt="Video Stream"
        @error="handleStreamError"
      />

      <!-- WebRTC Stream -->
      <video
        v-else-if="streamMode === 'webrtc' && !mockMode"
        ref="videoRef"
        autoplay
        playsinline
        muted
        class="video-feed"
      ></video>

      <!-- Mock Video Display -->
      <div v-else-if="mockMode" class="mock-video">
        <div class="mock-grid"></div>
        <div class="mock-noise"></div>
        <div class="mock-content">
          <div class="mock-horizon"></div>
          <div class="mock-target">
            <div class="target-ring ring-1"></div>
            <div class="target-ring ring-2"></div>
            <div class="target-ring ring-3"></div>
            <div class="target-dot"></div>
          </div>
        </div>
      </div>

      <!-- No Stream -->
      <div v-else class="no-stream">
        <div class="no-stream-content">
          <div class="no-stream-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <polygon points="23 7 16 12 23 17 23 7" />
              <rect x="1" y="5" width="15" height="14" rx="2" />
            </svg>
          </div>
          <p class="no-stream-text">NO VIDEO SIGNAL</p>
          <button @click="startStream" class="btn-cyber">
            <span class="btn-text">INITIALIZE STREAM</span>
          </button>
        </div>
      </div>

      <!-- HUD Overlay -->
      <div class="hud-overlay">
        <!-- Corner Brackets -->
        <div class="hud-corner top-left"></div>
        <div class="hud-corner top-right"></div>
        <div class="hud-corner bottom-left"></div>
        <div class="hud-corner bottom-right"></div>
      </div>

      <!-- Top Right Info Panel - Status -->
      <div class="info-panel top-right-panel">
        <div class="info-row">
          <span class="info-label">MODE</span>
          <span class="info-value" :class="detectionTypeClass">{{ detectionTypeLabel }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">VOLT</span>
          <span class="info-value" :class="voltageStatusClass">{{ voltage.toFixed(1) }}V</span>
        </div>
        <div class="info-row">
          <span class="info-label">TEMP</span>
          <span class="info-value" :class="tempStatusClass">{{ temperature.toFixed(0) }}°C</span>
        </div>
        <div class="info-row">
          <span class="info-label">RSSI</span>
          <span class="info-value" :class="rssiStatusClass">{{ rssi }}dBm</span>
        </div>
      </div>

      <!-- Bottom Left Info Panel - Media -->
      <div class="info-panel bottom-left-panel">
        <div class="info-row">
          <span class="info-label">ZOOM</span>
          <span class="info-value status-primary">{{ zoomLevel }}×</span>
        </div>
        <div class="info-row">
          <svg class="info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <polyline points="21 15 16 10 5 21" />
          </svg>
          <span class="info-value">{{ photoCount }}</span>
        </div>
        <div class="info-row">
          <svg class="info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="23 7 16 12 23 17 23 7" />
            <rect x="1" y="5" width="15" height="14" rx="2" />
          </svg>
          <span class="info-value">{{ videoCount }}</span>
        </div>
      </div>

      <!-- Pan Scale (Bottom Edge) -->
      <div class="pan-scale-container">
        <div class="pan-scale-track">
          <div class="pan-scale-bg"></div>
          <div class="pan-scale-marks">
            <span class="pan-mark" style="left: 0%">-90</span>
            <span class="pan-mark" style="left: 25%">-45</span>
            <span class="pan-mark center" style="left: 50%">0</span>
            <span class="pan-mark" style="left: 75%">45</span>
            <span class="pan-mark" style="left: 100%">90</span>
          </div>
          <div class="pan-indicator-container">
            <div class="pan-indicator" :style="{ left: panIndicatorPos + '%' }">
              <div class="indicator-arrow"></div>
              <div class="indicator-value">{{ panAngle.toFixed(0) }}°</div>
            </div>
          </div>
        </div>
        <div class="pan-label">PAN</div>
      </div>

      <!-- Tilt Scale (Right Edge) -->
      <div class="tilt-scale-container">
        <div class="tilt-label">TILT</div>
        <div class="tilt-scale-track">
          <div class="tilt-scale-bg"></div>
          <div class="tilt-scale-marks">
            <span class="tilt-mark" style="top: 0%">60</span>
            <span class="tilt-mark" style="top: 25%">30</span>
            <span class="tilt-mark center" style="top: 50%">0</span>
            <span class="tilt-mark" style="top: 75%">-30</span>
            <span class="tilt-mark" style="top: 100%">-60</span>
          </div>
          <div class="tilt-indicator-container">
            <div class="tilt-indicator" :style="{ top: tiltIndicatorPos + '%' }">
              <div class="indicator-arrow-h"></div>
              <div class="indicator-value">{{ tiltAngle.toFixed(0) }}°</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recording Indicator -->
      <div v-if="recording" class="recording-indicator">
        <span class="rec-dot"></span>
        <span class="rec-text">REC</span>
        <span class="rec-time">{{ recordTime }}</span>
      </div>

      <!-- Light Mode Indicator -->
      <div class="light-indicator" :class="lightModeClass">
        <svg class="light-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
        <span class="light-label">{{ headLightLabel }}</span>
      </div>

      <!-- Mock Mode Label -->
      <div v-if="mockMode" class="mock-label">
        <span class="label-dot"></span>
        SIMULATION
      </div>

      <!-- Crosshair -->
      <div v-if="showCrosshair" class="crosshair">
        <div class="crosshair-h"></div>
        <div class="crosshair-v"></div>
        <div class="crosshair-center"></div>
        <!-- Crosshair corner markers -->
        <div class="crosshair-corner tl"></div>
        <div class="crosshair-corner tr"></div>
        <div class="crosshair-corner bl"></div>
        <div class="crosshair-corner br"></div>
      </div>

      <!-- Detection Overlay -->
      <div v-if="detections.length > 0" class="detection-overlay">
        <div
          v-for="detection in detections"
          :key="detection.id"
          class="detection-box"
          :style="getDetectionStyle(detection)"
        >
          <span class="detection-label">
            {{ detection.label }} {{ detection.confidence }}%
          </span>
        </div>
      </div>

      <!-- Control Bar -->
      <div class="control-bar">
        <div class="control-left">
          <button
            @click="toggleRecord"
            :class="['control-btn', recording ? 'recording' : '']"
          >
            <svg v-if="!recording" class="btn-icon" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="12" cy="12" r="8" />
            </svg>
            <svg v-else class="btn-icon" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="6" width="12" height="12" rx="1" />
            </svg>
            <span>{{ recording ? 'STOP' : 'REC' }}</span>
          </button>
          <button @click="capturePhoto" class="control-btn">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            <span>CAPTURE</span>
          </button>
        </div>

        <div class="control-center">
          <!-- Zoom Controls -->
          <div class="zoom-controls">
            <button
              v-for="zoom in [1, 2, 4]"
              :key="zoom"
              @click="setZoom(zoom)"
              :class="['zoom-btn', zoomLevel === zoom ? 'active' : '']"
            >
              {{ zoom }}×
            </button>
          </div>
        </div>

        <div class="control-right">
          <!-- Flashlight Toggle -->
          <button @click="cycleHeadLight" :class="['control-btn', headLight !== 'off' ? 'active' : '', headLight === 'on' ? 'light-active' : '']" :title="'Light: ' + headLight.toUpperCase()">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
            <span>{{ headLight.toUpperCase() }}</span>
          </button>

          <!-- Crosshair Toggle -->
          <button @click="toggleCrosshair" :class="['control-btn', showCrosshair ? 'active' : '']">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="22" y1="12" x2="18" y2="12" />
              <line x1="6" y1="12" x2="2" y2="12" />
              <line x1="12" y1="6" x2="12" y2="2" />
              <line x1="12" y1="22" x2="12" y2="18" />
            </svg>
          </button>

          <!-- Settings Menu -->
          <div class="dropdown">
            <button @click="toggleSettings" class="control-btn">
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
            </button>
            <div v-if="showSettings" class="dropdown-menu">
              <div class="dropdown-header">STREAM MODE</div>
              <button
                @click="switchStream('mjpeg')"
                :class="['dropdown-item', streamMode === 'mjpeg' ? 'active' : '']"
              >
                <span class="item-check">{{ streamMode === 'mjpeg' ? '◆' : '◇' }}</span>
                MJPEG STREAM
              </button>
              <button
                @click="switchStream('webrtc')"
                :class="['dropdown-item', streamMode === 'webrtc' ? 'active' : '', !webrtcAvailable ? 'disabled' : '']"
                :disabled="!webrtcAvailable"
              >
                <span class="item-check">{{ streamMode === 'webrtc' ? '◆' : '◇' }}</span>
                WEBRTC {{ !webrtcAvailable ? '(N/A)' : '' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useControlStore } from '@/stores/control'
import { useSystemStore } from '@/stores/system'
import { isMockMode as globalMockMode } from '@/services/api'

const controlStore = useControlStore()
const systemStore = useSystemStore()

const {
  zoomLevel,
  recording,
  recordTime,
  detectionType,
  detections,
  panAngle,
  tiltAngle,
  headLight
} = storeToRefs(controlStore)

const {
  temperature,
  voltage,
  rssi,
  photoCount,
  videoCount
} = storeToRefs(systemStore)

const { fetchMediaCount } = systemStore

const { setZoom, capturePhoto, toggleRecord, cycleHeadLight } = controlStore

// Local state
const videoRef = ref(null)
const mjpegRef = ref(null)
const streamMode = ref('mjpeg')
const mjpegActive = ref(true)
const showSettings = ref(false)
const showCrosshair = ref(true)
const webrtcAvailable = ref(false)
const mockMode = ref(false)

// WebRTC state
let peerConnection = null
let pendingStream = null

// Computed
const videoUrl = computed(() => {
  if (import.meta.env.DEV) {
    return '/video_feed'
  }
  const host = window.location.hostname
  const port = 5080
  return `http://${host}:${port}/video_feed`
})

const apiBaseUrl = computed(() => {
  if (import.meta.env.DEV) {
    return '/api'
  }
  const host = window.location.hostname
  const port = 5080
  return `http://${host}:${port}/api`
})

// Detection type display
const detectionTypeLabel = computed(() => {
  const labels = {
    none: 'STANDBY',
    motion: 'MOTION',
    faces: 'FACE',
    objects: 'OBJECT',
    color: 'COLOR',
    hand: 'HAND',
    auto: 'AUTO DRIVE',
    mp_face: 'MP FACE',
    mp_pose: 'POSE'
  }
  return labels[detectionType.value] || 'STANDBY'
})

const detectionTypeClass = computed(() => {
  if (detectionType.value === 'none') return 'status-dim'
  return 'status-active'
})

// Status classes
const tempStatusClass = computed(() => {
  if (temperature.value > 70) return 'status-danger'
  if (temperature.value > 60) return 'status-warning'
  return 'status-good'
})

const voltageStatusClass = computed(() => {
  if (voltage.value < 10.8) return 'status-danger'
  if (voltage.value < 11.2) return 'status-warning'
  return 'status-good'
})

const rssiStatusClass = computed(() => {
  if (rssi.value < -70) return 'status-danger'
  if (rssi.value < -60) return 'status-warning'
  return 'status-good'
})

// Light mode
const headLightLabel = computed(() => {
  const labels = { off: 'OFF', auto: 'AUTO', on: 'ON' }
  return labels[headLight.value] || 'OFF'
})

const lightModeClass = computed(() => {
  if (headLight.value === 'on') return 'light-on'
  if (headLight.value === 'auto') return 'light-auto'
  return 'light-off'
})

// PT indicator positions (convert angle to percentage)
const panIndicatorPos = computed(() => {
  // Pan: -90 to 90 -> 0% to 100%
  return ((panAngle.value + 90) / 180) * 100
})

const tiltIndicatorPos = computed(() => {
  // Tilt: -60 to 60 -> 100% to 0% (inverted for visual)
  return ((60 - tiltAngle.value) / 120) * 100
})

// Methods
function toggleCrosshair() {
  showCrosshair.value = !showCrosshair.value
}

// WebRTC Methods
const startWebRTC = async () => {
  console.log('Starting WebRTC connection...')
  console.log('videoRef.value:', videoRef.value)

  try {
    const config = {
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    }
    peerConnection = new RTCPeerConnection(config)
    peerConnection.addTransceiver('video', { direction: 'recvonly' })

    // 监听连接状态变化
    peerConnection.onconnectionstatechange = () => {
      console.log('Connection state:', peerConnection.connectionState)
    }

    peerConnection.oniceconnectionstatechange = () => {
      console.log('ICE connection state:', peerConnection.iceConnectionState)
    }

    peerConnection.ontrack = (event) => {
      console.log('Track received:', event.track.kind, event.streams)
      if (event.streams && event.streams[0]) {
        pendingStream = event.streams[0]
        // 确保 video 元素存在
        if (videoRef.value) {
          console.log('Setting srcObject on video element')
          videoRef.value.srcObject = pendingStream
        } else {
          console.log('videoRef.value is null, stream saved as pending')
        }
      }
    }

    const offer = await peerConnection.createOffer()
    await peerConnection.setLocalDescription(offer)
    console.log('Local description set')

    await new Promise((resolve) => {
      if (peerConnection.iceGatheringState === 'complete') {
        resolve()
      } else {
        const timeout = setTimeout(() => resolve(), 3000)
        peerConnection.onicegatheringstatechange = () => {
          console.log('ICE gathering state:', peerConnection.iceGatheringState)
          if (peerConnection.iceGatheringState === 'complete') {
            clearTimeout(timeout)
            resolve()
          }
        }
      }
    })

    console.log('Sending offer to server...')
    const response = await fetch(`${apiBaseUrl.value}/video/webrtc/offer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sdp: peerConnection.localDescription.sdp,
        type: peerConnection.localDescription.type
      })
    })

    if (!response.ok) {
      throw new Error('WebRTC not available')
    }

    const answer = await response.json()
    console.log('Received answer from server')
    await peerConnection.setRemoteDescription(answer)
    console.log('Remote description set')
  } catch (error) {
    console.error('WebRTC error:', error)
    streamMode.value = 'mjpeg'
  }
}

const stopWebRTC = () => {
  if (peerConnection) {
    peerConnection.close()
    peerConnection = null
  }
  pendingStream = null
  if (videoRef.value) {
    videoRef.value.srcObject = null
  }
}

const startStream = () => {
  streamMode.value = 'mjpeg'
  mockMode.value = false
}

const switchStream = async (mode) => {
  if (streamMode.value === 'webrtc') {
    stopWebRTC()
  }

  if (streamMode.value === 'mjpeg') {
    mjpegActive.value = false
    await new Promise(resolve => setTimeout(resolve, 100))
  }

  // 切换模式时重置 mockMode，让新的流模式可以正常渲染
  mockMode.value = false
  streamMode.value = mode
  showSettings.value = false

  if (mode === 'mjpeg') {
    mjpegActive.value = true
  } else if (mode === 'webrtc') {
    // 等待 Vue DOM 更新完成后再启动 WebRTC
    await nextTick()
    startWebRTC()
  }
}

const checkWebRTCAvailability = async () => {
  // Mock 模式下跳过 WebRTC 检查
  if (globalMockMode) {
    webrtcAvailable.value = false
    return
  }
  try {
    const response = await fetch(`${apiBaseUrl.value}/video/webrtc/status`)
    if (response.ok) {
      const data = await response.json()
      webrtcAvailable.value = data.available !== false
    }
  } catch (e) {
    webrtcAvailable.value = false
  }
}

const toggleSettings = () => {
  showSettings.value = !showSettings.value
}

const handleStreamError = () => {
  console.error('Stream error - enabling mock mode')
  mockMode.value = true
}

const getDetectionStyle = (detection) => {
  return {
    left: `${detection.x}%`,
    top: `${detection.y}%`,
    width: `${detection.width}%`,
    height: `${detection.height}%`
  }
}

const handleClickOutside = (e) => {
  if (showSettings.value && !e.target.closest('.dropdown')) {
    showSettings.value = false
  }
}

// Watch videoRef to apply pending stream when video element becomes available
watch(videoRef, (newVideoEl) => {
  if (newVideoEl && pendingStream) {
    console.log('videoRef now available, applying pending stream')
    newVideoEl.srcObject = pendingStream
  }
})

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  // Mock 模式下启用视频占位符
  if (globalMockMode) {
    mockMode.value = true
  }
  checkWebRTCAvailability()
  fetchMediaCount()
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  stopWebRTC()
})
</script>

<style scoped>
.video-stream {
  @apply w-full;
}

.video-container {
  @apply relative overflow-hidden;
  background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 100%);
  aspect-ratio: 16 / 9;
  border: 1px solid rgba(0, 240, 255, 0.3);
}

.video-feed {
  @apply w-full h-full object-cover;
}

/* Mock Video Display */
.mock-video {
  @apply absolute inset-0;
  background: linear-gradient(180deg, #0a0f14 0%, #0d1520 50%, #0a0f14 100%);
}

.mock-grid {
  @apply absolute inset-0;
  background-image:
    linear-gradient(rgba(0, 240, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 240, 255, 0.05) 1px, transparent 1px);
  background-size: 40px 40px;
}

.mock-noise {
  @apply absolute inset-0;
  background: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  opacity: 0.03;
}

.mock-content {
  @apply absolute inset-0 flex items-center justify-center;
}

.mock-horizon {
  @apply absolute left-0 right-0 h-px;
  top: 50%;
  background: linear-gradient(90deg, transparent 0%, rgba(0, 240, 255, 0.3) 20%, rgba(0, 240, 255, 0.5) 50%, rgba(0, 240, 255, 0.3) 80%, transparent 100%);
}

.mock-target {
  @apply relative w-24 h-24;
}

.target-ring {
  @apply absolute rounded-full border;
  border-color: rgba(0, 240, 255, 0.4);
}

.ring-1 { @apply inset-0; animation: ringPulse 2s ease-in-out infinite; }
.ring-2 { @apply inset-3; animation: ringPulse 2s ease-in-out infinite 0.3s; }
.ring-3 { @apply inset-6; animation: ringPulse 2s ease-in-out infinite 0.6s; }

@keyframes ringPulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.05); }
}

.target-dot {
  @apply absolute w-2 h-2 rounded-full bg-primary;
  top: 50%; left: 50%; transform: translate(-50%, -50%);
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.8);
}

.mock-label {
  @apply absolute bottom-14 left-3 flex items-center gap-2;
  @apply text-[10px] font-orbitron tracking-wider text-warning/70;
  z-index: 20;
}

.label-dot {
  @apply w-1.5 h-1.5 rounded-full bg-warning;
  animation: blink 1s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* No Stream */
.no-stream {
  @apply absolute inset-0 flex items-center justify-center;
  background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 100%);
}

.no-stream-content {
  @apply flex flex-col items-center gap-4 text-center;
}

.no-stream-icon {
  @apply w-16 h-16 text-primary/40;
}

.no-stream-text {
  @apply text-sm font-orbitron tracking-wider text-dark-text-tertiary;
}

.btn-cyber {
  @apply px-6 py-2 text-xs font-orbitron tracking-wider text-primary border border-primary/50 transition-all duration-300;
  background: rgba(0, 240, 255, 0.1);
  clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
}

.btn-cyber:hover {
  @apply border-primary;
  background: rgba(0, 240, 255, 0.2);
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
}

/* HUD Overlay */
.hud-overlay {
  @apply absolute inset-0 pointer-events-none;
  z-index: 5;
}

.hud-corner {
  @apply absolute w-6 h-6;
  border-color: rgba(0, 240, 255, 0.5);
}

.hud-corner.top-left { @apply top-2 left-2 border-l-2 border-t-2; }
.hud-corner.top-right { @apply top-2 right-2 border-r-2 border-t-2; }
.hud-corner.bottom-left { @apply bottom-2 left-2 border-l-2 border-b-2; }
.hud-corner.bottom-right { @apply bottom-2 right-2 border-r-2 border-b-2; }

/* Info Panels */
.info-panel {
  @apply absolute flex flex-col gap-1 px-2 py-1.5;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(0, 240, 255, 0.2);
  backdrop-filter: blur(4px);
  z-index: 15;
}

.top-right-panel { @apply top-3 right-3; }
.bottom-left-panel { @apply bottom-14 left-3; }

.info-row {
  @apply flex items-center gap-2;
}

.info-label {
  @apply text-[9px] font-orbitron tracking-wider text-dark-text-tertiary w-8;
}

.info-value {
  @apply text-[11px] font-mono font-bold;
}

.info-icon {
  @apply w-3 h-3 text-primary;
}

/* Status Colors */
.status-good { color: #00ff88; text-shadow: 0 0 6px rgba(0, 255, 136, 0.5); }
.status-warning { color: #ffff00; text-shadow: 0 0 6px rgba(255, 255, 0, 0.5); }
.status-danger { color: #ff0040; text-shadow: 0 0 6px rgba(255, 0, 64, 0.5); }
.status-primary { color: #00f0ff; text-shadow: 0 0 6px rgba(0, 240, 255, 0.5); }
.status-active { color: #00ff88; text-shadow: 0 0 8px rgba(0, 255, 136, 0.6); }
.status-dim { color: #666; }

/* Pan Scale (Bottom Edge) */
.pan-scale-container {
  @apply absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1;
  z-index: 15;
}

.pan-scale-track {
  @apply relative;
  width: 200px;
  height: 24px;
}

.pan-scale-bg {
  @apply absolute bottom-0 left-0 right-0 h-1;
  background: linear-gradient(90deg,
    rgba(0, 240, 255, 0.1) 0%,
    rgba(0, 240, 255, 0.3) 50%,
    rgba(0, 240, 255, 0.1) 100%
  );
}

.pan-scale-marks {
  @apply absolute inset-0 flex justify-between items-start;
}

.pan-mark {
  @apply absolute text-[8px] font-mono text-dark-text-tertiary/70 -translate-x-1/2;
}

.pan-mark.center {
  @apply text-primary font-bold;
}

.pan-indicator-container {
  @apply absolute bottom-0 left-0 right-0 h-full;
}

.pan-indicator {
  @apply absolute bottom-0 flex flex-col items-center;
  transform: translateX(-50%);
  transition: left 0.1s ease-out;
}

.indicator-arrow {
  @apply w-0 h-0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-bottom: 8px solid #00f0ff;
  filter: drop-shadow(0 0 4px rgba(0, 240, 255, 0.8));
}

.indicator-value {
  @apply text-[10px] font-mono font-bold text-primary mt-0.5;
  text-shadow: 0 0 8px rgba(0, 240, 255, 0.5);
}

.pan-label {
  @apply text-[8px] font-orbitron tracking-widest text-dark-text-tertiary/60;
}

/* Tilt Scale (Right Edge) */
.tilt-scale-container {
  @apply absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1;
  z-index: 15;
}

.tilt-label {
  @apply text-[8px] font-orbitron tracking-widest text-dark-text-tertiary/60;
  writing-mode: vertical-rl;
  text-orientation: mixed;
}

.tilt-scale-track {
  @apply relative;
  width: 28px;
  height: 120px;
}

.tilt-scale-bg {
  @apply absolute top-0 bottom-0 right-0 w-1;
  background: linear-gradient(180deg,
    rgba(0, 240, 255, 0.1) 0%,
    rgba(0, 240, 255, 0.3) 50%,
    rgba(0, 240, 255, 0.1) 100%
  );
}

.tilt-scale-marks {
  @apply absolute inset-0;
}

.tilt-mark {
  @apply absolute right-2 text-[8px] font-mono text-dark-text-tertiary/70 translate-y-[-50%];
}

.tilt-mark.center {
  @apply text-primary font-bold;
}

.tilt-indicator-container {
  @apply absolute top-0 bottom-0 right-0 w-full;
}

.tilt-indicator {
  @apply absolute right-0 flex items-center;
  transform: translateY(-50%);
  transition: top 0.1s ease-out;
}

.indicator-arrow-h {
  @apply w-0 h-0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-right: 8px solid #00f0ff;
  filter: drop-shadow(0 0 4px rgba(0, 240, 255, 0.8));
}

.tilt-indicator .indicator-value {
  @apply absolute right-3 text-[10px] font-mono font-bold text-primary whitespace-nowrap;
  text-shadow: 0 0 8px rgba(0, 240, 255, 0.5);
}

/* Recording Indicator */
.recording-indicator {
  @apply absolute top-3 left-1/2 -translate-x-1/2 flex items-center gap-2 px-3 py-1;
  background: rgba(255, 0, 64, 0.3);
  border: 1px solid rgba(255, 0, 64, 0.6);
  z-index: 20;
}

.rec-dot {
  @apply w-2 h-2 rounded-full bg-danger;
  animation: blink 1s ease-in-out infinite;
}

.rec-text {
  @apply text-[10px] font-orbitron tracking-wider text-danger;
}

.rec-time {
  @apply text-xs font-mono text-danger;
}

/* Light Indicator */
.light-indicator {
  @apply absolute top-3 right-28 flex items-center gap-1.5 px-2 py-1;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(0, 240, 255, 0.2);
  z-index: 15;
}

.light-icon {
  @apply w-3 h-3;
}

.light-label {
  @apply text-[9px] font-orbitron tracking-wider;
}

.light-off { @apply text-dark-text-tertiary; }
.light-auto { @apply text-warning; }
.light-auto .light-icon { @apply text-warning; }
.light-on { @apply text-primary; }
.light-on .light-icon { @apply text-primary; }

/* Crosshair */
.crosshair {
  @apply absolute inset-0 flex items-center justify-center pointer-events-none;
  z-index: 10;
}

.crosshair-h, .crosshair-v {
  @apply absolute;
  background: rgba(0, 240, 255, 0.4);
}

.crosshair-h { @apply w-12 h-px; }
.crosshair-v { @apply w-px h-12; }

.crosshair-center {
  @apply absolute w-3 h-3 rounded-full;
  border: 1px solid rgba(0, 240, 255, 0.5);
}

.crosshair-corner {
  @apply absolute w-4 h-4;
  border-color: rgba(0, 240, 255, 0.3);
}

.crosshair-corner.tl { top: calc(50% - 24px); left: calc(50% - 24px); @apply border-l border-t; }
.crosshair-corner.tr { top: calc(50% - 24px); right: calc(50% - 24px); @apply border-r border-t; }
.crosshair-corner.bl { bottom: calc(50% - 24px); left: calc(50% - 24px); @apply border-l border-b; }
.crosshair-corner.br { bottom: calc(50% - 24px); right: calc(50% - 24px); @apply border-r border-b; }

/* Detection Overlay */
.detection-overlay {
  @apply absolute inset-0 pointer-events-none;
  z-index: 12;
}

.detection-box {
  @apply absolute;
  border: 2px solid #00ff88;
  box-shadow: 0 0 15px rgba(0, 255, 136, 0.5), inset 0 0 15px rgba(0, 255, 136, 0.1);
}

.detection-label {
  @apply absolute -top-5 left-0 px-1.5 py-0.5 text-[9px] font-orbitron tracking-wider text-dark-bg-primary;
  background: #00ff88;
}

/* Control Bar */
.control-bar {
  @apply absolute bottom-0 left-0 right-0 p-2 flex items-center justify-between;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.9) 0%, transparent 100%);
  z-index: 25;
}

.control-left, .control-center, .control-right {
  @apply flex items-center gap-1.5;
}

.control-btn {
  @apply flex items-center gap-1 px-2 py-1;
  @apply text-[9px] font-orbitron tracking-wider text-dark-text-secondary transition-all duration-200;
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid rgba(0, 240, 255, 0.2);
}

.control-btn:hover {
  @apply text-primary border-primary;
  background: rgba(0, 240, 255, 0.2);
}

.control-btn.active {
  @apply text-primary border-primary;
  background: rgba(0, 240, 255, 0.15);
}

.control-btn.recording {
  @apply text-danger border-danger;
  background: rgba(255, 0, 64, 0.2);
}

.control-btn.light-active {
  @apply text-warning border-warning;
  background: rgba(255, 200, 0, 0.25);
}

.btn-icon { @apply w-3 h-3; }

/* Zoom Controls */
.zoom-controls {
  @apply flex overflow-hidden;
  border: 1px solid rgba(0, 240, 255, 0.2);
}

.zoom-btn {
  @apply px-2.5 py-1 text-[9px] font-orbitron tracking-wider text-dark-text-tertiary transition-all duration-200;
  background: rgba(0, 240, 255, 0.05);
}

.zoom-btn:hover {
  @apply text-primary;
  background: rgba(0, 240, 255, 0.15);
}

.zoom-btn.active {
  @apply text-dark-bg-primary;
  background: #00f0ff;
}

/* Dropdown */
.dropdown { @apply relative; }

.dropdown-menu {
  @apply absolute bottom-full right-0 mb-2 min-w-40 overflow-hidden;
  background: rgba(10, 15, 20, 0.95);
  border: 1px solid rgba(0, 240, 255, 0.3);
  backdrop-filter: blur(10px);
  z-index: 30;
}

.dropdown-header {
  @apply px-3 py-1.5 text-[8px] font-orbitron tracking-wider text-dark-text-tertiary;
  background: rgba(0, 240, 255, 0.05);
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.dropdown-item {
  @apply w-full flex items-center gap-2 px-3 py-1.5;
  @apply text-[9px] font-orbitron tracking-wider text-dark-text-secondary transition-all duration-200;
}

.dropdown-item:hover {
  @apply text-primary;
  background: rgba(0, 240, 255, 0.1);
}

.dropdown-item.active { @apply text-primary; }
.dropdown-item.disabled { @apply opacity-40 cursor-not-allowed; }
.item-check { @apply text-primary; }
</style>
