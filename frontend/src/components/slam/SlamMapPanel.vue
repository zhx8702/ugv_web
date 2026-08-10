<template>
  <div class="slam-map-panel">
    <!-- Map Canvas -->
    <div class="map-wrapper" ref="mapWrapper">
      <canvas
        ref="mapCanvas"
        class="map-canvas"
        @mousedown="onMouseDown"
        @mousemove="onMouseMove"
        @mouseup="onMouseUp"
        @wheel="onWheel"
        @click="onMapClick"
      ></canvas>

      <!-- Robot info overlay -->
      <div class="robot-info">
        <span>X: {{ robotPose.x.toFixed(2) }}m</span>
        <span>Y: {{ robotPose.y.toFixed(2) }}m</span>
        <span>θ: {{ robotPose.theta.toFixed(1) }}°</span>
      </div>

      <!-- Nav goal marker -->
      <div v-if="navGoal" class="nav-goal-info">
        GOAL: {{ navGoal.x.toFixed(2) }}, {{ navGoal.y.toFixed(2) }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRosbridge } from '@/composables/useRosbridge'
import { useROS2Store } from '@/stores/ros2'

const props = defineProps({
  navMode: { type: Boolean, default: false },
})

const emit = defineEmits(['goal-set'])

const ros2Store = useROS2Store()
const { rosConnected, connect, subscribe, publish } = useRosbridge()

// Refs
const mapCanvas = ref(null)
const mapWrapper = ref(null)

// Map data
const mapInfo = reactive({
  width: 0,
  height: 0,
  resolution: 0.05, // meters per pixel
  originX: 0,
  originY: 0,
  data: null,
})

const robotPose = reactive({ x: 0, y: 0, theta: 0 })
const navGoal = ref(null)
const scanPoints = ref([])
const navPath = ref([])

// Pan/zoom state
const viewState = reactive({
  scale: 1,
  offsetX: 0,
  offsetY: 0,
  dragging: false,
  dragStartX: 0,
  dragStartY: 0,
})

let mapSubscription = null
let poseSubscription = null
let scanSubscription = null
let pathSubscription = null
let animFrame = null

// ----------------------------------------------------------------
// Rosbridge connection & subscriptions
// ----------------------------------------------------------------

function setupSubscriptions() {
  if (!rosConnected.value) return

  // Subscribe to /map (OccupancyGrid)
  mapSubscription = subscribe('/map', 'nav_msgs/OccupancyGrid', (msg) => {
    mapInfo.width = msg.info.width
    mapInfo.height = msg.info.height
    mapInfo.resolution = msg.info.resolution
    mapInfo.originX = msg.info.origin.position.x
    mapInfo.originY = msg.info.origin.position.y
    mapInfo.data = msg.data
    renderMap()
  }, 500) // throttle to 2 Hz

  // Subscribe to /robot_pose (PoseStamped)
  poseSubscription = subscribe('/robot_pose', 'geometry_msgs/PoseStamped', (msg) => {
    robotPose.x = msg.pose.position.x
    robotPose.y = msg.pose.position.y

    // Quaternion to yaw
    const q = msg.pose.orientation
    const siny = 2 * (q.w * q.z + q.x * q.y)
    const cosy = 1 - 2 * (q.y * q.y + q.z * q.z)
    robotPose.theta = Math.atan2(siny, cosy) * (180 / Math.PI)

    renderMap()
  }, 200)

  // Subscribe to /scan for laser overlay
  scanSubscription = subscribe('/scan', 'sensor_msgs/LaserScan', (msg) => {
    const points = []
    let angle = msg.angle_min
    for (const r of msg.ranges) {
      if (r > msg.range_min && r < msg.range_max && isFinite(r)) {
        // Transform scan point to map frame (approximate: robot pose + scan angle)
        const worldAngle = (robotPose.theta * Math.PI / 180) + angle
        points.push({
          x: robotPose.x + r * Math.cos(worldAngle),
          y: robotPose.y + r * Math.sin(worldAngle),
        })
      }
      angle += msg.angle_increment
    }
    scanPoints.value = points
  }, 500)

  // Subscribe to /plan (nav2 planned path)
  pathSubscription = subscribe('/plan', 'nav_msgs/Path', (msg) => {
    navPath.value = msg.poses.map(p => ({
      x: p.pose.position.x,
      y: p.pose.position.y,
    }))
    renderMap()
  }, 1000)
}

