<template>
  <div class="alert-view">
    <!-- 3D背景效果 -->
    <TechBackground 
      :intensity="1.0"
      :particle-count="120"
      :enable-grid="true"
      :enable-pulse="true"
      :enable-data-flow="true"
    />
    
    <!-- 页面头部 -->
    <div class="view-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <ArrowLeftIcon />
          <span>返回主大屏</span>
        </button>
        <div class="page-title">
          <h1>预警管理中心</h1>
          <p class="page-subtitle">健康预警监控与应急响应系统</p>
        </div>
      </div>
      
      <div class="header-right">
        <div class="alert-stats">
          <div class="stat-card critical">
            <div class="stat-icon">
              <ExclamationTriangleIcon />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ criticalAlerts }}</div>
              <div class="stat-label">紧急预警</div>
            </div>
          </div>
          <div class="stat-card active">
            <div class="stat-icon">
              <BellIcon />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ activeAlerts }}</div>
              <div class="stat-label">活跃预警</div>
            </div>
          </div>
          <div class="stat-card resolved">
            <div class="stat-icon">
              <CheckCircleIcon />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ resolvedToday }}</div>
              <div class="stat-label">今日解决</div>
            </div>
          </div>
        </div>
        
        <div class="header-actions">
          <button class="emergency-btn" @click="triggerEmergencyMode">
            <SirenIcon />
            紧急模式
          </button>
          <button class="config-btn" @click="showAlertConfig">
            <CogIcon />
            预警配置
          </button>
        </div>
      </div>
    </div>
    
    <!-- 预警管理主体 -->
    <div class="alert-content">
      <!-- 预警实时监控 -->
      <div class="monitoring-section">
        <div class="section-header">
          <h3>实时监控</h3>
          <div class="monitoring-controls">
            <button 
              class="control-btn"
              :class="{ active: autoRefresh }"
              @click="toggleAutoRefresh"
            >
              <RefreshIcon :class="{ spinning: autoRefresh }" />
              {{ autoRefresh ? '停止刷新' : '自动刷新' }}
            </button>
            <select v-model="selectedSeverity" class="severity-filter">
              <option value="all">全部级别</option>
              <option value="critical">紧急</option>
              <option value="high">重要</option>
              <option value="medium">一般</option>
              <option value="low">提醒</option>
            </select>
          </div>
        </div>
        
        <div class="alert-grid">
          <div 
            v-for="alert in filteredAlerts" 
            :key="alert.id"
            class="alert-card"
            :class="[`severity-${alert.severity}`, { 'alert-new': alert.isNew }]"
            @click="selectAlert(alert)"
          >
            <div class="alert-header">
              <div class="severity-indicator" :class="alert.severity">
                <component :is="getSeverityIcon(alert.severity)" />
              </div>
              <div class="alert-time">{{ formatAlertTime(alert.timestamp) }}</div>
              <div class="alert-status" :class="alert.status">
                {{ getStatusText(alert.status) }}
              </div>
            </div>
            
            <div class="alert-content-card">
              <h4 class="alert-title">{{ alert.title }}</h4>
              <p class="alert-message">{{ alert.message }}</p>
              
              <div class="alert-meta">
                <div class="meta-item">
                  <UserIcon class="meta-icon" />
                  <span>{{ alert.affectedUser || '系统级' }}</span>
                </div>
                <div class="meta-item">
                  <ClockIcon class="meta-icon" />
                  <span>{{ getAlertDuration(alert.timestamp) }}</span>
                </div>
                <div class="meta-item" v-if="alert.deviceId">
                  <CpuChipIcon class="meta-icon" />
                  <span>{{ alert.deviceName }}</span>
                </div>
              </div>
            </div>
            
            <div class="alert-actions">
              <button 
                class="alert-action-btn primary"
                @click.stop="acknowledgeAlert(alert.id)"
                v-if="alert.status === 'active'"
              >
                <CheckIcon />
                确认
              </button>
              <button 
                class="alert-action-btn warning"
                @click.stop="escalateAlert(alert.id)"
                v-if="alert.severity !== 'critical'"
              >
                <ArrowUpIcon />
                升级
              </button>
              <button 
                class="alert-action-btn danger"
                @click.stop="resolveAlert(alert.id)"
              >
                <XMarkIcon />
                解决
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 预警趋势分析 -->
      <div class="analysis-section">
        <div class="section-header">
          <h3>预警趋势分析</h3>
          <div class="time-range-selector">
            <button 
              v-for="range in timeRanges"
              :key="range.value"
              class="time-btn"
              :class="{ active: selectedTimeRange === range.value }"
              @click="selectTimeRange(range.value)"
            >
              {{ range.label }}
            </button>
          </div>
        </div>
        
        <div class="analysis-grid">
          <div class="analysis-item trend-chart">
            <h4>预警趋势</h4>
            <div class="chart-container">
              <AlertTrendChart 
                :data="alertTrendData"
                :time-range="selectedTimeRange"
              />
            </div>
          </div>
          
          <div class="analysis-item severity-distribution">
            <h4>严重程度分布</h4>
            <div class="chart-container">
              <SeverityPieChart :data="severityDistribution" />
            </div>
          </div>
          
          <div class="analysis-item response-time">
            <h4>响应时间统计</h4>
            <div class="response-metrics">
              <div class="metric-item">
                <div class="metric-label">平均响应时间</div>
                <div class="metric-value">{{ avgResponseTime }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">最快响应</div>
                <div class="metric-value">{{ fastestResponse }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">解决率</div>
                <div class="metric-value">{{ resolutionRate }}%</div>
              </div>
            </div>
          </div>
          
          <div class="analysis-item alert-sources">
            <h4>预警来源</h4>
            <div class="source-list">
              <div 
                v-for="source in alertSources"
                :key="source.name"
                class="source-item"
              >
                <div class="source-info">
                  <span class="source-name">{{ source.name }}</span>
                  <span class="source-count">{{ source.count }}</span>
                </div>
                <div class="source-bar">
                  <div 
                    class="source-fill"
                    :style="{ width: (source.count / maxSourceCount) * 100 + '%' }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 预警规则管理 -->
      <div class="rules-section">
        <div class="section-header">
          <h3>预警规则</h3>
          <button class="add-rule-btn" @click="showAddRule">
            <PlusIcon />
            添加规则
          </button>
        </div>
        
        <div class="rules-table">
          <div class="table-header">
            <div class="header-cell">规则名称</div>
            <div class="header-cell">触发条件</div>
            <div class="header-cell">严重程度</div>
            <div class="header-cell">状态</div>
            <div class="header-cell">操作</div>
          </div>
          
          <div class="table-body">
            <div 
              v-for="rule in alertRules"
              :key="rule.id"
              class="table-row"
            >
              <div class="table-cell">
                <div class="rule-name">{{ rule.name }}</div>
                <div class="rule-description">{{ rule.description }}</div>
              </div>
              <div class="table-cell">
                <div class="condition-text">{{ rule.condition }}</div>
              </div>
              <div class="table-cell">
                <div class="severity-badge" :class="rule.severity">
                  {{ getSeverityText(rule.severity) }}
                </div>
              </div>
              <div class="table-cell">
                <div class="status-toggle">
                  <input 
                    type="checkbox" 
                    :checked="rule.enabled"
                    @change="toggleRule(rule.id)"
                    class="toggle-switch"
                  />
                </div>
              </div>
              <div class="table-cell">
                <div class="rule-actions">
                  <button 
                    class="rule-action-btn"
                    @click="editRule(rule.id)"
                    title="编辑"
                  >
                    <PencilIcon />
                  </button>
                  <button 
                    class="rule-action-btn"
                    @click="testRule(rule.id)"
                    title="测试"
                  >
                    <PlayIcon />
                  </button>
                  <button 
                    class="rule-action-btn danger"
                    @click="deleteRule(rule.id)"
                    title="删除"
                  >
                    <TrashIcon />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 预警详情模态框 -->
    <Transition name="modal">
      <div v-if="selectedAlert" class="alert-detail-modal" @click="closeAlertDetail">
        <div class="detail-content" @click.stop>
          <div class="detail-header">
            <h3>预警详情</h3>
            <button class="close-detail" @click="closeAlertDetail">
              <XMarkIcon />
            </button>
          </div>
          
          <div class="detail-body">
            <div class="alert-overview">
              <div class="severity-display" :class="selectedAlert.severity">
                <component :is="getSeverityIcon(selectedAlert.severity)" />
                <span>{{ getSeverityText(selectedAlert.severity) }}</span>
              </div>
              <h2>{{ selectedAlert.title }}</h2>
              <p class="alert-description">{{ selectedAlert.message }}</p>
            </div>
            
            <div class="alert-timeline">
              <h4>处理时间线</h4>
              <div class="timeline-list">
                <div 
                  v-for="event in selectedAlert.timeline"
                  :key="event.id"
                  class="timeline-item"
                >
                  <div class="timeline-time">{{ formatTime(event.timestamp) }}</div>
                  <div class="timeline-event">{{ event.description }}</div>
                  <div class="timeline-user">{{ event.user }}</div>
                </div>
              </div>
            </div>
            
            <div class="alert-recommendations">
              <h4>处理建议</h4>
              <ul class="recommendation-list">
                <li v-for="rec in selectedAlert.recommendations" :key="rec">
                  {{ rec }}
                </li>
              </ul>
            </div>
          </div>
          
          <div class="detail-actions">
            <button class="detail-action-btn primary" @click="handleAlert('acknowledge')">
              确认预警
            </button>
            <button class="detail-action-btn warning" @click="handleAlert('escalate')">
              升级处理
            </button>
            <button class="detail-action-btn success" @click="handleAlert('resolve')">
              标记解决
            </button>
            <button class="detail-action-btn" @click="handleAlert('assign')">
              分配处理
            </button>
          </div>
        </div>
      </div>
    </Transition>
    
    <!-- 全局提示 -->
    <GlobalToast ref="toast" />
  </div>
</template>

<script setup lang="ts">
import { 
  ArrowLeftIcon,
  ExclamationTriangleIcon,
  BellIcon,
  CheckCircleIcon,
  RefreshIcon,
  CogIcon,
  CheckIcon,
  ArrowUpIcon,
  XMarkIcon,
  UserIcon,
  ClockIcon,
  CpuChipIcon,
  PlusIcon,
  PencilIcon,
  PlayIcon,
  TrashIcon
} from '@element-plus/icons-vue'
import TechBackground from '@/components/effects/TechBackground.vue'
import AlertTrendChart from '@/components/charts/AlertTrendChart.vue'
import SeverityPieChart from '@/components/charts/SeverityPieChart.vue'
import GlobalToast from '@/components/common/GlobalToast.vue'
import { useAlertStore } from '@/stores/alert'
import { useRouter } from 'vue-router'

// 自定义图标组件
const SirenIcon = {
  name: 'SirenIcon',
  template: `
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2L8 6h8l-4-4zm0 20l4-4H8l4 4zm-6-9h12v2H6v-2zm2-4h8v2H8V9zm8 8H8v2h8v-2z"/>
    </svg>
  `
}

// Store and router
const alertStore = useAlertStore()
const router = useRouter()
const toast = ref<InstanceType<typeof GlobalToast>>()

// 组件状态
const selectedSeverity = ref('all')
const selectedTimeRange = ref('24h')
const autoRefresh = ref(true)
const selectedAlert = ref(null)

// 时间范围选项
const timeRanges = [
  { value: '1h', label: '1小时' },
  { value: '6h', label: '6小时' },
  { value: '24h', label: '24小时' },
  { value: '7d', label: '7天' },
  { value: '30d', label: '30天' }
]

// 模拟预警数据
const alerts = ref([
  {
    id: 'alert_001',
    title: '用户心率异常',
    message: '用户张三心率持续超过100 BPM，当前值：108 BPM',
    severity: 'critical',
    status: 'active',
    timestamp: new Date(Date.now() - 5 * 60000),
    affectedUser: '张三',
    deviceId: 'device_001',
    deviceName: '智能手环-001',
    isNew: true,
    timeline: [
      { id: 1, timestamp: new Date(Date.now() - 5 * 60000), description: '预警触发', user: '系统' },
      { id: 2, timestamp: new Date(Date.now() - 3 * 60000), description: '已通知医护人员', user: '系统' }
    ],
    recommendations: [
      '立即联系用户确认身体状况',
      '建议安排医疗检查',
      '监控后续心率变化'
    ]
  },
  {
    id: 'alert_002',
    title: '设备电量低',
    message: '智能手环-002电量低于10%，可能影响数据采集',
    severity: 'high',
    status: 'acknowledged',
    timestamp: new Date(Date.now() - 15 * 60000),
    affectedUser: '李四',
    deviceId: 'device_002',
    deviceName: '智能手环-002',
    isNew: false,
    timeline: [
      { id: 1, timestamp: new Date(Date.now() - 15 * 60000), description: '电量预警触发', user: '系统' },
      { id: 2, timestamp: new Date(Date.now() - 10 * 60000), description: '预警已确认', user: '管理员' }
    ],
    recommendations: [
      '提醒用户及时充电',
      '检查充电设备状态',
      '考虑备用设备'
    ]
  },
  {
    id: 'alert_003',
    title: '血压读数异常',
    message: '用户王五血压读数异常：收缩压165 mmHg',
    severity: 'high',
    status: 'active',
    timestamp: new Date(Date.now() - 30 * 60000),
    affectedUser: '王五',
    deviceId: 'device_003',
    deviceName: '血压监护仪-003',
    isNew: false,
    timeline: [
      { id: 1, timestamp: new Date(Date.now() - 30 * 60000), description: '血压异常预警', user: '系统' }
    ],
    recommendations: [
      '建议立即复测血压',
      '联系医生进行评估',
      '检查用药情况'
    ]
  },
  {
    id: 'alert_004',
    title: '数据同步失败',
    message: '设备数据同步失败，已连续3次尝试',
    severity: 'medium',
    status: 'resolved',
    timestamp: new Date(Date.now() - 60 * 60000),
    affectedUser: null,
    deviceId: 'device_004',
    deviceName: '智能秤-004',
    isNew: false,
    timeline: [
      { id: 1, timestamp: new Date(Date.now() - 60 * 60000), description: '同步失败预警', user: '系统' },
      { id: 2, timestamp: new Date(Date.now() - 45 * 60000), description: '技术人员介入', user: '技术支持' },
      { id: 3, timestamp: new Date(Date.now() - 30 * 60000), description: '问题已解决', user: '技术支持' }
    ],
    recommendations: [
      '检查网络连接',
      '重启设备',
      '验证同步服务状态'
    ]
  }
])

// 预警规则数据
const alertRules = ref([
  {
    id: 'rule_001',
    name: '心率异常预警',
    description: '心率超出正常范围时触发',
    condition: '心率 > 100 BPM 或 < 60 BPM',
    severity: 'high',
    enabled: true
  },
  {
    id: 'rule_002',
    name: '设备电量低预警',
    description: '设备电量低于阈值时触发',
    condition: '电量 < 20%',
    severity: 'medium',
    enabled: true
  },
  {
    id: 'rule_003',
    name: '血压异常预警',
    description: '血压读数异常时触发',
    condition: '收缩压 > 160 mmHg 或 舒张压 > 100 mmHg',
    severity: 'critical',
    enabled: true
  },
  {
    id: 'rule_004',
    name: '数据同步失败预警',
    description: '设备数据同步连续失败时触发',
    condition: '连续失败 >= 3次',
    severity: 'medium',
    enabled: false
  }
])

// 计算属性
const criticalAlerts = computed(() => alerts.value.filter(a => a.severity === 'critical' && a.status === 'active').length)
const activeAlerts = computed(() => alerts.value.filter(a => a.status === 'active').length)
const resolvedToday = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return alerts.value.filter(a => a.status === 'resolved' && a.timestamp >= today).length
})

