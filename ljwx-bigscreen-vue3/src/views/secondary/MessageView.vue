<template>
  <div class="message-view">
    <!-- 3D背景效果 -->
    <TechBackground 
      :intensity="0.5"
      :particle-count="40"
      :enable-grid="false"
      :enable-pulse="true"
      :enable-data-flow="false"
    />
    
    <!-- 页面头部 -->
    <div class="view-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <ArrowLeftIcon />
          <span>返回主大屏</span>
        </button>
        <div class="page-title">
          <h1>消息管理中心</h1>
          <p class="page-subtitle">系统通知与用户消息统一管理</p>
        </div>
      </div>
      
      <div class="header-right">
        <div class="message-stats">
          <div class="stat-item">
            <span class="stat-label">未读消息</span>
            <span class="stat-value unread">{{ unreadCount }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">今日消息</span>
            <span class="stat-value">{{ todayCount }}</span>
          </div>
        </div>
        <button class="compose-btn" @click="showComposeModal">
          <PencilIcon />
          发送消息
        </button>
      </div>
    </div>
    
    <!-- 消息管理主体 -->
    <div class="message-content">
      <!-- 侧边栏 -->
      <div class="message-sidebar">
        <div class="sidebar-header">
          <h3>消息分类</h3>
          <button class="refresh-btn" @click="refreshMessages">
            <RefreshIcon :class="{ spinning: isRefreshing }" />
          </button>
        </div>
        
        <div class="message-categories">
          <div 
            v-for="category in messageCategories"
            :key="category.key"
            class="category-item"
            :class="{ active: selectedCategory === category.key }"
            @click="selectCategory(category.key)"
          >
            <div class="category-icon">
              <component :is="category.icon" />
            </div>
            <div class="category-info">
              <div class="category-name">{{ category.name }}</div>
              <div class="category-count">{{ category.count }}</div>
            </div>
            <div v-if="category.unread > 0" class="unread-badge">
              {{ category.unread }}
            </div>
          </div>
        </div>
        
        <!-- 快速过滤 -->
        <div class="quick-filters">
          <h4>快速过滤</h4>
          <div class="filter-buttons">
            <button 
              v-for="filter in quickFilters"
              :key="filter.key"
              class="filter-btn"
              :class="{ active: selectedFilter === filter.key }"
              @click="applyFilter(filter.key)"
            >
              {{ filter.label }}
            </button>
          </div>
        </div>
      </div>
      
      <!-- 消息列表 -->
      <div class="message-main">
        <div class="message-header">
          <div class="header-info">
            <h3>{{ getCurrentCategoryName() }}</h3>
            <span class="message-count">{{ filteredMessages.length }} 条消息</span>
          </div>
          
          <div class="header-actions">
            <div class="search-box">
              <MagnifyingGlassIcon class="search-icon" />
              <input 
                v-model="searchQuery"
                type="text" 
                placeholder="搜索消息..."
                class="search-input"
              />
            </div>
            <button class="action-btn" @click="markAllAsRead" :disabled="unreadCount === 0">
              <CheckIcon />
              全部已读
            </button>
            <button class="action-btn danger" @click="deleteSelected" :disabled="selectedMessages.length === 0">
              <TrashIcon />
              删除选中
            </button>
          </div>
        </div>
        
        <div class="message-list">
          <div class="list-header">
            <div class="select-all">
              <input 
                type="checkbox" 
                :checked="allSelected"
                @change="toggleSelectAll"
                class="checkbox"
              />
            </div>
            <div class="header-cell sender">发送者</div>
            <div class="header-cell subject">主题</div>
            <div class="header-cell time">时间</div>
            <div class="header-cell priority">优先级</div>
            <div class="header-cell actions">操作</div>
          </div>
          
          <div class="list-body">
            <div 
              v-for="message in paginatedMessages"
              :key="message.id"
              class="message-item"
              :class="{ 
                'unread': !message.isRead,
                'selected': selectedMessages.includes(message.id),
                'priority-high': message.priority === 'high',
                'priority-urgent': message.priority === 'urgent'
              }"
              @click="selectMessage(message)"
            >
              <div class="message-select">
                <input 
                  type="checkbox" 
                  :checked="selectedMessages.includes(message.id)"
                  @change="toggleMessageSelect(message.id)"
                  @click.stop
                  class="checkbox"
                />
              </div>
              <div class="message-sender">
                <div class="sender-avatar">
                  <component :is="getSenderIcon(message.senderType)" />
                </div>
                <div class="sender-info">
                  <div class="sender-name">{{ message.senderName }}</div>
                  <div class="sender-type">{{ getSenderTypeName(message.senderType) }}</div>
                </div>
              </div>
              <div class="message-subject">
                <div class="subject-text">{{ message.subject }}</div>
                <div class="subject-preview">{{ message.preview }}</div>
              </div>
              <div class="message-time">
                <div class="time-display">{{ formatTime(message.timestamp) }}</div>
                <div class="time-relative">{{ getRelativeTime(message.timestamp) }}</div>
              </div>
              <div class="message-priority">
                <div class="priority-badge" :class="message.priority">
                  {{ getPriorityText(message.priority) }}
                </div>
              </div>
              <div class="message-actions">
                <button 
                  class="action-icon"
                  @click.stop="toggleRead(message.id)"
                  :title="message.isRead ? '标记为未读' : '标记为已读'"
                >
                  <component :is="message.isRead ? EyeSlashIcon : EyeIcon" />
                </button>
                <button 
                  class="action-icon"
                  @click.stop="replyMessage(message.id)"
                  title="回复"
                >
                  <ArrowUturnLeftIcon />
                </button>
                <button 
                  class="action-icon danger"
                  @click.stop="deleteMessage(message.id)"
                  title="删除"
                >
                  <TrashIcon />
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 分页 -->
        <div class="message-pagination">
          <div class="pagination-info">
            显示 {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, filteredMessages.length) }} 
            / 共 {{ filteredMessages.length }} 条
          </div>
          <div class="pagination-controls">
            <button 
              class="page-btn"
              :disabled="currentPage === 1"
              @click="changePage(currentPage - 1)"
            >
              <ChevronLeftIcon />
            </button>
            <button 
              v-for="page in visiblePages"
              :key="page"
              class="page-btn"
              :class="{ active: page === currentPage }"
              @click="changePage(page)"
            >
              {{ page }}
            </button>
            <button 
              class="page-btn"
              :disabled="currentPage === totalPages"
              @click="changePage(currentPage + 1)"
            >
              <ChevronRightIcon />
            </button>
          </div>
        </div>
      </div>
      
      <!-- 消息详情 -->
      <div v-if="selectedMessage" class="message-detail">
        <div class="detail-header">
          <h3>消息详情</h3>
          <button class="close-detail" @click="selectedMessage = null">
            <XMarkIcon />
          </button>
        </div>
        
        <div class="detail-content">
          <div class="message-meta">
            <div class="meta-item">
              <span class="meta-label">发送者:</span>
              <span class="meta-value">{{ selectedMessage.senderName }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">时间:</span>
              <span class="meta-value">{{ formatFullTime(selectedMessage.timestamp) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">优先级:</span>
              <span class="meta-value priority" :class="selectedMessage.priority">
                {{ getPriorityText(selectedMessage.priority) }}
              </span>
            </div>
          </div>
          
          <div class="message-subject-full">
            <h4>{{ selectedMessage.subject }}</h4>
          </div>
          
          <div class="message-body">
            <div v-html="selectedMessage.content"></div>
          </div>
          
          <div class="message-attachments" v-if="selectedMessage.attachments?.length">
            <h5>附件:</h5>
            <div class="attachment-list">
              <div 
                v-for="attachment in selectedMessage.attachments"
                :key="attachment.id"
                class="attachment-item"
              >
                <DocumentIcon class="attachment-icon" />
                <span class="attachment-name">{{ attachment.name }}</span>
                <button class="download-btn">
                  <ArrowDownTrayIcon />
                </button>
              </div>
            </div>
          </div>
          
          <div class="detail-actions">
            <button class="detail-action-btn primary" @click="replyMessage(selectedMessage.id)">
              <ArrowUturnLeftIcon />
              回复
            </button>
            <button class="detail-action-btn" @click="forwardMessage(selectedMessage.id)">
              <ArrowUturnRightIcon />
              转发
            </button>
            <button class="detail-action-btn danger" @click="deleteMessage(selectedMessage.id)">
              <TrashIcon />
              删除
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 撰写消息模态框 -->
    <Transition name="modal">
      <div v-if="showCompose" class="compose-modal" @click="closeCompose">
        <div class="compose-content" @click.stop>
          <div class="compose-header">
            <h3>发送消息</h3>
            <button class="close-compose" @click="closeCompose">
              <XMarkIcon />
            </button>
          </div>
          <div class="compose-form">
            <div class="form-row">
              <label>收件人:</label>
              <select v-model="composeData.recipient" class="form-select">
                <option value="">选择收件人</option>
                <option value="all">所有用户</option>
                <option value="department">部门用户</option>
                <option value="specific">指定用户</option>
              </select>
            </div>
            <div class="form-row">
              <label>优先级:</label>
              <select v-model="composeData.priority" class="form-select">
                <option value="low">普通</option>
                <option value="normal">一般</option>
                <option value="high">重要</option>
                <option value="urgent">紧急</option>
              </select>
            </div>
            <div class="form-row">
              <label>主题:</label>
              <input v-model="composeData.subject" type="text" class="form-input" placeholder="请输入消息主题">
            </div>
            <div class="form-row">
              <label>内容:</label>
              <textarea v-model="composeData.content" class="form-textarea" rows="6" placeholder="请输入消息内容"></textarea>
            </div>
            <div class="compose-actions">
              <button class="compose-btn-action primary" @click="sendMessage">
                <PaperAirplaneIcon />
                发送
              </button>
              <button class="compose-btn-action" @click="saveDraft">
                <DocumentIcon />
                保存草稿
              </button>
              <button class="compose-btn-action" @click="closeCompose">
                取消
              </button>
            </div>
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
  PencilIcon,
  RefreshIcon,
  MagnifyingGlassIcon,
  CheckIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowUturnLeftIcon,
  ArrowUturnRightIcon,
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  DocumentIcon,
  ArrowDownTrayIcon,
  PaperAirplaneIcon,
  InboxIcon,
  ExclamationTriangleIcon,
  BellIcon,
  UserIcon,
  CogIcon
} from '@element-plus/icons-vue'
import TechBackground from '@/components/effects/TechBackground.vue'
import GlobalToast from '@/components/common/GlobalToast.vue'
import { useRouter } from 'vue-router'

// Router
const router = useRouter()
const toast = ref<InstanceType<typeof GlobalToast>>()

// 组件状态
const selectedCategory = ref('all')
const selectedFilter = ref('all')
const searchQuery = ref('')
const selectedMessages = ref<string[]>([])
const selectedMessage = ref(null)
const isRefreshing = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const showCompose = ref(false)

// 撰写消息数据
const composeData = ref({
  recipient: '',
  priority: 'normal',
  subject: '',
  content: ''
})

// 消息分类配置
const messageCategories = ref([
  { key: 'all', name: '全部消息', icon: InboxIcon, count: 156, unread: 23 },
  { key: 'system', name: '系统通知', icon: CogIcon, count: 45, unread: 12 },
  { key: 'alert', name: '健康预警', icon: ExclamationTriangleIcon, count: 28, unread: 8 },
  { key: 'notification', name: '设备通知', icon: BellIcon, count: 67, unread: 3 },
  { key: 'user', name: '用户消息', icon: UserIcon, count: 16, unread: 0 }
])

// 快速过滤配置
const quickFilters = [
  { key: 'all', label: '全部' },
  { key: 'unread', label: '未读' },
  { key: 'today', label: '今天' },
  { key: 'urgent', label: '紧急' }
]

// 模拟消息数据
const messages = ref([
  {
    id: 'msg_001',
    senderName: '健康监控系统',
    senderType: 'system',
    subject: '用户心率异常预警',
    preview: '检测到用户张三的心率持续偏高，建议立即关注...',
    content: '<p>检测到用户张三的心率在过去30分钟内持续超过100 BPM，当前心率为108 BPM。</p><p>建议立即联系用户确认身体状况，必要时安排医疗检查。</p>',
    timestamp: new Date(Date.now() - 5 * 60000),
    priority: 'urgent',
    category: 'alert',
    isRead: false,
    attachments: []
  },
  {
    id: 'msg_002',
    senderName: '设备管理系统',
    senderType: 'system',
    subject: '设备电量低警告',
    preview: '智能手环-001电量低于20%，请及时充电...',
    content: '<p>设备：智能手环-001</p><p>当前电量：12%</p><p>请提醒用户及时充电以确保数据采集的连续性。</p>',
    timestamp: new Date(Date.now() - 15 * 60000),
    priority: 'high',
    category: 'notification',
    isRead: false,
    attachments: []
  },
  {
    id: 'msg_003',
    senderName: '李医生',
    senderType: 'user',
    subject: '关于王小明的健康评估报告',
    preview: '已完成王小明的健康评估，请查看详细报告...',
    content: '<p>经过详细分析，王小明的整体健康状况良好。</p><p>建议继续保持当前的运动和饮食习惯。</p><p>下次复查时间建议在3个月后。</p>',
    timestamp: new Date(Date.now() - 60 * 60000),
    priority: 'normal',
    category: 'user',
    isRead: true,
    attachments: [
      { id: 'att_001', name: '健康评估报告.pdf', size: '2.3MB' }
    ]
  },
  {
    id: 'msg_004',
    senderName: '数据同步服务',
    senderType: 'system',
    subject: '每日数据同步完成',
    preview: '今日健康数据同步已完成，共处理3,247条记录...',
    content: '<p>同步统计：</p><ul><li>心率数据：1,156条</li><li>步数数据：892条</li><li>睡眠数据：78条</li><li>血压数据：234条</li></ul><p>所有数据同步正常。</p>',
    timestamp: new Date(Date.now() - 2 * 60 * 60000),
    priority: 'low',
    category: 'system',
    isRead: true,
    attachments: []
  },
  {
    id: 'msg_005',
    senderName: '系统管理员',
    senderType: 'system',
    subject: '系统维护通知',
    preview: '系统将于今晚23:00-01:00进行维护升级...',
    content: '<p>为了提供更好的服务，系统将于今晚23:00-01:00进行维护升级。</p><p>维护期间可能影响数据同步和实时监控功能。</p><p>请提前做好相关准备工作。</p>',
    timestamp: new Date(Date.now() - 3 * 60 * 60000),
    priority: 'high',
    category: 'system',
    isRead: false,
    attachments: []
  }
])

// 计算属性
const unreadCount = computed(() => messages.value.filter(m => !m.isRead).length)
const todayCount = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return messages.value.filter(m => m.timestamp >= today).length
})

