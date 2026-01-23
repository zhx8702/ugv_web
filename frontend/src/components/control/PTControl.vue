<template>
  <div class="pt-control">
    <!-- Mode Controls -->
    <div class="mode-row">
      <button
        @click="toggleSteady"
        :class="['mode-btn', { active: ptSteady }]"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <circle cx="12" cy="12" r="3" />
        </svg>
        <span>STEADY</span>
      </button>
      <button
        @click="toggleAhead"
        :class="['mode-btn', { active: ptAhead }]"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M5 12h14M12 5l7 7-7 7" />
        </svg>
        <span>AHEAD</span>
      </button>
    </div>

    <!-- Main Control Area with Direction Buttons -->
    <div class="main-control">
      <!-- Direction Buttons Container -->
      <div class="direction-container">
        <!-- Top Button (Tilt Up) -->
        <button
          class="dir-btn dir-up"
          @mousedown="startMove('up')"
          @mouseup="stopMove"
          @mouseleave="stopMove"
          @touchstart.prevent="startMove('up')"
          @touchend="stopMove"
        >
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 4l-8 8h5v8h6v-8h5z"/></svg>
        </button>

        <!-- Left Button (Pan Left) -->
        <button
          class="dir-btn dir-left"
          @mousedown="startMove('left')"
          @mouseup="stopMove"
          @mouseleave="stopMove"
          @touchstart.prevent="startMove('left')"
          @touchend="stopMove"
        >
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 12l8-8v5h8v6h-8v5z"/></svg>
        </button>

        <!-- Circular PT Pad (Joystick style - speed control) -->
        <div
          ref="padRef"
          class="pt-pad"
          @mousedown="handlePadStart"
          @touchstart.prevent="handlePadStart"
        >
          <!-- Rings -->
          <div class="pad-rings">
            <div class="ring ring-outer"></div>
            <div class="ring ring-inner"></div>
          </div>

          <!-- Axis Lines -->
          <div class="axis-lines">
            <div class="axis-h"></div>
            <div class="axis-v"></div>
          </div>

          <!-- Speed Indicator (shows joystick offset, not actual angle) -->
          <div
            class="joystick-knob"
            :class="{ active: isDragging }"
            :style="joystickStyle"
          >
            <div class="knob-inner"></div>
            <div class="knob-glow"></div>
          </div>

          <!-- Center Reset Button -->
          <button class="center-btn" @click="centerPT" title="Reset to Center">
            <span>⊕</span>
          </button>
        </div>

        <!-- Right Button (Pan Right) -->
        <button
          class="dir-btn dir-right"
          @mousedown="startMove('right')"
          @mouseup="stopMove"
          @mouseleave="stopMove"
          @touchstart.prevent="startMove('right')"
          @touchend="stopMove"
        >
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 12l-8 8v-5H4v-6h8V4z"/></svg>
        </button>

        <!-- Bottom Button (Tilt Down) -->
        <button
          class="dir-btn dir-down"
          @mousedown="startMove('down')"
          @mouseup="stopMove"
          @mouseleave="stopMove"
          @touchstart.prevent="startMove('down')"
          @touchend="stopMove"
        >
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 20l8-8h-5V4h-6v8H4z"/></svg>
        </button>
      </div>
    </div>

    <!-- Quick Position Presets -->
    <div class="presets-row">
      <button
        v-for="preset in presets"
        :key="preset.name"
        :class="['preset-btn', { active: isActivePreset(preset) }]"
        @click="gotoPreset(preset)"
      >
        <span class="preset-label">{{ preset.label }}</span>
        <span class="preset-angle">{{ preset.pan }}°, {{ preset.tilt }}°</span>
      </button>
    </div>

    <!-- Angle Display -->
    <div class="pt-values">
      <div class="value-item">
        <span class="value-label">PAN</span>
        <div class="value-bar">
          <div class="value-track"></div>
          <div class="value-center"></div>
          <div class="value-fill" :class="panAngle >= 0 ? 'positive' : 'negative'" :style="panFillStyle"></div>
        </div>
        <span class="value-number" :class="valueClass(panAngle)">{{ formatAngle(panAngle) }}</span>
      </div>
      <div class="value-item">
        <span class="value-label">TILT</span>
        <div class="value-bar">
          <div class="value-track"></div>
          <div class="value-center"></div>
          <div class="value-fill" :class="tiltAngle >= 0 ? 'positive' : 'negative'" :style="tiltFillStyle"></div>
        </div>
        <span class="value-number" :class="valueClass(tiltAngle)">{{ formatAngle(tiltAngle) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useControlStore } from '@/stores/control'

const controlStore = useControlStore()
const { panAngle, tiltAngle, ptSteady, ptAhead } = storeToRefs(controlStore)
const { movePT, centerPT } = controlStore

// Refs
const padRef = ref(null)
const isDragging = ref(false)

// Joystick offset (for visual feedback, normalized -1 to 1)
const joystickX = ref(0)
const joystickY = ref(0)

// Movement timer for continuous movement
let moveTimer = null
const MOVE_INTERVAL = 50 // ms between moves
const BASE_SPEED = 3 // degrees per interval at max deflection

// Constants
const padRadius = 60 // Half of pad size (120px)

// Presets - quick position shortcuts
const presets = [
  { name: 'L45', label: 'L45', pan: -45, tilt: 0 },
  { name: 'CENTER', label: 'CTR', pan: 0, tilt: 0 },
  { name: 'R45', label: 'R45', pan: 45, tilt: 0 }
]

// Computed
const formatAngle = (angle) => {
  const v = Math.round(angle)
  return v > 0 ? `+${v}°` : `${v}°`
}

const valueClass = (angle) => {
  if (angle > 0) return 'positive'
  if (angle < 0) return 'negative'
  return 'zero'
}

// Joystick visual position (follows user input, returns to center when released)
const joystickStyle = computed(() => {
  const x = joystickX.value * (padRadius - 16)
  const y = -joystickY.value * (padRadius - 16)
  return {
    transform: `translate(${x}px, ${y}px)`
  }
})

// Value bar fill styles (shows actual angle position)
const panFillStyle = computed(() => {
  const center = 50
  const pos = ((panAngle.value + 90) / 180) * 100
  if (panAngle.value >= 0) {
    return { left: `${center}%`, width: `${pos - center}%` }
  } else {
    return { left: `${pos}%`, width: `${center - pos}%` }
  }
})

const tiltFillStyle = computed(() => {
  const center = 50
  const pos = ((tiltAngle.value + 60) / 120) * 100
  if (tiltAngle.value >= 0) {
    return { left: `${center}%`, width: `${pos - center}%` }
  } else {
    return { left: `${pos}%`, width: `${center - pos}%` }
  }
})

// Direction button handlers (hold to move)
function startMove(direction) {
  stopMove() // Clear any existing timer

  const moves = {
    up: { pan: 0, tilt: BASE_SPEED },
    down: { pan: 0, tilt: -BASE_SPEED },
    left: { pan: -BASE_SPEED, tilt: 0 },
    right: { pan: BASE_SPEED, tilt: 0 }
  }

  const move = moves[direction]
  if (!move) return

  // Immediate first move
  movePT(move.pan, move.tilt)

  // Continue moving while held
  moveTimer = setInterval(() => {
    movePT(move.pan, move.tilt)
  }, MOVE_INTERVAL)
}

function stopMove() {
  if (moveTimer) {
    clearInterval(moveTimer)
    moveTimer = null
  }
}

// Joystick pad interaction (speed control mode)
function handlePadStart(e) {
  isDragging.value = true

  if (e.type === 'mousedown') {
    document.addEventListener('mousemove', handlePadMove)
    document.addEventListener('mouseup', handlePadEnd)
  } else {
    document.addEventListener('touchmove', handlePadMove, { passive: false })
    document.addEventListener('touchend', handlePadEnd)
  }

  handlePadMove(e)
  startJoystickMove()
}

function handlePadMove(e) {
  if (!isDragging.value || !padRef.value) return
  e.preventDefault()

  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY

  const rect = padRef.value.getBoundingClientRect()
  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 2

  let deltaX = clientX - centerX
  let deltaY = centerY - clientY // Invert Y for tilt

  // Normalize to -1 to 1 range
  const maxOffset = padRadius - 16
  let normX = deltaX / maxOffset
  let normY = deltaY / maxOffset

  // Clamp to circle
  const distance = Math.sqrt(normX ** 2 + normY ** 2)
  if (distance > 1) {
    normX /= distance
    normY /= distance
  }

  joystickX.value = normX
  joystickY.value = normY
}

function handlePadEnd() {
  isDragging.value = false

  // Return joystick to center
  joystickX.value = 0
  joystickY.value = 0

  stopJoystickMove()

  document.removeEventListener('mousemove', handlePadMove)
  document.removeEventListener('mouseup', handlePadEnd)
  document.removeEventListener('touchmove', handlePadMove)
  document.removeEventListener('touchend', handlePadEnd)
}

// Continuous movement based on joystick position
let joystickMoveTimer = null

function startJoystickMove() {
  stopJoystickMove()

  joystickMoveTimer = setInterval(() => {
    if (!isDragging.value) {
      stopJoystickMove()
      return
    }

    // Speed proportional to joystick deflection
    const panSpeed = joystickX.value * BASE_SPEED
    const tiltSpeed = joystickY.value * BASE_SPEED

    // Only move if there's significant input (dead zone)
    if (Math.abs(panSpeed) > 0.1 || Math.abs(tiltSpeed) > 0.1) {
      movePT(panSpeed, tiltSpeed)
    }
  }, MOVE_INTERVAL)
}

function stopJoystickMove() {
  if (joystickMoveTimer) {
    clearInterval(joystickMoveTimer)
    joystickMoveTimer = null
  }
}

function gotoPreset(preset) {
  const deltaPan = preset.pan - panAngle.value
  const deltaTilt = preset.tilt - tiltAngle.value
  movePT(deltaPan, deltaTilt)
}

function isActivePreset(preset) {
  return Math.abs(panAngle.value - preset.pan) < 5 &&
         Math.abs(tiltAngle.value - preset.tilt) < 5
}

function toggleSteady() {
  controlStore.ptSteady = !controlStore.ptSteady
}

function toggleAhead() {
  controlStore.ptAhead = !controlStore.ptAhead
}

onUnmounted(() => {
  stopMove()
  stopJoystickMove()
  document.removeEventListener('mousemove', handlePadMove)
  document.removeEventListener('mouseup', handlePadEnd)
  document.removeEventListener('touchmove', handlePadMove)
  document.removeEventListener('touchend', handlePadEnd)
})
</script>

<style scoped>
.pt-control {
  @apply flex flex-col items-center gap-4;
}

/* Mode Row */
.mode-row {
  @apply flex w-full gap-2;
}

.mode-btn {
  @apply flex-1 flex items-center justify-center gap-2 py-2 px-3;
  @apply bg-dark-bg-tertiary/50 border border-dark-border rounded;
  @apply text-xs font-orbitron text-dark-text-tertiary;
  @apply transition-all duration-200;
}

.mode-btn svg {
  @apply w-4 h-4;
}

.mode-btn:hover {
  @apply border-primary/50 text-dark-text-secondary;
}

.mode-btn.active {
  @apply bg-primary/20 border-primary text-primary;
  box-shadow: 0 0 15px rgba(0, 240, 255, 0.2);
}

/* Main Control Area */
.main-control {
  @apply flex items-center gap-3;
}

/* Direction Container - grid layout for buttons around pad */
.direction-container {
  display: grid;
  grid-template-columns: 32px 120px 32px;
  grid-template-rows: 32px 120px 32px;
  grid-template-areas:
    ". up ."
    "left pad right"
    ". down .";
  gap: 4px;
  align-items: center;
  justify-items: center;
}

/* Direction Buttons */
.dir-btn {
  @apply flex items-center justify-center;
  @apply text-dark-text-tertiary;
  @apply transition-all duration-150;
  @apply select-none;
  width: 32px;
  height: 32px;
  background: rgba(0, 240, 255, 0.06);
  border: 1px solid rgba(0, 240, 255, 0.15);
  border-radius: 6px;
}

.dir-btn svg {
  width: 16px;
  height: 16px;
}

.dir-btn:hover {
  @apply text-dark-text-secondary;
  background: rgba(0, 240, 255, 0.12);
  border-color: rgba(0, 240, 255, 0.3);
}

.dir-btn:active {
  @apply text-primary;
  background: rgba(0, 240, 255, 0.2);
  border-color: rgba(0, 240, 255, 0.5);
  box-shadow: 0 0 12px rgba(0, 240, 255, 0.3);
  transform: scale(0.95);
}

.dir-up { grid-area: up; }
.dir-down { grid-area: down; }
.dir-left { grid-area: left; }
.dir-right { grid-area: right; }

/* PT Pad - joystick style speed control */
.pt-pad {
  grid-area: pad;
  @apply relative rounded-full;
  @apply cursor-grab select-none touch-none;
  width: 120px;
  height: 120px;
  background: radial-gradient(circle at center, rgba(0, 240, 255, 0.05) 0%, rgba(3, 7, 18, 0.9) 70%);
  border: 2px solid rgba(0, 240, 255, 0.2);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.pt-pad:hover {
  border-color: rgba(0, 240, 255, 0.4);
}

.pt-pad:active {
  cursor: grabbing;
  border-color: rgba(0, 240, 255, 0.6);
  box-shadow: 0 0 30px rgba(0, 240, 255, 0.2);
}

.pad-rings {
  @apply absolute inset-0 flex items-center justify-center pointer-events-none;
}

.ring {
  @apply absolute rounded-full;
  border: 1px solid rgba(0, 240, 255, 0.12);
}

.ring-outer {
  width: 90px;
  height: 90px;
}

.ring-inner {
  width: 50px;
  height: 50px;
}

/* Axis Lines */
.axis-lines {
  @apply absolute inset-0 pointer-events-none;
}

.axis-h, .axis-v {
  @apply absolute;
  background: rgba(0, 240, 255, 0.1);
}

.axis-h {
  @apply top-1/2 left-3 right-3 h-px -translate-y-1/2;
}

.axis-v {
  @apply left-1/2 top-3 bottom-3 w-px -translate-x-1/2;
}

/* Joystick Knob (speed indicator) */
.joystick-knob {
  @apply absolute top-1/2 left-1/2 pointer-events-none;
  width: 28px;
  height: 28px;
  margin-left: -14px;
  margin-top: -14px;
  transition: transform 0.15s ease-out;
}

.joystick-knob.active {
  transition: none;
}

.knob-inner {
  @apply absolute inset-0 rounded-full;
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.8) 0%, rgba(0, 128, 255, 0.9) 100%);
  box-shadow: 0 0 12px rgba(0, 240, 255, 0.5), inset 0 1px 2px rgba(255, 255, 255, 0.3);
}