const filteredAlerts = computed(() => {
  let filtered = alerts.value
  
  if (selectedSeverity.value !== 'all') {
    filtered = filtered.filter(a => a.severity === selectedSeverity.value)
  }
  
  return filtered.sort((a, b) => {
    // 按严重程度和时间排序
    const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 }
    const severityDiff = severityOrder[b.severity as keyof typeof severityOrder] - severityOrder[a.severity as keyof typeof severityOrder]
    if (severityDiff !== 0) return severityDiff
    
    return b.timestamp.getTime() - a.timestamp.getTime()
  })
})

const alertTrendData = computed(() => {
  // 生成模拟趋势数据
  const hours = selectedTimeRange.value === '1h' ? 1 : 
                selectedTimeRange.value === '6h' ? 6 : 
                selectedTimeRange.value === '24h' ? 24 : 
                selectedTimeRange.value === '7d' ? 168 : 720
  
  return Array.from({ length: Math.min(hours, 50) }, (_, i) => ({
    timestamp: new Date(Date.now() - i * 60 * 60 * 1000),
    count: Math.floor(Math.random() * 10) + 1
  })).reverse()
})

const severityDistribution = computed(() => [
  { name: '紧急', value: alerts.value.filter(a => a.severity === 'critical').length, color: '#ff4757' },
  { name: '重要', value: alerts.value.filter(a => a.severity === 'high').length, color: '#ffa726' },
  { name: '一般', value: alerts.value.filter(a => a.severity === 'medium').length, color: '#42a5f5' },
  { name: '提醒', value: alerts.value.filter(a => a.severity === 'low').length, color: '#66bb6a' }
])

