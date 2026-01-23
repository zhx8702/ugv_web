<template>
  <div class="mobile-pt-control">
    <!-- Direction buttons in cross layout -->
    <div class="pt-grid">
      <!-- Up (Tilt Up) -->
      <button
        class="pt-btn up"
        :class="{ active: activeDir === 'up' }"
        @touchstart.prevent="startMove('up')"
        @touchend.prevent="stopMove"
        @touchcancel.prevent="stopMove"
      >
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 4l-8 8h5v8h6v-8h5z"/>
        </svg>
      </button>

      <!-- Left (Pan Left) -->
      <button
        class="pt-btn left"
        :class="{ active: activeDir === 'left' }"
        @touchstart.prevent="startMove('left')"
        @touchend.prevent="stopMove"
        @touchcancel.prevent="stopMove"
      >
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M4 12l8-8v5h8v6h-8v5z"/>
        </svg>
      </button>

      <!-- Center (Reset) -->
      <button
        class="pt-btn center"
        :class="{ active: activeDir === 'center' }"
        @touchstart.prevent="centerPT"
        @touchend.prevent="activeDir = null"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3" />
          <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
        </svg>
      </button>

      <!-- Right (Pan Right) -->
      <button
        class="pt-btn right"
        :class="{ active: activeDir === 'right' }"
        @touchstart.prevent="startMove('right')"
        @touchend.prevent="stopMove"
        @touchcancel.prevent="stopMove"
      >
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 12l-8 8v-5H4v-6h8V4z"/>
        </svg>
      </button>

      <!-- Down (Tilt Down) -->
      <button
        class="pt-btn down"
        :class="{ active: activeDir === 'down' }"
        @touchstart.prevent="startMove('down')"
        @touchend.prevent="stopMove"
        @touchcancel.prevent="stopMove"
      >
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 20l8-8h-5V4h-6v8H4z"/>
        </svg>
      </button>
    </div>

    <!-- Angle display -->
    <div class="angle-display">
      <span class="angle-item">
        <span class="angle-label">P</span>
        <span class="angle-value" :class="panAngle >= 0 ? 'positive' : 'negative'">
          {{ panAngle >= 0 ? '+' : '' }}{{ Math.round(panAngle) }}°
        </span>
      </span>
      <span class="angle-divider">/</span>
      <span class="angle-item">
        <span class="angle-label">T</span>
        <span class="angle-value" :class="tiltAngle >= 0 ? 'positive' : 'negative'">
          {{ tiltAngle >= 0 ? '+' : '' }}{{ Math.round(tiltAngle) }}°
        </span>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useControlStore } from '@/stores/control'

const controlStore = useControlStore()
const { panAngle, tiltAngle } = storeToRefs(controlStore)
const { movePT, centerPT: resetPT } = controlStore

const activeDir = ref(null)
let moveTimer = null
const MOVE_INTERVAL = 50
const MOVE_SPEED = 4 // degrees per interval

const moves = {
  up: { pan: 0, tilt: MOVE_SPEED },
  down: { pan: 0, tilt: -MOVE_SPEED },
  left: { pan: -MOVE_SPEED, tilt: 0 },
  right: { pan: MOVE_SPEED, tilt: 0 }
}

function startMove(direction) {
  stopMove()
  activeDir.value = direction

  const move = moves[direction]
  if (!move) return

  // Immediate first move
  movePT(move.pan, move.tilt)

  // Continue while held
  moveTimer = setInterval(() => {
    movePT(move.pan, move.tilt)
  }, MOVE_INTERVAL)
}

function stopMove() {
  activeDir.value = null
  if (moveTimer) {
    clearInterval(moveTimer)
    moveTimer = null
  }
}

function centerPT() {
  activeDir.value = 'center'
  resetPT()
}

onUnmounted(() => {
  stopMove()
})
</script>

<style scoped>
.mobile-pt-control {
  @apply flex flex-col items-center gap-2 w-full h-full;
}

/* Grid layout for buttons */
.pt-grid {
  @apply flex-1 grid gap-1;
  grid-template-columns: 1fr 1fr 1fr;
  grid-template-rows: 1fr 1fr 1fr;
  grid-template-areas:
    ". up ."
    "left center right"
    ". down .";
  width: 100%;
  max-width: 140px;
}

.pt-btn {
  @apply flex items-center justify-center;
  @apply text-dark-text-secondary;
  @apply transition-all duration-100;
  @apply select-none;
  background: rgba(0, 240, 255, 0.08);
  border: 1px solid rgba(0, 240, 255, 0.2);
  border-radius: 8px;
  -webkit-tap-highlight-color: transparent;
  min-height: 36px;
}

.pt-btn svg {
  @apply w-5 h-5;
}

.pt-btn.up { grid-area: up; }
.pt-btn.down { grid-area: down; }
.pt-btn.left { grid-area: left; }
.pt-btn.right { grid-area: right; }
.pt-btn.center { grid-area: center; }

.pt-btn.center {
  background: rgba(0, 240, 255, 0.05);
  border-color: rgba(0, 240, 255, 0.15);
}

.pt-btn.center svg {
  @apply w-4 h-4 text-primary/50;
}

/* Active state */
.pt-btn.active {
  @apply text-primary;
  background: rgba(0, 240, 255, 0.25);
  border-color: rgba(0, 240, 255, 0.6);
  box-shadow: 0 0 15px rgba(0, 240, 255, 0.4);
  transform: scale(0.95);
}

.pt-btn.center.active {
  @apply text-secondary;
  background: rgba(0, 255, 136, 0.2);
  border-color: rgba(0, 255, 136, 0.5);
}

/* Angle display */
.angle-display {
  @apply flex items-center justify-center gap-1;
  @apply text-[9px] font-mono;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(0, 240, 255, 0.1);
  border-radius: 4px;
}

.angle-item {
  @apply flex items-center gap-1;
}

.angle-label {
  @apply text-dark-text-tertiary;
}

.angle-value {
  @apply font-bold;
  min-width: 32px;
  text-align: right;
}

.angle-value.positive {
  @apply text-secondary;
}

.angle-value.negative {
  @apply text-warning;
}

.angle-divider {
  @apply text-dark-text-tertiary/50 mx-1;
}
</style>
