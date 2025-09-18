<template>
  <div class="personal-dashboard">
    <!-- 3D背景效果 -->
    <TechBackground 
      :intensity="0.8"
      :particle-count="80"
      :enable-grid="true"
      :enable-pulse="false"
      :enable-data-flow="true"
    />
    
    <!-- 个人仪表板网格 -->
    <div class="personal-grid">
      <!-- 第一行：个人概览 -->
      <div class="grid-row row-personal-overview">
        <!-- 个人健康档案 -->
        <div class="grid-item item-profile">
          <PersonalHealthProfile 
            :user-info="userProfile"
            :health-summary="healthSummary"
            :last-updated="lastHealthUpdate"
          />
        </div>
        
        <!-- 今日健康状态 -->
        <div class="grid-item item-daily-status">
          <DailyHealthStatus 
            :vital-signs="todayVitalSigns"
            :activity-summary="todayActivity"
            :goal-progress="dailyGoalProgress"
          />
        </div>
        
        <!-- 健康目标进度 -->
        <div class="grid-item item-goals">
          <HealthGoalsProgress 
            :goals="personalGoals"
            :achievements="recentAchievements"
            @goal-update="handleGoalUpdate"
          />
        </div>
      </div>
      
      <!-- 第二行：生命体征详情 -->
      <div class="grid-row row-vital-details">
        <!-- 心率趋势 -->
        <div class="grid-item item-chart">
          <VitalSignChart 
            :data="heartRateData"
            :type="'heartRate'"
            title="心率趋势"
            unit="BPM"
            :time-range="vitalSignsTimeRange"
          />
        </div>
        
        <!-- 血氧趋势 -->
        <div class="grid-item item-chart">
          <VitalSignChart 
            :data="bloodOxygenData"
            :type="'bloodOxygen'"
            title="血氧饱和度"
            unit="%"
            :time-range="vitalSignsTimeRange"
          />
        </div>
        
        <!-- 血压趋势 -->
        <div class="grid-item item-chart">
          <BloodPressureChart 
            :data="bloodPressureData"
            :time-range="vitalSignsTimeRange"
            title="血压趋势"
          />
        </div>
      </div>
      
      <!-- 第三行：运动与睡眠 -->
      <div class="grid-row row-activity-sleep">
        <!-- 运动统计 -->
        <div class="grid-item item-activity">
          <ActivityDashboard 
            :daily-stats="dailyActivityStats"
            :weekly-summary="weeklyActivitySummary"
            :exercise-goals="exerciseGoals"
            @activity-detail="showActivityDetail"
          />
        </div>
        
        <!-- 睡眠分析 -->
        <div class="grid-item item-sleep">
          <SleepAnalysisDashboard 
            :sleep-data="sleepAnalysisData"
            :sleep-trends="sleepTrends"
            :sleep-recommendations="sleepRecommendations"
          />
        </div>
        
        <!-- 压力与情绪 -->
        <div class="grid-item item-mental">
          <MentalHealthDashboard 
            :stress-data="stressLevelData"
            :mood-data="moodTrendData"
            :mindfulness-stats="mindfulnessStats"
            @stress-relief="showStressReliefSuggestions"
          />
        </div>
      </div>
      
      <!-- 第四行：健康建议与设备 -->
      <div class="grid-row row-recommendations">
        <!-- 个性化健康建议 -->
        <div class="grid-item item-recommendations">
          <PersonalizedRecommendations 
            :recommendations="healthRecommendations"
            :priority-actions="priorityActions"
            @recommendation-action="handleRecommendationAction"
          />
        </div>
        
        <!-- 设备连接状态 -->
        <div class="grid-item item-devices">
          <PersonalDevicePanel 
            :connected-devices="connectedDevices"
            :device-history="deviceSyncHistory"
            @device-action="handleDeviceAction"
          />
        </div>
        
        <!-- 数据统计 -->
        <div class="grid-item item-statistics">
          <PersonalDataStats 
            :data-completeness="dataCompleteness"
            :collection-stats="dataCollectionStats"
            :privacy-settings="privacySettings"
          />
        </div>
      </div>
    </div>
    
    <!-- 个人化控制面板 -->
    <div class="personal-controls">
      <!-- 时间范围选择 -->
      <div class="time-range-selector">
        <div class="selector-label">数据范围</div>
        <div class="time-buttons">
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
      
      <!-- 个人设置快捷入口 -->
      <div class="personal-settings">
        <button 
          class="setting-btn"
          @click="showNotificationSettings"
          title="通知设置"
        >
          <BellIcon />
        </button>
        
        <button 
          class="setting-btn"
          @click="showPrivacySettings"
          title="隐私设置"
        >
          <ShieldCheckIcon />
        </button>
        
        <button 
          class="setting-btn"
          @click="showDataExport"
          title="数据导出"
        >
          <ArrowDownTrayIcon />
        </button>
        
        <button 
          class="setting-btn"
          @click="showHealthProfile"
          title="健康档案"
        >
          <UserCircleIcon />
        </button>
      </div>
      
      <!-- 紧急联系 -->
      <div class="emergency-contact">
        <button 
          class="emergency-btn"
          @click="triggerEmergencyContact"
          title="紧急联系"
        >
          <PhoneIcon />
          <span>紧急联系</span>
        </button>
      </div>
    </div>
    
    <!-- 详情模态框 -->
    <Transition name="modal">
      <div v-if="showDetailModal" class="detail-modal" @click="closeDetailModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>{{ modalTitle }}</h3>
            <button class="modal-close" @click="closeDetailModal">
              <XMarkIcon />
            </button>
          </div>
          <div class="modal-body">
            <component :is="modalComponent" v-bind="modalProps" />
          </div>
        </div>
      </div>
    </Transition>
    
    <!-- 全局通知 -->
    <GlobalToast ref="toast" />
  </div>
