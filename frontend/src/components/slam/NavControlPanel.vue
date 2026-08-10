<template>
  <div class="nav-control-panel">
    <!-- Nav Status -->
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">NAV STATUS</span>
        <span :class="['panel-badge', navStatusBadge]">{{ navStatusText }}</span>
      </div>
      <div class="panel-content">
        <div class="info-row">
          <span class="info-label">State</span>
          <span class="info-value">{{ navState }}</span>
        </div>
        <div class="info-row" v-if="currentGoal">
          <span class="info-label">Target</span>
          <span class="info-value">{{ currentGoal.x.toFixed(2) }}, {{ currentGoal.y.toFixed(2) }}</span>
        </div>

        <!-- Nav2 Launch -->
        <div class="control-group mt-3">
          <div class="action-buttons">
            <button
              v-if="!nav2Running"
              class="btn btn-primary btn-full"
              @click="startNav2"
              :disabled="startingNav"
            >
              <svg viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              <span>{{ startingNav ? 'Starting...' : 'Start Nav2' }}</span>
            </button>
            <button
              v-else
              class="btn btn-danger btn-full"
              @click="stopNav2"
              :disabled="stoppingNav"
            >
              <svg viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
                <rect x="6" y="6" width="12" height="12" rx="1" />
              </svg>
              <span>{{ stoppingNav ? 'Stopping...' : 'Stop Nav2' }}</span>
            </button>
          </div>
        </div>

        <!-- Cancel Navigation -->
        <button
          v-if="navigating"
          class="btn btn-warning btn-full mt-2"
          @click="cancelNavigation"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
          <span>Cancel Navigation</span>
        </button>
      </div>
    </div>

    <!-- Algorithm Selection -->
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">PLANNER</span>
        <span class="panel-badge">{{ navAlgorithm.toUpperCase() }}</span>
      </div>
      <div class="panel-content">
        <div class="algo-select">
          <button
            v-for="algo in plannerAlgorithms"
            :key="algo.value"
            :class="['algo-btn', { active: navAlgorithm === algo.value }]"
            @click="navAlgorithm = algo.value"
          >
            {{ algo.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Waypoints -->
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">WAYPOINTS</span>
        <span class="panel-badge">{{ waypoints.length }}/7</span>
      </div>
      <div class="panel-content">
        <div class="waypoint-grid">
          <button
            v-for="wp in waypointSlots"
            :key="wp.label"
            :class="['waypoint-btn', { saved: wp.saved, active: wp.label === activeWaypoint }]"
            @click="onWaypointClick(wp)"
            @contextmenu.prevent="saveCurrentAsWaypoint(wp.label)"
          >
            <span class="wp-label">{{ wp.label.toUpperCase() }}</span>
            <span v-if="wp.saved" class="wp-coords">
              {{ wp.x.toFixed(1) }},{{ wp.y.toFixed(1) }}
            </span>
            <span v-else class="wp-empty">--</span>
          </button>
        </div>
        <p class="wp-hint">Click to navigate, right-click to save current position</p>

        <!-- Go to coordinates -->
        <div class="goto-section mt-3">
          <span class="section-label">Go to coordinates</span>
          <div class="goto-row">
            <input v-model.number="gotoX" class="coord-input" placeholder="X" type="number" step="0.1" />
            <input v-model.number="gotoY" class="coord-input" placeholder="Y" type="number" step="0.1" />
            <button class="btn btn-accent" @click="navigateToCoord" :disabled="!canGoto">
              GO
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRosbridge } from '@/composables/useRosbridge'
import { useToast } from '@/composables/useToast'
import {
  startNav2Service,
  stopNav2Service,
  cancelNav2Navigation,
  getNavWaypoints,
  saveNavWaypoint,
} from '@/services/api'

const props = defineProps({
  robotPose: { type: Object, default: () => ({ x: 0, y: 0, theta: 0 }) },
})

const emit = defineEmits(['navigate', 'cancel'])

const toast = useToast()
const { rosConnected, publish } = useRosbridge()

// State
const nav2Running = ref(false)
const navigating = ref(false)
const navState = ref('IDLE')
const currentGoal = ref(null)
const activeWaypoint = ref(null)
const navAlgorithm = ref('teb')
const startingNav = ref(false)
const stoppingNav = ref(false)
const gotoX = ref(0)
const gotoY = ref(0)

const plannerAlgorithms = [
  { value: 'teb', label: 'TEB' },
  { value: 'dwa', label: 'DWA' },
]

// Waypoints (a-g)
const waypoints = reactive([
  { label: 'a', saved: false, x: 0, y: 0 },
  { label: 'b', saved: false, x: 0, y: 0 },
  { label: 'c', saved: false, x: 0, y: 0 },
  { label: 'd', saved: false, x: 0, y: 0 },
  { label: 'e', saved: false, x: 0, y: 0 },
  { label: 'f', saved: false, x: 0, y: 0 },
  { label: 'g', saved: false, x: 0, y: 0 },
])

const waypointSlots = computed(() => waypoints)

const canGoto = computed(() => {
  return nav2Running.value && (gotoX.value !== 0 || gotoY.value !== 0)
})

const navStatusText = computed(() => {
  if (!nav2Running.value) return 'OFFLINE'
  if (navigating.value) return 'NAVIGATING'
  return 'READY'
})

const navStatusBadge = computed(() => {
  if (!nav2Running.value) return 'badge-err'
  if (navigating.value) return 'badge-warn'
  return 'badge-ok'
})

// Actions
async function startNav2() {
  startingNav.value = true
  try {
    await startNav2Service(navAlgorithm.value)
    nav2Running.value = true
    toast.success('Nav2 started')
  } catch (e) {
    toast.error('Failed to start Nav2')
  } finally {
    startingNav.value = false
  }
}

async function stopNav2() {
  stoppingNav.value = true
  try {
    await stopNav2Service()
    nav2Running.value = false
    navigating.value = false
    toast.success('Nav2 stopped')
  } catch (e) {
    toast.error('Failed to stop Nav2')
  } finally {
    stoppingNav.value = false
  }
}

function publishGoal(x, y, theta = 0) {
  if (!rosConnected.value) {
    toast.error('Not connected to ROS2')
    return
  }

  const goal = {
    header: {
      stamp: { sec: 0, nanosec: 0 },
      frame_id: 'map',
    },
    pose: {
      position: { x, y, z: 0.0 },
      orientation: {
        x: 0.0,
        y: 0.0,
        z: Math.sin(theta / 2),
        w: Math.cos(theta / 2),
      },
    },
  }

  publish('/goal_pose', 'geometry_msgs/PoseStamped', goal)
  currentGoal.value = { x, y }
  navigating.value = true
  navState.value = 'NAVIGATING'
  emit('navigate', { x, y })
}

function onWaypointClick(wp) {
  if (!wp.saved) {
    toast.error(`Waypoint ${wp.label.toUpperCase()} not set. Right-click to save.`)
    return
  }
  activeWaypoint.value = wp.label
  publishGoal(wp.x, wp.y)
  toast.success(`Navigating to waypoint ${wp.label.toUpperCase()}`)
}

function saveCurrentAsWaypoint(label) {
  const wp = waypoints.find(w => w.label === label)
  if (!wp) return

  wp.x = props.robotPose.x
  wp.y = props.robotPose.y
  wp.saved = true
  toast.success(`Waypoint ${label.toUpperCase()} saved: (${wp.x.toFixed(2)}, ${wp.y.toFixed(2)})`)
}

function navigateToCoord() {
  publishGoal(gotoX.value, gotoY.value)
  toast.success(`Navigating to (${gotoX.value}, ${gotoY.value})`)
}

async function cancelNavigation() {
  try {
    await cancelNav2Navigation()
    navigating.value = false
    navState.value = 'CANCELLED'
    currentGoal.value = null
    activeWaypoint.value = null
    emit('cancel')
    toast.success('Navigation cancelled')
  } catch (e) {
    toast.error('Failed to cancel')
  }
}

// Public method for parent (Slam.vue) to trigger goal from map click
function setGoalFromMap(goal) {
  publishGoal(goal.x, goal.y)
}

defineExpose({ setGoalFromMap, navigating, currentGoal })
</script>

<style scoped>
.nav-control-panel {
  @apply flex flex-col gap-4;
}

/* Panel Styles */
.panel {
  background: rgba(3, 7, 18, 0.8);
  border: 1px solid rgba(0, 240, 255, 0.1);
  clip-path: polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px);
}