.knob-glow {
  @apply absolute inset-0 rounded-full;
  background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.4), transparent 60%);
}

.joystick-knob.active .knob-inner {
  background: linear-gradient(135deg, rgba(0, 255, 136, 0.9) 0%, rgba(0, 200, 100, 1) 100%);
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.6), inset 0 1px 2px rgba(255, 255, 255, 0.4);
}

/* Center Button */
.center-btn {
  @apply absolute top-1/2 left-1/2 z-10;
  @apply flex items-center justify-center;
  @apply text-primary/40 text-sm;
  @apply transition-all duration-150;
  width: 24px;
  height: 24px;
  margin-left: -12px;
  margin-top: -12px;
  background: rgba(3, 7, 18, 0.9);
  border: 1px solid rgba(0, 240, 255, 0.15);
  border-radius: 50%;
}

.center-btn:hover {
  @apply text-primary;
  border-color: rgba(0, 240, 255, 0.5);
  background: rgba(0, 240, 255, 0.1);
}

.center-btn:active {
  @apply bg-primary text-dark-bg-primary;
  transform: scale(0.9);
}

/* Presets Row - horizontal quick position buttons */
.presets-row {
  @apply flex w-full gap-2;
}

.preset-btn {
  @apply flex-1 flex flex-col items-center justify-center py-1.5;
  @apply text-dark-text-tertiary;
  @apply transition-all duration-150;
  background: rgba(0, 240, 255, 0.04);
  border: 1px solid rgba(0, 240, 255, 0.1);
  border-radius: 4px;
}