const avgResponseTime = computed(() => '2.3分钟')
const fastestResponse = computed(() => '30秒')
const resolutionRate = computed(() => 87)

const alertSources = computed(() => [
  { name: '心率监控', count: 15 },
  { name: '血压监控', count: 12 },
  { name: '设备状态', count: 8 },
  { name: '数据同步', count: 5 },
  { name: '电量监控', count: 3 }
])

const maxSourceCount = computed(() => Math.max(...alertSources.value.map(s => s.count)))

// 方法
const goBack = () => {
  router.push('/dashboard/main')
}

const getSeverityIcon = (severity: string) => {
  const icons = {
    critical: ExclamationTriangleIcon,
    high: ExclamationTriangleIcon,
    medium: BellIcon,
    low: BellIcon
  }
  return icons[severity as keyof typeof icons] || BellIcon
}

const getSeverityText = (severity: string) => {
  const texts = {
    critical: '紧急',
    high: '重要',
    medium: '一般',
    low: '提醒'
  }
  return texts[severity as keyof typeof texts] || severity
}

const getStatusText = (status: string) => {
  const texts = {
    active: '活跃',
    acknowledged: '已确认',
    resolved: '已解决',
    assigned: '已分配'
  }
  return texts[status as keyof typeof texts] || status
}

