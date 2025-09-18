import { defineStore } from 'pinia'
import type { HealthAlert, AlertAction } from '@/types/health'

interface AlertState {
  alerts: HealthAlert[]
  isLoading: boolean
  lastUpdateTime: number
  emergencyMode: boolean
  filters: {
    severity: 'all' | 'low' | 'medium' | 'high' | 'critical'
    type: 'all' | 'vital_sign' | 'exercise' | 'sleep' | 'mental_health' | 'medication'
    status: 'all' | 'unread' | 'read' | 'resolved'
  }
  notifications: {
    sound: boolean
    popup: boolean
    email: boolean
  }
}

export const useAlertStore = defineStore('alert', {
  state: (): AlertState => ({
    alerts: [
      {
        id: 'alert_001',
        userId: 'user_123',
        type: 'vital_sign',
        severity: 'high',
        title: '心率异常',
        message: '检测到心率持续偏高（98 BPM），建议立即检查',
        timestamp: new Date(Date.now() - 300000), // 5分钟前
        isRead: false,
        isResolved: false,
        actions: [
          { id: 'ack', label: '确认', type: 'acknowledge' },
          { id: 'escalate', label: '升级', type: 'escalate' },
          { id: 'ignore', label: '忽略', type: 'ignore' }
        ]
      },
      {
        id: 'alert_002',
        userId: 'user_124',
        type: 'sleep',
        severity: 'medium',
        title: '睡眠质量下降',
        message: '连续3天睡眠评分低于60分，建议调整作息',
        timestamp: new Date(Date.now() - 1800000), // 30分钟前
        isRead: true,
        isResolved: false,
        actions: [
          { id: 'ack', label: '确认', type: 'acknowledge' },
          { id: 'schedule', label: '安排咨询', type: 'custom' }
        ]
      },
      {
        id: 'alert_003',
        userId: 'user_125',
        type: 'mental_health',
        severity: 'critical',
        title: '压力水平过高',
        message: '压力指数达到85%，建议立即采取减压措施',
        timestamp: new Date(Date.now() - 600000), // 10分钟前
        isRead: false,
        isResolved: false,
        actions: [
          { id: 'emergency', label: '紧急处理', type: 'escalate' },
          { id: 'contact', label: '联系医生', type: 'custom' }
        ]
      },
      {
        id: 'alert_004',
        userId: 'user_126',
        type: 'exercise',
        severity: 'low',
        title: '运动量不足',
        message: '本周运动量仅为目标的30%，建议增加活动',
        timestamp: new Date(Date.now() - 3600000), // 1小时前
        isRead: true,
        isResolved: true,
        actions: [
          { id: 'plan', label: '制定计划', type: 'custom' }
        ]
      }
    ],
    isLoading: false,
    lastUpdateTime: Date.now(),
    emergencyMode: false,
    filters: {
      severity: 'all',
      type: 'all',
      status: 'all'
    },
    notifications: {
      sound: true,
      popup: true,
      email: false
    }
  }),

  getters: {
    // 获取过滤后的预警
    getFilteredAlerts: (state) => (severityFilter?: string) => {
      let filtered = [...state.alerts]
      
      const severity = severityFilter || state.filters.severity
      if (severity !== 'all') {
        filtered = filtered.filter(alert => alert.severity === severity)
      }
      
      if (state.filters.type !== 'all') {
        filtered = filtered.filter(alert => alert.type === state.filters.type)
      }
      
      if (state.filters.status !== 'all') {
        switch (state.filters.status) {
          case 'unread':
            filtered = filtered.filter(alert => !alert.isRead)
            break
          case 'read':
            filtered = filtered.filter(alert => alert.isRead && !alert.isResolved)
            break
          case 'resolved':
            filtered = filtered.filter(alert => alert.isResolved)
            break
        }
      }
      
      return filtered.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    },
    
    // 未读预警数量
    unreadCount: (state) => state.alerts.filter(alert => !alert.isRead).length,
    
    // 严重预警数量
    criticalCount: (state) => state.alerts.filter(alert => 
      alert.severity === 'critical' && !alert.isResolved
    ).length,
    
    // 高优先级预警数量
    highPriorityCount: (state) => state.alerts.filter(alert => 
      (alert.severity === 'high' || alert.severity === 'critical') && !alert.isResolved
    ).length,
    
    // 按类型分组的预警统计
    alertsByType: (state) => {
      const grouped = state.alerts.reduce((acc, alert) => {
        if (!acc[alert.type]) {
          acc[alert.type] = {
            total: 0,
            unread: 0,
            resolved: 0,
            critical: 0
          }
        }
        
        acc[alert.type].total++
        if (!alert.isRead) acc[alert.type].unread++
        if (alert.isResolved) acc[alert.type].resolved++
        if (alert.severity === 'critical') acc[alert.type].critical++
        
        return acc
      }, {} as Record<string, any>)
      
      return grouped
    },
    
    // 按严重程度分组的预警统计
    alertsBySeverity: (state) => {
      const grouped = state.alerts.reduce((acc, alert) => {
        if (!acc[alert.severity]) {
          acc[alert.severity] = 0
        }
        acc[alert.severity]++
        return acc
      }, {} as Record<string, number>)
      
      return grouped
    },
    
    // 最近的预警
    recentAlerts: (state) => {
      return state.alerts
        .filter(alert => !alert.isResolved)
        .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
        .slice(0, 5)
    }
  },

  actions: {
    // 获取预警列表
    async fetchAlerts() {
      this.isLoading = true
      try {
        const response = await fetch('/api/alerts')
        const data = await response.json()
        
        this.alerts = data.map((alert: any) => ({
          ...alert,
          timestamp: new Date(alert.timestamp)
        }))
        
        this.lastUpdateTime = Date.now()
      } catch (error) {
        console.error('Failed to fetch alerts:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },
    
    // 处理预警
    async handleAlert(alertId: string, action: string) {
      const alert = this.alerts.find(a => a.id === alertId)
      if (!alert) return
      
      try {
        const response = await fetch(`/api/alerts/${alertId}/action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action })
        })
        
        if (response.ok) {
          switch (action) {
            case 'acknowledge':
            case 'ack':
              alert.isRead = true
              break
            case 'resolve':
              alert.isResolved = true
              alert.isRead = true
              break
            case 'ignore':
              alert.isRead = true
              break
            case 'escalate':
              alert.severity = 'critical'
              this.notifyEscalation(alert)
              break
          }
        }
      } catch (error) {
        console.error('Failed to handle alert:', error)
        throw error
      }
    },
    
    // 创建新预警
    async createAlert(alertData: Partial<HealthAlert>) {
      try {
        const response = await fetch('/api/alerts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(alertData)
        })
        
        if (response.ok) {
          const newAlert = await response.json()
          this.alerts.unshift({
            ...newAlert,
            timestamp: new Date(newAlert.timestamp)
          })
          
          // 触发通知
          this.triggerNotification(newAlert)
        }
      } catch (error) {
        console.error('Failed to create alert:', error)
        throw error
      }
    },
    
    // 批量处理预警
    async batchHandleAlerts(alertIds: string[], action: string) {
      try {
        const response = await fetch('/api/alerts/batch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ alertIds, action })
        })
        
        if (response.ok) {
          alertIds.forEach(id => {
            const alert = this.alerts.find(a => a.id === id)
            if (alert) {
              switch (action) {
                case 'mark_read':
                  alert.isRead = true
                  break
                case 'resolve':
                  alert.isResolved = true
                  alert.isRead = true
                  break
              }
            }
          })
        }
      } catch (error) {
        console.error('Failed to batch handle alerts:', error)
        throw error
      }
    },
    
    // 设置过滤器
    setFilter(filterType: keyof AlertState['filters'], value: string) {
      this.filters[filterType] = value as any
    },
    
    // 清除过滤器
    clearFilters() {
      this.filters = {
        severity: 'all',
        type: 'all',
        status: 'all'
      }
    },
    
    // 触发紧急模式
    async triggerEmergencyMode() {
      this.emergencyMode = true
      
      try {
        const response = await fetch('/api/alerts/emergency', {
          method: 'POST'
        })
        
        if (response.ok) {
          // 播放紧急警报声
          this.playEmergencySound()
          
          // 发送紧急通知
          this.sendEmergencyNotifications()
        }
      } catch (error) {
        console.error('Failed to trigger emergency mode:', error)
        throw error
      }
    },
    
    // 退出紧急模式
    async exitEmergencyMode() {
      this.emergencyMode = false
      
      try {
        const response = await fetch('/api/alerts/emergency', {
          method: 'DELETE'
        })
        
        return response.ok
      } catch (error) {
        console.error('Failed to exit emergency mode:', error)
        throw error
      }
    },
    
    // 更新通知设置
    updateNotificationSettings(settings: Partial<AlertState['notifications']>) {
      this.notifications = { ...this.notifications, ...settings }
      
      // 保存到本地存储
      localStorage.setItem('alertNotificationSettings', JSON.stringify(this.notifications))
    },
    
    // 触发通知
    triggerNotification(alert: HealthAlert) {
      if (this.notifications.sound) {
        this.playAlertSound(alert.severity)
      }
      
      if (this.notifications.popup) {
        this.showPopupNotification(alert)
      }
      
      if (this.notifications.email) {
        this.sendEmailNotification(alert)
      }
    },
    
    // 播放预警声音
    playAlertSound(severity: string) {
      const audio = new Audio()
      switch (severity) {
        case 'critical':
          audio.src = '/sounds/critical-alert.mp3'
          break
        case 'high':
          audio.src = '/sounds/high-alert.mp3'
          break
        case 'medium':
          audio.src = '/sounds/medium-alert.mp3'
          break
        default:
          audio.src = '/sounds/low-alert.mp3'
      }
      audio.play().catch(console.error)
    },
    
    // 播放紧急警报声
    playEmergencySound() {
      const audio = new Audio('/sounds/emergency-alarm.mp3')
      audio.loop = true
      audio.play().catch(console.error)
      
      // 10秒后停止
      setTimeout(() => {
        audio.pause()
        audio.currentTime = 0
      }, 10000)
    },
    
    // 显示弹窗通知
    showPopupNotification(alert: HealthAlert) {
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(alert.title, {
          body: alert.message,
          icon: '/icons/alert.png',
          tag: alert.id
        })
      }
    },
    
    // 发送邮件通知
    async sendEmailNotification(alert: HealthAlert) {
      try {
        await fetch('/api/notifications/email', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            alertId: alert.id,
            userId: alert.userId,
            severity: alert.severity
          })
        })
      } catch (error) {
        console.error('Failed to send email notification:', error)
      }
    },
    
    // 发送紧急通知
    async sendEmergencyNotifications() {
      try {
        await fetch('/api/notifications/emergency', {
          method: 'POST'
        })
      } catch (error) {
        console.error('Failed to send emergency notifications:', error)
      }
    },
    
    // 升级预警通知
    notifyEscalation(alert: HealthAlert) {
      console.log(`Alert ${alert.id} has been escalated to critical level`)
      this.triggerNotification(alert)
    },
    
    // 获取预警统计
    async getAlertStatistics(timeRange: string) {
      try {
        const response = await fetch(`/api/alerts/statistics?range=${timeRange}`)
        const data = await response.json()
        return data
      } catch (error) {
        console.error('Failed to fetch alert statistics:', error)
        throw error
      }
    },
    
    // 导出预警报告
    async exportAlertReport(options: any = {}) {
      try {
        const response = await fetch('/api/alerts/report/export', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(options)
        })
        
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `alert-report-${new Date().toISOString().split('T')[0]}.pdf`
        a.click()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error('Failed to export alert report:', error)
        throw error
      }
    },
    
    // 自动刷新预警
    startAutoRefresh(interval = 30000) {
      setInterval(() => {
        this.fetchAlerts()
      }, interval)
    }
  }
})