const filteredMessages = computed(() => {
  let filtered = messages.value

  // 按分类过滤
  if (selectedCategory.value !== 'all') {
    filtered = filtered.filter(m => m.category === selectedCategory.value)
  }

  // 按快速过滤器过滤
  switch (selectedFilter.value) {
    case 'unread':
      filtered = filtered.filter(m => !m.isRead)
      break
    case 'today':
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      filtered = filtered.filter(m => m.timestamp >= today)
      break
    case 'urgent':
      filtered = filtered.filter(m => m.priority === 'urgent' || m.priority === 'high')
      break
  }

  // 按搜索查询过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(m => 
      m.subject.toLowerCase().includes(query) ||
      m.senderName.toLowerCase().includes(query) ||
      m.preview.toLowerCase().includes(query)
    )
  }

  return filtered.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
})

const paginatedMessages = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredMessages.value.slice(start, end)
})

const totalPages = computed(() => Math.ceil(filteredMessages.value.length / pageSize.value))

const visiblePages = computed(() => {
  const current = currentPage.value
  const total = totalPages.value
  const delta = 2
  const range = []
  
  for (let i = Math.max(1, current - delta); i <= Math.min(total, current + delta); i++) {
    range.push(i)
  }
  
  return range
})

const allSelected = computed(() => {
  return paginatedMessages.value.length > 0 && 
         paginatedMessages.value.every(m => selectedMessages.value.includes(m.id))
})

