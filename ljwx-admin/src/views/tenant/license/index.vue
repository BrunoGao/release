<template>
  <div class="tenant-license">
    <!-- 页面头部 -->
    <div class="header-section">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">🔐 我的License</h1>
          <p class="page-subtitle">管理当前租户的License配置和使用状态</p>
        </div>
        <div class="action-buttons">
          <NButton 
            type="primary" 
            @click="refreshData"
            :loading="loading"
          >
            <template #icon>
              <NIcon><RefreshOutline /></NIcon>
            </template>
            刷新
          </NButton>
          <NButton 
            type="success" 
            @click="showImportModal = true"
            v-if="hasPermission('license:self:import')"
          >
            <template #icon>
              <NIcon><CloudUploadOutline /></NIcon>
            </template>
            导入License
          </NButton>
        </div>
      </div>
    </div>

    <!-- License状态概览 -->
    <div class="status-overview">
      <NCard title="📊 License 状态概览" class="overview-card">
        <div class="status-grid">
          <div class="status-item">
            <div class="status-icon">
              <NIcon size="24" :color="licenseStatus.effectiveLicenseEnabled ? '#52c41a' : '#ff4d4f'">
                <CheckmarkCircleOutline v-if="licenseStatus.effectiveLicenseEnabled" />
                <CloseCircleOutline v-else />
              </NIcon>
            </div>
            <div class="status-content">
              <div class="status-title">License状态</div>
              <div class="status-value" :class="{ 'success': licenseStatus.effectiveLicenseEnabled, 'error': !licenseStatus.effectiveLicenseEnabled }">
                {{ licenseStatus.effectiveLicenseEnabled ? '正常' : '异常' }}
              </div>
            </div>
          </div>

          <div class="status-item">
            <div class="status-icon">
              <NIcon size="24" color="#1890ff">
                <TimeOutline />
              </NIcon>
            </div>
            <div class="status-content">
              <div class="status-title">剩余时间</div>
              <div class="status-value" :class="getRemainingDaysClass(licenseStatus.remainingDays)">
                {{ licenseStatus.remainingDays || 0 }} 天
              </div>
            </div>
          </div>

          <div class="status-item">
            <div class="status-icon">
              <NIcon size="24" color="#722ed1">
                <PhonePortraitOutline />
              </NIcon>
            </div>
            <div class="status-content">
              <div class="status-title">设备使用</div>
              <div class="status-value">
                {{ currentDevices }} / {{ maxDevices }} 台
              </div>
            </div>
          </div>

          <div class="status-item">
            <div class="status-icon">
              <NIcon size="24" color="#13c2c2">
                <StatsChartOutline />
              </NIcon>
            </div>
            <div class="status-content">
              <div class="status-title">使用率</div>
              <div class="status-value">
                {{ deviceUsageRate }}%
              </div>
            </div>
          </div>
        </div>
      </NCard>
    </div>

    <!-- License详细信息 -->
    <NCard title="ℹ️ License 详细信息" class="details-card" v-if="licenseInfo">
      <NDescriptions :column="2" bordered>
        <NDescriptionsItem label="许可证ID">
          {{ licenseInfo.licenseId || '--' }}
        </NDescriptionsItem>
        <NDescriptionsItem label="客户名称">
          {{ licenseInfo.customerName || '--' }}
        </NDescriptionsItem>
        <NDescriptionsItem label="许可证类型">
          <NBadge 
            :type="getLicenseTypeColor(licenseInfo.licenseType)"
            :text="licenseInfo.licenseType || '标准版'"
          />
        </NDescriptionsItem>
        <NDescriptionsItem label="版本号">
          {{ licenseInfo.version || '--' }}
        </NDescriptionsItem>
        <NDescriptionsItem label="生效日期">
          {{ formatDate(licenseInfo.startDate) }}
        </NDescriptionsItem>
        <NDescriptionsItem label="到期日期">
          {{ formatDate(licenseInfo.endDate) }}
        </NDescriptionsItem>
        <NDescriptionsItem label="最大设备数">
          {{ licenseInfo.maxDevices || '--' }}
        </NDescriptionsItem>
        <NDescriptionsItem label="最大用户数">
          {{ licenseInfo.maxUsers || '--' }}
        </NDescriptionsItem>
        <NDescriptionsItem label="创建时间">
          {{ formatDate(licenseInfo.createTime) }}
        </NDescriptionsItem>
        <NDescriptionsItem label="硬件指纹">
          <NText code>{{ licenseInfo.hardwareFingerprint || '--' }}</NText>
        </NDescriptionsItem>
      </NDescriptions>

      <!-- 功能列表 -->
      <div class="features-section" v-if="licenseInfo.features && licenseInfo.features.length > 0">
        <h4>🔧 包含功能</h4>
        <div class="features-grid">
          <NBadge 
            v-for="feature in licenseInfo.features" 
            :key="feature"
            type="info"
            :text="getFeatureName(feature)"
            class="feature-badge"
          />
        </div>
      </div>

      <!-- 备注信息 -->
      <div class="remarks-section" v-if="licenseInfo.remarks">
        <h4>📝 备注信息</h4>
        <NText>{{ licenseInfo.remarks }}</NText>
      </div>
    </NCard>

    <!-- 使用监控 -->
    <NCard title="📈 使用监控" class="monitoring-card">
      <div class="monitoring-content">
        <!-- 设备使用率图表 -->
        <div class="chart-section">
          <h4>设备使用率</h4>
          <div class="chart-container">
            <div id="device-usage-chart" style="height: 200px;"></div>
          </div>
        </div>

        <!-- 最近活动设备 -->
        <div class="recent-devices" v-if="recentDevices.length > 0">
          <h4>最近活跃设备</h4>
          <div class="device-list">
            <div 
              v-for="device in recentDevices" 
              :key="device.deviceSn"
              class="device-item"
            >
              <div class="device-info">
                <NIcon><PhonePortraitOutline /></NIcon>
                <span class="device-sn">{{ device.deviceSn }}</span>
              </div>
              <div class="device-status">
                <NBadge type="success" text="在线" />
                <span class="last-activity">{{ formatTime(device.lastActivity) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </NCard>

    <!-- 警告信息 -->
    <div class="alerts-section" v-if="alerts.length > 0">
      <NAlert
        v-for="(alert, index) in alerts"
        :key="index"
        :type="alert.type"
        :title="alert.title"
        :description="alert.description"
        class="alert-item"
        show-icon
        closable
      />
    </div>

    <!-- License导入弹窗 -->
    <NModal
      v-model:show="showImportModal"
      preset="dialog"
      title="导入License文件"
      positive-text="导入"
      negative-text="取消"
      @positive-click="handleImportLicense"
      @negative-click="showImportModal = false"
    >
      <div class="import-content">
        <NAlert type="info" title="导入说明" class="import-notice">
          <ul>
            <li>请选择有效的.lic格式License文件</li>
            <li>文件大小不能超过10MB</li>
            <li>导入后将覆盖现有的License配置</li>
            <li>请确保License文件与当前硬件环境匹配</li>
          </ul>
        </NAlert>

        <NUpload
          ref="uploadRef"
          :max="1"
          accept=".lic"
          :show-file-list="true"
          :default-upload="false"
          @change="handleFileChange"
        >
          <NUploadDragger>
            <div style="margin-bottom: 12px">
              <NIcon size="48" :depth="3">
                <CloudUploadOutline />
              </NIcon>
            </div>
            <NText style="font-size: 16px">
              点击或者拖动License文件到该区域来上传
            </NText>
            <NP depth="3" style="margin: 8px 0 0 0">
              支持.lic格式，文件大小不超过10MB
            </NP>
          </NUploadDragger>
        </NUpload>
      </div>
    </NModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { 
  NCard, NButton, NIcon, NModal, NUpload, NUploadDragger, NText, NP,
  NDescriptions, NDescriptionsItem, NBadge, NAlert,
  useMessage
} from 'naive-ui'
import { 
  RefreshOutline, CloudUploadOutline, CheckmarkCircleOutline, 
  CloseCircleOutline, TimeOutline, PhonePortraitOutline, StatsChartOutline
} from '@vicons/ionicons5'
import { formatDate, formatTime } from '@/utils/date'
import { hasPermission } from '@/utils/auth'
import * as echarts from 'echarts'

// 响应式数据
const loading = ref(false)
const showImportModal = ref(false)
const uploadRef = ref()
const selectedFile = ref<File | null>(null)

// License状态数据
const licenseStatus = ref<Api.License.TenantLicenseStatus>({
  customerId: 0,
  customerSupportLicense: false,
  systemLicenseEnabled: false,
  systemLicenseValid: false,
  effectiveLicenseEnabled: false
})

const licenseInfo = ref<Api.License.LicenseInfo | null>(null)
const currentDevices = ref(0)
const recentDevices = ref([])
const alerts = ref([])

// 消息提示
const message = useMessage()

// 计算属性
const maxDevices = computed(() => licenseInfo.value?.maxDevices || 0)
const deviceUsageRate = computed(() => {
  if (maxDevices.value === 0) return 0
  return Math.round((currentDevices.value / maxDevices.value) * 100)
})

// 生命周期
onMounted(() => {
  loadData()
  initCharts()
})

// 方法
const refreshData = () => {
  loadData()
}

const loadData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadLicenseStatus(),
      loadDeviceUsage(),
      checkAlerts()
    ])
  } catch (error) {
    console.error('加载数据失败:', error)
    message.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const loadLicenseStatus = async () => {
  try {
    // 获取当前用户的客户ID（这里需要根据实际情况调整）
    const customerId = getCurrentCustomerId()
    
    const response = await fetch(`/api/license/management/tenant/${customerId}/status`)
    const data = await response.json()
    
    if (data.success) {
      licenseStatus.value = data.data
      licenseInfo.value = data.data.licenseInfo
    }
  } catch (error) {
    console.error('加载License状态失败:', error)
  }
}

const loadDeviceUsage = async () => {
  try {
    // 这里应该调用BigScreen的API获取设备使用情况
    // 暂时使用模拟数据
    currentDevices.value = 15
    recentDevices.value = [
      { deviceSn: 'DEV001', lastActivity: new Date().toISOString() },
      { deviceSn: 'DEV002', lastActivity: new Date(Date.now() - 300000).toISOString() },
      { deviceSn: 'DEV003', lastActivity: new Date(Date.now() - 600000).toISOString() }
    ]
  } catch (error) {
    console.error('加载设备使用情况失败:', error)
  }
}

const checkAlerts = () => {
  const alertList = []
  
  // 检查License状态
  if (!licenseStatus.value.effectiveLicenseEnabled) {
    alertList.push({
      type: 'error',
      title: 'License状态异常',
      description: licenseStatus.value.error || '当前License无效或已禁用，请联系管理员'
    })
  }
  
  // 检查过期时间
  if (licenseStatus.value.remainingDays && licenseStatus.value.remainingDays <= 30) {
    const type = licenseStatus.value.remainingDays <= 7 ? 'error' : 'warning'
    alertList.push({
      type,
      title: 'License即将过期',
      description: `您的License将在${licenseStatus.value.remainingDays}天后过期，请及时续期`
    })
  }
  
  // 检查设备使用率
  if (deviceUsageRate.value >= 90) {
    alertList.push({
      type: 'warning',
      title: '设备使用率过高',
      description: `当前设备使用率为${deviceUsageRate.value}%，接近License限制`
    })
  }
  
  alerts.value = alertList
}

const initCharts = () => {
  // 初始化设备使用率图表
  const chartDom = document.getElementById('device-usage-chart')
  if (chartDom) {
    const chart = echarts.init(chartDom)
    
    const option = {
      tooltip: {
        trigger: 'item'
      },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        data: [
          { value: currentDevices.value, name: '已使用设备', itemStyle: { color: '#1890ff' } },
          { value: Math.max(0, maxDevices.value - currentDevices.value), name: '剩余设备', itemStyle: { color: '#f0f0f0' } }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }
    
    chart.setOption(option)
    
    // 响应式处理
    window.addEventListener('resize', () => {
      chart.resize()
    })
  }
}

const handleFileChange = ({ file }: any) => {
  selectedFile.value = file.file
}

const handleImportLicense = async () => {
  if (!selectedFile.value) {
    message.error('请选择License文件')
    return false
  }
  
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    const response = await fetch('/api/license/management/tenant/import', {
      method: 'POST',
      body: formData
    })
    const data = await response.json()
    
    if (data.success) {
      message.success('License导入成功')
      showImportModal.value = false
      selectedFile.value = null
      uploadRef.value?.clear()
      await loadData()
    } else {
      message.error(data.message || 'License导入失败')
      return false
    }
  } catch (error) {
    message.error('License导入失败')
    return false
  }
}

// 工具方法
const getRemainingDaysClass = (days: number) => {
  if (days > 30) return 'success'
  if (days > 7) return 'warning'
  return 'error'
}

const getLicenseTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    'enterprise': 'success',
    'professional': 'info',
    'standard': 'warning',
    'trial': 'error'
  }
  return colorMap[type?.toLowerCase()] || 'default'
}

