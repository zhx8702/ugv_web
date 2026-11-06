<template>
  <div class="video-library">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <polygon points="23 7 16 12 23 17 23 7" />
            <rect x="1" y="5" width="15" height="14" rx="2" />
          </svg>
        </div>
        <div class="header-text">
          <h1 class="header-title">VIDEO VAULT</h1>
          <div class="header-subtitle">
            <span class="prefix">//</span>
            MISSION RECORDINGS DATABASE
          </div>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-primary" :class="{ recording: isRecording }" @click="toggleRecording">
          <span class="rec-indicator" v-if="isRecording"></span>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
            <circle cx="12" cy="12" r="10" />
            <circle cx="12" cy="12" r="4" fill="currentColor" />
          </svg>
          {{ isRecording ? 'RECORDING...' : 'RECORD' }}
        </button>
        <button class="btn btn-outline btn-danger" :disabled="selectedVideos.length === 0" @click="deleteSelected">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
          DELETE {{ selectedVideos.length > 0 ? `(${selectedVideos.length})` : '' }}
        </button>
      </div>
    </div>

    <!-- Storage Panel -->
    <div class="storage-panel">
      <div class="storage-header">
        <div class="storage-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-5 h-5">
            <rect x="2" y="2" width="20" height="8" rx="2" />
            <rect x="2" y="14" width="20" height="8" rx="2" />
            <line x1="6" y1="6" x2="6.01" y2="6" />
            <line x1="6" y1="18" x2="6.01" y2="18" />
          </svg>
        </div>
        <div class="storage-info">
          <span class="storage-label">VIDEO STORAGE</span>
          <span class="storage-value">{{ usedStorage }} MB / {{ totalStorage }} MB</span>
        </div>
        <div class="storage-percent" :class="storageClass">{{ storagePercent }}%</div>
      </div>
      <div class="storage-bar">
        <div class="storage-fill" :class="storageClass" :style="{ width: storagePercent + '%' }"></div>
        <div class="storage-markers">
          <div class="marker" style="left: 50%"><span>50%</span></div>
          <div class="marker" style="left: 80%"><span>80%</span></div>
        </div>
      </div>
    </div>

    <!-- Video List -->
    <div class="video-list" v-if="videos.length > 0">
      <div
        v-for="(video, index) in videos"
        :key="video.id"
        class="video-card"
        :class="{ selected: selectedVideos.includes(video.id) }"
        :style="{ animationDelay: `${index * 100}ms` }"
      >
        <div class="video-select" @click="toggleSelect(video.id)">
          <div class="select-box" :class="{ checked: selectedVideos.includes(video.id) }">
            <svg v-if="selectedVideos.includes(video.id)" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
        </div>

        <div class="video-thumbnail">
          <img v-if="video.thumbnail" :src="video.thumbnail" alt="" class="thumb-img" />
          <video v-else :src="video.url" preload="metadata" muted></video>
          <div class="thumbnail-overlay">
            <button class="play-btn" @click="playVideo(video)">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
            </button>
          </div>
          <div class="video-duration">{{ video.duration }}</div>
          <!-- HUD Corners -->
          <div class="thumb-corner tl"></div>
          <div class="thumb-corner br"></div>
        </div>

        <div class="video-info">
          <h3 class="video-name">{{ video.name }}</h3>
          <div class="video-meta">
            <div class="meta-row">
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                  <line x1="16" y1="2" x2="16" y2="6" />
                  <line x1="8" y1="2" x2="8" y2="6" />
                  <line x1="3" y1="10" x2="21" y2="10" />
                </svg>
                {{ video.date }}
              </span>
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                {{ video.time }}
              </span>
            </div>
            <div class="meta-row">
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                </svg>
                {{ video.size }}
              </span>
              <span class="meta-item resolution">
                {{ video.resolution }}
              </span>
            </div>
          </div>
        </div>

        <div class="video-actions">
          <button class="action-btn" @click="playVideo(video)" title="Play">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
          </button>
          <button class="action-btn" @click="downloadVideo(video)" title="Download">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          </button>
          <button class="action-btn danger" @click="deleteVideo(video)" title="Delete">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div class="empty-state" v-else>
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <polygon points="23 7 16 12 23 17 23 7" />
          <rect x="1" y="5" width="15" height="14" rx="2" />
        </svg>
        <div class="empty-pulse"></div>
      </div>
      <h3 class="empty-title">NO RECORDINGS FOUND</h3>
      <p class="empty-text">Start recording mission footage to build your archive</p>
      <button class="btn btn-primary" @click="toggleRecording">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
          <circle cx="12" cy="12" r="10" />
          <circle cx="12" cy="12" r="4" fill="currentColor" />
        </svg>
        START RECORDING
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getVideos, deleteVideo as apiDeleteVideo, startRecording, stopRecording } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { useSystemStore } from '@/stores/system'