// 方法
const goBack = () => {
  router.push('/dashboard/main')
}

const getCurrentCategoryName = () => {
  const category = messageCategories.value.find(c => c.key === selectedCategory.value)
  return category ? category.name : '消息列表'
}

const getSenderIcon = (senderType: string) => {
  const icons = {
    system: CogIcon,
    user: UserIcon,
    device: BellIcon
  }
  return icons[senderType as keyof typeof icons] || UserIcon
}

const getSenderTypeName = (senderType: string) => {
  const typeNames = {
    system: '系统',
    user: '用户',
    device: '设备'
  }
  return typeNames[senderType as keyof typeof typeNames] || senderType
}

const getPriorityText = (priority: string) => {
  const priorityTexts = {
    low: '普通',
    normal: '一般',
    high: '重要',
    urgent: '紧急'
  }
  return priorityTexts[priority as keyof typeof priorityTexts] || priority
}

const formatTime = (time: Date) => {
  return time.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatFullTime = (time: Date) => {
  return time.toLocaleString('zh-CN')
}

const getRelativeTime = (time: Date) => {
  const now = new Date()
  const diff = now.getTime() - time.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  return `${days}天前`
}

const selectCategory = (category: string) => {
  selectedCategory.value = category
  currentPage.value = 1
}

const applyFilter = (filter: string) => {
  selectedFilter.value = filter
  currentPage.value = 1
}

const refreshMessages = async () => {
  isRefreshing.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    toast.value?.success('消息列表已刷新')
  } finally {
    isRefreshing.value = false
  }
}

