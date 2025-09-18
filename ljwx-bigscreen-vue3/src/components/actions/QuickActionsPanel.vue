<template>
  <div class="quick-actions-panel">
    <div class="panel-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <Lightning />
        </el-icon>
        <h3 class="panel-title">快速操作</h3>
      </div>
      <el-button 
        v-if="showSettings" 
        type="text" 
        @click="openSettings"
        class="settings-btn"
      >
        <el-icon>
          <Setting />
        </el-icon>
      </el-button>
    </div>

    <div class="actions-grid">
      <div 
        v-for="action in visibleActions" 
        :key="action.id"
        class="action-item"
        :class="{ 
          disabled: action.disabled,
          danger: action.type === 'danger',
          primary: action.type === 'primary'
        }"
        @click="handleAction(action)"
      >
        <div class="action-icon">
          <el-icon>
            <component :is="getActionIcon(action.icon)" />
          </el-icon>
          <div v-if="action.badge" class="action-badge">
            {{ action.badge }}
          </div>
        </div>
        <div class="action-content">
          <h4 class="action-title">{{ action.title }}</h4>
          <p class="action-description">{{ action.description }}</p>
          <div v-if="action.shortcut" class="action-shortcut">
            {{ action.shortcut }}
          </div>
        </div>
      </div>
    </div>

    <!-- 展开/收起按钮 -->
    <div v-if="actions.length > maxVisible" class="expand-toggle">
      <el-button 
        type="text" 
        @click="expanded = !expanded"
        class="expand-btn"
      >
        <span>{{ expanded ? '收起' : `显示更多 (${hiddenCount})` }}</span>
        <el-icon class="expand-icon" :class="{ rotated: expanded }">
          <ArrowDown />
        </el-icon>
      </el-button>
    </div>

    <!-- 设置对话框 -->
    <el-dialog 
      v-model="settingsVisible" 
      title="操作设置" 
      width="500px"
      append-to-body
    >
      <div class="settings-content">
        <h4>显示设置</h4>
        <div class="setting-group">
          <el-checkbox v-model="settings.showDescriptions">
            显示操作说明
          </el-checkbox>
          <el-checkbox v-model="settings.showShortcuts">
            显示快捷键
          </el-checkbox>
          <el-checkbox v-model="settings.compactMode">
            紧凑模式
          </el-checkbox>
        </div>

        <h4>操作管理</h4>
        <div class="actions-manager">
          <div 
            v-for="action in actions" 
            :key="action.id" 
            class="action-setting"
          >
            <el-checkbox 
              v-model="action.visible" 
              :label="action.title"
            />
            <el-select 
              v-model="action.priority" 
              size="small" 
              style="width: 80px; margin-left: 10px"
            >
              <el-option label="高" value="high" />
              <el-option label="中" value="medium" />
              <el-option label="低" value="low" />
            </el-select>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="settingsVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { 
  Lightning, 
  Setting, 
  ArrowDown,
  Refresh,
  Download,
  Upload,
  Bell,
  Warning,
  Document,
  VideoPlay,
  Share,
  Tools,
  User,
  Monitor,
  DataLine,
  Location
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface QuickAction {
  id: string
  title: string
  description: string
  icon: string
  type: 'default' | 'primary' | 'success' | 'warning' | 'danger'
  handler?: string
  disabled?: boolean
  visible?: boolean
  priority?: 'high' | 'medium' | 'low'
  badge?: string
  shortcut?: string
  category?: string
}

interface ActionSettings {
  showDescriptions: boolean
  showShortcuts: boolean
  compactMode: boolean
  maxVisible: number
}

interface Props {
  actions?: QuickAction[]
  showSettings?: boolean
  maxVisible?: number
  category?: string
}