const getFeatureName = (feature: string) => {
  const featureMap: Record<string, string> = {
    'bigscreen_access': '大屏访问',
    'user_management': '用户管理',
    'device_monitoring': '设备监控',
    'health_analytics': '健康分析',
    'alert_management': '告警管理',
    'data_export': '数据导出',
    'api_access': 'API接口',
    'advanced_charts': '高级图表'
  }
  return featureMap[feature] || feature
}

const getCurrentCustomerId = () => {
  // 这里需要根据实际的用户管理逻辑来获取当前用户的客户ID
  // 暂时返回模拟值
  return 1
}
</script>

<style scoped>
.tenant-license {
  padding: 20px;
}

.header-section {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #1a1a1a;
}

.page-subtitle {
  color: #666;
  margin: 0;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.status-overview {
  margin-bottom: 24px;
}

.overview-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.overview-card :deep(.n-card-header) {
  color: white;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.status-icon {
  flex-shrink: 0;
}

.status-content {
  flex: 1;
}

.status-title {
  font-size: 14px;
  opacity: 0.8;
  margin-bottom: 4px;
}

.status-value {
  font-size: 18px;
  font-weight: 600;
}

.status-value.success {
  color: #52c41a;
}

.status-value.warning {
  color: #faad14;
}

.status-value.error {
  color: #ff4d4f;
}

.details-card,
.monitoring-card {
  margin-bottom: 24px;
}

.features-section,
.remarks-section {
  margin-top: 24px;
}

.features-section h4,
.remarks-section h4 {
  margin-bottom: 12px;
  color: #1a1a1a;
}

.features-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.feature-badge {
  margin-bottom: 8px;
}

.monitoring-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.chart-section h4,
.recent-devices h4 {
  margin-bottom: 16px;
  color: #1a1a1a;
}

.chart-container {
  height: 200px;
}

.device-list {
  max-height: 200px;
  overflow-y: auto;
}

.device-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  margin-bottom: 8px;
}

.device-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-sn {
  font-weight: 500;
}

.device-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.alerts-section {
  margin-bottom: 24px;
}

.alert-item {
  margin-bottom: 12px;
}

.import-content {
  padding: 20px 0;
}

.import-notice {
  margin-bottom: 20px;
}

.import-notice ul {
  margin: 0;
  padding-left: 20px;
}

.import-notice li {
  margin-bottom: 4px;
}

@media (max-width: 1200px) {
  .status-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .monitoring-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .status-grid {
    grid-template-columns: 1fr;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
}
</style>