const selectMessage = (message: any) => {
  selectedMessage.value = message
  if (!message.isRead) {
    toggleRead(message.id)
  }
}

const toggleMessageSelect = (messageId: string) => {
  const index = selectedMessages.value.indexOf(messageId)
  if (index > -1) {
    selectedMessages.value.splice(index, 1)
  } else {
    selectedMessages.value.push(messageId)
  }
}

const toggleSelectAll = () => {
  if (allSelected.value) {
    selectedMessages.value = []
  } else {
    selectedMessages.value = paginatedMessages.value.map(m => m.id)
  }
}

const toggleRead = (messageId: string) => {
  const message = messages.value.find(m => m.id === messageId)
  if (message) {
    message.isRead = !message.isRead
  }
}

const markAllAsRead = () => {
  messages.value.forEach(message => {
    message.isRead = true
  })
  toast.value?.success('所有消息已标记为已读')
}

const deleteSelected = () => {
  if (selectedMessages.value.length === 0) return
  
  const count = selectedMessages.value.length
  selectedMessages.value.forEach(id => {
    const index = messages.value.findIndex(m => m.id === id)
    if (index > -1) {
      messages.value.splice(index, 1)
    }
  })
  
  selectedMessages.value = []
  selectedMessage.value = null
  toast.value?.success(`已删除 ${count} 条消息`)
}