const props = withDefaults(defineProps<Props>(), {
  actions: () => [
    {
      id: 'refresh-data',
      title: '刷新数据',
      description: '获取最新的健康数据',
      icon: 'refresh',
      type: 'primary',
      visible: true,
      priority: 'high',
      shortcut: 'Ctrl+R'
    },
    {
      id: 'export-report',
      title: '导出报告',
      description: '导出健康评估报告',
      icon: 'download',
      type: 'default',
      visible: true,
      priority: 'high',
      shortcut: 'Ctrl+E'
    },
    {
      id: 'sync-devices',
      title: '同步设备',
      description: '同步所有健康设备数据',
      icon: 'upload',
      type: 'default',
      visible: true,
      priority: 'medium',
      badge: '3'
    },
    {
      id: 'alert-center',
      title: '预警中心',
      description: '查看健康预警信息',
      icon: 'bell',
      type: 'warning',
      visible: true,
      priority: 'high',
      badge: '2'
    },
    {
      id: 'emergency-mode',
      title: '紧急模式',
      description: '启动紧急响应程序',
      icon: 'warning',
      type: 'danger',
      visible: true,
      priority: 'high'
    },
    {
      id: 'generate-insights',
      title: '生成洞察',
      description: '基于AI分析生成健康洞察',
      icon: 'dataLine',
      type: 'success',
      visible: true,
      priority: 'medium'
    },
    {
      id: 'share-dashboard',
      title: '分享面板',
      description: '分享当前健康面板',
      icon: 'share',
      type: 'default',
      visible: true,
      priority: 'low'
    },
    {
      id: 'device-config',
      title: '设备配置',
      description: '管理健康监测设备',
      icon: 'tools',
      type: 'default',
      visible: true,
      priority: 'medium'
    }
  ],
  showSettings: true,
  maxVisible: 6
})

// 定义事件
const emit = defineEmits<{
  'action-executed': [action: QuickAction]
}>()

// 响应式数据
const expanded = ref(false)
const settingsVisible = ref(false)

// 设置数据
const settings = reactive<ActionSettings>({
  showDescriptions: true,
  showShortcuts: true,
  compactMode: false,
  maxVisible: props.maxVisible
})

// 计算属性
const visibleActions = computed(() => {
  const filtered = props.actions.filter(action => action.visible !== false)
  const sorted = filtered.sort((a, b) => {
    const priorityOrder = { high: 3, medium: 2, low: 1 }
    return (priorityOrder[b.priority || 'medium'] - priorityOrder[a.priority || 'medium'])
  })
  
  if (expanded.value) {
    return sorted
  }
  
  return sorted.slice(0, settings.maxVisible)
})

const hiddenCount = computed(() => {
  return Math.max(0, props.actions.filter(a => a.visible !== false).length - settings.maxVisible)
})

// 方法
const getActionIcon = (iconName: string) => {
  const iconMap = {
    refresh: Refresh,
    download: Download,
    upload: Upload,
    bell: Bell,
    warning: Warning,
    document: Document,
    videoPlay: VideoPlay,
    share: Share,
    tools: Tools,
    user: User,
    monitor: Monitor,
    dataLine: DataLine,
    location: Location
  }
  return iconMap[iconName as keyof typeof iconMap] || Document
}

const handleAction = async (action: QuickAction) => {
  if (action.disabled) {
    return
  }

  try {
    // 根据动作类型执行不同的逻辑
    switch (action.id) {
      case 'refresh-data':
        await handleRefreshData()
        break
      case 'export-report':
        await handleExportReport()
        break
      case 'sync-devices':
        await handleSyncDevices()
        break
      case 'alert-center':
        await handleAlertCenter()
        break
      case 'emergency-mode':
        await handleEmergencyMode()
        break
      case 'generate-insights':
        await handleGenerateInsights()
        break
      case 'share-dashboard':
        await handleShareDashboard()
        break
      case 'device-config':
        await handleDeviceConfig()
        break
      default:
        console.log('未知操作:', action.id)
    }

    emit('action-executed', action)
    ElMessage.success(`${action.title} 执行成功`)
  } catch (error) {
    console.error('Action execution failed:', error)
    ElMessage.error(`${action.title} 执行失败`)
  }
}

const handleRefreshData = async () => {
  // 刷新数据逻辑
  console.log('刷新健康数据...')
  await new Promise(resolve => setTimeout(resolve, 1000))
}

const handleExportReport = async () => {
  // 导出报告逻辑
  console.log('导出健康报告...')
  await new Promise(resolve => setTimeout(resolve, 1500))
}

const handleSyncDevices = async () => {
  // 同步设备逻辑
  console.log('同步设备数据...')
  await new Promise(resolve => setTimeout(resolve, 2000))
}

const handleAlertCenter = async () => {
  // 打开预警中心
  console.log('打开预警中心...')
  // 可以发出路由事件或打开模态框
}

const handleEmergencyMode = async () => {
  const result = await ElMessageBox.confirm(
    '确认启动紧急模式吗？这将触发所有紧急响应程序。',
    '紧急模式确认',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )

  if (result === 'confirm') {
    console.log('启动紧急模式...')
  }
}

