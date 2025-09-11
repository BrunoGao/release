<template>
  <div class="alert-performance-dashboard p-4">
    <!-- 页面头部 -->
    <div class="page-header mb-4 flex justify-between items-center">
      <div class="header-left">
        <h2 class="text-xl font-semibold flex items-center gap-2 mb-1">
          <n-icon size="20">
            <icon-ic:baseline-trending-up />
          </n-icon>
          告警系统性能监控
        </h2>
        <p class="text-gray-600 text-sm">实时监控告警规则引擎、缓存系统和消息发布器的性能状态</p>
      </div>
      <div class="header-right">
        <n-space>
          <n-button @click="refreshData" :loading="loading">
            <template #icon>
              <n-icon><icon-ic:baseline-refresh /></n-icon>
            </template>
            刷新数据
          </n-button>
          <n-button @click="exportData">
            <template #icon>
              <n-icon><icon-ic:baseline-download /></n-icon>
            </template>
            导出报告
          </n-button>
        </n-space>
      </div>
    </div>
    
    <!-- 系统状态概览 -->
    <div class="status-overview mb-4">
      <n-alert 
        :title="systemStatus.title"
        :type="systemStatus.type"
        closable
        class="status-alert"
      >
        {{ systemStatus.description }}
      </n-alert>
    </div>
    
    <!-- 核心指标卡片 -->
    <n-grid :cols="4" :x-gap="20" class="metrics-cards mb-4">
      <n-grid-item v-for="metric in coreMetrics" :key="metric.key">
        <n-card class="metric-card">
          <div class="metric-content flex items-center p-4">
            <div class="metric-icon w-15 h-15 rounded-xl flex items-center justify-center mr-4 text-white text-xl" :style="{ background: metric.gradient }">
              <n-icon size="24">
                <component :is="metric.icon" />
              </n-icon>
            </div>
            <div class="metric-info">
              <div class="metric-value text-2xl font-bold">{{ metric.value }}</div>
              <div class="metric-label text-gray-500 text-sm">{{ metric.label }}</div>
              <div class="metric-trend flex items-center gap-1 text-sm" :class="metric.trendClass">
                <n-icon><icon-ic:baseline-trending-up /></n-icon>
                {{ metric.trend }}
              </div>
            </div>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>
    
    <!-- 性能图表 -->
    <n-grid :cols="2" :x-gap="20" class="charts-section">
      <n-grid-item>
        <n-card title="告警处理性能">
          <div class="chart-placeholder h-80 flex items-center justify-center bg-gray-50 rounded">
            <div class="text-center">
              <n-icon size="48" class="mb-4 text-gray-400">
                <icon-ic:baseline-show-chart />
              </n-icon>
              <p class="text-gray-500">性能图表功能开发中</p>
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card title="系统负载状态">
          <div class="chart-placeholder h-80 flex items-center justify-center bg-gray-50 rounded">
            <div class="text-center">
              <n-icon size="48" class="mb-4 text-gray-400">
                <icon-ic:baseline-monitor />
              </n-icon>
              <p class="text-gray-500">负载监控图表开发中</p>
            </div>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useMessage } from 'naive-ui'

const message = useMessage()
const loading = ref(false)

// 系统状态
const systemStatus = reactive({
  title: '系统运行正常',
  type: 'success' as const,
  description: '所有告警服务组件运行状态良好，性能指标正常'
})

// 核心指标
const coreMetrics = reactive([
  {
    key: 'alertsProcessed',
    label: '今日处理告警',
    value: '1,234',
    trend: '+12.5%',
    trendClass: 'text-green-500',
    status: 'healthy',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    icon: 'icon-ic:baseline-notifications'
  },
  {
    key: 'avgResponseTime',
    label: '平均响应时间',
    value: '156ms',
    trend: '-8.3%',
    trendClass: 'text-green-500',
    status: 'healthy',
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    icon: 'icon-ic:baseline-speed'
  },
  {
    key: 'errorRate',
    label: '错误率',
    value: '0.12%',
    trend: '-45.2%',
    trendClass: 'text-green-500',
    status: 'healthy',
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    icon: 'icon-ic:baseline-error-outline'
  },
  {
    key: 'throughput',
    label: '吞吐量/分钟',
    value: '2,567',
    trend: '+18.9%',
    trendClass: 'text-green-500',
    status: 'healthy',
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    icon: 'icon-ic:baseline-speed'
  }
])

onMounted(() => {
  loadPerformanceData()
})

const loadPerformanceData = () => {
  // 模拟加载性能数据
  console.log('Loading performance data...')
}

const refreshData = () => {
  loading.value = true
  setTimeout(() => {
    loadPerformanceData()
    loading.value = false
    message.success('数据刷新成功')
  }, 1000)
}

const exportData = () => {
  message.info('导出功能开发中...')
}
</script>

<style scoped>
.metric-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.metric-content {
  display: flex;
  align-items: center;
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
  margin-bottom: 5px;
}

.metric-trend {
  font-size: 12px;
}

.chart-placeholder {
  background: #fafbfc;
  border: 2px dashed #e4e7ed;
}
</style>