const deleteMessage = (messageId: string) => {
  const index = messages.value.findIndex(m => m.id === messageId)
  if (index > -1) {
    messages.value.splice(index, 1)
    if (selectedMessage.value?.id === messageId) {
      selectedMessage.value = null
    }
    toast.value?.success('消息已删除')
  }
}

const replyMessage = (messageId: string) => {
  const message = messages.value.find(m => m.id === messageId)
  if (message) {
    composeData.value = {
      recipient: message.senderName,
      priority: 'normal',
      subject: `回复: ${message.subject}`,
      content: ''
    }
    showCompose.value = true
  }
}

const forwardMessage = (messageId: string) => {
  toast.value?.info('转发功能开发中')
}

const changePage = (page: number) => {
  currentPage.value = page
  selectedMessages.value = []
}

const showComposeModal = () => {
  composeData.value = {
    recipient: '',
    priority: 'normal',
    subject: '',
    content: ''
  }
  showCompose.value = true
}

const closeCompose = () => {
  showCompose.value = false
}

const sendMessage = () => {
  if (!composeData.value.subject || !composeData.value.content) {
    toast.value?.error('请填写完整的消息内容')
    return
  }
  
  toast.value?.success('消息发送成功')
  closeCompose()
}

const saveDraft = () => {
  toast.value?.info('草稿已保存')
}

// 生命周期
onMounted(() => {
  console.log('消息管理页面已加载')
})
</script>

<style lang="scss" scoped>
.message-view {
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
  
  .message-stats {
    display: flex;
    gap: var(--spacing-lg);
  }
  
  .stat-item {
    text-align: center;
    
    .stat-label {
      display: block;
      font-size: var(--font-xs);
      color: var(--text-secondary);
      margin-bottom: var(--spacing-xs);
    }
    
    .stat-value {
      display: block;
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      font-family: var(--font-tech);
      
      &.unread {
        color: var(--warning);
      }
    }
  }
  
  .compose-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-lg);
    background: var(--primary-500);
    color: white;
    border: none;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all var(--duration-fast);
    font-weight: 500;
    
    &:hover {
      background: var(--primary-600);
      transform: translateY(-1px);
      box-shadow: var(--shadow-md);
    }
  }
}

