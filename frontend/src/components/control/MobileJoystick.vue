<template>
  <div class="mobile-joystick" ref="containerRef">
    <!-- Touch area - entire component -->
    <div
      class="joystick-area"
      @touchstart.prevent="handleTouchStart"
      @touchmove.prevent="handleTouchMove"
      @touchend.prevent="handleTouchEnd"
      @touchcancel.prevent="handleTouchEnd"
    >
      <!-- Visual joystick base (appears where user touches) -->
      <div
        v-if="isActive"
        class="joystick-base"
        :style="baseStyle"
      >
        <div class="base-ring"></div>
        <div class="base-center"></div>
      </div>

      <!-- Joystick knob -->
      <div
        v-if="isActive"
        class="joystick-knob"
        :style="knobStyle"
      >
        <div class="knob-inner"></div>
      </div>

      <!-- Idle state hint -->
      <div v-if="!isActive" class="idle-hint">
        <div class="hint-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v8M8 12h8" />
          </svg>
        </div>
        <span class="hint-text">TOUCH TO MOVE</span>
      </div>
    </div>

    <!-- Direction indicators -->
    <div class="direction-indicators">
      <span class="indicator top" :class="{ active: direction.y > 0.3 }">FWD</span>
      <span class="indicator bottom" :class="{ active: direction.y < -0.3 }">REV</span>
      <span class="indicator left" :class="{ active: direction.x < -0.3 }">L</span>
      <span class="indicator right" :class="{ active: direction.x > 0.3 }">R</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onUnmounted } from 'vue'
import { useControlStore } from '@/stores/control'

const controlStore = useControlStore()
const containerRef = ref(null)

// State
const isActive = ref(false)
const touchId = ref(null)
const basePosition = reactive({ x: 0, y: 0 })
const knobPosition = reactive({ x: 0, y: 0 })
const direction = reactive({ x: 0, y: 0 })

const maxDistance = 50 // Maximum knob travel distance

// Computed styles
const baseStyle = computed(() => ({
  left: `${basePosition.x}px`,
  top: `${basePosition.y}px`
}))

const knobStyle = computed(() => ({
  left: `${knobPosition.x}px`,
  top: `${knobPosition.y}px`
}))

// Touch handlers
function handleTouchStart(e) {
  if (isActive.value) return

  const touch = e.touches[0]
  const rect = containerRef.value.getBoundingClientRect()

  // Set base position where user touched
  basePosition.x = touch.clientX - rect.left
  basePosition.y = touch.clientY - rect.top
  knobPosition.x = basePosition.x
  knobPosition.y = basePosition.y

  touchId.value = touch.identifier
  isActive.value = true
}

function handleTouchMove(e) {
  if (!isActive.value) return

  // Find our touch
  const touch = Array.from(e.touches).find(t => t.identifier === touchId.value)
  if (!touch) return

  const rect = containerRef.value.getBoundingClientRect()
  const currentX = touch.clientX - rect.left
  const currentY = touch.clientY - rect.top

  // Calculate delta from base position
  let deltaX = currentX - basePosition.x
  let deltaY = currentY - basePosition.y

  // Clamp to max distance (circular boundary)
  const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY)
  if (distance > maxDistance) {
    const angle = Math.atan2(deltaY, deltaX)
    deltaX = Math.cos(angle) * maxDistance
    deltaY = Math.sin(angle) * maxDistance
  }

  // Update knob position
  knobPosition.x = basePosition.x + deltaX
  knobPosition.y = basePosition.y + deltaY

  // Calculate normalized direction (-1 to 1)
  direction.x = deltaX / maxDistance
  direction.y = -deltaY / maxDistance // Invert Y for forward/backward

  // Send movement command
  sendCommand()
}

function handleTouchEnd(e) {
  // Check if our touch ended
  const touch = Array.from(e.changedTouches).find(t => t.identifier === touchId.value)
  if (!touch) return

  isActive.value = false
  touchId.value = null
  direction.x = 0
  direction.y = 0

  // Stop movement
  controlStore.stopRover()
}

function sendCommand() {
  const forward = direction.y
  const turn = direction.x

  // Differential drive calculation
  let leftSpeed = forward + turn
  let rightSpeed = forward - turn

  // Normalize if exceeds 1
  const maxValue = Math.max(Math.abs(leftSpeed), Math.abs(rightSpeed))
  if (maxValue > 1) {
    leftSpeed /= maxValue
    rightSpeed /= maxValue
  }

  controlStore.moveRover(leftSpeed, rightSpeed)
}

onUnmounted(() => {
  controlStore.stopRover()
})
</script>

<style scoped>
.mobile-joystick {
  @apply relative w-full h-full;
  min-height: 120px;
}

.joystick-area {
  @apply absolute inset-0;
  touch-action: none;
}

/* Joystick base (appears on touch) */
.joystick-base {
  @apply absolute pointer-events-none;
  width: 100px;
  height: 100px;
  margin-left: -50px;
  margin-top: -50px;
}

.base-ring {
  @apply absolute inset-0 rounded-full;
  border: 2px solid rgba(0, 240, 255, 0.3);
  background: radial-gradient(circle, rgba(0, 240, 255, 0.1) 0%, transparent 70%);
}

.base-center {
  @apply absolute rounded-full;
  width: 10px;
  height: 10px;
  top: 50%;
  left: 50%;
  margin-left: -5px;
  margin-top: -5px;
  background: rgba(0, 240, 255, 0.4);
}

/* Joystick knob */
.joystick-knob {
  @apply absolute pointer-events-none;
  width: 56px;
  height: 56px;
  margin-left: -28px;
  margin-top: -28px;
  z-index: 10;
}

.knob-inner {
  @apply absolute inset-0 rounded-full;
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.9) 0%, rgba(0, 128, 255, 1) 100%);
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.5), inset 0 2px 10px rgba(255, 255, 255, 0.3);
}

/* Idle hint */
.idle-hint {
  @apply absolute inset-0 flex flex-col items-center justify-center;
  opacity: 0.5;
}

.hint-icon {
  @apply w-12 h-12 text-primary mb-2;
}

.hint-icon svg {
  @apply w-full h-full;
}

.hint-text {
  @apply text-[10px] font-orbitron tracking-wider text-dark-text-tertiary;
}

/* Direction indicators */
.direction-indicators {
  @apply absolute inset-0 pointer-events-none;
}

.indicator {
  @apply absolute text-[8px] font-orbitron tracking-wider;
  @apply text-dark-text-tertiary/30 transition-all duration-150;
}

.indicator.active {
  @apply text-primary;
  text-shadow: 0 0 8px rgba(0, 240, 255, 0.8);
}

.indicator.top {
  @apply top-1 left-1/2 -translate-x-1/2;
}

.indicator.bottom {
  @apply bottom-1 left-1/2 -translate-x-1/2;
}

.indicator.left {
  @apply left-1 top-1/2 -translate-y-1/2;
}

.indicator.right {
  @apply right-1 top-1/2 -translate-y-1/2;
}
</style>
