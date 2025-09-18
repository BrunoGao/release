import { defineStore } from 'pinia'
import type { 
  HealthMetrics, 
  VitalSigns, 
  HealthTrend,
  DepartmentStats,
  ExerciseStats,
  SleepAnalysis,
  MentalHealthData
} from '@/types/health'

interface HealthState {
  // 总体健康指标
  overallMetrics: HealthMetrics
  
  // 实时生命体征
  realtimeVitalSigns: VitalSigns
  
  // 健康趋势数据
  healthTrends: Record<string, HealthTrend[]>
  
  // 部门统计
  departmentStatistics: DepartmentStats[]
  
  // 运动健康统计
  exerciseStatistics: ExerciseStats
  
  // 睡眠分析数据
  sleepAnalysisData: SleepAnalysis
  
  // 心理健康指标
  mentalHealthMetrics: MentalHealthData
  
  // 数据更新状态
  lastUpdateTime: number
  isLoading: boolean
  
  // 缓存设置
  cacheTimeout: number
}

export const useHealthStore = defineStore('health', {
  state: (): HealthState => ({
    overallMetrics: {
      totalScore: 85,
      scoreTrend: 'up',
      riskLevel: 'low',
      lastAssessment: new Date(),
      keyIndicators: {
        cardiovascular: 88,
        respiratory: 92,
        metabolic: 80,
        mental: 78,
        physical: 85
      },
      improvementAreas: ['睡眠质量', '运动量'],
      achievements: ['心率稳定', '血氧正常']
    },
    
    realtimeVitalSigns: {
      heartRate: {
        current: 72,
        trend: 'stable',
        range: { min: 60, max: 100 },
        timestamp: new Date(),
        quality: 'excellent'
      },
      bloodOxygen: {
        current: 98,
        trend: 'stable',
        range: { min: 95, max: 100 },
        timestamp: new Date(),
        quality: 'excellent'
      },
      bloodPressure: {
        systolic: 120,
        diastolic: 80,
        trend: 'stable',
        timestamp: new Date(),
        quality: 'good'
      },
      temperature: {
        current: 36.5,
        trend: 'stable',
        range: { min: 36.0, max: 37.5 },
        timestamp: new Date(),
        quality: 'excellent'
      }
    },
    
    healthTrends: {},
    departmentStatistics: [],
    exerciseStatistics: {
      dailySteps: 8500,
      weeklyDistance: 45.2,
      caloriesBurned: 2100,
      activeMinutes: 180,
      trends: {
        steps: 'up',
        distance: 'stable',
        calories: 'up'
      },
      goals: {
        dailySteps: 10000,
        weeklyDistance: 50,
        dailyCalories: 2500
      }
    },
    
    sleepAnalysisData: {
      lastNightScore: 82,
      averageDuration: 7.5,
      sleepStages: {
        deep: 22,
        light: 58,
        rem: 20
      },
      sleepEfficiency: 88,
      trends: {
        duration: 'stable',
        quality: 'up',
        efficiency: 'up'
      },
      recommendations: ['保持规律作息', '睡前减少屏幕时间']
    },
    
    mentalHealthMetrics: {
      stressLevels: {
        current: 35,
        average: 40,
        trend: 'down'
      },
      moodTrends: {
        happiness: 75,
        anxiety: 25,
        energy: 80,
        focus: 70
      },
      suggestions: [
        '建议进行10分钟冥想',
        '适当增加户外活动',
        '保持社交互动'
      ]
    },
    
    lastUpdateTime: Date.now(),
    isLoading: false,
    cacheTimeout: 5 * 60 * 1000 // 5分钟缓存
  }),

  getters: {
    // 获取特定时间范围的趋势数据
    getTrendData: (state) => (timeRange: string) => {
      return state.healthTrends[timeRange] || []
    },
    
    // 健康评分等级
    healthScoreLevel: (state) => {
      const score = state.overallMetrics.totalScore
      if (score >= 90) return { level: 'excellent', color: '#00ff9d', text: '优秀' }
      if (score >= 80) return { level: 'good', color: '#66bb6a', text: '良好' }
      if (score >= 70) return { level: 'fair', color: '#ffa726', text: '一般' }
      return { level: 'poor', color: '#ff6b6b', text: '较差' }
    },
    
    // 生命体征状态汇总
    vitalSignsStatus: (state) => {
      const signs = state.realtimeVitalSigns
      const normalCount = Object.values(signs).filter(sign => 
        sign.quality === 'excellent' || sign.quality === 'good'
      ).length
      const totalCount = Object.keys(signs).length
      
      return {
        normal: normalCount,
        total: totalCount,
        percentage: (normalCount / totalCount) * 100,
        status: normalCount === totalCount ? 'all_normal' : 
                normalCount >= totalCount * 0.8 ? 'mostly_normal' : 'attention_needed'
      }
    },
    
    // 运动目标完成度
    exerciseGoalProgress: (state) => {
      const stats = state.exerciseStatistics
      return {
        steps: (stats.dailySteps / stats.goals.dailySteps) * 100,
        distance: (stats.weeklyDistance / stats.goals.weeklyDistance) * 100,
        calories: (stats.caloriesBurned / stats.goals.dailyCalories) * 100
      }
    },
    
    // 需要关注的健康指标
    concerningMetrics: (state) => {
      const concerns = []
      
      // 检查生命体征
      Object.entries(state.realtimeVitalSigns).forEach(([key, sign]) => {
        if (sign.quality === 'poor' || sign.trend === 'down') {
          concerns.push({
            type: 'vital_sign',
            metric: key,
            severity: sign.quality === 'poor' ? 'high' : 'medium',
            message: `${key} 需要关注`
          })
        }
      })
      
      // 检查压力水平
      if (state.mentalHealthMetrics.stressLevels.current > 70) {
        concerns.push({
          type: 'mental_health',
          metric: 'stress',
          severity: 'high',
          message: '压力水平过高'
        })
      }
      
      // 检查睡眠质量
      if (state.sleepAnalysisData.lastNightScore < 60) {
        concerns.push({
          type: 'sleep',
          metric: 'quality',
          severity: 'medium',
          message: '睡眠质量需要改善'
        })
      }
      
      return concerns
    }
  },

  actions: {
    // 获取总体健康指标
    async fetchOverallMetrics() {
      if (this.isLoading) return
      
      this.isLoading = true
      try {
        const response = await fetch('/api/health/metrics/overall')
        const data = await response.json()
        
        this.overallMetrics = {
          ...data,
          lastAssessment: new Date(data.lastAssessment)
        }
        
        this.lastUpdateTime = Date.now()
      } catch (error) {
        console.error('Failed to fetch overall metrics:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },
    
    // 获取实时生命体征
    async fetchVitalSigns() {
      try {
        const response = await fetch('/api/health/vital-signs/realtime')
        const data = await response.json()
        
        this.realtimeVitalSigns = {
          heartRate: { ...data.heartRate, timestamp: new Date(data.heartRate.timestamp) },
          bloodOxygen: { ...data.bloodOxygen, timestamp: new Date(data.bloodOxygen.timestamp) },
          bloodPressure: { ...data.bloodPressure, timestamp: new Date(data.bloodPressure.timestamp) },
          temperature: { ...data.temperature, timestamp: new Date(data.temperature.timestamp) }
        }
      } catch (error) {
        console.error('Failed to fetch vital signs:', error)
        throw error
      }
    },
    
    // 获取健康趋势数据
    async fetchTrendData(timeRange: string) {
      if (this.healthTrends[timeRange] && 
          Date.now() - this.lastUpdateTime < this.cacheTimeout) {
        return this.healthTrends[timeRange]
      }
      
      try {
        const response = await fetch(`/api/health/trends?range=${timeRange}`)
        const data = await response.json()
        
        this.healthTrends[timeRange] = data.map((item: any) => ({
          ...item,
          timestamp: new Date(item.timestamp)
        }))
        
        return this.healthTrends[timeRange]
      } catch (error) {
        console.error('Failed to fetch trend data:', error)
        throw error
      }
    },
    
    // 获取部门统计数据
    async fetchDepartmentStats() {
      try {
        const response = await fetch('/api/health/department/statistics')
        const data = await response.json()
        
        this.departmentStatistics = data
      } catch (error) {
        console.error('Failed to fetch department stats:', error)
        throw error
      }
    },
    
    // 获取运动健康统计
    async fetchExerciseStats() {
      try {
        const response = await fetch('/api/health/exercise/statistics')
        const data = await response.json()
        
        this.exerciseStatistics = data
      } catch (error) {
        console.error('Failed to fetch exercise stats:', error)
        throw error
      }
    },
    
    // 获取睡眠分析数据
    async fetchSleepAnalysis() {
      try {
        const response = await fetch('/api/health/sleep/analysis')
        const data = await response.json()
        
        this.sleepAnalysisData = data
      } catch (error) {
        console.error('Failed to fetch sleep analysis:', error)
        throw error
      }
    },
    
    // 获取心理健康指标
    async fetchMentalHealthMetrics() {
      try {
        const response = await fetch('/api/health/mental/metrics')
        const data = await response.json()
        
        this.mentalHealthMetrics = data
      } catch (error) {
        console.error('Failed to fetch mental health metrics:', error)
        throw error
      }
    },
    
    // 同步所有健康数据
    async syncData() {
      await Promise.all([
        this.fetchOverallMetrics(),
        this.fetchVitalSigns(),
        this.fetchExerciseStats(),
        this.fetchSleepAnalysis(),
        this.fetchMentalHealthMetrics()
      ])
    },
    
    // 更新健康目标
    async updateHealthGoals(goals: any) {
      try {
        const response = await fetch('/api/health/goals', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(goals)
        })
        
        if (response.ok) {
          // 更新本地状态
          this.exerciseStatistics.goals = { ...this.exerciseStatistics.goals, ...goals }
        }
      } catch (error) {
        console.error('Failed to update health goals:', error)
        throw error
      }
    },
    
    // 生成健康报告
    async generateHealthReport(options: any = {}) {
      try {
        const response = await fetch('/api/health/report/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(options)
        })
        
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `health-report-${new Date().toISOString().split('T')[0]}.pdf`
        a.click()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error('Failed to generate health report:', error)
        throw error
      }
    },
    
    // 清理过期缓存
    clearExpiredCache() {
      const now = Date.now()
      if (now - this.lastUpdateTime > this.cacheTimeout) {
        this.healthTrends = {}
      }
    },
    
    // 重置状态
    resetState() {
      this.$reset()
    }
  }
})