// ========== 主体内容 ==========
.message-content {
  flex: 1;
  display: flex;
  position: relative;
  z-index: 1;
  overflow: hidden;
}

// ========== 侧边栏 ==========
.message-sidebar {
  width: 280px;
  background: var(--bg-card);
  border-right: 1px solid var(--border-primary);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-secondary);
  
  h3 {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  .refresh-btn {
    width: 32px;
    height: 32px;
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-sm);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    display: flex;
    align-items: center;
    justify-content: center;
    
    .spinning {
      animation: spin 1s linear infinite;
    }
    
    &:hover {
      color: var(--primary-500);
      border-color: var(--primary-500);
      background: rgba(0, 255, 157, 0.1);
    }
  }
}

.message-categories {
  flex: 1;
  padding: var(--spacing-md);
}

.category-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast);
  position: relative;
  margin-bottom: var(--spacing-sm);
  
  &:hover {
    background: var(--bg-secondary);
  }
  
  &.active {
    background: rgba(0, 255, 157, 0.2);
    color: var(--primary-500);
    
    .category-icon {
      color: var(--primary-500);
    }
  }
  
  .category-icon {
    width: 20px;
    height: 20px;
    color: var(--text-secondary);
  }
  
  .category-info {
    flex: 1;
    
    .category-name {
      font-size: var(--font-sm);
      font-weight: 500;
      color: var(--text-primary);
    }
    
    .category-count {
      font-size: var(--font-xs);
      color: var(--text-tertiary);
    }
  }
  
  .unread-badge {
    background: var(--warning);
    color: white;
    font-size: var(--font-xs);
    padding: 2px 6px;
    border-radius: var(--radius-full);
    min-width: 18px;
    text-align: center;
  }
}

.quick-filters {
  padding: var(--spacing-md);
  border-top: 1px solid var(--border-secondary);
  
  h4 {
    font-size: var(--font-sm);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
  }
  
  .filter-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-xs);
  }
  
  .filter-btn {
    padding: var(--spacing-xs) var(--spacing-sm);
    border: 1px solid var(--border-tertiary);
    border-radius: var(--radius-sm);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    font-size: var(--font-xs);
    cursor: pointer;
    transition: all var(--duration-fast);
    
    &:hover {
      color: var(--text-primary);
      border-color: var(--border-secondary);
    }
    
    &.active {
      background: var(--primary-500);
      color: white;
      border-color: var(--primary-500);
    }
  }
}

// ========== 消息列表 ==========
.message-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  backdrop-filter: blur(10px);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-secondary);
  
  .header-info {
    h3 {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 var(--spacing-xs) 0;
    }
    
    .message-count {
      font-size: var(--font-sm);
      color: var(--text-secondary);
    }
  }
  
  .header-actions {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }
  
  .search-box {
    position: relative;
    
    .search-icon {
      position: absolute;
      left: var(--spacing-sm);
      top: 50%;
      transform: translateY(-50%);
      width: 16px;
      height: 16px;
      color: var(--text-tertiary);
    }
    
    .search-input {
      padding: var(--spacing-sm) var(--spacing-sm) var(--spacing-sm) var(--spacing-xl);
      border: 1px solid var(--border-secondary);
      border-radius: var(--radius-md);
      background: var(--bg-secondary);
      color: var(--text-primary);
      width: 200px;
      
      &:focus {
        outline: none;
        border-color: var(--primary-500);
      }
      
      &::placeholder {
        color: var(--text-tertiary);
      }
    }
  }
  
  .action-btn {
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
    font-size: var(--font-sm);
    
    &:hover:not(:disabled) {
      color: var(--primary-500);
      border-color: var(--primary-500);
      background: rgba(0, 255, 157, 0.1);
    }
    
    &.danger:hover:not(:disabled) {
      color: var(--error);
      border-color: var(--error);
      background: rgba(255, 107, 107, 0.1);
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

.message-list {
  flex: 1;
  overflow-y: auto;
}

.list-header {
  display: grid;
  grid-template-columns: 40px 200px 1fr 120px 80px 100px;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-tertiary);
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-secondary);
  
  .header-cell {
    display: flex;
    align-items: center;
  }
}