const formatAlertTime = (time: Date) => {
  return time.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatTime = (time: Date) => {
  return time.toLocaleString('zh-CN')
}

const getAlertDuration = (startTime: Date) => {
  const now = new Date()
  const diff = now.getTime() - startTime.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时`
  const days = Math.floor(hours / 24)
  return `${days}天`
}

const selectTimeRange = (range: string) => {
  selectedTimeRange.value = range
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const selectAlert = (alert: any) => {
  selectedAlert.value = alert
}

const closeAlertDetail = () => {
  selectedAlert.value = null
}

const acknowledgeAlert = (alertId: string) => {
  const alert = alerts.value.find(a => a.id === alertId)
  if (alert) {
    alert.status = 'acknowledged'
    alert.isNew = false
    toast.value?.success('预警已确认')
  }
}

const escalateAlert = (alertId: string) => {
  const alert = alerts.value.find(a => a.id === alertId)
  if (alert) {
    const severityLevels = ['low', 'medium', 'high', 'critical']
    const currentIndex = severityLevels.indexOf(alert.severity)
    if (currentIndex < severityLevels.length - 1) {
      alert.severity = severityLevels[currentIndex + 1] as any
      toast.value?.warning('预警已升级')
    }
  }
}

const resolveAlert = (alertId: string) => {
  const alert = alerts.value.find(a => a.id === alertId)
  if (alert) {
    alert.status = 'resolved'
    toast.value?.success('预警已解决')
  }
}

const handleAlert = (action: string) => {
  if (!selectedAlert.value) return
  
  switch (action) {
    case 'acknowledge':
      acknowledgeAlert(selectedAlert.value.id)
      break
    case 'escalate':
      escalateAlert(selectedAlert.value.id)
      break
    case 'resolve':
      resolveAlert(selectedAlert.value.id)
      break
    case 'assign':
      toast.value?.info('分配功能开发中')
      break
  }
  
  closeAlertDetail()
}

const triggerEmergencyMode = () => {
  toast.value?.error('紧急模式已激活！')
}

const showAlertConfig = () => {
  toast.value?.info('预警配置功能开发中')
}

const showAddRule = () => {
  toast.value?.info('添加规则功能开发中')
}

const toggleRule = (ruleId: string) => {
  const rule = alertRules.value.find(r => r.id === ruleId)
  if (rule) {
    rule.enabled = !rule.enabled
    toast.value?.success(`规则已${rule.enabled ? '启用' : '禁用'}`)
  }
}

const editRule = (ruleId: string) => {
  toast.value?.info('编辑规则功能开发中')
}

const testRule = (ruleId: string) => {
  toast.value?.info('测试规则功能开发中')
}

const deleteRule = (ruleId: string) => {
  const index = alertRules.value.findIndex(r => r.id === ruleId)
  if (index > -1) {
    alertRules.value.splice(index, 1)
    toast.value?.success('规则已删除')
  }
}

// 自动刷新
let refreshInterval: number
const startAutoRefresh = () => {
  refreshInterval = window.setInterval(() => {
    // 模拟新预警
    if (Math.random() < 0.3) {
      // 30% 概率产生新预警
      toast.value?.warning('检测到新预警')
    }
  }, 10000)
}

const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
}

// 生命周期
onMounted(() => {
  console.log('预警管理页面已加载')
  if (autoRefresh.value) {
    startAutoRefresh()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style lang="scss" scoped>
.alert-view {
  width: 100%;
  height: 100vh;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

// ========== 页面头部 ==========
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-primary);
  backdrop-filter: blur(10px);
  z-index: 10;
  position: relative;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast);
  
  &:hover {
    color: var(--primary-500);
    border-color: var(--primary-500);
    background: rgba(0, 255, 157, 0.1);
  }
}

.page-title {
  h1 {
    font-size: var(--font-2xl);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-xs) 0;
  }
  
  .page-subtitle {
    font-size: var(--font-sm);
    color: var(--text-secondary);
    margin: 0;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.alert-stats {
  display: flex;
  gap: var(--spacing-md);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  
  .stat-icon {
    width: 32px;
    height: 32px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
  }
  
  .stat-info {
    .stat-value {
      font-size: var(--font-lg);
      font-weight: 700;
      font-family: var(--font-tech);
      margin-bottom: var(--spacing-xs);
    }
    
    .stat-label {
      font-size: var(--font-xs);
      color: var(--text-secondary);
    }
  }
  
  &.critical {
    .stat-icon {
      background: rgba(255, 71, 87, 0.2);
      color: #ff4757;
    }
    .stat-value {
      color: #ff4757;
    }
  }
  
  &.active {
    .stat-icon {
      background: rgba(255, 167, 38, 0.2);
      color: #ffa726;
    }
    .stat-value {
      color: #ffa726;
    }
  }
  
  &.resolved {
    .stat-icon {
      background: rgba(102, 187, 106, 0.2);
      color: #66bb6a;
    }
    .stat-value {
      color: #66bb6a;
    }
  }
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
  
  .emergency-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-lg);
    background: linear-gradient(135deg, #ff4757, #ff6b83);
    color: white;
    border: none;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all var(--duration-fast);
    font-weight: 600;
    animation: emergency-pulse 2s ease-in-out infinite;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-lg);
    }
  }
  
  .config-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-lg);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    
    &:hover {
      color: var(--primary-500);
      border-color: var(--primary-500);
      background: rgba(0, 255, 157, 0.1);
    }
  }
}

// ========== 主体内容 ==========
.alert-content {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

// ========== 监控区域 ==========
.monitoring-section,
.analysis-section,
.rules-section {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  backdrop-filter: blur(10px);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  
  h3 {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
}

.monitoring-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  
  .control-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    
    .spinning {
      animation: spin 1s linear infinite;
    }
    
    &:hover {
      color: var(--primary-500);
      border-color: var(--primary-500);
      background: rgba(0, 255, 157, 0.1);
    }
    
    &.active {
      background: var(--primary-500);
      color: white;
      border-color: var(--primary-500);
    }
  }
  
  .severity-filter {
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-primary);
    cursor: pointer;
    
    &:focus {
      outline: none;
      border-color: var(--primary-500);
    }
  }
}

// ========== 预警卡片 ==========
.alert-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: var(--spacing-lg);
}

.alert-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  cursor: pointer;
  transition: all var(--duration-normal);
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  }
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-xl);
    border-color: var(--primary-500);
  }
  
  &.severity-critical {
    &::before { background: #ff4757; }
    .severity-indicator { color: #ff4757; }
  }
  
  &.severity-high {
    &::before { background: #ffa726; }
    .severity-indicator { color: #ffa726; }
  }
  
  &.severity-medium {
    &::before { background: #42a5f5; }
    .severity-indicator { color: #42a5f5; }
  }
  
  &.severity-low {
    &::before { background: #66bb6a; }
    .severity-indicator { color: #66bb6a; }
  }
  
  &.alert-new {
    animation: new-alert-pulse 2s ease-in-out infinite;
  }
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  
  .severity-indicator {
    display: flex;
    align-items: center;
    font-size: 20px;
  }
  
  .alert-time {
    font-size: var(--font-sm);
    color: var(--text-secondary);
    font-family: var(--font-tech);
  }
  
  .alert-status {
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
    font-size: var(--font-xs);
    font-weight: 500;
    
    &.active {
      background: rgba(255, 167, 38, 0.2);
      color: #ffa726;
    }
    
    &.acknowledged {
      background: rgba(66, 165, 245, 0.2);
      color: #42a5f5;
    }
    
    &.resolved {
      background: rgba(102, 187, 106, 0.2);
      color: #66bb6a;
    }
  }
}

.alert-content-card {
  margin-bottom: var(--spacing-md);
  
  .alert-title {
    font-size: var(--font-md);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-sm) 0;
  }
  
  .alert-message {
    font-size: var(--font-sm);
    color: var(--text-secondary);
    line-height: var(--leading-relaxed);
    margin: 0 0 var(--spacing-md) 0;
  }
  
  .alert-meta {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }
  
  .meta-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    font-size: var(--font-xs);
    color: var(--text-tertiary);
    
    .meta-icon {
      width: 12px;
      height: 12px;
    }
  }
}

.alert-actions {
  display: flex;
  gap: var(--spacing-sm);
  
  .alert-action-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm);
    border: 1px solid var(--border-tertiary);
    border-radius: var(--radius-md);
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    font-size: var(--font-sm);
    
    &:hover {
      transform: translateY(-1px);
    }
    
    &.primary:hover {
      color: var(--primary-500);
      border-color: var(--primary-500);
      background: rgba(0, 255, 157, 0.1);
    }
    
    &.warning:hover {
      color: var(--warning);
      border-color: var(--warning);
      background: rgba(255, 167, 38, 0.1);
    }
    
    &.danger:hover {
      color: var(--error);
      border-color: var(--error);
      background: rgba(255, 107, 107, 0.1);
    }
  }
}

// ========== 分析区域 ==========
.time-range-selector {
  display: flex;
  gap: var(--spacing-xs);
  
  .time-btn {
    padding: var(--spacing-xs) var(--spacing-sm);
    border: 1px solid var(--border-tertiary);
    border-radius: var(--radius-sm);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    font-size: var(--font-sm);
    
    &:hover {
      color: var(--text-primary);
    }
    
    &.active {
      background: var(--primary-500);
      color: white;
      border-color: var(--primary-500);
    }
  }
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
}

.analysis-item {
  background: var(--bg-secondary);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  
  h4 {
    font-size: var(--font-md);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
  }
  
  .chart-container {
    height: 200px;
  }
  
  &.trend-chart {
    grid-column: 1 / -1;
  }
  
  &.response-time {
    .response-metrics {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-md);
      
      .metric-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .metric-label {
          font-size: var(--font-sm);
          color: var(--text-secondary);
        }
        
        .metric-value {
          font-size: var(--font-lg);
          font-weight: 600;
          color: var(--text-primary);
          font-family: var(--font-tech);
        }
      }
    }
  }
  
  &.alert-sources {
    .source-list {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-md);
      
      .source-item {
        .source-info {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--spacing-xs);
          
          .source-name {
            font-size: var(--font-sm);
            color: var(--text-primary);
          }
          
          .source-count {
            font-size: var(--font-sm);
            font-weight: 600;
            color: var(--primary-500);
            font-family: var(--font-tech);
          }
        }
        
        .source-bar {
          height: 6px;
          background: var(--bg-tertiary);
          border-radius: var(--radius-full);
          overflow: hidden;
          
          .source-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary-500), var(--tech-500));
            border-radius: var(--radius-full);
            transition: width var(--duration-normal);
          }
        }
      }
    }
  }
}

// ========== 规则表格 ==========
.add-rule-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--primary-500);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast);
  
  &:hover {
    background: var(--primary-600);
    transform: translateY(-1px);
  }
}

.rules-table {
  .table-header {
    display: grid;
    grid-template-columns: 2fr 2fr 1fr 1fr 1fr;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    background: var(--bg-secondary);
    border-radius: var(--radius-md) var(--radius-md) 0 0;
    border-bottom: 1px solid var(--border-tertiary);
    
    .header-cell {
      font-size: var(--font-sm);
      font-weight: 600;
      color: var(--text-secondary);
    }
  }
  
  .table-body {
    .table-row {
      display: grid;
      grid-template-columns: 2fr 2fr 1fr 1fr 1fr;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      border-bottom: 1px solid var(--border-tertiary);
      transition: all var(--duration-fast);
      
      &:hover {
        background: var(--bg-secondary);
      }
      
      &:last-child {
        border-bottom: none;
        border-radius: 0 0 var(--radius-md) var(--radius-md);
      }
    }
  }
  
  .table-cell {
    display: flex;
    align-items: center;
    
    .rule-name {
      font-size: var(--font-sm);
      font-weight: 500;
      color: var(--text-primary);
      margin-bottom: var(--spacing-xs);
    }
    
    .rule-description {
      font-size: var(--font-xs);
      color: var(--text-secondary);
    }
    
    .condition-text {
      font-size: var(--font-sm);
      color: var(--text-secondary);
      font-family: var(--font-mono);
    }
    
    .severity-badge {
      padding: var(--spacing-xs) var(--spacing-sm);
      border-radius: var(--radius-sm);
      font-size: var(--font-xs);
      font-weight: 500;
      
      &.critical {
        background: rgba(255, 71, 87, 0.2);
        color: #ff4757;
      }
      
      &.high {
        background: rgba(255, 167, 38, 0.2);
        color: #ffa726;
      }
      
      &.medium {
        background: rgba(66, 165, 245, 0.2);
        color: #42a5f5;
      }
      
      &.low {
        background: rgba(102, 187, 106, 0.2);
        color: #66bb6a;
      }
    }
    
    .toggle-switch {
      width: 40px;
      height: 20px;
      appearance: none;
      background: var(--bg-tertiary);
      border-radius: var(--radius-full);
      position: relative;
      cursor: pointer;
      transition: all var(--duration-fast);
      
      &:checked {
        background: var(--primary-500);
      }
      
      &::before {
        content: '';
        position: absolute;
        top: 2px;
        left: 2px;
        width: 16px;
        height: 16px;
        background: white;
        border-radius: 50%;
        transition: all var(--duration-fast);
      }
      
      &:checked::before {
        transform: translateX(20px);
      }
    }
    
    .rule-actions {
      display: flex;
      gap: var(--spacing-xs);
      
      .rule-action-btn {
        width: 28px;
        height: 28px;
        border: none;
        background: var(--bg-tertiary);
        color: var(--text-secondary);
        border-radius: var(--radius-sm);
        cursor: pointer;
        transition: all var(--duration-fast);
        display: flex;
        align-items: center;
        justify-content: center;
        
        &:hover {
          background: var(--primary-500);
          color: white;
        }
        
        &.danger:hover {
          background: var(--error);
        }
      }
    }
  }
}

// ========== 详情模态框 ==========
.alert-detail-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  backdrop-filter: blur(4px);
}

.detail-content {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-xl);
  width: 800px;
  max-width: 90vw;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: var(--shadow-2xl);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-secondary);
  
  h3 {
    margin: 0;
    color: var(--text-primary);
    font-size: var(--font-lg);
    font-weight: 600;
  }
  
  .close-detail {
    width: 32px;
    height: 32px;
    border: none;
    background: var(--bg-secondary);
    color: var(--text-secondary);
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: all var(--duration-fast);
    display: flex;
    align-items: center;
    justify-content: center;
    
    &:hover {
      background: var(--error);
      color: white;
    }
  }
}

.detail-body {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  
  .alert-overview {
    margin-bottom: var(--spacing-xl);
    
    .severity-display {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      margin-bottom: var(--spacing-md);
      font-size: var(--font-md);
      font-weight: 600;
      
      &.critical { color: #ff4757; }
      &.high { color: #ffa726; }
      &.medium { color: #42a5f5; }
      &.low { color: #66bb6a; }
    }
    
    h2 {
      font-size: var(--font-xl);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 var(--spacing-md) 0;
    }
    
    .alert-description {
      font-size: var(--font-md);
      color: var(--text-secondary);
      line-height: var(--leading-relaxed);
      margin: 0;
    }
  }
  
  .alert-timeline,
  .alert-recommendations {
    margin-bottom: var(--spacing-lg);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 var(--spacing-md) 0;
    }
  }
  
  .timeline-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    
    .timeline-item {
      display: grid;
      grid-template-columns: 150px 1fr 100px;
      gap: var(--spacing-md);
      padding: var(--spacing-sm);
      background: var(--bg-secondary);
      border-radius: var(--radius-md);
      
      .timeline-time {
        font-size: var(--font-sm);
        color: var(--text-secondary);
        font-family: var(--font-tech);
      }
      
      .timeline-event {
        font-size: var(--font-sm);
        color: var(--text-primary);
      }
      
      .timeline-user {
        font-size: var(--font-sm);
        color: var(--text-tertiary);
        text-align: right;
      }
    }
  }
  
  .recommendation-list {
    list-style: none;
    padding: 0;
    margin: 0;
    
    li {
      padding: var(--spacing-sm);
      margin-bottom: var(--spacing-sm);
      background: var(--bg-secondary);
      border-radius: var(--radius-md);
      border-left: 3px solid var(--primary-500);
      font-size: var(--font-sm);
      color: var(--text-primary);
      
      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}

.detail-actions {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-secondary);
  
  .detail-action-btn {
    flex: 1;
    padding: var(--spacing-md);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    font-size: var(--font-sm);
    font-weight: 500;
    
    &:hover {
      transform: translateY(-1px);
    }
    
    &.primary {
      background: var(--primary-500);
      color: white;
      border-color: var(--primary-500);
      
      &:hover {
        background: var(--primary-600);
      }
    }
    
    &.warning {
      background: var(--warning);
      color: white;
      border-color: var(--warning);
      
      &:hover {
        background: #ff8f00;
      }
    }
    
    &.success {
      background: var(--success);
      color: white;
      border-color: var(--success);
      
      &:hover {
        background: #4caf50;
      }
    }
  }
}

// ========== 过渡动画 ==========
.modal-enter-active,
.modal-leave-active {
  transition: all var(--duration-normal);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

// ========== 动画 ==========
@keyframes emergency-pulse {
  0% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(255, 71, 87, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0); }
}

@keyframes new-alert-pulse {
  0% { border-color: var(--border-secondary); }
  50% { border-color: var(--warning); }
  100% { border-color: var(--border-secondary); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// ========== 响应式设计 ==========
@media (max-width: 1024px) {
  .header-right {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .alert-stats {
    flex-wrap: wrap;
  }
  
  .alert-grid {
    grid-template-columns: 1fr;
  }
  
  .analysis-grid {
    grid-template-columns: 1fr;
  }
  
  .rules-table .table-header,
  .rules-table .table-row {
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }
}

@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .monitoring-controls {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
  
  .detail-content {
    width: 95vw;
    height: 90vh;
  }
  
  .detail-actions {
    flex-direction: column;
  }
}

@media (prefers-reduced-motion: reduce) {
  .alert-card,
  .emergency-btn,
  .new-alert-pulse,
  .emergency-pulse {
    animation: none;
    transition: none;
  }
  
  .spinning {
    animation: none;
  }
}
</style>