</template>

<script setup lang="ts">
import { 
  BellIcon, 
  ShieldCheckIcon, 
  ArrowDownTrayIcon,
  UserCircleIcon,
  PhoneIcon,
  XMarkIcon
} from '@element-plus/icons-vue'
import TechBackground from '@/components/effects/TechBackground.vue'
import PersonalHealthProfile from '@/components/personal/PersonalHealthProfile.vue'
import DailyHealthStatus from '@/components/personal/DailyHealthStatus.vue'
import HealthGoalsProgress from '@/components/personal/HealthGoalsProgress.vue'
import VitalSignChart from '@/components/charts/VitalSignChart.vue'
import BloodPressureChart from '@/components/charts/BloodPressureChart.vue'
import ActivityDashboard from '@/components/personal/ActivityDashboard.vue'
import SleepAnalysisDashboard from '@/components/personal/SleepAnalysisDashboard.vue'
import MentalHealthDashboard from '@/components/personal/MentalHealthDashboard.vue'
import PersonalizedRecommendations from '@/components/personal/PersonalizedRecommendations.vue'
import PersonalDevicePanel from '@/components/personal/PersonalDevicePanel.vue'
import PersonalDataStats from '@/components/personal/PersonalDataStats.vue'
import GlobalToast from '@/components/common/GlobalToast.vue'

import { useSystemStore } from '@/stores/system'
import { useHealthStore } from '@/stores/health'
import { usePersonalStore } from '@/stores/personal'

// Store instances
const systemStore = useSystemStore()
const healthStore = useHealthStore()
const personalStore = usePersonalStore()

const toast = ref<InstanceType<typeof GlobalToast>>()

// 组件状态
const selectedTimeRange = ref('7d')
const showDetailModal = ref(false)
const modalTitle = ref('')
const modalComponent = ref(null)
const modalProps = ref({})

// 时间范围选项
const timeRanges = [
  { value: '1d', label: '今天' },
  { value: '3d', label: '3天' },
  { value: '7d', label: '7天' },
  { value: '30d', label: '30天' },
  { value: '90d', label: '3个月' }
]

// 计算属性 - 个人资料和健康数据
const userProfile = computed(() => personalStore.userProfile)
const healthSummary = computed(() => personalStore.healthSummary)
const lastHealthUpdate = computed(() => personalStore.lastHealthUpdate)

const todayVitalSigns = computed(() => personalStore.todayVitalSigns)
const todayActivity = computed(() => personalStore.todayActivity)
const dailyGoalProgress = computed(() => personalStore.dailyGoalProgress)

const personalGoals = computed(() => personalStore.personalGoals)
const recentAchievements = computed(() => personalStore.recentAchievements)

// 计算属性 - 生命体征数据
const heartRateData = computed(() => personalStore.getVitalSignData('heartRate', selectedTimeRange.value))
const bloodOxygenData = computed(() => personalStore.getVitalSignData('bloodOxygen', selectedTimeRange.value))
const bloodPressureData = computed(() => personalStore.getVitalSignData('bloodPressure', selectedTimeRange.value))
const vitalSignsTimeRange = computed(() => selectedTimeRange.value)

// 计算属性 - 运动与睡眠数据
const dailyActivityStats = computed(() => personalStore.dailyActivityStats)
const weeklyActivitySummary = computed(() => personalStore.weeklyActivitySummary)
const exerciseGoals = computed(() => personalStore.exerciseGoals)

const sleepAnalysisData = computed(() => personalStore.sleepAnalysisData)
const sleepTrends = computed(() => personalStore.sleepTrends)
const sleepRecommendations = computed(() => personalStore.sleepRecommendations)

const stressLevelData = computed(() => personalStore.stressLevelData)
const moodTrendData = computed(() => personalStore.moodTrendData)
const mindfulnessStats = computed(() => personalStore.mindfulnessStats)