.list-body {
  .message-item {
    display: grid;
    grid-template-columns: 40px 200px 1fr 120px 80px 100px;
    gap: var(--spacing-sm);
    padding: var(--spacing-md) var(--spacing-lg);
    border-bottom: 1px solid var(--border-tertiary);
    cursor: pointer;
    transition: all var(--duration-fast);
    position: relative;
    
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 3px;
      background: transparent;
      transition: background var(--duration-fast);
    }
    
    &:hover {
      background: var(--bg-secondary);
    }
    
    &.selected {
      background: rgba(0, 255, 157, 0.1);
    }
    
    &.unread {
      background: rgba(255, 255, 255, 0.02);
      
      &::before {
        background: var(--primary-500);
      }
      
      .message-subject .subject-text {
        font-weight: 600;
      }
    }
    
    &.priority-high::before {
      background: var(--warning);
    }
    
    &.priority-urgent::before {
      background: var(--error);
    }
  }
}

.message-select {
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-sender {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  
  .sender-avatar {
    width: 32px;
    height: 32px;
    border-radius: var(--radius-md);
    background: var(--bg-tertiary);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
    font-size: 16px;
  }
  
  .sender-info {
    .sender-name {
      font-size: var(--font-sm);
      font-weight: 500;
      color: var(--text-primary);
    }
    
    .sender-type {
      font-size: var(--font-xs);
      color: var(--text-tertiary);
    }
  }
}

.message-subject {
  .subject-text {
    font-size: var(--font-sm);
    color: var(--text-primary);
    margin-bottom: var(--spacing-xs);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .subject-preview {
    font-size: var(--font-xs);
    color: var(--text-tertiary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.message-time {
  text-align: center;
  
  .time-display {
    font-size: var(--font-sm);
    color: var(--text-primary);
    font-family: var(--font-tech);
  }
  
  .time-relative {
    font-size: var(--font-xs);
    color: var(--text-tertiary);
  }
}

.message-priority {
  display: flex;
  align-items: center;
  justify-content: center;
  
  .priority-badge {
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
    font-size: var(--font-xs);
    font-weight: 500;
    
    &.low {
      background: rgba(158, 158, 158, 0.2);
      color: #9e9e9e;
    }
    
    &.normal {
      background: rgba(33, 150, 243, 0.2);
      color: #2196f3;
    }
    
    &.high {
      background: rgba(255, 152, 0, 0.2);
      color: #ff9800;
    }
    
    &.urgent {
      background: rgba(244, 67, 54, 0.2);
      color: #f44336;
    }
  }
}

.message-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  
  .action-icon {
    width: 24px;
    height: 24px;
    border: none;
    background: none;
    color: var(--text-tertiary);
    cursor: pointer;
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--duration-fast);
    
    &:hover {
      background: var(--bg-tertiary);
      color: var(--primary-500);
    }
    
    &.danger:hover {
      color: var(--error);
    }
  }
}

// ========== 分页 ==========
.message-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--border-secondary);
  
  .pagination-info {
    font-size: var(--font-sm);
    color: var(--text-secondary);
  }
  
  .pagination-controls {
    display: flex;
    gap: var(--spacing-xs);
  }
  
  .page-btn {
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
    font-size: var(--font-sm);
    
    &:hover:not(:disabled) {
      color: var(--primary-500);
      border-color: var(--primary-500);
      background: rgba(0, 255, 157, 0.1);
    }
    
    &.active {
      background: var(--primary-500);
      color: white;
      border-color: var(--primary-500);
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

// ========== 消息详情 ==========
.message-detail {
  width: 400px;
  background: var(--bg-card);
  border-left: 1px solid var(--border-primary);
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
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
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

.detail-content {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
}

.message-meta {
  margin-bottom: var(--spacing-lg);
  
  .meta-item {
    display: flex;
    margin-bottom: var(--spacing-sm);
    
    .meta-label {
      width: 60px;
      font-size: var(--font-sm);
      color: var(--text-secondary);
    }
    
    .meta-value {
      flex: 1;
      font-size: var(--font-sm);
      color: var(--text-primary);
      
      &.priority {
        &.urgent { color: var(--error); }
        &.high { color: var(--warning); }
        &.normal { color: var(--info); }
        &.low { color: var(--text-secondary); }
      }
    }
  }
}

.message-subject-full {
  margin-bottom: var(--spacing-lg);
  
  h4 {
    font-size: var(--font-md);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
}

.message-body {
  margin-bottom: var(--spacing-lg);
  font-size: var(--font-sm);
  color: var(--text-primary);
  line-height: var(--leading-relaxed);
}

.message-attachments {
  margin-bottom: var(--spacing-lg);
  
  h5 {
    font-size: var(--font-sm);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-sm) 0;
  }
  
  .attachment-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }
  
  .attachment-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm);
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    
    .attachment-icon {
      width: 16px;
      height: 16px;
      color: var(--text-secondary);
    }
    
    .attachment-name {
      flex: 1;
      font-size: var(--font-sm);
      color: var(--text-primary);
    }
    
    .download-btn {
      width: 24px;
      height: 24px;
      border: none;
      background: none;
      color: var(--text-secondary);
      cursor: pointer;
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--duration-fast);
      
      &:hover {
        background: var(--bg-tertiary);
        color: var(--primary-500);
      }
    }
  }
}

.detail-actions {
  display: flex;
  gap: var(--spacing-sm);
  
  .detail-action-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    font-size: var(--font-sm);
    
    &:hover {
      color: var(--primary-500);
      border-color: var(--primary-500);
      background: rgba(0, 255, 157, 0.1);
    }
    
    &.primary {
      background: var(--primary-500);
      color: white;
      border-color: var(--primary-500);
      
      &:hover {
        background: var(--primary-600);
      }
    }
    
    &.danger:hover {
      color: var(--error);
      border-color: var(--error);
      background: rgba(255, 107, 107, 0.1);
    }
  }
}

