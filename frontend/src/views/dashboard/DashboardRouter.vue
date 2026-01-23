<template>
  <Suspense>
    <template #default>
      <component :is="DashboardComponent" />
    </template>
    <template #fallback>
      <div class="loading-screen">
        <div class="loading-spinner"></div>
        <div class="loading-text">Loading Dashboard...</div>
      </div>
    </template>
  </Suspense>
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue'
import { useDeviceDetection } from '@/composables/useDeviceDetection'

const { isMobile } = useDeviceDetection()

const DashboardComponent = computed(() => {
  if (isMobile.value) {
    return defineAsyncComponent(() => import('./MobileDashboard.vue'))
  }
  return defineAsyncComponent(() => import('./DesktopDashboard.vue'))
})
</script>

<style scoped>
.loading-screen {
  @apply fixed inset-0 flex flex-col items-center justify-center;
  background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 100%);
}

.loading-spinner {
  @apply w-12 h-12 rounded-full;
  border: 2px solid rgba(0, 240, 255, 0.2);
  border-top-color: #00f0ff;
  animation: spin 1s linear infinite;
}

.loading-text {
  @apply mt-4 text-sm font-orbitron tracking-wider text-primary/60;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
