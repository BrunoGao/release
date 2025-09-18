import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useSystemStore } from '@/stores/system'

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'MainBigScreen',
    component: () => import('@/views/MainDashboard.vue'),
    meta: {
      title: '智能健康数据分析平台',
      transition: 'fade'
    }
  },
  {
    path: '/bigscreen',
    name: 'BigScreen',
    component: () => import('@/views/MainDashboard.vue'),
    meta: {
      title: '智能健康数据分析平台',
      transition: 'fade'
    }
  },
  {
    path: '/test',
    name: 'TestDashboard',
    component: () => import('@/views/TestDashboard.vue'),
    meta: {
      title: '系统测试',
      transition: 'fade'
    }
  },
  {
    path: '/dashboard',
    component: () => import('@/layouts/DashboardLayout.vue'),
    children: [
      {
        path: 'main',
        name: 'MainDashboard',
        component: () => import('@/views/MainDashboard.vue'),
        meta: {
          title: '主大屏',
          icon: 'Monitor',
          transition: 'scale',
          keepAlive: true
        }
      },
      {
        path: 'personal',
        name: 'PersonalDashboard', 
        component: () => import('@/views/PersonalDashboard.vue'),
        meta: {
          title: '个人健康',
          icon: 'User',
          transition: 'slide-left',
          keepAlive: true
        }
      }
    ]
  },
  {
    path: '/views',
    component: () => import('@/layouts/ViewLayout.vue'),
    children: [
      {
        path: 'device',
        name: 'DeviceView',
        component: () => import('@/views/secondary/DeviceView.vue'),
        meta: {
          title: '设备监控',
          icon: 'Monitor',
          parent: 'MainDashboard'
        }
      },
      {
        path: 'message',
        name: 'MessageView',
        component: () => import('@/views/secondary/MessageView.vue'),
        meta: {
          title: '消息管理',
          icon: 'ChatDotRound',
          parent: 'MainDashboard'
        }
      },
      {
        path: 'alert',
        name: 'AlertView',
        component: () => import('@/views/secondary/AlertView.vue'),
        meta: {
          title: '告警管理',
          icon: 'Warning',
          parent: 'MainDashboard'
        }
      },
      {
        path: 'health',
        name: 'HealthView',
        component: () => import('@/views/secondary/HealthView.vue'),
        meta: {
          title: '健康数据',
          icon: 'TrendCharts',
          parent: 'PersonalDashboard'
        }
      },
      {
        path: 'health/profile',
        name: 'HealthProfileView',
        component: () => import('@/views/health/ProfileView.vue'),
        meta: {
          title: '健康画像',
          icon: 'Avatar',
          parent: 'PersonalDashboard'
        }
      },
      {
        path: 'health/recommendation',
        name: 'HealthRecommendationView',
        component: () => import('@/views/health/RecommendationView.vue'),
        meta: {
          title: '健康建议',
          icon: 'Opportunity',
          parent: 'PersonalDashboard'
        }
      },
      {
        path: 'health/prediction',
        name: 'HealthPredictionView',
        component: () => import('@/views/health/PredictionView.vue'),
        meta: {
          title: '健康预测',
          icon: 'TrendCharts',
          parent: 'PersonalDashboard'
        }
      },
      {
        path: 'health/score',
        name: 'HealthScoreView',
        component: () => import('@/views/health/ScoreView.vue'),
        meta: {
          title: '健康评分',
          icon: 'Medal',
          parent: 'PersonalDashboard'
        }
      },
      {
        path: 'track',
        name: 'TrackView',
        component: () => import('@/views/secondary/TrackView.vue'),
        meta: {
          title: '轨迹追踪',
          icon: 'LocationInformation',
          parent: 'PersonalDashboard'
        }
      },
      {
        path: 'user',
        name: 'UserView',
        component: () => import('@/views/secondary/UserView.vue'),
        meta: {
          title: '用户管理',
          icon: 'UserFilled',
          parent: 'MainDashboard'
        }
      }
    ]
  },
  {
    path: '/fullscreen/:viewName',
    name: 'FullscreenView',
    component: () => import('@/layouts/FullscreenLayout.vue'),
    meta: {
      title: '全屏模式',
      transition: 'fade'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFound.vue'),
    meta: {
      title: '页面未找到'
    }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - LJWX BigScreen`
  }
  
  // 页面访问统计
  console.log(`📍 路由跳转: ${from.path} → ${to.path}`)
  
  next()
})

router.afterEach((to, from) => {
  // 确保加载状态被清除
  setTimeout(() => {
    const systemStore = useSystemStore()
    systemStore.setLoading(false)
  }, 100)
})

// 路由错误处理
router.onError((error) => {
  console.error('路由错误:', error)
  // 这里可以集成错误上报
})

export default router