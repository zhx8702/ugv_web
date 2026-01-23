<template>
  <div class="ai-chat-panel flex flex-col h-full bg-gray-900 rounded-lg overflow-hidden">
    <!-- 头部 -->
    <div class="flex items-center justify-between px-4 py-3 bg-gray-800 border-b border-gray-700">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <span class="text-white font-medium">AI 助手</span>
        <span v-if="isConnected" class="w-2 h-2 rounded-full bg-green-500"></span>
        <span v-else class="w-2 h-2 rounded-full bg-red-500"></span>
      </div>
      <div class="flex items-center gap-2">
        <!-- TTS 模式切换 -->
        <div class="relative">
          <button
            @click="showTTSMenu = !showTTSMenu"
            class="p-2 rounded-lg transition-colors flex items-center gap-1"
            :class="ttsMode !== 'never' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-400'"
            title="语音播报模式"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
            </svg>
            <span class="text-xs">{{ ttsModeLabel }}</span>
          </button>
          <!-- TTS 下拉菜单 -->
          <div
            v-if="showTTSMenu"
            class="absolute right-0 mt-1 w-36 bg-gray-800 rounded-lg shadow-lg border border-gray-700 z-10"
          >
            <button
              v-for="mode in ttsModes"
              :key="mode.value"
              @click="setTTSMode(mode.value)"
              class="w-full px-3 py-2 text-left text-sm hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg flex items-center gap-2"
              :class="ttsMode === mode.value ? 'text-purple-400' : 'text-gray-300'"
            >
              <span v-if="ttsMode === mode.value">✓</span>
              <span v-else class="w-3"></span>
              {{ mode.label }}
            </button>
          </div>
        </div>
        <button
          @click="clearChat"
          class="p-2 rounded-lg bg-gray-700 text-gray-400 hover:bg-gray-600 transition-colors"
          title="清空对话"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="flex"
        :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <div
          class="max-w-[80%] rounded-lg px-4 py-2"
          :class="msg.role === 'user'
            ? 'bg-purple-600 text-white'
            : 'bg-gray-700 text-gray-100'"
        >
          <!-- 消息内容 -->
          <div class="whitespace-pre-wrap">{{ msg.content }}</div>

          <!-- 执行的命令 -->
          <div v-if="msg.commands && msg.commands.length > 0" class="mt-2 pt-2 border-t border-gray-600">
            <div class="text-xs text-gray-400 mb-1">执行命令:</div>
            <div
              v-for="(cmd, cmdIndex) in msg.commands"
              :key="cmdIndex"
              class="text-xs bg-gray-800 rounded px-2 py-1 font-mono"
            >
              {{ JSON.stringify(cmd) }}
            </div>
          </div>

          <!-- 时间戳 -->
          <div class="text-xs mt-1 opacity-60">
            {{ formatTime(msg.timestamp) }}
          </div>
        </div>
      </div>

      <!-- 加载指示器 -->
      <div v-if="isLoading" class="flex justify-start">
        <div class="bg-gray-700 rounded-lg px-4 py-2">
          <div class="flex items-center gap-2">
            <div class="flex space-x-1">
              <div class="w-2 h-2 bg-purple-500 rounded-full animate-bounce"></div>
              <div class="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
              <div class="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            </div>
            <span class="text-gray-400 text-sm">AI 正在思考...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷命令 -->
    <div class="px-4 py-2 border-t border-gray-700">
      <div class="flex gap-2 overflow-x-auto pb-2">
        <button
          v-for="cmd in quickCommands"
          :key="cmd.text"
          @click="sendQuickCommand(cmd.text)"
          class="flex-shrink-0 px-3 py-1 text-sm bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-full transition-colors"
        >
          {{ cmd.label }}
        </button>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="p-4 border-t border-gray-700">
      <div class="flex gap-2">
        <input
          v-model="inputMessage"
          @keydown.enter="sendMessage"
          type="text"
          placeholder="输入指令，如：向前走两步..."
          class="flex-1 bg-gray-800 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          :disabled="isLoading"
        />
        <button
          @click="sendMessage"
          :disabled="isLoading || !inputMessage.trim()"
          class="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
        <button
          @click="emergencyStop"
          class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          title="紧急停止"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
          </svg>
        </button>
      </div>
    </div>

    <!-- 音频播放器（隐藏） -->
    <audio ref="audioPlayer" class="hidden"></audio>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useSocketStore } from '@/stores/socket'

