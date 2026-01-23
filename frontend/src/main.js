import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './style.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

app.mount('#app')

// 初始化应用状态
import { useSettingsStore } from './stores/settings'
import { useControlStore } from './stores/control'

const settingsStore = useSettingsStore()
const controlStore = useControlStore()

// 加载配置并初始化控制状态
settingsStore.fetchConfig().then(() => {
  controlStore.initFromSettings()
})