.panel-header {
  @apply flex items-center justify-between px-4 py-3;
  background: rgba(0, 240, 255, 0.05);
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.panel-title {
  @apply text-xs font-orbitron font-semibold text-primary tracking-wider;
}

.panel-badge {
  @apply text-[10px] font-mono px-2 py-0.5;
  @apply text-secondary bg-secondary/10;
  border: 1px solid rgba(0, 255, 136, 0.3);
}

.badge-ok {
  @apply text-secondary bg-secondary/10;
  border-color: rgba(0, 255, 136, 0.3);
}
.badge-err {
  @apply text-danger bg-danger/10;
  border-color: rgba(255, 0, 64, 0.3);
}
.badge-warn {
  @apply text-warning bg-warning/10;
  border-color: rgba(255, 255, 0, 0.3);
}

.panel-content {
  @apply p-4;
}

/* Info rows */
.info-row {
  @apply flex items-center justify-between py-1;
}

.info-label {
  @apply text-[11px] font-mono text-dark-text-tertiary uppercase tracking-wider;
}

.info-value {
  @apply text-sm font-mono text-dark-text-secondary;
}

/* Control groups */
.control-group {
  @apply mb-3;
}

.section-label {
  @apply block text-[10px] font-mono text-dark-text-tertiary mb-2 uppercase tracking-wider;
}

/* Algorithm buttons */
.algo-select {
  @apply flex gap-2;
}

.algo-btn {
  @apply flex-1 py-2 text-xs font-mono;
  @apply text-dark-text-tertiary bg-dark-bg-tertiary/30;
  @apply border border-transparent;
  @apply transition-all duration-150;
}

.algo-btn:hover {
  @apply text-dark-text-secondary;
}

.algo-btn.active {
  @apply text-primary bg-primary/10;
  border-color: rgba(0, 240, 255, 0.3);
}

/* Buttons */
.action-buttons {
  @apply flex gap-2;
}

.btn {
  @apply flex items-center justify-center gap-2 px-4 py-2;
  @apply text-sm font-orbitron font-medium;
  @apply transition-all duration-200;
  clip-path: polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px);
}

.btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}

.btn-full {
  @apply w-full;
}

.btn-primary {
  @apply text-dark-bg-primary bg-primary;
}
.btn-primary:hover:not(:disabled) {
  @apply bg-primary/80;
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.4);
}

.btn-danger {
  @apply text-white bg-danger;
}
.btn-danger:hover:not(:disabled) {
  @apply bg-danger/80;
  box-shadow: 0 0 20px rgba(255, 0, 64, 0.4);
}

.btn-warning {
  @apply text-dark-bg-primary bg-warning;
}
.btn-warning:hover:not(:disabled) {
  @apply bg-warning/80;
}

.btn-accent {
  @apply text-dark-bg-primary bg-secondary;
}
.btn-accent:hover:not(:disabled) {
  @apply bg-secondary/80;
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.4);
}

/* Waypoints */
.waypoint-grid {
  @apply grid grid-cols-4 gap-2;
}

.waypoint-btn {
  @apply flex flex-col items-center gap-0.5 py-2 px-1;
  @apply text-dark-text-tertiary bg-dark-bg-tertiary/30;
  @apply border border-dark-border;
  @apply transition-all duration-150 cursor-pointer;
}

.waypoint-btn:hover {
  @apply border-primary/50;
}

.waypoint-btn.saved {
  @apply text-dark-text-secondary;
  border-color: rgba(0, 240, 255, 0.2);
}

.waypoint-btn.active {
  @apply text-primary bg-primary/10;
  border-color: rgba(0, 240, 255, 0.5);
  box-shadow: 0 0 8px rgba(0, 240, 255, 0.2);
}

.wp-label {
  @apply text-xs font-orbitron font-bold;
}

.wp-coords {
  @apply text-[9px] font-mono text-primary;
}

.wp-empty {
  @apply text-[9px] font-mono text-dark-text-tertiary/50;
}

.wp-hint {
  @apply mt-2 text-[10px] font-mono text-dark-text-tertiary/60 text-center;
}

/* Go to coords */
.goto-section {
  border-top: 1px solid rgba(0, 240, 255, 0.08);
  @apply pt-3;
}

.goto-row {
  @apply flex gap-2;
}

.coord-input {
  @apply flex-1 px-2 py-2 text-sm font-mono text-center;
  @apply text-dark-text-primary bg-dark-bg-tertiary/50;
  @apply border border-dark-border;
  @apply focus:border-primary focus:outline-none;
  @apply placeholder:text-dark-text-tertiary/50;
  min-width: 0;
}
</style>
