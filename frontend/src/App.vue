<template>
  <div id="app" class="min-h-screen bg-dark-bg-primary">
    <AppHeader v-if="!isLogin" />
    <main class="container mx-auto px-4 py-6">
      <router-view />
    </main>
    <ToastContainer />
    <ConfirmDialog />
    <ConnectionIndicator v-if="!isLogin" />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useSystemStore } from '@/stores/system'
import { useWebSocket } from '@/composables/useWebSocket'
import AppHeader from '@/components/layout/AppHeader.vue'
import ToastContainer from '@/components/common/ToastContainer.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import ConnectionIndicator from '@/components/common/ConnectionIndicator.vue'

const route = useRoute()
const isLogin = computed(() => route.path === '/login')
const systemStore = useSystemStore()
const { connect, disconnect } = useWebSocket()

function startSession() {
  connect()
  systemStore.startMonitoring()
}

onMounted(() => {
  if (!isLogin.value) startSession()
})

watch(isLogin, (loginPage) => {
  if (loginPage) {
    disconnect()
    systemStore.stopMonitoring()
  } else {
    startSession()
  }
})

onUnmounted(() => {
  disconnect()
  systemStore.stopMonitoring()
})
</script>