const toast = useToast()
const systemStore = useSystemStore()
const videos = ref([])
const loading = ref(false)
const selectedVideos = ref([])
const isRecording = ref(false)
const usedStorage = ref(0)
const totalStorage = ref(5000)

const storagePercent = computed(() => {
  return Math.round((usedStorage.value / totalStorage.value) * 100)
})

const storageClass = computed(() => {
  if (storagePercent.value >= 80) return 'danger'
  if (storagePercent.value >= 50) return 'warning'
  return 'normal'
})

// 格式化文件大小
function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 格式化时长 (秒 -> MM:SS)
function formatDuration(seconds) {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 加载视频列表
async function loadVideos() {
  loading.value = true
  try {
    const data = await getVideos()
    videos.value = data.map(video => ({
      id: video.id,
      name: video.name,
      url: video.url,
      thumbnail: video.thumbnail,
      date: video.created?.split(' ')[0] || '',
      time: video.created?.split(' ')[1] || '',
      duration: formatDuration(video.duration),
      size: formatSize(video.size),
      resolution: video.resolution || '1080p'
    }))
    // 计算已用存储
    const totalBytes = data.reduce((sum, v) => sum + v.size, 0)
    usedStorage.value = Math.round(totalBytes / (1024 * 1024))
    // 更新全局媒体计数
    systemStore.fetchMediaCount()
  } catch (error) {
    console.error('Failed to load videos:', error)
    toast.error('Failed to load videos')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadVideos()
})

function toggleSelect(id) {
  const index = selectedVideos.value.indexOf(id)
  if (index === -1) {
    selectedVideos.value.push(id)
  } else {
    selectedVideos.value.splice(index, 1)
  }
}

function playVideo(video) {
  // 在新窗口打开视频
  window.open(video.url, '_blank')
}

function downloadVideo(video) {
  const link = document.createElement('a')
  link.href = video.url
  link.download = video.name
  link.click()
}

async function deleteVideo(video) {
  try {
    await apiDeleteVideo(video.id)
    toast.success(`Deleted ${video.name}`)
    loadVideos()
  } catch (error) {
    console.error('Failed to delete video:', error)
    toast.error('Failed to delete video')
  }
}

async function deleteSelected() {
  if (selectedVideos.value.length === 0) return

  try {
    for (const id of selectedVideos.value) {
      await apiDeleteVideo(id)
    }
    toast.success(`Deleted ${selectedVideos.value.length} video(s)`)
    selectedVideos.value = []
    loadVideos()
  } catch (error) {
    console.error('Failed to delete videos:', error)
    toast.error('Failed to delete videos')
  }
}

async function toggleRecording() {
  try {
    if (isRecording.value) {
      await stopRecording()
      isRecording.value = false
      toast.success('Recording stopped')
      // 延迟刷新列表，等待视频保存
      setTimeout(() => loadVideos(), 1000)
    } else {
      await startRecording()
      isRecording.value = true
      toast.success('Recording started')
    }
  } catch (error) {
    console.error('Failed to toggle recording:', error)
    toast.error('Failed to toggle recording')
  }
}
</script>

<style scoped>
.video-library {
  @apply p-6 min-h-screen;
  animation: fadeIn 0.5s ease-out;
}

/* Page Header */
.page-header {
  @apply flex items-center justify-between mb-6 pb-4;
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.header-left {
  @apply flex items-center gap-4;
}

.header-icon {
  @apply w-10 h-10 text-primary;
  filter: drop-shadow(0 0 8px rgba(0, 240, 255, 0.5));
}

.header-text {
  @apply flex flex-col;
}

.header-title {
  @apply text-2xl font-orbitron font-bold tracking-widest;
  background: linear-gradient(135deg, #00f0ff 0%, #0080ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-subtitle {
  @apply text-xs font-mono text-dark-text-tertiary flex items-center gap-2;
}

.header-subtitle .prefix {
  @apply text-primary;
}

.header-actions {
  @apply flex items-center gap-3;
}

.btn.recording {
  @apply bg-danger/30 border-danger text-danger;
  animation: recordPulse 1s ease-in-out infinite;
}

.rec-indicator {
  @apply w-3 h-3 bg-danger rounded-full mr-2;
  animation: pulse 1s ease-in-out infinite;
}

/* Storage Panel */
.storage-panel {
  @apply mb-6 p-4;
  background: linear-gradient(135deg, rgba(10, 22, 40, 0.9) 0%, rgba(3, 7, 18, 0.95) 100%);
  border: 1px solid rgba(0, 240, 255, 0.15);
  clip-path: polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px);
}

.storage-header {
  @apply flex items-center gap-4 mb-3;
}

.storage-icon {
  @apply text-primary;
}

.storage-info {
  @apply flex-1 flex flex-col;
}

.storage-label {
  @apply text-[10px] font-orbitron tracking-wider text-dark-text-tertiary uppercase;
}

.storage-value {
  @apply text-sm font-mono text-dark-text-primary;
}

.storage-percent {
  @apply text-2xl font-orbitron font-bold;
  text-shadow: 0 0 10px currentColor;
}

.storage-percent.normal {
  @apply text-primary;
}

.storage-percent.warning {
  @apply text-warning;
}

.storage-percent.danger {
  @apply text-danger;
}

.storage-bar {
  @apply relative h-3 bg-dark-bg-tertiary rounded-sm overflow-hidden;
}

.storage-fill {
  @apply absolute inset-y-0 left-0;
  transition: width 0.5s ease-out;
}

.storage-fill.normal {
  background: linear-gradient(90deg, #00f0ff, #0080ff);
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
}

.storage-fill.warning {
  background: linear-gradient(90deg, #ffff00, #ff6b35);
  box-shadow: 0 0 10px rgba(255, 255, 0, 0.5);
}

.storage-fill.danger {
  background: linear-gradient(90deg, #ff6b35, #ff0040);
  box-shadow: 0 0 10px rgba(255, 0, 64, 0.5);
}

.storage-markers {
  @apply absolute inset-0;
}

.marker {
  @apply absolute top-0 bottom-0 w-px bg-dark-text-tertiary/30;
}

.marker span {
  @apply absolute -top-5 left-1/2 -translate-x-1/2 text-[10px] font-mono text-dark-text-tertiary;
}

/* Video List */
.video-list {
  @apply space-y-4;
}

/* Video Card */
.video-card {
  @apply flex items-center gap-4 p-4;
  background: linear-gradient(135deg, rgba(10, 22, 40, 0.9) 0%, rgba(3, 7, 18, 0.95) 100%);
  border: 1px solid rgba(0, 240, 255, 0.15);
  clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
  animation: slideUp 0.5s ease-out both;
  transition: all 0.3s ease;
}

.video-card:hover {
  border-color: rgba(0, 240, 255, 0.3);
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.1);
}

.video-card.selected {
  border-color: var(--cyber-cyan);
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.2);
}

/* Select Box */
.video-select {
  @apply cursor-pointer;
}

.select-box {
  @apply w-6 h-6 flex items-center justify-center;
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.3);
  clip-path: polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px);
  transition: all 0.2s ease;
}

.select-box:hover {
  border-color: var(--cyber-cyan);
}

.select-box.checked {
  background: var(--cyber-cyan);
  border-color: var(--cyber-cyan);
}

.select-box svg {
  @apply w-4 h-4 text-dark-bg-primary;
}

/* Video Thumbnail */
.video-thumbnail {
  @apply relative w-40 h-24 flex-shrink-0 overflow-hidden;
  background: var(--dark-bg);
}

.video-thumbnail video,
.video-thumbnail .thumb-img {
  @apply w-full h-full object-cover;
  filter: saturate(0.8);
  transition: all 0.3s ease;
}

.video-card:hover .video-thumbnail video,
.video-card:hover .video-thumbnail .thumb-img {
  filter: saturate(1);
  transform: scale(1.05);
}

.thumbnail-overlay {
  @apply absolute inset-0 flex items-center justify-center opacity-0;
  background: rgba(3, 7, 18, 0.6);
  transition: opacity 0.3s ease;
}

.video-card:hover .thumbnail-overlay {
  @apply opacity-100;
}

.play-btn {
  @apply w-12 h-12 flex items-center justify-center rounded-full;
  background: rgba(0, 240, 255, 0.2);
  border: 2px solid var(--cyber-cyan);
  color: var(--cyber-cyan);
  transition: all 0.2s ease;
}

.play-btn:hover {
  background: rgba(0, 240, 255, 0.3);
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.5);
  transform: scale(1.1);
}

