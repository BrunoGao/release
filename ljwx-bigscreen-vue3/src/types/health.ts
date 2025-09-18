// 健康数据相关类型定义

export interface HealthMetrics {
  totalScore: number
  scoreTrend: 'up' | 'down' | 'stable'
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  lastAssessment: Date
  keyIndicators: {
    cardiovascular: number  // 心血管健康
    respiratory: number     // 呼吸系统
    metabolic: number       // 代谢健康
    mental: number          // 心理健康
    physical: number        // 身体健康
  }
  improvementAreas: string[]
  achievements: string[]
}

export interface VitalSignReading {
  current: number
  trend: 'up' | 'down' | 'stable'
  range: {
    min: number
    max: number
  }
  timestamp: Date
  quality: 'excellent' | 'good' | 'fair' | 'poor'
  unit?: string
}

export interface BloodPressureReading {
  systolic: number
  diastolic: number
  trend: 'up' | 'down' | 'stable'
  timestamp: Date
  quality: 'excellent' | 'good' | 'fair' | 'poor'
}

export interface VitalSigns {
  heartRate: VitalSignReading
  bloodOxygen: VitalSignReading
  bloodPressure: BloodPressureReading
  temperature: VitalSignReading
}

export interface HealthTrend {
  timestamp: Date
  value: number
  metric: string
  category: string
  unit?: string
}

export interface DepartmentStats {
  departmentId: string
  departmentName: string
  totalEmployees: number
  healthScore: number
  riskDistribution: {
    low: number
    medium: number
    high: number
    critical: number
  }
  topIssues: string[]
  improvement: number
}

export interface ExerciseStats {
  dailySteps: number
  weeklyDistance: number  // km
  caloriesBurned: number
  activeMinutes: number
  trends: {
    steps: 'up' | 'down' | 'stable'
    distance: 'up' | 'down' | 'stable'
    calories: 'up' | 'down' | 'stable'
  }
  goals: {
    dailySteps: number
    weeklyDistance: number
    dailyCalories: number
  }
}

export interface SleepAnalysis {
  lastNightScore: number
  averageDuration: number  // hours
  sleepStages: {
    deep: number     // percentage
    light: number    // percentage
    rem: number      // percentage
  }
  sleepEfficiency: number  // percentage
  trends: {
    duration: 'up' | 'down' | 'stable'
    quality: 'up' | 'down' | 'stable'
    efficiency: 'up' | 'down' | 'stable'
  }
  recommendations: string[]
}

export interface MentalHealthData {
  stressLevels: {
    current: number
    average: number
    trend: 'up' | 'down' | 'stable'
  }
  moodTrends: {
    happiness: number
    anxiety: number
    energy: number
    focus: number
  }
  suggestions: string[]
}

// 设备相关类型
export interface DeviceInfo {
  deviceId: string
  deviceType: 'wearable' | 'sensor' | 'monitor'
  brand: string
  model: string
  batteryLevel: number
  connectionStatus: 'connected' | 'disconnected' | 'syncing'
  lastSyncTime: Date
  location?: {
    latitude: number
    longitude: number
    address?: string
  }
}

export interface DeviceData {
  deviceId: string
  timestamp: Date
  metrics: Record<string, number>
  quality: 'excellent' | 'good' | 'fair' | 'poor'
}

// 预警相关类型
export interface HealthAlert {
  id: string
  userId: string
  type: 'vital_sign' | 'exercise' | 'sleep' | 'mental_health' | 'medication'
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  message: string
  timestamp: Date
  isRead: boolean
  isResolved: boolean
  actions?: AlertAction[]
}

export interface AlertAction {
  id: string
  label: string
  type: 'acknowledge' | 'escalate' | 'ignore' | 'custom'
  handler?: string
}

// 用户健康档案
export interface HealthProfile {
  userId: string
  basicInfo: {
    age: number
    gender: 'male' | 'female' | 'other'
    height: number  // cm
    weight: number  // kg
    bloodType?: string
  }
  medicalHistory: {
    conditions: string[]
    medications: string[]
    allergies: string[]
    surgeries: string[]
  }
  lifestyle: {
    smokingStatus: 'never' | 'former' | 'current'
    drinkingFrequency: 'never' | 'occasional' | 'regular' | 'daily'
    exerciseFrequency: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active'
    dietType: 'regular' | 'vegetarian' | 'vegan' | 'keto' | 'other'
  }
  preferences: {
    units: 'metric' | 'imperial'
    language: string
    notifications: {
      email: boolean
      push: boolean
      sms: boolean
    }
  }
}

// 健康目标
export interface HealthGoal {
  id: string
  userId: string
  type: 'weight_loss' | 'fitness' | 'sleep' | 'stress' | 'nutrition' | 'custom'
  title: string
  description: string
  targetValue: number
  currentValue: number
  unit: string
  deadline: Date
  progress: number  // percentage
  status: 'active' | 'completed' | 'paused' | 'cancelled'
  milestones: GoalMilestone[]
}

export interface GoalMilestone {
  id: string
  title: string
  targetValue: number
  deadline: Date
  isCompleted: boolean
  completedAt?: Date
}

// 健康建议
export interface HealthRecommendation {
  id: string
  userId: string
  type: 'exercise' | 'nutrition' | 'sleep' | 'stress' | 'medical'
  priority: 'low' | 'medium' | 'high'
  title: string
  description: string
  actions: string[]
  estimatedImpact: 'low' | 'medium' | 'high'
  difficulty: 'easy' | 'moderate' | 'challenging'
  timeframe: string
  isImplemented: boolean
  feedback?: {
    rating: number
    comment: string
  }
}

// 数据质量指标
export interface DataQuality {
  completeness: number     // 数据完整性 (0-100)
  accuracy: number         // 数据准确性 (0-100)
  timeliness: number      // 数据及时性 (0-100)
  consistency: number     // 数据一致性 (0-100)
  overall: number         // 总体质量评分 (0-100)
  lastUpdated: Date
}

// 聚合统计
export interface AggregatedStats {
  period: 'hour' | 'day' | 'week' | 'month' | 'year'
  startDate: Date
  endDate: Date
  metrics: {
    [key: string]: {
      min: number
      max: number
      avg: number
      median: number
      stdDev: number
      count: number
    }
  }
}

// API响应类型
export interface HealthApiResponse<T> {
  success: boolean
  data: T
  message?: string
  errors?: string[]
  metadata?: {
    total: number
    page: number
    limit: number
    hasMore: boolean
  }
}

// 导出类型
export interface HealthDataExport {
  format: 'pdf' | 'excel' | 'csv' | 'json'
  dateRange: {
    start: Date
    end: Date
  }
  includeMetrics: string[]
  includeTrends: boolean
  includeRecommendations: boolean
  language: string
}