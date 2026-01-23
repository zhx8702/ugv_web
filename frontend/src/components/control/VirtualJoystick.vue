<template>
  <div class="virtual-joystick">
    <!-- Mode Switcher -->
    <div class="mode-switcher">
      <button
        :class="['mode-btn', { active: mode === 'dpad' }]"
        @click="mode = 'dpad'"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2v8M12 14v8M2 12h8M14 12h8" />
        </svg>
        <span>D-PAD</span>
      </button>
      <button
        :class="['mode-btn', { active: mode === 'joystick' }]"
        @click="mode = 'joystick'"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" />
          <circle cx="12" cy="12" r="4" />
        </svg>
        <span>STICK</span>
      </button>
    </div>

    <!-- D-PAD Mode -->
    <div v-if="mode === 'dpad'" class="dpad-container">
      <div class="dpad-grid">
        <!-- Top Row -->
        <button
          class="dpad-btn corner"
          @mousedown="startMove(-0.7, 0.7)"
          @touchstart.prevent="startMove(-0.7, 0.7)"
          @mouseup="stopMove"
          @touchend="stopMove"
          @mouseleave="stopMove"
        >
          <span>↖</span>
        </button>
        <button
          class="dpad-btn main"
          @mousedown="startMove(0, 1)"
          @touchstart.prevent="startMove(0, 1)"
          @mouseup="stopMove"
          @touchend="stopMove"
          @mouseleave="stopMove"
        >
          <span>↑</span>
        </button>
        <button
          class="dpad-btn corner"
          @mousedown="startMove(0.7, 0.7)"
          @touchstart.prevent="startMove(0.7, 0.7)"
          @mouseup="stopMove"
          @touchend="stopMove"
          @mouseleave="stopMove"
        >
          <span>↗</span>
        </button>

        <!-- Middle Row -->
        <button
          class="dpad-btn main"
          @mousedown="startMove(-1, 0)"
          @touchstart.prevent="startMove(-1, 0)"
          @mouseup="stopMove"
          @touchend="stopMove"
          @mouseleave="stopMove"
        >
          <span>←</span>
        </button>
        <button class="dpad-btn center" @click="stopMove">
          <span>■</span>
        </button>
        <button
          class="dpad-btn main"
          @mousedown="startMove(1, 0)"
          @touchstart.prevent="startMove(1, 0)"
          @mouseup="stopMove"
          @touchend="stopMove"
          @mouseleave="stopMove"
        >
          <span>→</span>
        </button>

        <!-- Bottom Row -->
        <button
          class="dpad-btn corner"
          @mousedown="startMove(-0.7, -0.7)"
          @touchstart.prevent="startMove(-0.7, -0.7)"
          @mouseup="stopMove"
          @touchend="stopMove"
          @mouseleave="stopMove"
        >
          <span>↙</span>
        </button>
        <button
          class="dpad-btn main"
          @mousedown="startMove(0, -1)"
          @touchstart.prevent="startMove(0, -1)"
          @mouseup="stopMove"
          @touchend="stopMove"
          @mouseleave="stopMove"
        >
          <span>↓</span>
        </button>
        <button
          class="dpad-btn corner"
          @mousedown="startMove(0.7, -0.7)"
          @touchstart.prevent="startMove(0.7, -0.7)"
          @mouseup="stopMove"
          @touchend="stopMove"
          @mouseleave="stopMove"
        >
          <span>↘</span>
        </button>
      </div>
    </div>

    <!-- Joystick Mode -->
    <div v-else class="joystick-container">
      <div
        ref="baseRef"
        class="joystick-base"
        @mousedown="handleStart"
        @touchstart="handleStart"
      >
        <!-- Direction Indicators -->
        <div class="joystick-rings">
          <div class="ring ring-outer"></div>
          <div class="ring ring-middle"></div>
        </div>

        <!-- Direction Labels -->
        <div class="direction-labels">
          <span class="label label-top">FWD</span>
          <span class="label label-bottom">REV</span>
          <span class="label label-left">L</span>
          <span class="label label-right">R</span>
        </div>

        <!-- Joystick Stick -->
        <div
          ref="stickRef"
          class="joystick-stick"
          :class="{ active: isDragging }"
          :style="stickStyle"
        >
          <div class="stick-inner"></div>
          <div class="stick-glow"></div>
        </div>

        <!-- Center Point -->
        <div class="center-point"></div>
      </div>
    </div>

    <!-- Value Display -->
    <div class="joystick-values">
      <div class="value-item">
        <span class="value-label">SPD</span>
        <div class="value-bar">
          <div class="value-fill" :style="{ width: speedPercent + '%' }"></div>
        </div>
        <span class="value-number">{{ speedPercent }}%</span>
      </div>
      <div class="value-item">
        <span class="value-label">DIR</span>
        <span class="value-number angle">{{ angle }}°</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useControlStore } from '@/stores/control'