// 计算属性 - 建议与设备数据
const healthRecommendations = computed(() => personalStore.healthRecommendations)
const priorityActions = computed(() => personalStore.priorityActions)

const connectedDevices = computed(() => personalStore.connectedDevices)
const deviceSyncHistory = computed(() => personalStore.deviceSyncHistory)

const dataCompleteness = computed(() => personalStore.dataCompleteness)
const dataCollectionStats = computed(() => personalStore.dataCollectionStats)
const privacySettings = computed(() => personalStore.privacySettings)

// 事件处理方法
const selectTimeRange = (range: string) => {
  selectedTimeRange.value = range
  personalStore.updateTimeRange(range)
}

const handleGoalUpdate = async (goalId: string, update: any) => {
  try {
    await personalStore.updatePersonalGoal(goalId, update)
    toast.value?.success('健康目标已更新')
  } catch (error) {
    toast.value?.error('目标更新失败')
  }
}

const showActivityDetail = (activityType: string) => {
  modalTitle.value = '运动详情'
  modalComponent.value = 'ActivityDetailView'
  modalProps.value = { activityType, timeRange: selectedTimeRange.value }
  showDetailModal.value = true
}

const showStressReliefSuggestions = () => {
  modalTitle.value = '减压建议'
  modalComponent.value = 'StressReliefSuggestions'
  modalProps.value = { currentStress: stressLevelData.value.current }
  showDetailModal.value = true
}

const handleRecommendationAction = async (recommendationId: string, action: string) => {
  try {
    await personalStore.handleRecommendationAction(recommendationId, action)
    toast.value?.success('操作已完成')
  } catch (error) {
    toast.value?.error('操作失败')
  }
}

const handleDeviceAction = async (deviceId: string, action: string) => {
  try {
    await personalStore.handleDeviceAction(deviceId, action)
    toast.value?.success(`设备${action}成功`)
  } catch (error) {
    toast.value?.error(`设备${action}失败`)
  }
}

// 设置相关方法
const showNotificationSettings = () => {
  modalTitle.value = '通知设置'
  modalComponent.value = 'NotificationSettingsView'
  modalProps.value = { settings: personalStore.notificationSettings }
  showDetailModal.value = true
}

const showPrivacySettings = () => {
  modalTitle.value = '隐私设置'
  modalComponent.value = 'PrivacySettingsView'
  modalProps.value = { settings: privacySettings.value }
  showDetailModal.value = true
}

const showDataExport = () => {
  modalTitle.value = '数据导出'
  modalComponent.value = 'DataExportView'
  modalProps.value = { availableData: personalStore.availableExportData }
  showDetailModal.value = true
}

const showHealthProfile = () => {
  modalTitle.value = '健康档案'
  modalComponent.value = 'HealthProfileEditor'
  modalProps.value = { profile: userProfile.value }
  showDetailModal.value = true
}

const triggerEmergencyContact = async () => {
  try {
    await personalStore.triggerEmergencyContact()
    toast.value?.warning('紧急联系已触发')
  } catch (error) {
    toast.value?.error('紧急联系失败')
  }
}

const closeDetailModal = () => {
  showDetailModal.value = false
  modalComponent.value = null
  modalProps.value = {}
}

// 键盘快捷键
const handleKeydown = (e: KeyboardEvent) => {
  if (e.ctrlKey || e.metaKey) {
    switch (e.key) {
      case 'r':
        e.preventDefault()
        personalStore.refreshAllData()
        break
      case 'e':
        e.preventDefault()
        showDataExport()
        break
      case 'p':
        e.preventDefault()
        showHealthProfile()
        break
      case 'Escape':
        if (showDetailModal.value) {
          closeDetailModal()
        }
        break
    }
  }
}

