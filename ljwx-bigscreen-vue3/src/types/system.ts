// 系统类型定义

export type Theme = 'light' | 'dark' | 'auto'

export interface LoadingState {
  id: string
  text: string
  progress?: number
  startTime: number
}

export interface PerformanceMetrics {
  pageLoadTime: number
  apiResponseTimes: Record<string, number>
  memoryUsage: number
  renderTime: number
  errorCount: number
}

export interface SystemHealth {
  score: number
  status: 'excellent' | 'good' | 'warning' | 'error'
}

export interface UserPreferences {
  autoRefresh: boolean
  refreshInterval: number
  showAnimations: boolean
  enableSounds: boolean
  language: string
}

export interface RealtimeStatus {
  wsConnected: boolean
  lastUpdate: Date | null
  updateCount: number
}

// 组件相关类型
export interface ComponentSize {
  width: number
  height: number
}

export interface ChartConfig {
  type: string
  title: string
  dataSource: string
  refreshInterval: number
  options: Record<string, any>
}

// API 相关类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  timestamp: string
}

export interface PaginationParams {
  page: number
  pageSize: number
  total?: number
}

// 健康数据相关类型
export interface HealthData {
  id: string
  userId: string
  timestamp: string
  heartRate?: number
  bloodPressure?: {
    systolic: number
    diastolic: number
  }
  bloodOxygen?: number
  temperature?: number
  steps?: number
  calories?: number
  sleep?: {
    duration: number
    quality: 'excellent' | 'good' | 'fair' | 'poor'
  }
  stress?: number
  location?: {
    latitude: number
    longitude: number
  }
}

export interface HealthScore {
  overall: number
  cardiovascular: number
  respiratory: number
  activity: number
  sleep: number
  mental: number
  trend: 'up' | 'down' | 'stable'
}

// 设备相关类型
export interface DeviceInfo {
  id: string
  name: string
  type: 'watch' | 'band' | 'sensor'
  model: string
  version: string
  batteryLevel: number
  status: 'online' | 'offline' | 'charging' | 'low_battery'
  lastSeen: string
  userId?: string
  location?: {
    latitude: number
    longitude: number
  }
}

// 消息相关类型
export interface MessageInfo {
  id: string
  type: 'info' | 'warning' | 'error' | 'success'
  title: string
  content: string
  timestamp: string
  read: boolean
  priority: 'low' | 'medium' | 'high' | 'urgent'
  source: string
  userId?: string
}

// 告警相关类型
export interface AlertInfo {
  id: string
  type: 'health' | 'device' | 'system'
  level: 'info' | 'warning' | 'critical' | 'emergency'
  title: string
  description: string
  timestamp: string
  status: 'active' | 'acknowledged' | 'resolved'
  userId?: string
  deviceId?: string
  rules: string[]
  actions: AlertAction[]
}

export interface AlertAction {
  type: 'notification' | 'email' | 'sms' | 'webhook'
  target: string
  executed: boolean
  executedAt?: string
}

// 用户相关类型
export interface UserInfo {
  id: string
  username: string
  nickname: string
  avatar?: string
  email?: string
  phone?: string
  department?: string
  position?: string
  status: 'active' | 'inactive' | 'suspended'
  lastLogin?: string
  createdAt: string
  profile?: {
    age?: number
    gender?: 'male' | 'female' | 'other'
    height?: number
    weight?: number
    bloodType?: string
    allergies?: string[]
    medications?: string[]
    emergencyContact?: {
      name: string
      phone: string
      relationship: string
    }
  }
}

// 图表相关类型
export interface ChartData {
  categories: string[]
  series: ChartSeries[]
  options?: Record<string, any>
}

export interface ChartSeries {
  name: string
  type: 'line' | 'bar' | 'pie' | 'scatter' | 'gauge' | 'radar'
  data: any[]
  color?: string
  stack?: string
}

// 3D 特效相关类型
export interface Effect3DConfig {
  type: 'particles' | 'waves' | 'dna' | 'network' | 'pulse'
  intensity: number
  speed: number
  color: string
  enabled: boolean
}

// 路由相关类型
export interface RouteMetaInfo {
  title: string
  icon?: string
  transition?: string
  keepAlive?: boolean
  parent?: string
  permission?: string[]
}

// WebSocket 消息类型
export interface WSMessage {
  type: 'health_data' | 'device_status' | 'alert' | 'system_message'
  payload: any
  timestamp: string
  id: string
}

// 错误类型
export interface ErrorInfo {
  code: string
  message: string
  details?: any
  timestamp: string
  source: 'api' | 'component' | 'system'
  level: 'info' | 'warning' | 'error' | 'critical'
}