function cleanupSubscriptions() {
  if (mapSubscription) { mapSubscription.unsubscribe(); mapSubscription = null }
  if (poseSubscription) { poseSubscription.unsubscribe(); poseSubscription = null }
  if (pathSubscription) { pathSubscription.unsubscribe(); pathSubscription = null }
  if (scanSubscription) { scanSubscription.unsubscribe(); scanSubscription = null }
}

// ----------------------------------------------------------------
// Canvas rendering
// ----------------------------------------------------------------

function renderMap() {
  if (!mapCanvas.value) return
  const canvas = mapCanvas.value
  const ctx = canvas.getContext('2d')

  // Size canvas to wrapper
  const wrapper = mapWrapper.value
  if (wrapper) {
    canvas.width = wrapper.clientWidth
    canvas.height = wrapper.clientHeight
  }

  const w = canvas.width
  const h = canvas.height

  // Clear
  ctx.fillStyle = '#0a0f14'
  ctx.fillRect(0, 0, w, h)

  if (!mapInfo.data || mapInfo.width === 0) {
    ctx.fillStyle = '#333'
    ctx.font = '14px monospace'
    ctx.textAlign = 'center'
    ctx.fillText('Waiting for /map data...', w / 2, h / 2)
    return
  }

  ctx.save()

  // Apply pan/zoom
  ctx.translate(w / 2 + viewState.offsetX, h / 2 + viewState.offsetY)
  ctx.scale(viewState.scale, viewState.scale)

  // Draw occupancy grid
  const cellSize = 1 // 1 pixel per cell at scale=1
  const mapW = mapInfo.width
  const mapH = mapInfo.height
  const startX = -mapW / 2
  const startY = -mapH / 2

  const imgData = ctx.createImageData(mapW, mapH)
  for (let i = 0; i < mapInfo.data.length; i++) {
    const val = mapInfo.data[i]
    const px = i * 4
    if (val === -1 || val === 255) {
      // Unknown – dark gray
      imgData.data[px] = 40
      imgData.data[px + 1] = 40
      imgData.data[px + 2] = 50
    } else if (val === 0) {
      // Free – dark
      imgData.data[px] = 20
      imgData.data[px + 1] = 25
      imgData.data[px + 2] = 30
    } else {
      // Occupied – bright cyan
      const intensity = Math.min(255, val * 2.5)
      imgData.data[px] = 0
      imgData.data[px + 1] = Math.floor(intensity * 0.9)
      imgData.data[px + 2] = intensity
    }
    imgData.data[px + 3] = 255
  }

  // Put image data onto an offscreen canvas then draw scaled
  const offscreen = new OffscreenCanvas(mapW, mapH)
  const offCtx = offscreen.getContext('2d')
  offCtx.putImageData(imgData, 0, 0)
  ctx.drawImage(offscreen, startX, startY, mapW, mapH)

  // Helper: world coords → canvas pixel coords
  const worldToPixel = (wx, wy) => {
    const px = (wx - mapInfo.originX) / mapInfo.resolution + startX
    // OccupancyGrid is row-major from bottom, canvas Y is flipped
    const py = mapH - (wy - mapInfo.originY) / mapInfo.resolution + startY
    return [px, py]
  }

  // Draw laser scan points
  ctx.fillStyle = 'rgba(0, 255, 136, 0.6)'
  for (const pt of scanPoints.value) {
    const [px, py] = worldToPixel(pt.x, pt.y)
    ctx.fillRect(px - 0.5, py - 0.5, 1, 1)
  }

  // Draw navigation path
  if (navPath.value.length > 1) {
    ctx.strokeStyle = 'rgba(255, 200, 0, 0.7)'
    ctx.lineWidth = 1.5
    ctx.setLineDash([3, 3])
    ctx.beginPath()
    const [startPx, startPy] = worldToPixel(navPath.value[0].x, navPath.value[0].y)
    ctx.moveTo(startPx, startPy)
    for (let i = 1; i < navPath.value.length; i++) {
      const [npx, npy] = worldToPixel(navPath.value[i].x, navPath.value[i].y)
      ctx.lineTo(npx, npy)
    }
    ctx.stroke()
    ctx.setLineDash([])
  }

  // Draw robot position
  const [rx, ry] = worldToPixel(robotPose.x, robotPose.y)
  const thetaRad = robotPose.theta * Math.PI / 180

  ctx.save()
  ctx.translate(rx, ry)
  ctx.rotate(-thetaRad)

  // Triangle pointing in heading direction
  ctx.fillStyle = '#00f0ff'
  ctx.beginPath()
  ctx.moveTo(6, 0)
  ctx.lineTo(-4, -4)
  ctx.lineTo(-4, 4)
  ctx.closePath()
  ctx.fill()

  ctx.strokeStyle = 'rgba(0, 240, 255, 0.4)'
  ctx.lineWidth = 0.5
  ctx.beginPath()
  ctx.arc(0, 0, 8, 0, Math.PI * 2)
  ctx.stroke()

  ctx.restore()

  // Draw navigation goal if set
  if (navGoal.value) {
    const [gx, gy] = worldToPixel(navGoal.value.x, navGoal.value.y)
    ctx.strokeStyle = '#ff0040'
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.arc(gx, gy, 6, 0, Math.PI * 2)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(gx - 8, gy)
    ctx.lineTo(gx + 8, gy)
    ctx.moveTo(gx, gy - 8)
    ctx.lineTo(gx, gy + 8)
    ctx.stroke()
  }

  ctx.restore()
}