// ========== 撰写消息模态框 ==========
.compose-modal {
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

.compose-content {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-xl);
  width: 600px;
  max-width: 90vw;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: var(--shadow-2xl);
  backdrop-filter: blur(10px);
}

.compose-header {
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
  
  .close-compose {
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

.compose-form {
  padding: var(--spacing-lg);
  
  .form-row {
    margin-bottom: var(--spacing-md);
    
    label {
      display: block;
      font-size: var(--font-sm);
      font-weight: 500;
      color: var(--text-primary);
      margin-bottom: var(--spacing-sm);
    }
    
    .form-select,
    .form-input,
    .form-textarea {
      width: 100%;
      padding: var(--spacing-sm);
      border: 1px solid var(--border-secondary);
      border-radius: var(--radius-md);
      background: var(--bg-secondary);
      color: var(--text-primary);
      font-size: var(--font-sm);
      
      &:focus {
        outline: none;
        border-color: var(--primary-500);
      }
      
      &::placeholder {
        color: var(--text-tertiary);
      }
    }
    
    .form-textarea {
      resize: vertical;
      min-height: 120px;
    }
  }
  
  .compose-actions {
    display: flex;
    gap: var(--spacing-sm);
    justify-content: flex-end;
    
    .compose-btn-action {
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
      font-size: var(--font-sm);
      
      &:hover {
        color: var(--primary-500);
        border-color: var(--primary-500);
        background: rgba(0, 255, 157, 0.1);
      }
      
      &.primary {
        background: var(--primary-500);
        color: white;
        border-color: var(--primary-500);
        
        &:hover {
          background: var(--primary-600);
        }
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
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// ========== 响应式设计 ==========
@media (max-width: 1024px) {
  .message-content {
    flex-direction: column;
  }
  
  .message-sidebar {
    width: auto;
    height: 200px;
    border-right: none;
    border-bottom: 1px solid var(--border-primary);
  }
  
  .message-detail {
    width: auto;
    height: 300px;
    border-left: none;
    border-top: 1px solid var(--border-primary);
  }
}

@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .list-header,
  .message-item {
    grid-template-columns: 1fr;
    gap: var(--spacing-xs);
  }
  
  .message-sidebar {
    height: auto;
  }
  
  .message-detail {
    height: auto;
  }
}

@media (prefers-reduced-motion: reduce) {
  .category-item,
  .message-item,
  .action-btn {
    transition: none;
  }
  
  .spinning {
    animation: none;
  }
}
</style>