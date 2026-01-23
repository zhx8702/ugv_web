<template>
  <div class="system-monitor">
    <!-- CPU & RAM Charts -->
    <div class="charts-grid">
      <div class="chart-container">
        <div class="chart-header">
          <span class="chart-label">CPU LOAD</span>
          <span class="chart-value" :class="cpuStatusClass">{{ cpuUsage.toFixed(0) }}<span class="unit">%</span></span>
        </div>
        <div class="chart-bar">
          <div class="bar-fill cpu-bar" :style="{ width: cpuUsage + '%' }"></div>
          <div class="bar-segments">
            <div v-for="i in 10" :key="i" class="segment"></div>
          </div>
        </div>
        <v-chart class="chart" :option="cpuChartOption" autoresize />
      </div>

      <div class="chart-container">
        <div class="chart-header">
          <span class="chart-label">MEMORY</span>
          <span class="chart-value" :class="ramStatusClass">{{ ramUsage.toFixed(0) }}<span class="unit">%</span></span>
        </div>
        <div class="chart-bar">
          <div class="bar-fill ram-bar" :style="{ width: ramUsage + '%' }"></div>
          <div class="bar-segments">
            <div v-for="i in 10" :key="i" class="segment"></div>
          </div>
        </div>
        <v-chart class="chart" :option="ramChartOption" autoresize />
      </div>
    </div>

    <!-- Temperature & Voltage -->
    <div class="gauges-grid">
      <div class="gauge-item">
        <div class="gauge-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z" />
          </svg>
        </div>
        <div class="gauge-data">
          <span class="gauge-label">TEMP</span>
          <span class="gauge-value" :class="tempStatusClass">
            {{ temperature.toFixed(1) }}<span class="unit">°C</span>
          </span>
        </div>
        <div class="gauge-bar">
          <div class="gauge-fill" :class="tempStatusClass" :style="{ width: (temperature / 100) * 100 + '%' }"></div>
        </div>
      </div>

      <div class="gauge-item">
        <div class="gauge-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="7" width="18" height="10" rx="2" />
            <line x1="22" y1="11" x2="22" y2="13" />
          </svg>
        </div>
        <div class="gauge-data">
          <span class="gauge-label">POWER</span>
          <span class="gauge-value" :class="voltageStatusClass">
            {{ voltage.toFixed(2) }}<span class="unit">V</span>
          </span>
        </div>
        <div class="gauge-bar">
          <div class="gauge-fill" :class="voltageStatusClass" :style="{ width: ((voltage - 10) / 3) * 100 + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- Additional Metrics -->
    <div class="metrics-grid">
      <div class="metric-item">
        <div class="metric-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="23 7 16 12 23 17 23 7" />
            <rect x="1" y="5" width="15" height="14" rx="2" />
          </svg>
        </div>
        <div class="metric-data">
          <span class="metric-label">FPS</span>
          <span class="metric-value">{{ fps.toFixed(1) }}</span>
        </div>
      </div>
      <div class="metric-item">
        <div class="metric-icon signal-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12.55a11 11 0 0 1 14.08 0" />
            <path d="M1.42 9a16 16 0 0 1 21.16 0" />
            <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
            <line x1="12" y1="20" x2="12.01" y2="20" />
          </svg>
        </div>
        <div class="metric-data">
          <span class="metric-label">RSSI</span>
          <span class="metric-value">{{ rssi }}<span class="unit">dBm</span></span>
        </div>
      </div>
    </div>

    <!-- Mock Mode Indicator -->
    <div v-if="mockMode" class="mock-indicator">
      <span class="mock-dot"></span>
      SIMULATION MODE
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { useSystemStore } from '@/stores/system'

// Register ECharts components
use([CanvasRenderer, LineChart, GridComponent])

const systemStore = useSystemStore()
const {
  cpuUsage,
  cpuHistory,
  ramUsage,
  ramHistory,
  temperature,
  voltage,
  fps,
  rssi,
  mockMode
} = storeToRefs(systemStore)

// CPU Chart Option
const cpuChartOption = computed(() => ({
  grid: { left: 0, right: 0, top: 5, bottom: 0 },
  xAxis: { type: 'category', show: false, data: cpuHistory.value.map((_, i) => i) },
  yAxis: { type: 'value', min: 0, max: 100, show: false },
  series: [{
    data: cpuHistory.value,
    type: 'line',
    smooth: true,
    symbol: 'none',
    lineStyle: { color: '#00f0ff', width: 1.5 },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(0, 240, 255, 0.3)' },
          { offset: 1, color: 'rgba(0, 240, 255, 0.02)' }
        ]
      }
    }
  }]
}))

// RAM Chart Option
const ramChartOption = computed(() => ({
  grid: { left: 0, right: 0, top: 5, bottom: 0 },
  xAxis: { type: 'category', show: false, data: ramHistory.value.map((_, i) => i) },
  yAxis: { type: 'value', min: 0, max: 100, show: false },
  series: [{
    data: ramHistory.value,
    type: 'line',
    smooth: true,
    symbol: 'none',
    lineStyle: { color: '#00ff88', width: 1.5 },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(0, 255, 136, 0.3)' },
          { offset: 1, color: 'rgba(0, 255, 136, 0.02)' }
        ]
      }
    }
  }]
}))

