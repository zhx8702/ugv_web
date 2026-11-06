<template>
  <div class="voice-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-title">
        <div class="title-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="23" />
            <line x1="8" y1="23" x2="16" y2="23" />
          </svg>
        </div>
        <div>
          <h1 class="title-text">VOICE CONTROL</h1>
          <p class="title-sub">// AUDIO & TTS MANAGEMENT</p>
        </div>
      </div>
      <div class="header-badges">
        <div class="tts-badge" :class="ttsAvailable ? 'tts-on' : 'tts-off'">
          TTS {{ ttsAvailable ? (ttsEngine || 'READY') : 'OFF' }}
        </div>
        <div class="header-status" :class="statusClass">
          <span class="status-dot"></span>
          <span>{{ playing ? 'PLAYING' : 'IDLE' }}</span>
        </div>
      </div>
    </div>

    <div class="voice-content">
      <!-- Left Column: TTS & Controls -->
      <div class="voice-main">
        <!-- TTS Section -->
        <div class="panel tts-panel">
          <div class="panel-header">
            <span class="panel-title">TEXT TO SPEECH</span>
            <span class="panel-badge" :class="{ 'badge-off': !ttsAvailable }">
              {{ ttsAvailable ? (ttsEngine || 'TTS') : 'UNAVAILABLE' }}
            </span>
          </div>
          <div class="panel-content">
            <p v-if="!ttsAvailable" class="tts-hint">
              TTS 未就绪：车上需要 espeak（已推荐）或 pyttsx3。
            </p>
            <div class="tts-input-group">
              <textarea
                v-model="ttsText"
                class="tts-input"
                placeholder="输入要播报的文字，支持中英文。Ctrl+Enter 发送"
                rows="3"
                :disabled="!ttsAvailable"
                @keydown.ctrl.enter="speakTTS"
              ></textarea>
              <div class="tts-actions">
                <button class="btn btn-primary" @click="speakTTS" :disabled="!ttsAvailable || !ttsText.trim() || speaking">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                  </svg>
                  <span>{{ speaking ? 'Speaking...' : 'Speak' }}</span>
                </button>
                <button class="btn btn-secondary" @click="ttsText = ''" :disabled="!ttsText">
                  Clear
                </button>
              </div>
            </div>

            <!-- Quick Phrases -->
            <div class="quick-phrases">
              <span class="section-label">Quick Phrases</span>
              <div class="phrase-grid">
                <button
                  v-for="phrase in quickPhrases"
                  :key="phrase"
                  class="phrase-btn"
                  @click="speakPhrase(phrase)"
                >
                  {{ phrase }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Volume Control -->
        <div class="panel volume-panel">
          <div class="panel-header">
            <span class="panel-title">VOLUME CONTROL</span>
            <span class="volume-value">{{ Math.round(volume * 100) }}%</span>
          </div>
          <div class="panel-content">
            <div class="volume-control">
              <button class="vol-btn" @click="adjustVolume(-0.1)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-5 h-5">
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                </svg>
              </button>
              <div class="volume-slider-container">
                <input
                  type="range"
                  v-model.number="volume"
                  min="0"
                  max="1"
                  step="0.05"
                  class="volume-slider"
                  @change="updateVolume"
                />
                <div class="volume-track">
                  <div class="volume-fill" :style="{ width: `${volume * 100}%` }"></div>
                </div>
              </div>
              <button class="vol-btn" @click="adjustVolume(0.1)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-5 h-5">
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                </svg>
              </button>
            </div>

            <!-- Playback Control -->
            <div class="playback-control">
              <button class="ctrl-btn stop-btn" @click="stopPlayback" :disabled="!playing">
                <svg viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5">
                  <rect x="6" y="6" width="12" height="12" rx="1" />
                </svg>
                <span>Stop</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Audio Library -->
      <div class="voice-sidebar">
        <div class="panel audio-panel">
          <div class="panel-header">
            <span class="panel-title">AUDIO LIBRARY</span>
            <button class="refresh-btn" @click="loadAudioFiles" :disabled="loading">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4" :class="{ 'animate-spin': loading }">
                <path d="M23 4v6h-6M1 20v-6h6" />
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
              </svg>
            </button>
          </div>
          <div class="panel-content">
            <!-- Category Tabs -->
            <div class="category-tabs">
              <button
                v-for="cat in categories"
                :key="cat.value"
                :class="['cat-tab', { active: selectedCategory === cat.value }]"
                @click="selectCategory(cat.value)"
              >
                {{ cat.label }}
              </button>
            </div>

            <!-- Audio Files List -->
            <div class="audio-list">
              <div v-if="loading" class="loading-state">
                <div class="loading-spinner"></div>
                <span>Loading...</span>
              </div>
              <div v-else-if="filteredFiles.length === 0" class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-12 h-12">
                  <path d="M9 18V5l12-2v13" />
                  <circle cx="6" cy="18" r="3" />
                  <circle cx="18" cy="16" r="3" />
                </svg>
                <span>No audio files</span>
              </div>
              <div v-else class="file-list">
                <button
                  v-for="file in filteredFiles"
                  :key="file.path"
                  :class="['file-item', { playing: currentFile === file.path }]"
                  @click="playFile(file)"
                >
                  <div class="file-icon">
                    <svg v-if="currentFile === file.path && playing" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
                      <rect x="6" y="4" width="4" height="16" rx="1" />
                      <rect x="14" y="4" width="4" height="16" rx="1" />
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
                      <polygon points="5 3 19 12 5 21 5 3" />
                    </svg>
                  </div>
                  <div class="file-info">
                    <span class="file-name">{{ file.name }}</span>
                    <span class="file-category">{{ file.category }}</span>
                  </div>
                </button>
              </div>
            </div>

            <!-- Random Play -->
            <div class="random-play">
              <button class="btn btn-accent" @click="playRandom">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
                  <polyline points="16 3 21 3 21 8" />
                  <line x1="4" y1="20" x2="21" y2="3" />
                  <polyline points="21 16 21 21 16 21" />
                  <line x1="15" y1="15" x2="21" y2="21" />
                  <line x1="4" y1="4" x2="9" y2="9" />
                </svg>
                <span>Play Random</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import {
  getAudioFiles,
  playAudioFile,
  playRandomAudio,
  speakText,
  stopAudio,
  getAudioVolume,
  setAudioVolume,
  getAudioStatus
} from '@/services/api'

const toast = useToast()

// State
const ttsText = ref('')
const speaking = ref(false)
const playing = ref(false)
const volume = ref(0.5)
const loading = ref(false)
const audioFiles = ref([])
const selectedCategory = ref('all')
const currentFile = ref(null)
const ttsAvailable = ref(false)
const ttsEngine = ref('')

// Categories
const categories = [
  { value: 'all', label: 'All' },
  { value: 'robot_started', label: 'Startup' },
  { value: 'connected', label: 'Connect' },
  { value: 'others', label: 'Others' }
]

// Quick phrases for TTS
const quickPhrases = [
  '你好，我是巡逻车',
  '任务完成',
  '发现异常',
  '电量偏低',
  '准备出发',
  'Hello, ready to go'
]

// Computed
const filteredFiles = computed(() => {
  if (selectedCategory.value === 'all') {
    return audioFiles.value
  }
  return audioFiles.value.filter(f => f.category === selectedCategory.value)
})

const statusClass = computed(() => playing.value ? 'status-playing' : 'status-idle')

// Methods
async function loadAudioFiles() {
  loading.value = true
  try {
    const data = await getAudioFiles()
    audioFiles.value = data.files || []
  } catch (e) {
    toast.error('Failed to load audio files')
  } finally {
    loading.value = false
  }
}

async function loadVolume() {
  try {
    const data = await getAudioVolume()
    volume.value = data.volume || 0.5
  } catch (e) {
    console.error('Failed to get volume:', e)
  }
}

async function updateVolume() {
  try {
    await setAudioVolume(volume.value)
  } catch (e) {
    toast.error('Failed to set volume')
  }
}

function adjustVolume(delta) {
  volume.value = Math.max(0, Math.min(1, volume.value + delta))
  updateVolume()
}

async function speakTTS() {
  if (!ttsText.value.trim() || !ttsAvailable.value) return
  speaking.value = true
  playing.value = true
  try {
    const data = await speakText(ttsText.value)
    if (data && data.success === false) {
      toast.error(data.error || 'TTS failed')
      speaking.value = false
      playing.value = false
      return
    }
    toast.success('Speaking...')
  } catch (e) {
    toast.error(e?.response?.data?.error || 'TTS failed')
    playing.value = false
  } finally {
    speaking.value = false
  }
}

function speakPhrase(phrase) {
  ttsText.value = phrase
  speakTTS()
}

async function playFile(file) {
  currentFile.value = file.path
  playing.value = true
  try {
    await playAudioFile(file.path)
  } catch (e) {
    toast.error('Failed to play audio')
    playing.value = false
    currentFile.value = null
  }
}

async function playRandom() {
  const category = selectedCategory.value === 'all' ? 'others' : selectedCategory.value
  playing.value = true
  try {
    await playRandomAudio(category, true)
  } catch (e) {
    toast.error('Failed to play random audio')
    playing.value = false
  }
}

async function stopPlayback() {
  try {
    await stopAudio()
    playing.value = false
    currentFile.value = null
  } catch (e) {
    toast.error('Failed to stop')
  }
}

function selectCategory(cat) {
  selectedCategory.value = cat
}

// Check playing status periodically
let statusInterval = null

async function checkStatus() {
  try {
    const data = await getAudioStatus()
    playing.value = data.playing || false
    ttsAvailable.value = !!data.tts_available
    ttsEngine.value = data.tts_engine || ''
    if (!playing.value) {
      currentFile.value = null
    }
  } catch (e) {
    // Ignore status check errors
  }
}

onMounted(() => {
  loadAudioFiles()
  loadVolume()
  checkStatus()
  statusInterval = setInterval(checkStatus, 2000)
})

// Cleanup
import { onUnmounted } from 'vue'
onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval)
  }
})
</script>