const handleGenerateInsights = async () => {
  console.log('生成AI健康洞察...')
  await new Promise(resolve => setTimeout(resolve, 3000))
}

const handleShareDashboard = async () => {
  console.log('分享健康面板...')
  // 生成分享链接或打开分享对话框
}

const handleDeviceConfig = async () => {
  console.log('打开设备配置...')
  // 打开设备配置面板
}

const openSettings = () => {
  settingsVisible.value = true
}

const saveSettings = () => {
  // 保存设置到本地存储
  localStorage.setItem('quickActionsSettings', JSON.stringify(settings))
  localStorage.setItem('quickActionsConfig', JSON.stringify(props.actions))
  
  settingsVisible.value = false
  ElMessage.success('设置已保存')
}

// 生命周期
onMounted(() => {
  // 从本地存储加载设置
  const savedSettings = localStorage.getItem('quickActionsSettings')
  if (savedSettings) {
    Object.assign(settings, JSON.parse(savedSettings))
  }
})
</script>

<style lang="scss" scoped>
.quick-actions-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

// ========== 面板头部 ==========
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-light);
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(0, 255, 157, 0.02) 100%);
  
  .title-section {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    
    .header-icon {
      color: var(--primary-500);
      font-size: 20px;
    }
    
    .panel-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .settings-btn {
    color: var(--text-secondary);
    
    &:hover {
      color: var(--primary-500);
    }
  }
}

// ========== 操作网格 ==========
.actions-grid {
  flex: 1;
  padding: var(--spacing-md);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-md);
  overflow-y: auto;
}

.action-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--bg-elevated);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    border-color: var(--primary-300);
  }
  
  &.primary {
    border-color: var(--primary-300);
    
    .action-icon {
      background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
      color: white;
    }
  }
  
  &.danger {
    border-color: var(--error-300);
    
    .action-icon {
      background: linear-gradient(135deg, var(--error-500), var(--error-600));
      color: white;
    }
  }
  
  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
    
    &:hover {
      transform: none;
      box-shadow: none;
    }
  }
}

.action-icon {
  position: relative;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-500);
  font-size: 20px;
  flex-shrink: 0;
  
  .action-badge {
    position: absolute;
    top: -6px;
    right: -6px;
    width: 18px;
    height: 18px;
    background: var(--error-500);
    color: white;
    border-radius: var(--radius-full);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: 600;
  }
}

.action-content {
  flex: 1;
  
  .action-title {
    font-size: var(--font-md);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-xs) 0;
  }
  
  .action-description {
    font-size: var(--font-sm);
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-xs) 0;
    line-height: 1.4;
  }
  
  .action-shortcut {
    font-size: var(--font-xs);
    color: var(--text-muted);
    background: var(--bg-secondary);
    padding: 2px 6px;
    border-radius: var(--radius-sm);
    display: inline-block;
    font-family: var(--font-mono);
  }
}

// ========== 展开控制 ==========
.expand-toggle {
  padding: var(--spacing-md);
  border-top: 1px solid var(--border-light);
  text-align: center;
  
  .expand-btn {
    color: var(--text-secondary);
    
    .expand-icon {
      margin-left: var(--spacing-xs);
      transition: transform 0.3s ease;
      
      &.rotated {
        transform: rotate(180deg);
      }
    }
  }
}

// ========== 设置对话框 ==========
.settings-content {
  .setting-group {
    margin-bottom: var(--spacing-lg);
    
    .el-checkbox {
      display: block;
      margin-bottom: var(--spacing-sm);
    }
  }
  
  .actions-manager {
    max-height: 300px;
    overflow-y: auto;
    
    .action-setting {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--spacing-sm);
      border-radius: var(--radius-sm);
      
      &:hover {
        background: var(--bg-secondary);
      }
    }
  }
  
  h4 {
    color: var(--text-primary);
    font-size: var(--font-md);
    font-weight: 600;
    margin-bottom: var(--spacing-md);
  }
}

// ========== 响应式设计 ==========
@media (max-width: 768px) {
  .actions-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }
  
  .action-item {
    padding: var(--spacing-sm);
  }
  
  .action-icon {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }
  
  .panel-header {
    padding: var(--spacing-md);
  }
}

@media (max-width: 480px) {
  .action-item {
    flex-direction: column;
    text-align: center;
    gap: var(--spacing-sm);
  }
  
  .action-content {
    .action-description {
      display: none;
    }
  }
}
</style>