.preset-label {
  @apply text-[10px] font-orbitron font-medium;
}

.preset-angle {
  @apply text-[8px] font-mono opacity-50;
}

.preset-btn:hover {
  @apply text-dark-text-secondary;
  background: rgba(0, 240, 255, 0.1);
  border-color: rgba(0, 240, 255, 0.3);
}

.preset-btn.active {
  @apply text-primary;
  background: rgba(0, 240, 255, 0.15);
  border-color: rgba(0, 240, 255, 0.5);
}

/* Value Display */
.pt-values {
  @apply w-full grid grid-cols-2 gap-3;
}

.value-item {
  @apply flex items-center gap-2 px-3 py-2;
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.1);
  clip-path: polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px);
}

.value-label {
  @apply text-[10px] font-orbitron text-dark-text-tertiary tracking-wider;
}

.value-bar {
  @apply flex-1 relative h-1.5 rounded-full overflow-hidden;
}

.value-track {
  @apply absolute inset-0;
  background: rgba(0, 240, 255, 0.08);
}

.value-center {
  @apply absolute top-0 bottom-0 w-px;
  left: 50%;
  background: rgba(0, 240, 255, 0.3);
}

.value-fill {
  @apply absolute top-0 h-full;
  transition: left 0.1s, width 0.1s;
}

.value-fill.positive {
  background: linear-gradient(90deg, rgba(0, 240, 255, 0.4) 0%, rgba(0, 255, 136, 0.7) 100%);
}

.value-fill.negative {
  background: linear-gradient(90deg, rgba(255, 200, 0, 0.7) 0%, rgba(0, 240, 255, 0.4) 100%);
}

.value-number {
  @apply text-sm font-mono font-bold min-w-[3rem] text-right;
}

.value-number.positive { @apply text-secondary; }
.value-number.negative { @apply text-warning; }
.value-number.zero { @apply text-primary; }
</style>