.play-btn svg {
  @apply w-5 h-5 ml-1;
}

.video-duration {
  @apply absolute bottom-2 right-2 px-2 py-0.5 text-xs font-mono text-dark-text-primary;
  background: rgba(3, 7, 18, 0.8);
}

.thumb-corner {
  @apply absolute w-3 h-3;
}

.thumb-corner.tl {
  @apply top-1 left-1;
  border-top: 1px solid var(--cyber-cyan);
  border-left: 1px solid var(--cyber-cyan);
}

.thumb-corner.br {
  @apply bottom-1 right-1;
  border-bottom: 1px solid var(--cyber-cyan);
  border-right: 1px solid var(--cyber-cyan);
}

/* Video Info */
.video-info {
  @apply flex-1 min-w-0;
}

.video-name {
  @apply text-base font-orbitron font-semibold tracking-wider text-dark-text-primary mb-2 truncate;
}

.video-meta {
  @apply space-y-1;
}

.meta-row {
  @apply flex items-center gap-4;
}

.meta-item {
  @apply flex items-center gap-1.5 text-xs font-mono text-dark-text-tertiary;
}

.meta-item.resolution {
  @apply px-2 py-0.5 bg-primary/10 text-primary border border-primary/30;
  clip-path: polygon(3px 0, 100% 0, 100% calc(100% - 3px), calc(100% - 3px) 100%, 0 100%, 0 3px);
}

