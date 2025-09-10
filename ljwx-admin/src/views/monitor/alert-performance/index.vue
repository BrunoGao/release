<template>
  <div class="alert-performance-dashboard">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>
          <el-icon><TrendCharts /></el-icon>
          告警系统性能监控
        </h2>
        <p>实时监控告警规则引擎、缓存系统和消息发布器的性能状态</p>
      </div>
      <div class="header-right">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button @click="exportData">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
      </div>
    </div>
    
    <!-- 系统状态概览 -->
    <div class="status-overview">
      <el-alert 
        :title="systemStatus.title"
        :type="systemStatus.type"
        :description="systemStatus.description"
        show-icon
        :closable="false"
        class="status-alert"
      />
    </div>
    
    <!-- 核心指标卡片 -->
    <el-row :gutter="20" class="metrics-cards">
      <el-col :span="6" v-for="metric in coreMetrics" :key="metric.key">
        <el-card class="metric-card" :class="metric.status">
          <div class="metric-content">
            <div class="metric-icon" :style="{ background: metric.gradient }">
              <component :is="metric.icon" />
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ metric.value }}</div>
              <div class="metric-label">{{ metric.label }}</div>
              <div class="metric-trend" :class="metric.trendClass">
                <el-icon><TrendCharts /></el-icon>
                {{ metric.trend }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-section">
      <!-- 缓存性能图表 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>缓存命中率</span>
              <el-tag :type="cacheStatus.type" size="small">{{ cacheStatus.text }}</el-tag>
            </div>
          </template>
          <div ref="cacheChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      
      <!-- 告警生成趋势 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>告警生成趋势</span>
              <el-dropdown @command="handlePeriodChange">
                <el-button size="small">
                  {{ currentPeriod }}
                  <el-icon><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="today">今天</el-dropdown-item>
                    <el-dropdown-item command="week">本周</el-dropdown-item>
                    <el-dropdown-item command="month">本月</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
          <div ref="alertTrendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="charts-section">
      <!-- 系统负载图表 -->
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>系统负载</span>
          </template>
          <div ref="systemLoadChartRef" class="chart-container small"></div>
        </el-card>
      </el-col>
      
      <!-- 线程池状态 -->
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>线程池状态</span>
          </template>
          <div ref="threadPoolChartRef" class="chart-container small"></div>
        </el-card>
      </el-col>
      
      <!-- 消息分发统计 -->
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>消息分发</span>
          </template>
          <div ref="messageStatsChartRef" class="chart-container small"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 详细数据表格 -->
    <el-row :gutter="20" class="tables-section">
      <!-- 规则性能排行 -->
      <el-col :span="12">
        <el-card class="table-card">
          <template #header>
            <div class="card-header">
              <span>规则执行性能排行</span>
              <el-button size="small" @click="refreshRulePerformance">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <el-table :data="rulePerformanceData" size="small" max-height="400">
            <el-table-column prop="ruleName" label="规则名称" show-overflow-tooltip />
            <el-table-column prop="ruleType" label="类型" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.ruleType === 'COMPOSITE' ? 'success' : ''" size="small">
                  {{ row.ruleType === 'COMPOSITE' ? '复合' : '单征' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="avgExecutionTime" label="平均耗时(ms)" width="100" align="center">
              <template #default="{ row }">
                <span :class="getPerformanceClass(row.avgExecutionTime)">
                  {{ Math.round(row.avgExecutionTime * 100) / 100 }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="totalExecutions" label="执行次数" width="80" align="center" />
            <el-table-column prop="successRate" label="成功率" width="80" align="center">
              <template #default="{ row }">
                <span :class="getSuccessRateClass(row.successRate)">
                  {{ Math.round(row.successRate * 100) / 100 }}%
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <!-- 系统资源使用 -->
      <el-col :span="12">
        <el-card class="table-card">
          <template #header>
            <div class="card-header">
              <span>系统资源使用</span>
              <el-button size="small" @click="refreshSystemLoad">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="resource-stats">
            <div class="resource-item">
              <div class="resource-label">内存使用</div>
              <el-progress 
                :percentage="systemLoad.memory?.usagePercent || 0"
                :status="systemLoad.memory?.usagePercent > 80 ? 'exception' : 'success'"
                :show-text="false"
              />
              <div class="resource-value">
                {{ formatBytes(systemLoad.memory?.usedMemory || 0) }} / 
                {{ formatBytes(systemLoad.memory?.totalMemory || 0) }}
              </div>
            </div>
            
            <div class="resource-item" v-if="systemLoad.cpu">
              <div class="resource-label">CPU使用</div>
              <el-progress 
                :percentage="systemLoad.cpu?.processCpuLoad || 0"
                :status="systemLoad.cpu?.processCpuLoad > 80 ? 'exception' : 'success'"
                :show-text="false"
              />
              <div class="resource-value">{{ systemLoad.cpu?.processCpuLoad || 0 }}%</div>
            </div>
            
            <div class="resource-item">
              <div class="resource-label">可用处理器</div>
              <div class="resource-big-value">{{ systemLoad.availableProcessors || 0 }}</div>
            </div>
            
            <div class="resource-item">
              <div class="resource-label">线程池队列</div>
              <div class="resource-stats-grid">
                <div class="stat-item">
                  <span class="stat-label">规则引擎</span>
                  <span class="stat-value">{{ threadPoolStatus.ruleEngine?.queueSize || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">缓存管理</span>
                  <span class="stat-value">{{ threadPoolStatus.cacheManager?.activeThreads || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 操作控制面板 -->
    <el-card class="control-panel">
      <template #header>
        <span>系统控制</span>
      </template>
      <div class="control-buttons">
        <el-button @click="clearAllCache" type="warning" :loading="operationLoading">
          <el-icon><Delete /></el-icon>
          清空所有缓存
        </el-button>
        <el-button @click="showClearCustomerCache" type="info">
          <el-icon><Delete /></el-icon>
          清空客户缓存
        </el-button>
        <el-button @click="healthCheck" type="success">
          <el-icon><CircleCheck /></el-icon>
          系统健康检查
        </el-button>
      </div>
    </el-card>
    
    <!-- 清空客户缓存对话框 -->
    <el-dialog v-model="clearCacheDialogVisible" title="清空客户缓存" width="400px">
      <el-form>
        <el-form-item label="客户ID" required>
          <el-input-number 
            v-model="targetCustomerId" 
            placeholder="请输入客户ID"
            :min="1"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="clearCacheDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="clearCustomerCache" :loading="operationLoading">
          确定清空
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import {
  TrendCharts, Refresh, Download, ArrowDown, Delete, CircleCheck
} from '@element-plus/icons-vue'
import {
  getPerformanceStats,
  getCacheHealth,
  clearAllCache as clearAllCacheAPI,
  clearCustomerCache as clearCustomerCacheAPI,
  getSystemLoad,
  getThreadPoolStatus,
  getRulePerformanceRanking,
  getAlertStats
} from '@/service/api/monitor/alert-performance'

// 响应式数据
const loading = ref(false)
const operationLoading = ref(false)
const clearCacheDialogVisible = ref(false)
const targetCustomerId = ref<number>()
const currentPeriod = ref('今天')

// 图表引用
const cacheChartRef = ref()
const alertTrendChartRef = ref()
const systemLoadChartRef = ref()
const threadPoolChartRef = ref()
const messageStatsChartRef = ref()

// 图表实例
let cacheChart: echarts.ECharts | null = null
let alertTrendChart: echarts.ECharts | null = null
let systemLoadChart: echarts.ECharts | null = null
let threadPoolChart: echarts.ECharts | null = null
let messageStatsChart: echarts.ECharts | null = null

// 定时器
let refreshTimer: number | null = null

// 数据
const performanceData = reactive({
  engine: {},
  cache: {},
  message: {},
  overview: {}
})

const systemLoad = reactive({
  memory: null,
  cpu: null,
  availableProcessors: 0
})

const threadPoolStatus = reactive({
  ruleEngine: {},
  cacheManager: {}
})

const rulePerformanceData = ref([])

// 计算属性
const systemStatus = computed(() => {
  const overview = performanceData.overview as any
  if (overview.systemHealthy) {
    return {
      title: '系统运行正常',
      type: 'success' as const,
      description: '告警系统各模块运行正常，性能指标良好。'
    }
  } else {
    return {
      title: '系统存在告警',
      type: 'warning' as const,
      description: overview.issues || '系统存在性能问题，请关注相关指标。'
    }
  }
})

const coreMetrics = computed(() => [
  {
    key: 'processing_speed',
    label: '处理速度',
    value: '1,250/s',
    trend: '+15%',
    trendClass: 'trend-up',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    icon: 'TrendCharts',
    status: 'good'
  },
  {
    key: 'avg_response_time',
    label: '平均响应时间',
    value: Math.round((performanceData.message as any).avgProcessingTime || 45) + 'ms',
    trend: '-8%',
    trendClass: 'trend-down',
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    icon: 'Timer',
    status: 'good'
  },
  {
    key: 'success_rate',
    label: '成功率',
    value: Math.round((performanceData.message as any).successRate || 99.8) + '%',
    trend: '+0.2%',
    trendClass: 'trend-up',
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    icon: 'CircleCheck',
    status: 'excellent'
  },
  {
    key: 'cache_hit_rate',
    label: '缓存命中率',
    value: Math.round((performanceData.cache as any).hit_rate || 94.2) + '%',
    trend: '+12%',
    trendClass: 'trend-up',
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    icon: 'Coin',
    status: 'good'
  }
])

const cacheStatus = computed(() => {
  const hitRate = (performanceData.cache as any).hit_rate || 0
  if (hitRate > 90) {
    return { type: 'success' as const, text: '优秀' }
  } else if (hitRate > 70) {
    return { type: 'warning' as const, text: '良好' }
  } else {
    return { type: 'danger' as const, text: '需优化' }
  }
})

// 生命周期
onMounted(async () => {
  await initCharts()
  await loadAllData()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
  disposeCharts()
})

// 方法
const initCharts = async () => {
  await nextTick()
  
  try {
    // 缓存命中率图表
    if (cacheChartRef.value) {
      cacheChart = echarts.init(cacheChartRef.value)
      const cacheOption = {
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: generateTimeLabels() },
        yAxis: { type: 'value', max: 100, min: 0 },
        series: [
          {
            name: 'L1缓存',
            type: 'line',
            data: generateRandomData(24, 85, 95),
            smooth: true,
            itemStyle: { color: '#409eff' }
          },
          {
            name: 'L2缓存',
            type: 'line',
            data: generateRandomData(24, 75, 85),
            smooth: true,
            itemStyle: { color: '#67c23a' }
          },
          {
            name: 'L3数据库',
            type: 'line',
            data: generateRandomData(24, 60, 75),
            smooth: true,
            itemStyle: { color: '#e6a23c' }
          }
        ]
      }
      cacheChart.setOption(cacheOption)
    }
    
    // 告警趋势图表
    if (alertTrendChartRef.value) {
      alertTrendChart = echarts.init(alertTrendChartRef.value)
      const alertOption = {
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: generateTimeLabels() },
        yAxis: { type: 'value' },
        series: [
          {
            name: '总告警数',
            type: 'bar',
            data: generateRandomData(24, 50, 200),
            itemStyle: { color: '#409eff' }
          },
          {
            name: '紧急告警',
            type: 'line',
            data: generateRandomData(24, 0, 20),
            itemStyle: { color: '#f56c6c' }
          }
        ]
      }
      alertTrendChart.setOption(alertOption)
    }
    
    // 系统负载图表
    if (systemLoadChartRef.value) {
      systemLoadChart = echarts.init(systemLoadChartRef.value)
      const loadOption = {
        tooltip: { trigger: 'item' },
        series: [{
          type: 'gauge',
          radius: '80%',
          data: [{ value: 65, name: 'CPU使用率' }],
          detail: { formatter: '{value}%' }
        }]
      }
      systemLoadChart.setOption(loadOption)
    }
    
    // 线程池图表
    if (threadPoolChartRef.value) {
      threadPoolChart = echarts.init(threadPoolChartRef.value)
      const threadOption = {
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: ['规则引擎', '缓存管理', '消息发布'] },
        yAxis: { type: 'value' },
        series: [{
          type: 'bar',
          data: [8, 6, 4],
          itemStyle: { color: '#67c23a' }
        }]
      }
      threadPoolChart.setOption(threadOption)
    }
    
    // 消息统计图表
    if (messageStatsChartRef.value) {
      messageStatsChart = echarts.init(messageStatsChartRef.value)
      const messageOption = {
        tooltip: { trigger: 'item' },
        series: [{
          type: 'pie',
          radius: '70%',
          data: [
            { value: 435, name: '微信' },
            { value: 679, name: '内部消息' },
            { value: 234, name: '短信' },
            { value: 135, name: '邮件' }
          ]
        }]
      }
      messageStatsChart.setOption(messageOption)
    }
    
  } catch (error) {
    console.error('初始化图表失败:', error)
  }
}

const loadAllData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadPerformanceData(),
      loadSystemLoadData(),
      loadThreadPoolStatus(),
      loadRulePerformanceData()
    ])
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

const loadPerformanceData = async () => {
  try {
    const response = await getPerformanceStats()
    if (response.success) {
      Object.assign(performanceData, response.data)
    }
  } catch (error) {
    console.error('加载性能数据失败:', error)
  }
}

const loadSystemLoadData = async () => {
  try {
    const response = await getSystemLoad()
    if (response.success) {
      Object.assign(systemLoad, response.data)
      updateSystemLoadChart()
    }
  } catch (error) {
    console.error('加载系统负载失败:', error)
  }
}

const loadThreadPoolStatus = async () => {
  try {
    const response = await getThreadPoolStatus()
    if (response.success) {
      Object.assign(threadPoolStatus, response.data)
      updateThreadPoolChart()
    }
  } catch (error) {
    console.error('加载线程池状态失败:', error)
  }
}

const loadRulePerformanceData = async () => {
  try {
    const response = await getRulePerformanceRanking(10)
    if (response.success) {
      rulePerformanceData.value = response.data.topPerformanceRules || []
    }
  } catch (error) {
    console.error('加载规则性能数据失败:', error)
  }
}

const refreshData = () => {
  loadAllData()
}

const refreshRulePerformance = () => {
  loadRulePerformanceData()
}

const refreshSystemLoad = () => {
  loadSystemLoadData()
}

const startAutoRefresh = () => {
  refreshTimer = window.setInterval(() => {
    loadAllData()
  }, 30000) // 30秒自动刷新
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

const updateSystemLoadChart = () => {
  if (systemLoadChart && systemLoad.cpu) {
    const option = {
      series: [{
        data: [{ value: systemLoad.cpu.processCpuLoad, name: 'CPU使用率' }]
      }]
    }
    systemLoadChart.setOption(option)
  }
}

const updateThreadPoolChart = () => {
  if (threadPoolChart) {
    const data = [
      threadPoolStatus.ruleEngine?.activeThreads || 0,
      threadPoolStatus.cacheManager?.activeThreads || 0,
      4 // 消息发布器线程数（示例）
    ]
    const option = {
      series: [{ data }]
    }
    threadPoolChart.setOption(option)
  }
}

const disposeCharts = () => {
  [cacheChart, alertTrendChart, systemLoadChart, threadPoolChart, messageStatsChart]
    .forEach(chart => chart?.dispose())
}

const handlePeriodChange = (period: string) => {
  currentPeriod.value = period
  // 重新加载对应时期的数据
  loadPerformanceData()
}

const showClearCustomerCache = () => {
  clearCacheDialogVisible.value = true
}

const clearAllCache = async () => {
  try {
    await ElMessageBox.confirm(
      '确定清空所有本地缓存吗？这可能会暂时影响系统性能。',
      '确认操作',
      { type: 'warning' }
    )
    
    operationLoading.value = true
    const response = await clearAllCacheAPI()
    
    if (response.success) {
      ElMessage.success('缓存清空成功')
      await loadPerformanceData()
    } else {
      ElMessage.error('缓存清空失败: ' + response.message)
    }
    
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败: ' + (error.message || '未知错误'))
    }
  } finally {
    operationLoading.value = false
  }
}

const clearCustomerCache = async () => {
  if (!targetCustomerId.value) {
    ElMessage.warning('请输入客户ID')
    return
  }
  
  try {
    operationLoading.value = true
    const response = await clearCustomerCacheAPI(targetCustomerId.value)
    
    if (response.success) {
      ElMessage.success('客户缓存清空成功')
      clearCacheDialogVisible.value = false
      targetCustomerId.value = undefined
      await loadPerformanceData()
    } else {
      ElMessage.error('缓存清空失败: ' + response.message)
    }
    
  } catch (error: any) {
    ElMessage.error('操作失败: ' + (error.message || '未知错误'))
  } finally {
    operationLoading.value = false
  }
}

const healthCheck = async () => {
  try {
    operationLoading.value = true
    const response = await getCacheHealth()
    
    if (response.success && response.data.healthy) {
      ElMessage.success('系统健康检查通过')
    } else {
      ElMessage.warning('系统健康检查发现问题: ' + (response.data.error || '未知问题'))
    }
    
  } catch (error: any) {
    ElMessage.error('健康检查失败: ' + (error.message || '未知错误'))
  } finally {
    operationLoading.value = false
  }
}

const exportData = () => {
  const data = {
    performance: performanceData,
    systemLoad,
    threadPoolStatus,
    rulePerformance: rulePerformanceData.value,
    exportTime: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `alert-performance-report-${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)
}

// 工具函数
const generateTimeLabels = () => {
  const labels = []
  for (let i = 23; i >= 0; i--) {
    const time = new Date()
    time.setHours(time.getHours() - i)
    labels.push(time.getHours().toString().padStart(2, '0') + ':00')
  }
  return labels
}

const generateRandomData = (count: number, min: number, max: number) => {
  return Array.from({ length: count }, () => 
    Math.floor(Math.random() * (max - min + 1)) + min
  )
}

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getPerformanceClass = (time: number) => {
  if (time < 20) return 'performance-excellent'
  if (time < 50) return 'performance-good'
  return 'performance-poor'
}

const getSuccessRateClass = (rate: number) => {
  if (rate > 99) return 'success-rate-excellent'
  if (rate > 95) return 'success-rate-good'
  return 'success-rate-poor'
}
</script>

<style scoped>
.alert-performance-dashboard {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 5px 0;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-left p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 10px;
}

.status-overview {
  margin-bottom: 20px;
}

.status-alert {
  border-radius: 8px;
}

.metrics-cards {
  margin-bottom: 20px;
}

.metric-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.metric-card.good {
  border-left: 4px solid #67c23a;
}

.metric-card.excellent {
  border-left: 4px solid #409eff;
}

.metric-content {
  display: flex;
  align-items: center;
  padding: 20px;
}

.metric-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px;
  font-size: 24px;
  color: white;
}

.metric-info {
  flex: 1;
}

.metric-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.metric-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.metric-trend {
  font-size: 12px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.trend-up {
  color: #67c23a;
}

.trend-down {
  color: #409eff;
}

.charts-section {
  margin-bottom: 20px;
}

.chart-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.chart-container {
  height: 300px;
}

.chart-container.small {
  height: 200px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tables-section {
  margin-bottom: 20px;
}

.table-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.resource-stats {
  padding: 10px 0;
}

.resource-item {
  margin-bottom: 20px;
}

.resource-item:last-child {
  margin-bottom: 0;
}

.resource-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.resource-value {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.resource-big-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.resource-stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 10px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 6px;
}

.stat-label {
  font-size: 12px;
  color: #606266;
}

.stat-value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.control-panel {
  margin-bottom: 20px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.control-buttons {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.performance-excellent {
  color: #67c23a;
  font-weight: bold;
}

.performance-good {
  color: #e6a23c;
}

.performance-poor {
  color: #f56c6c;
  font-weight: bold;
}

.success-rate-excellent {
  color: #67c23a;
  font-weight: bold;
}

.success-rate-good {
  color: #e6a23c;
}

.success-rate-poor {
  color: #f56c6c;
  font-weight: bold;
}

@media (max-width: 1200px) {
  .charts-section .el-col {
    margin-bottom: 20px;
  }
  
  .metrics-cards .el-col {
    margin-bottom: 15px;
  }
}

@media (max-width: 768px) {
  .alert-performance-dashboard {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  
  .header-right {
    justify-content: center;
  }
  
  .metric-content {
    flex-direction: column;
    text-align: center;
  }
  
  .metric-icon {
    margin-right: 0;
    margin-bottom: 15px;
  }
  
  .control-buttons {
    justify-content: center;
  }
  
  .resource-stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>