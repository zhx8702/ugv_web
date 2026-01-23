<template>
  <div
    v-if="!connected"
    class="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50"
  >
    <div class="bg-danger text-white px-6 py-3 rounded-lg shadow-xl flex items-center gap-3">
      <div class="animate-pulse">
        <div class="w-3 h-3 bg-white rounded-full"></div>
      </div>
      <span class="font-medium">Connection Lost - Trying to reconnect...</span>
    </div>
  </div>
</template>

<script setup>
import { useWebSocket } from '@/composables/useWebSocket'

const { connected } = useWebSocket()
</script>
