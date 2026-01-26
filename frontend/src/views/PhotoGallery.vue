<template>
  <div class="photo-gallery">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <path d="M21 15l-5-5L5 21" />
          </svg>
        </div>
        <div class="header-text">
          <h1 class="header-title">IMAGE ARCHIVE</h1>
          <div class="header-subtitle">
            <span class="prefix">//</span>
            CAPTURED RECONNAISSANCE DATA
          </div>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-primary" @click="capture">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
            <circle cx="12" cy="13" r="4" />
          </svg>
          CAPTURE
        </button>
        <button class="btn btn-outline btn-danger" :disabled="selectedPhotos.length === 0" @click="deleteSelected">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
          DELETE {{ selectedPhotos.length > 0 ? `(${selectedPhotos.length})` : '' }}
        </button>
      </div>
    </div>

    <!-- Storage Panel -->
    <div class="storage-panel">
      <div class="storage-header">
        <div class="storage-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-5 h-5">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
            <line x1="12" y1="22.08" x2="12" y2="12" />
          </svg>
        </div>
        <div class="storage-info">
          <span class="storage-label">STORAGE ALLOCATION</span>
          <span class="storage-value">{{ usedStorage }} MB / {{ totalStorage }} MB</span>
        </div>
        <div class="storage-percent">{{ storagePercent }}%</div>
      </div>
      <div class="storage-bar">
        <div class="storage-fill" :style="{ width: storagePercent + '%' }"></div>
        <div class="storage-segments">
          <div v-for="i in 20" :key="i" class="segment"></div>
        </div>
      </div>
    </div>

    <!-- Gallery Grid -->
    <div class="gallery-section" v-if="photos.length > 0">
      <div class="gallery-grid">
        <div
          v-for="(photo, index) in photos"
          :key="photo.id"
          class="photo-card"
          :class="{ selected: selectedPhotos.includes(photo.id) }"
          @click="toggleSelect(photo.id)"
          :style="{ animationDelay: `${index * 50}ms` }"
        >
          <div class="photo-frame">
            <div class="photo-image">
              <img :src="photo.thumbnail" :alt="photo.name" />
            </div>
            <div class="photo-overlay" @click="toggleSelect(photo.id)">
              <div class="overlay-actions">
                <button class="overlay-btn" @click.stop="viewPhoto(photo)" title="View">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                </button>
                <button class="overlay-btn" @click.stop="downloadPhoto(photo)" title="Download">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                </button>
              </div>
            </div>
            <div class="select-indicator" v-if="selectedPhotos.includes(photo.id)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <!-- HUD Corners -->
            <div class="frame-corner tl"></div>
            <div class="frame-corner tr"></div>
            <div class="frame-corner bl"></div>
            <div class="frame-corner br"></div>
          </div>
          <div class="photo-info">
            <div class="photo-name">{{ photo.name }}</div>
            <div class="photo-meta">
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3 h-3">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                  <line x1="16" y1="2" x2="16" y2="6" />
                  <line x1="8" y1="2" x2="8" y2="6" />
                  <line x1="3" y1="10" x2="21" y2="10" />
                </svg>
                {{ photo.date }}
              </span>
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3 h-3">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                </svg>
                {{ photo.size }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div class="empty-state" v-else>
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <path d="M21 15l-5-5L5 21" />
        </svg>
        <div class="empty-pulse"></div>
      </div>
      <h3 class="empty-title">NO IMAGES IN ARCHIVE</h3>
      <p class="empty-text">Capture reconnaissance images to populate the archive</p>
      <button class="btn btn-primary" @click="capture">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
          <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
          <circle cx="12" cy="13" r="4" />
        </svg>
        INITIATE CAPTURE
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getPhotos, deletePhoto, capturePhoto } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { useSystemStore } from '@/stores/system'

const toast = useToast()
const systemStore = useSystemStore()
const photos = ref([])
const loading = ref(false)
const selectedPhotos = ref([])
const usedStorage = ref(0)
const totalStorage = ref(1000)

const storagePercent = computed(() => {
  return Math.round((usedStorage.value / totalStorage.value) * 100)
})

// 格式化文件大小
function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 加载照片列表
async function loadPhotos() {
  loading.value = true
  try {
    const data = await getPhotos()
    photos.value = data.map(photo => ({
      id: photo.id,
      name: photo.name,
      thumbnail: photo.thumbnail,
      date: photo.created,
      size: formatSize(photo.size)
    }))
    // 计算已用存储
    const totalBytes = data.reduce((sum, p) => sum + p.size, 0)
    usedStorage.value = Math.round(totalBytes / (1024 * 1024))
    // 更新全局媒体计数
    systemStore.fetchMediaCount()
  } catch (error) {
    console.error('Failed to load photos:', error)
    toast.error('Failed to load photos')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPhotos()
})

function toggleSelect(id) {
  const index = selectedPhotos.value.indexOf(id)
  if (index === -1) {
    selectedPhotos.value.push(id)
  } else {
    selectedPhotos.value.splice(index, 1)
  }
}

function viewPhoto(photo) {
  // 在新窗口打开完整图片
  window.open(photo.thumbnail, '_blank')
}