const controlStore = useControlStore()

// Mode
const mode = ref('dpad')

// Refs
const baseRef = ref(null)

// State
const stickX = ref(0)
const stickY = ref(0)
const isDragging = ref(false)
const maxDistance = 55

// D-PAD state
const currentTurn = ref(0)
const currentForward = ref(0)

// Computed
const speedPercent = computed(() => {
  if (mode.value === 'dpad') {
    const speed = Math.sqrt(currentTurn.value ** 2 + currentForward.value ** 2)
    return Math.round(Math.min(speed * 100, 100))
  }
  const distance = Math.sqrt(stickX.value ** 2 + stickY.value ** 2)
  const percent = Math.min((distance / maxDistance) * 100, 100)
  return Math.round(percent)
})

const angle = computed(() => {
  if (mode.value === 'dpad') {
    if (currentTurn.value === 0 && currentForward.value === 0) return 0
    let deg = Math.atan2(currentTurn.value, currentForward.value) * (180 / Math.PI)
    if (deg < 0) deg += 360
    return Math.round(deg)
  }
  if (stickX.value === 0 && stickY.value === 0) return 0
  let deg = Math.atan2(stickX.value, -stickY.value) * (180 / Math.PI)
  if (deg < 0) deg += 360
  return Math.round(deg)
})

const stickStyle = computed(() => {
  return {
    transform: `translate(${stickX.value}px, ${stickY.value}px)`
  }
})

// D-PAD Methods
const startMove = (turn, forward) => {
  currentTurn.value = turn
  currentForward.value = forward
  sendDpadCommand(turn, forward)
}

const stopMove = () => {
  currentTurn.value = 0
  currentForward.value = 0
  controlStore.stopRover()
}

const sendDpadCommand = (turn, forward) => {
  let leftSpeed = forward + turn
  let rightSpeed = forward - turn

  const maxValue = Math.max(Math.abs(leftSpeed), Math.abs(rightSpeed))
  if (maxValue > 1) {
    leftSpeed /= maxValue
    rightSpeed /= maxValue
  }

  controlStore.moveRover(leftSpeed, rightSpeed)
}

// Joystick Methods
const handleStart = (e) => {
  isDragging.value = true
  e.preventDefault()

  if (e.type === 'mousedown') {
    document.addEventListener('mousemove', handleMove)
    document.addEventListener('mouseup', handleEnd)
  } else {
    document.addEventListener('touchmove', handleMove, { passive: false })
    document.addEventListener('touchend', handleEnd)
  }

  handleMove(e)
}

const handleMove = (e) => {
  if (!isDragging.value || !baseRef.value) return

  e.preventDefault()

  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY

  const rect = baseRef.value.getBoundingClientRect()
  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 2

  let deltaX = clientX - centerX
  let deltaY = clientY - centerY

  const distance = Math.sqrt(deltaX ** 2 + deltaY ** 2)

  if (distance > maxDistance) {
    const angle = Math.atan2(deltaY, deltaX)
    deltaX = Math.cos(angle) * maxDistance
    deltaY = Math.sin(angle) * maxDistance
  }

  stickX.value = deltaX
  stickY.value = deltaY

  sendJoystickCommand()
}

const handleEnd = () => {
  isDragging.value = false

  document.removeEventListener('mousemove', handleMove)
  document.removeEventListener('mouseup', handleEnd)
  document.removeEventListener('touchmove', handleMove)
  document.removeEventListener('touchend', handleEnd)

  resetPosition()
}

const resetPosition = () => {
  const duration = 150
  const startX = stickX.value
  const startY = stickY.value
  const startTime = Date.now()

  const animate = () => {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    const easeProgress = 1 - Math.pow(1 - progress, 3)

    stickX.value = startX * (1 - easeProgress)
    stickY.value = startY * (1 - easeProgress)

    if (progress < 1) {
      requestAnimationFrame(animate)
    } else {
      stickX.value = 0
      stickY.value = 0
      controlStore.stopRover()
    }
  }

  requestAnimationFrame(animate)
}