<style scoped>
.voice-page {
  @apply max-w-6xl mx-auto;
}

/* Page Header */
.page-header {
  @apply flex items-center justify-between mb-6 pb-4;
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.header-title {
  @apply flex items-center gap-4;
}

.title-icon {
  @apply w-12 h-12 p-2.5;
  @apply text-primary;
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid rgba(0, 240, 255, 0.2);
  clip-path: polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px);
}

.title-text {
  @apply text-xl font-orbitron font-bold text-dark-text-primary tracking-wider;
}

.title-sub {
  @apply text-xs font-mono text-dark-text-tertiary mt-1;
}

.header-badges {
  @apply flex items-center gap-2;
}

.tts-badge {
  @apply px-3 py-2 text-[10px] font-mono tracking-wider;
  border: 1px solid rgba(0, 240, 255, 0.15);
  clip-path: polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px);
}
.tts-on {
  @apply text-secondary;
  background: rgba(0, 255, 136, 0.08);
}
.tts-off {
  @apply text-danger;
  background: rgba(255, 80, 80, 0.08);
}

.header-status {
  @apply flex items-center gap-2 px-4 py-2 text-xs font-mono;
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.1);
  clip-path: polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px);
}

.badge-off {
  @apply text-danger bg-danger/10;
  border-color: rgba(255, 80, 80, 0.3);
}