function downloadPhoto(photo) {
  // 创建下载链接
  const link = document.createElement('a')
  link.href = photo.thumbnail
  link.download = photo.name
  link.click()
}

async function deleteSelected() {
  if (selectedPhotos.value.length === 0) return

  try {
    for (const id of selectedPhotos.value) {
      await deletePhoto(id)
    }
    toast.success(`Deleted ${selectedPhotos.value.length} photo(s)`)
    selectedPhotos.value = []
    loadPhotos()
  } catch (error) {
    console.error('Failed to delete photos:', error)
    toast.error('Failed to delete photos')
  }
}

async function capture() {
  try {
    await capturePhoto()
    toast.success('Photo captured')
    // 延迟刷新列表，等待照片保存
    setTimeout(() => loadPhotos(), 500)
  } catch (error) {
    console.error('Failed to capture photo:', error)
    toast.error('Failed to capture photo')
  }
}
</script>

<style scoped>
.photo-gallery {
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
  @apply text-2xl font-orbitron font-bold text-primary;
  text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
}

.storage-bar {
  @apply relative h-3 bg-dark-bg-tertiary rounded-sm overflow-hidden;
}

.storage-fill {
  @apply absolute inset-y-0 left-0;
  background: linear-gradient(90deg, #00f0ff, #0080ff);
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
  transition: width 0.5s ease-out;
}

.storage-segments {
  @apply absolute inset-0 flex;
}

.segment {
  @apply flex-1 border-r border-dark-bg-primary/50;
}

.segment:last-child {
  @apply border-r-0;
}

/* Gallery Grid */
.gallery-section {
  @apply mt-6;
}

.gallery-grid {
  @apply grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4;
}

/* Photo Card */
.photo-card {
  @apply cursor-pointer;
  animation: slideUp 0.5s ease-out both;
}

.photo-frame {
  @apply relative aspect-[4/3] overflow-hidden;
  background: linear-gradient(135deg, rgba(10, 22, 40, 0.9) 0%, rgba(3, 7, 18, 0.95) 100%);
  border: 1px solid rgba(0, 240, 255, 0.15);
  transition: all 0.3s ease;
}

.photo-card:hover .photo-frame {
  border-color: rgba(0, 240, 255, 0.4);
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.2);
}

.photo-card.selected .photo-frame {
  border-color: var(--cyber-cyan);
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.4);
}

.photo-image {
  @apply absolute inset-0;
}

.photo-image img {
  @apply w-full h-full object-cover;
  filter: saturate(0.8) contrast(1.1);
  transition: all 0.3s ease;
}

.photo-card:hover .photo-image img {
  filter: saturate(1) contrast(1);
  transform: scale(1.05);
}

/* Photo Overlay */
.photo-overlay {
  @apply absolute inset-0 flex items-center justify-center opacity-0;
  background: rgba(3, 7, 18, 0.7);
  transition: opacity 0.3s ease;
}

.photo-card:hover .photo-overlay {
  @apply opacity-100;
}

.overlay-actions {
  @apply flex items-center gap-3;
}

.overlay-btn {
  @apply w-10 h-10 flex items-center justify-center text-dark-text-primary rounded;
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid rgba(0, 240, 255, 0.3);
  transition: all 0.2s ease;
}

.overlay-btn:hover {
  @apply text-primary;
  background: rgba(0, 240, 255, 0.2);
  box-shadow: 0 0 15px rgba(0, 240, 255, 0.3);
}

.overlay-btn svg {
  @apply w-5 h-5;
}

/* Select Indicator */
.select-indicator {
  @apply absolute top-2 right-2 w-6 h-6 flex items-center justify-center;
  background: var(--cyber-cyan);
  clip-path: polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px);
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.8);
}

.select-indicator svg {
  @apply w-4 h-4 text-dark-bg-primary;
}

/* Frame Corners */
.frame-corner {
  @apply absolute w-4 h-4;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.photo-card:hover .frame-corner {
  opacity: 1;
}

.frame-corner.tl {
  @apply top-1 left-1;
  border-top: 2px solid var(--cyber-cyan);
  border-left: 2px solid var(--cyber-cyan);
}

.frame-corner.tr {
  @apply top-1 right-1;
  border-top: 2px solid var(--cyber-cyan);
  border-right: 2px solid var(--cyber-cyan);
}

.frame-corner.bl {
  @apply bottom-1 left-1;
  border-bottom: 2px solid var(--cyber-cyan);
  border-left: 2px solid var(--cyber-cyan);
}

.frame-corner.br {
  @apply bottom-1 right-1;
  border-bottom: 2px solid var(--cyber-cyan);
  border-right: 2px solid var(--cyber-cyan);
}

/* Photo Info */
.photo-info {
  @apply p-3;
  background: rgba(10, 22, 40, 0.8);
  border: 1px solid rgba(0, 240, 255, 0.1);
  border-top: none;
}

.photo-name {
  @apply text-sm font-mono text-dark-text-primary truncate mb-1;
}

.photo-meta {
  @apply flex items-center gap-3 text-[10px] text-dark-text-tertiary;
}

.meta-item {
  @apply flex items-center gap-1;
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