/* Video Actions */
.video-actions {
  @apply flex items-center gap-2;
}

.action-btn {
  @apply w-10 h-10 flex items-center justify-center text-dark-text-tertiary;
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.2);
  clip-path: polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px);
  transition: all 0.2s ease;
}

.action-btn:hover {
  @apply text-primary;
  border-color: var(--cyber-cyan);
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
}

.action-btn.danger:hover {
  @apply text-danger;
  border-color: var(--cyber-red);
  box-shadow: 0 0 10px rgba(255, 0, 64, 0.3);
}

.action-btn svg {
  @apply w-5 h-5;
}

/* Empty State */
.empty-state {
  @apply flex flex-col items-center justify-center py-20;
}

.empty-icon {
  @apply relative w-24 h-24 text-dark-text-tertiary mb-6;
}

.empty-icon svg {
  @apply w-full h-full;
}

.empty-pulse {
  @apply absolute inset-0 rounded-full;
  border: 2px solid rgba(0, 240, 255, 0.2);
  animation: pulseRing 2s ease-out infinite;
}

.empty-title {
  @apply text-xl font-orbitron font-bold tracking-wider text-dark-text-primary mb-2;
}

.empty-text {
  @apply text-sm font-mono text-dark-text-tertiary mb-6;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes recordPulse {
  0%, 100% { box-shadow: 0 0 10px rgba(255, 0, 64, 0.3); }
  50% { box-shadow: 0 0 20px rgba(255, 0, 64, 0.6); }
}

@keyframes pulseRing {
  0% {
    transform: scale(0.9);
    opacity: 1;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}
</style>