.tts-hint {
  @apply mb-3 text-xs font-mono text-danger;
}

.status-dot {
  @apply w-2 h-2 rounded-full;
}

.status-idle {
  @apply text-dark-text-tertiary;
}
.status-idle .status-dot {
  @apply bg-dark-text-tertiary;
}

.status-playing {
  @apply text-secondary;
}
.status-playing .status-dot {
  @apply bg-secondary;
  box-shadow: 0 0 8px rgba(0, 255, 136, 0.6);
  animation: pulse 1s infinite;
}

/* Content Layout */
.voice-content {
  @apply grid gap-6;
  grid-template-columns: 1fr 320px;
}

@media (max-width: 900px) {
  .voice-content {
    grid-template-columns: 1fr;
  }
}

.voice-main {
  @apply flex flex-col gap-6;
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

.panel-content {
  @apply p-4;
}

/* TTS Panel */
.tts-input-group {
  @apply flex flex-col gap-3;
}

.tts-input {
  @apply w-full px-4 py-3 text-sm font-mono resize-none;
  @apply text-dark-text-primary bg-dark-bg-tertiary/50;
  @apply border border-dark-border rounded;
  @apply focus:border-primary focus:outline-none;
  @apply placeholder:text-dark-text-tertiary/50;
}

.tts-actions {
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

.btn-primary {
  @apply text-dark-bg-primary bg-primary;
}
.btn-primary:hover:not(:disabled) {
  @apply bg-primary/80;
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.4);
}

.btn-secondary {
  @apply text-dark-text-secondary bg-dark-bg-tertiary border border-dark-border;
}
.btn-secondary:hover:not(:disabled) {
  @apply border-primary/50 text-primary;
}

.btn-accent {
  @apply text-dark-bg-primary bg-secondary;
}
.btn-accent:hover:not(:disabled) {
  @apply bg-secondary/80;
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.4);
}