// ----------------------------------------------------------------
// Mouse interaction
// ----------------------------------------------------------------

function onMouseDown(e) {
  viewState.dragging = true
  viewState.dragStartX = e.clientX - viewState.offsetX
  viewState.dragStartY = e.clientY - viewState.offsetY
}

function onMouseMove(e) {
  if (!viewState.dragging) return
  viewState.offsetX = e.clientX - viewState.dragStartX
  viewState.offsetY = e.clientY - viewState.dragStartY
  renderMap()
}

function onMouseUp() {
  viewState.dragging = false
}

function onWheel(e) {
  e.preventDefault()
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  viewState.scale = Math.max(0.2, Math.min(10, viewState.scale * delta))
  renderMap()
}

function onMapClick(e) {
  if (!props.navMode || viewState.dragging) return
  if (!mapInfo.data || mapInfo.width === 0) return

  const canvas = mapCanvas.value
  const rect = canvas.getBoundingClientRect()
  const cx = e.clientX - rect.left
  const cy = e.clientY - rect.top

  // Reverse the transform to get map pixel coords
  const w = canvas.width
  const h = canvas.height
  const mapX = (cx - w / 2 - viewState.offsetX) / viewState.scale
  const mapY = (cy - h / 2 - viewState.offsetY) / viewState.scale

  const startX = -mapInfo.width / 2
  const startY = -mapInfo.height / 2

  // Pixel to world
  const worldX = (mapX - startX) * mapInfo.resolution + mapInfo.originX
  const worldY = (mapInfo.height - (mapY - startY)) * mapInfo.resolution + mapInfo.originY

  navGoal.value = { x: worldX, y: worldY }
  emit('goal-set', { x: worldX, y: worldY })
  renderMap()
}

// ----------------------------------------------------------------
// Lifecycle
// ----------------------------------------------------------------

watch(rosConnected, (val) => {
  if (val) setupSubscriptions()
  else cleanupSubscriptions()
})

onMounted(() => {
  // Connect to rosbridge on the same host
  connect(window.location.hostname, ros2Store.port || 5001)
  nextTick(() => renderMap())

  // Resize observer
  const ro = new ResizeObserver(() => renderMap())
  if (mapWrapper.value) ro.observe(mapWrapper.value)
})

onUnmounted(() => {
  cleanupSubscriptions()
  if (animFrame) cancelAnimationFrame(animFrame)
})

// Expose for parent
defineExpose({ navGoal, robotPose, renderMap })
</script>

<style scoped>
.slam-map-panel {
  @apply w-full h-full flex flex-col;
}

.map-wrapper {
  @apply relative flex-1 overflow-hidden;
  background: #0a0f14;
  border: 1px solid rgba(0, 240, 255, 0.2);
  min-height: 300px;
}

.map-canvas {
  @apply w-full h-full;
  cursor: grab;
}

.map-canvas:active {
  cursor: grabbing;
}

.robot-info {
  @apply absolute bottom-2 left-2 flex gap-3 px-2 py-1;
  @apply text-[10px] font-mono text-primary;
  background: rgba(0, 0, 0, 0.7);
  border: 1px solid rgba(0, 240, 255, 0.2);
}

.nav-goal-info {
  @apply absolute bottom-2 right-2 px-2 py-1;
  @apply text-[10px] font-mono text-danger;
  background: rgba(0, 0, 0, 0.7);
  border: 1px solid rgba(255, 0, 64, 0.3);
}
</style>