const sendJoystickCommand = () => {
  const forward = -stickY.value / maxDistance
  const turn = stickX.value / maxDistance

  let leftSpeed = forward + turn
  let rightSpeed = forward - turn

  const maxValue = Math.max(Math.abs(leftSpeed), Math.abs(rightSpeed))
  if (maxValue > 1) {
    leftSpeed /= maxValue
    rightSpeed /= maxValue
  }

  controlStore.moveRover(leftSpeed, rightSpeed)
}

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMove)
  document.removeEventListener('mouseup', handleEnd)
  document.removeEventListener('touchmove', handleMove)
  document.removeEventListener('touchend', handleEnd)
})
</script>

<style scoped>
.virtual-joystick {
  @apply flex flex-col items-center gap-4;
}

/* Mode Switcher */
.mode-switcher {
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

/* D-PAD Mode */
.dpad-container {
  @apply w-full flex justify-center;
}

.dpad-grid {
  @apply grid grid-cols-3 gap-2;
  width: 160px;
  height: 160px;
}

.dpad-btn {
  @apply flex items-center justify-center;
  @apply bg-dark-bg-tertiary border border-dark-border rounded-lg;
  @apply text-dark-text-secondary text-xl;
  @apply transition-all duration-150 select-none;
}

.dpad-btn:hover {
  @apply border-primary/50 bg-dark-bg-secondary;
}

.dpad-btn:active {
  @apply bg-primary border-primary text-white scale-95;
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.4);
}

.dpad-btn.main {
  @apply text-2xl;
}

.dpad-btn.center {
  @apply bg-dark-bg-secondary text-dark-text-tertiary text-sm;
}

.dpad-btn.center:active {
  @apply bg-danger border-danger;
}

/* Joystick Mode */
.joystick-container {
  @apply w-full flex justify-center;
}

.joystick-base {
  @apply relative rounded-full;
  @apply cursor-pointer select-none touch-none;
  width: 150px;
  height: 150px;
  background: radial-gradient(circle at center, rgba(0, 240, 255, 0.05) 0%, rgba(3, 7, 18, 0.9) 70%);
  border: 2px solid rgba(0, 240, 255, 0.2);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.joystick-base:hover {
  border-color: rgba(0, 240, 255, 0.4);
}

.joystick-base:active {
  border-color: rgba(0, 240, 255, 0.6);
  box-shadow: 0 0 30px rgba(0, 240, 255, 0.2);
}

.joystick-rings {
  @apply absolute inset-0 flex items-center justify-center pointer-events-none;
}

.ring {
  @apply absolute rounded-full;
  border: 1px solid rgba(0, 240, 255, 0.15);
}

.ring-outer {
  width: 120px;
  height: 120px;
}

.ring-middle {
  width: 70px;
  height: 70px;
}

.direction-labels {
  @apply absolute inset-0 pointer-events-none;
}

.label {
  @apply absolute text-[10px] font-orbitron text-dark-text-tertiary/50;
}

.label-top { @apply top-2 left-1/2 -translate-x-1/2; }
.label-bottom { @apply bottom-2 left-1/2 -translate-x-1/2; }
.label-left { @apply left-2 top-1/2 -translate-y-1/2; }
.label-right { @apply right-2 top-1/2 -translate-y-1/2; }

.joystick-stick {
  @apply absolute top-1/2 left-1/2;
  @apply rounded-full cursor-move;
  width: 56px;
  height: 56px;
  margin-left: -28px;
  margin-top: -28px;
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.8) 0%, rgba(0, 128, 255, 0.9) 100%);
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.3), inset 0 2px 10px rgba(255, 255, 255, 0.2);
  transition: box-shadow 0.2s;
  will-change: transform;
}

.joystick-stick.active {
  box-shadow: 0 0 30px rgba(0, 240, 255, 0.5), inset 0 2px 10px rgba(255, 255, 255, 0.3);
}

.stick-inner {
  @apply absolute inset-2 rounded-full;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.3) 0%, transparent 50%);
}

.stick-glow {
  @apply absolute inset-0 rounded-full;
  background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.4), transparent 60%);
}

.center-point {
  @apply absolute top-1/2 left-1/2;
  @apply w-3 h-3 rounded-full;
  transform: translate(-50%, -50%);
  background: rgba(0, 240, 255, 0.3);
  pointer-events: none;
}

/* Value Display */
.joystick-values {
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
  @apply flex-1 h-1.5 bg-dark-bg-tertiary rounded-full overflow-hidden;
}

.value-fill {
  @apply h-full bg-gradient-to-r from-primary to-blue-500 rounded-full;
  transition: width 0.1s ease-out;
}

.value-number {
  @apply text-sm font-mono font-bold text-primary min-w-[3rem] text-right;
}

.value-number.angle {
  @apply text-dark-text-primary;
}
</style>