// Status classes
const cpuStatusClass = computed(() => {
  if (cpuUsage.value > 80) return 'status-danger'
  if (cpuUsage.value > 60) return 'status-warning'
  return 'status-good'
})

const ramStatusClass = computed(() => {
  if (ramUsage.value > 85) return 'status-danger'
  if (ramUsage.value > 70) return 'status-warning'
  return 'status-good'
})

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

onMounted(() => {
  systemStore.startMonitoring()
})

onUnmounted(() => {
  systemStore.stopMonitoring()
})
</script>

<style scoped>
.system-monitor {
  @apply space-y-4;
}

/* Charts Grid */
.charts-grid {
  @apply space-y-4;
}

.chart-container {
  @apply p-3 rounded-sm;
  background: rgba(0, 240, 255, 0.03);
  border: 1px solid rgba(0, 240, 255, 0.1);
}

.chart-header {
  @apply flex items-center justify-between mb-2;
}

.chart-label {
  @apply text-[10px] font-orbitron tracking-wider text-dark-text-tertiary uppercase;
}

.chart-value {
  @apply text-lg font-mono font-bold;
}

.chart-value .unit {
  @apply text-xs ml-0.5 opacity-60;
}

.chart-bar {
  @apply relative h-2 mb-2 rounded-sm overflow-hidden;
  background: rgba(0, 240, 255, 0.1);
}

.bar-fill {
  @apply absolute inset-y-0 left-0 transition-all duration-300;
}

.cpu-bar {
  background: linear-gradient(90deg, #00f0ff, #0080ff);
  box-shadow: 0 0 8px rgba(0, 240, 255, 0.5);
}

.ram-bar {
  background: linear-gradient(90deg, #00ff88, #00b060);
  box-shadow: 0 0 8px rgba(0, 255, 136, 0.5);
}

.bar-segments {
  @apply absolute inset-0 flex;
}

.segment {
  @apply flex-1 border-r border-dark-bg-primary/30;
}

.segment:last-child {
  @apply border-r-0;
}

.chart {
  @apply w-full;
  height: 50px;
}

/* Gauges Grid */
.gauges-grid {
  @apply space-y-3;
}

.gauge-item {
  @apply flex items-center gap-3 p-3 rounded-sm;
  background: rgba(0, 240, 255, 0.03);
  border: 1px solid rgba(0, 240, 255, 0.1);
}

.gauge-icon {
  @apply w-8 h-8 text-primary flex-shrink-0;
}

.gauge-data {
  @apply flex-1 flex items-baseline gap-2;
}

.gauge-label {
  @apply text-[10px] font-orbitron tracking-wider text-dark-text-tertiary;
}

.gauge-value {
  @apply text-lg font-mono font-bold ml-auto;
}

.gauge-value .unit {
  @apply text-xs ml-0.5 opacity-60;
}

.gauge-bar {
  @apply w-20 h-1.5 rounded-full overflow-hidden flex-shrink-0;
  background: rgba(0, 240, 255, 0.1);
}

.gauge-fill {
  @apply h-full transition-all duration-300;
}

.gauge-fill.status-good {
  background: linear-gradient(90deg, #00ff88, #00b060);
  box-shadow: 0 0 6px rgba(0, 255, 136, 0.5);
}

.gauge-fill.status-warning {
  background: linear-gradient(90deg, #ffff00, #ff6b35);
  box-shadow: 0 0 6px rgba(255, 255, 0, 0.5);
}

.gauge-fill.status-danger {
  background: linear-gradient(90deg, #ff6b35, #ff0040);
  box-shadow: 0 0 6px rgba(255, 0, 64, 0.5);
}

/* Metrics Grid */
.metrics-grid {
  @apply grid grid-cols-2 gap-3;
}

.metric-item {
  @apply flex items-center gap-2 p-3 rounded-sm;
  background: rgba(0, 240, 255, 0.03);
  border: 1px solid rgba(0, 240, 255, 0.1);
}

.metric-icon {
  @apply w-5 h-5 text-primary;
}

.signal-icon {
  animation: pulse 2s ease-in-out infinite;
}

.metric-data {
  @apply flex flex-col;
}

.metric-label {
  @apply text-[10px] font-orbitron tracking-wider text-dark-text-tertiary;
}

.metric-value {
  @apply text-sm font-mono font-bold text-dark-text-primary;
}

.metric-value .unit {
  @apply text-xs ml-0.5 opacity-60;
}

/* Status Colors */
.status-good {
  @apply text-secondary;
  text-shadow: 0 0 8px rgba(0, 255, 136, 0.5);
}

.status-warning {
  @apply text-warning;
  text-shadow: 0 0 8px rgba(255, 255, 0, 0.5);
}

.status-danger {
  @apply text-danger;
  text-shadow: 0 0 8px rgba(255, 0, 64, 0.5);
}

/* Mock Indicator */
.mock-indicator {
  @apply flex items-center justify-center gap-2 py-2 text-[10px] font-orbitron tracking-wider;
  @apply text-warning/70;
}

.mock-dot {
  @apply w-1.5 h-1.5 rounded-full bg-warning;
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