const socketStore = useSocketStore()

// 状态
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const ttsMode = ref('auto')  // auto / always / never
const showTTSMenu = ref(false)
const isConnected = ref(false)
const messagesContainer = ref(null)
const audioPlayer = ref(null)

// TTS 模式选项
const ttsModes = [
  { value: 'auto', label: '智能播报' },
  { value: 'always', label: '总是播报' },
  { value: 'never', label: '关闭播报' }
]

// TTS 模式标签
const ttsModeLabel = computed(() => {
  const mode = ttsModes.find(m => m.value === ttsMode.value)
  return mode ? mode.label.slice(0, 2) : ''
})

// 快捷命令
const quickCommands = [
  { label: '前进', text: '向前走一步' },
  { label: '后退', text: '向后退一步' },
  { label: '左转', text: '向左转30度' },
  { label: '右转', text: '向右转30度' },
  { label: '停止', text: '停下来' },
  { label: '拍照', text: '拍一张照片' },
  { label: '看左边', text: '把摄像头转向左边' },
  { label: '看右边', text: '把摄像头转向右边' },
]

// 发送消息
const sendMessage = async () => {
  const text = inputMessage.value.trim()
  if (!text || isLoading.value) return

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: text,
    timestamp: new Date()
  })

  inputMessage.value = ''
  isLoading.value = true
  scrollToBottom()

  try {
    // 通过 WebSocket 发送
    socketStore.emit('ai_chat', {
      message: text,
      tts_mode: ttsMode.value  // auto / always / never
    })
  } catch (error) {
    console.error('发送消息失败:', error)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，发送消息时出现错误。',
      timestamp: new Date()
    })
    isLoading.value = false
  }
}

// 发送快捷命令
const sendQuickCommand = (text) => {
  inputMessage.value = text
  sendMessage()
}

// 紧急停止
const emergencyStop = () => {
  socketStore.emit('ai_stop', {})
  messages.value.push({
    role: 'assistant',
    content: '已发送紧急停止命令！',
    timestamp: new Date()
  })
}

// 清空对话
const clearChat = () => {
  messages.value = []
}

// 设置 TTS 模式
const setTTSMode = (mode) => {
  ttsMode.value = mode
  showTTSMenu.value = false
}

// 播放语音
const playAudio = (base64Audio, format = 'mp3') => {
  if (!audioPlayer.value || !base64Audio) return

  const audio = audioPlayer.value
  audio.src = `data:audio/${format};base64,${base64Audio}`
  audio.play().catch(err => {
    console.error('播放语音失败:', err)
  })
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 格式化时间
const formatTime = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 处理 AI 响应
const handleAIResponse = (data) => {
  isLoading.value = false

  if (data.type === 'error') {
    messages.value.push({
      role: 'assistant',
      content: `错误: ${data.error}`,
      timestamp: new Date()
    })
    return
  }

  // 添加 AI 回复
  messages.value.push({
    role: 'assistant',
    content: data.content,
    commands: data.commands,
    isCommandOnly: data.is_command_only,
    timestamp: new Date()
  })

  // 播放语音（服务端已根据 tts_mode 决定是否返回 TTS）
  if (data.tts) {
    playAudio(data.tts.audio_base64, data.tts.format)
  }

  scrollToBottom()
}

// 处理命令执行反馈
const handleCommandExecuted = (data) => {
  console.log('命令已执行:', data)
}

// 生命周期
onMounted(() => {
  // 监听 AI 响应
  socketStore.on('ai_response', handleAIResponse)
  socketStore.on('command_executed', handleCommandExecuted)

  // 监听连接状态
  isConnected.value = socketStore.connected

  // 添加欢迎消息
  messages.value.push({
    role: 'assistant',
    content: '你好！我是 UGV 机器人助手。你可以用自然语言告诉我你想让机器人做什么，比如"向前走两步"或"拍一张照片"。',
    timestamp: new Date()
  })
})

onUnmounted(() => {
  socketStore.off('ai_response', handleAIResponse)
  socketStore.off('command_executed', handleCommandExecuted)
})
</script>

<style scoped>
.ai-chat-panel {
  min-height: 400px;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #4b5563;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #6b7280;
}
</style>
