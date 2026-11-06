import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: 'Login', public: true }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/DashboardRouter.vue'),
    meta: { title: 'Dashboard' }
  },
  {
    path: '/desktop',
    name: 'DesktopDashboard',
    component: () => import('@/views/dashboard/DesktopDashboard.vue'),
    meta: { title: 'Dashboard', platform: 'desktop' }
  },
  {
    path: '/mobile',
    name: 'MobileDashboard',
    component: () => import('@/views/dashboard/MobileDashboard.vue'),
    meta: { title: 'Dashboard', platform: 'mobile' }
  },
  {
    path: '/voice',
    name: 'Voice',
    component: () => import('@/views/Voice.vue'),
    meta: { title: 'Voice Control' }
  },
  {
    path: '/photos',
    name: 'Photos',
    component: () => import('@/views/PhotoGallery.vue'),
    meta: { title: 'Photo Gallery' }
  },
  {
    path: '/videos',
    name: 'Videos',
    component: () => import('@/views/VideoLibrary.vue'),
    meta: { title: 'Video Library' }
  },
  {
    path: '/slam',
    name: 'Slam',
    component: () => import('@/views/Slam.vue'),
    meta: { title: 'SLAM Mapping' }
  },
  {
    path: '/tracking',
    name: 'Tracking',
    component: () => import('@/views/Tracking.vue'),
    meta: { title: 'Vision Tracking' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: 'Settings' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  document.title = `${to.meta.title} - UGV Rover` || 'UGV Rover Control'
  if (to.meta.public) {
    next()
    return
  }
  try {
    const { getAuthStatus } = await import('@/services/api')
    const status = await getAuthStatus()
    if (status.enabled && !status.authenticated) {
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
  } catch (e) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }
  next()
})

export default router
