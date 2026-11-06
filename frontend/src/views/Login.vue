<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-title">UGV ROVER</div>
      <div class="login-sub">// AUTH REQUIRED</div>
      <form class="login-form" @submit.prevent="submit">
        <label class="field">
          <span>USERNAME</span>
          <input v-model="username" autocomplete="username" />
        </label>
        <label class="field">
          <span>PASSWORD</span>
          <input v-model="password" type="password" autocomplete="current-password" />
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <button class="btn" type="submit" :disabled="loading">
          {{ loading ? 'SIGNING IN...' : 'LOGIN' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { login } from '@/services/api'

const router = useRouter()
const route = useRoute()
const username = ref('ws')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await login(username.value, password.value)
    const redirect = route.query.redirect || '/'
    router.replace(typeof redirect === 'string' ? redirect : '/')
  } catch (e) {
    error.value = e?.response?.data?.error || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  @apply min-h-[70vh] flex items-center justify-center;
}
.login-card {
  @apply w-full max-w-sm p-8;
  background: rgba(3, 7, 18, 0.9);
  border: 1px solid rgba(0, 240, 255, 0.2);
  clip-path: polygon(16px 0, 100% 0, 100% calc(100% - 16px), calc(100% - 16px) 100%, 0 100%, 0 16px);
}
.login-title {
  @apply text-2xl font-orbitron font-bold text-primary tracking-widest;
}
.login-sub {
  @apply mt-1 mb-6 text-xs font-mono text-dark-text-tertiary;
}
.field {
  @apply flex flex-col gap-1 mb-4 text-[10px] font-mono text-dark-text-tertiary tracking-wider;
}
.field input {
  @apply px-3 py-2 text-sm font-mono text-dark-text-primary bg-dark-bg-tertiary/60 border border-dark-border;
  @apply focus:border-primary focus:outline-none;
}
.error {
  @apply mb-3 text-xs font-mono text-danger;
}
.btn {
  @apply w-full py-2 font-orbitron text-sm text-dark-bg-primary bg-primary;
}
.btn:disabled {
  @apply opacity-50;
}
</style>