// 生命周期
onMounted(async () => {
  try {
    // 初始化个人数据
    await personalStore.initializePersonalDashboard()
    
    // 绑定键盘事件
    document.addEventListener('keydown', handleKeydown)
    
    // 设置为个人模式
    systemStore.setScreenMode('personal')
    
  } catch (error) {
    console.error('Personal dashboard initialization failed:', error)
    toast.value?.error('个人仪表板初始化失败')
  }
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// 响应式布局
const { width } = useWindowSize()
const isMobile = computed(() => width.value < 768)
const isTablet = computed(() => width.value >= 768 && width.value < 1024)

watch([isMobile, isTablet], () => {
  personalStore.updateLayoutMode({
    mobile: isMobile.value,
    tablet: isTablet.value,
    desktop: !isMobile.value && !isTablet.value
  })
})
</script>

<style lang="scss" scoped>
.personal-dashboard {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

// ========== 个人仪表板网格 ==========
.personal-grid {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  position: relative;
  z-index: 1;
}

.grid-row {
  display: flex;
  gap: var(--spacing-md);
  flex: 1;
  min-height: 0;
  
  &.row-personal-overview {
    flex: 1.2;
  }
  
  &.row-vital-details {
    flex: 1.5;
  }
  
  &.row-activity-sleep {
    flex: 1.3;
  }
  
  &.row-recommendations {
    flex: 1;
  }
}

.grid-item {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  position: relative;
  transition: all var(--duration-normal);
  
  &:hover {
    border-color: var(--primary-500);
    box-shadow: var(--shadow-xl);
    transform: translateY(-1px);
  }
  
  &.item-profile {
    flex: 1.2;
    min-width: 320px;
  }
  
  &.item-daily-status {
    flex: 1.5;
    min-width: 380px;
  }
  
  &.item-goals {
    flex: 1;
    min-width: 280px;
  }
  
  &.item-chart {
    flex: 1;
    min-width: 300px;
  }
  
  &.item-activity,
  &.item-sleep,
  &.item-mental {
    flex: 1;
    min-width: 320px;
  }
  
  &.item-recommendations {
    flex: 1.5;
    min-width: 400px;
  }
  
  &.item-devices,
  &.item-statistics {
    flex: 1;
    min-width: 280px;
  }
}

// ========== 个人化控制面板 ==========
.personal-controls {
  position: fixed;
  bottom: var(--spacing-lg);
  left: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  z-index: var(--z-floating);
}

.time-range-selector {
  background: var(--bg-card);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-sm);
  backdrop-filter: blur(10px);
  
  .selector-label {
    font-size: var(--font-xs);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xs);
    text-align: center;
  }
  
  .time-buttons {
    display: flex;
    gap: var(--spacing-xs);
  }
  
  .time-btn {
    padding: var(--spacing-xs) var(--spacing-sm);
    border: 1px solid var(--border-tertiary);
    border-radius: var(--radius-sm);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    font-size: var(--font-xs);
    cursor: pointer;
    transition: all var(--duration-fast);
    
    &:hover {
      color: var(--primary-500);
      border-color: var(--primary-500);
    }
    
    &.active {
      background: var(--primary-500);
      color: white;
      border-color: var(--primary-500);
    }
  }
}

.personal-settings {
  display: flex;
  gap: var(--spacing-xs);
  background: var(--bg-card);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xs);
  backdrop-filter: blur(10px);
  
  .setting-btn {
    width: 32px;
    height: 32px;
    border: 1px solid var(--border-tertiary);
    border-radius: var(--radius-sm);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    display: flex;
    align-items: center;
    justify-content: center;
    
    &:hover {
      color: var(--primary-500);
      border-color: var(--primary-500);
      background: rgba(0, 255, 157, 0.1);
    }
  }
}

.emergency-contact {
  .emergency-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    background: linear-gradient(135deg, var(--error), #ff8a80);
    color: white;
    border: none;
    border-radius: var(--radius-lg);
    font-weight: 600;
    cursor: pointer;
    transition: all var(--duration-fast);
    box-shadow: var(--shadow-md);
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-lg);
    }
    
    &:active {
      transform: translateY(0);
    }
  }
}

// ========== 详情模态框 ==========
.detail-modal {
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

.modal-content {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-xl);
  max-width: 80vw;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: var(--shadow-2xl);
  backdrop-filter: blur(10px);
}

.modal-header {
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
  
  .modal-close {
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

.modal-body {
  padding: var(--spacing-lg);
  overflow-y: auto;
  max-height: calc(80vh - 100px);
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

// ========== 响应式设计 ==========
@media (max-width: 1200px) {
  .grid-row {
    flex-wrap: wrap;
    
    .grid-item {
      &.item-recommendations {
        flex: 1 1 100%;
      }
      
      &.item-profile,
      &.item-daily-status,
      &.item-goals {
        flex: 1 1 calc(50% - var(--spacing-md) / 2);
        min-width: 280px;
      }
    }
  }
}

@media (max-width: 768px) {
  .personal-grid {
    padding: var(--spacing-md);
    gap: var(--spacing-sm);
  }
  
  .grid-row {
    flex-direction: column;
    
    .grid-item {
      flex: none;
      min-width: auto;
    }
  }
  
  .personal-controls {
    bottom: var(--spacing-sm);
    left: var(--spacing-sm);
    
    .time-buttons {
      flex-wrap: wrap;
    }
    
    .personal-settings {
      flex-wrap: wrap;
    }
  }
  
  .modal-content {
    max-width: 95vw;
    max-height: 95vh;
    margin: var(--spacing-sm);
  }
}

@media (prefers-reduced-motion: reduce) {
  .grid-item,
  .setting-btn,
  .emergency-btn,
  .modal-enter-active,
  .modal-leave-active {
    transition: none;
  }
}
</style>