/* Quick Phrases */
.quick-phrases {
  @apply mt-4;
}

.section-label {
  @apply block text-[10px] font-mono text-dark-text-tertiary mb-2 uppercase tracking-wider;
}

.phrase-grid {
  @apply grid grid-cols-3 gap-2;
}

.phrase-btn {
  @apply px-3 py-2 text-xs font-mono;
  @apply text-dark-text-secondary bg-dark-bg-tertiary/50;
  @apply border border-dark-border rounded;
  @apply transition-all duration-150;
}

.phrase-btn:hover {
  @apply text-primary border-primary/50;
  background: rgba(0, 240, 255, 0.05);
}

/* Volume Panel */
.volume-value {
  @apply text-sm font-mono font-bold text-primary;
}

.volume-control {
  @apply flex items-center gap-4;
}

.vol-btn {
  @apply p-2 text-dark-text-tertiary;
  @apply transition-colors duration-150;
}
.vol-btn:hover {
  @apply text-primary;
}

.volume-slider-container {
  @apply flex-1 relative h-8 flex items-center;
}

.volume-slider {
  @apply absolute inset-0 w-full opacity-0 cursor-pointer z-10;
}

.volume-track {
  @apply w-full h-2 rounded-full overflow-hidden;
  background: rgba(0, 240, 255, 0.1);
}

.volume-fill {
  @apply h-full;
  background: linear-gradient(90deg, var(--cyber-cyan) 0%, var(--cyber-green) 100%);
  transition: width 0.1s;
}

.playback-control {
  @apply mt-4 flex justify-center;
}

.ctrl-btn {
  @apply flex items-center gap-2 px-6 py-2;
  @apply text-sm font-orbitron;
  @apply transition-all duration-150;
  border-radius: 4px;
}

.stop-btn {
  @apply text-danger bg-danger/10 border border-danger/30;
}
.stop-btn:hover:not(:disabled) {
  @apply bg-danger/20 border-danger;
}
.stop-btn:disabled {
  @apply opacity-30 cursor-not-allowed;
}

/* Audio Panel */
.refresh-btn {
  @apply p-1 text-dark-text-tertiary;
  @apply transition-colors duration-150;
}
.refresh-btn:hover:not(:disabled) {
  @apply text-primary;
}

.category-tabs {
  @apply flex gap-1 mb-4;
}

.cat-tab {
  @apply flex-1 py-2 text-xs font-mono;
  @apply text-dark-text-tertiary bg-dark-bg-tertiary/30;
  @apply border border-transparent;
  @apply transition-all duration-150;
}

.cat-tab:hover {
  @apply text-dark-text-secondary;
}

.cat-tab.active {
  @apply text-primary bg-primary/10;
  border-color: rgba(0, 240, 255, 0.3);
}

.audio-list {
  @apply max-h-[300px] overflow-y-auto;
}

.loading-state,
.empty-state {
  @apply flex flex-col items-center justify-center py-8;
  @apply text-dark-text-tertiary text-sm;
}

.loading-spinner {
  @apply w-8 h-8 mb-2 border-2 border-primary/30 border-t-primary rounded-full;
  animation: spin 1s linear infinite;
}

.file-list {
  @apply flex flex-col gap-1;
}

.file-item {
  @apply flex items-center gap-3 px-3 py-2;
  @apply text-left;
  @apply text-dark-text-secondary bg-dark-bg-tertiary/30;
  @apply border border-transparent rounded;
  @apply transition-all duration-150;
}

.file-item:hover {
  @apply bg-primary/5 border-primary/20;
}

.file-item.playing {
  @apply bg-primary/10 border-primary/30 text-primary;
}

.file-icon {
  @apply w-6 h-6 flex items-center justify-center;
  @apply text-dark-text-tertiary;
}

.file-item.playing .file-icon {
  @apply text-primary;
}

.file-info {
  @apply flex-1 min-w-0;
}

.file-name {
  @apply block text-sm truncate;
}

.file-category {
  @apply block text-[10px] font-mono text-dark-text-tertiary;
}

.random-play {
  @apply mt-4;
}

.random-play .btn {
  @apply w-full;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
