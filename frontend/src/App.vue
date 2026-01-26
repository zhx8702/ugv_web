<template>
  <div id="app" class="min-h-screen bg-dark-bg-primary">
    <AppHeader />
    <main class="container mx-auto px-4 py-6">
      <router-view />
    </main>
    <ToastContainer />
    <ConfirmDialog />
    <ConnectionIndicator />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useSystemStore } from '@/stores/system'
import { useWebSocket } from '@/composables/useWebSocket'
import AppHeader from '@/components/layout/AppHeader.vue'
import ToastContainer from '@/components/common/ToastContainer.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import ConnectionIndicator from '@/components/common/ConnectionIndicator.vue'

const systemStore = useSystemStore()
const { connect, disconnect } = useWebSocket()

onMounted(() => {
  connect()
  systemStore.startMonitoring()
})

onUnmounted(() => {
  disconnect()
  systemStore.stopMonitoring()
})
</script>
