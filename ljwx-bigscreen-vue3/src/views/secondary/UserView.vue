<template>
  <div class="user-view">
    <!-- 3D背景效果 -->
    <TechBackground 
      :intensity="0.5"
      :particle-count="50"
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
          <h1>用户管理中心</h1>
          <p class="page-subtitle">用户信息管理与权限控制系统</p>
        </div>
      </div>
      
      <div class="header-right">
        <div class="user-stats">
          <div class="stat-item">
            <span class="stat-label">总用户数</span>
            <span class="stat-value">{{ totalUsers }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">活跃用户</span>
            <span class="stat-value active">{{ activeUsers }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">在线用户</span>
            <span class="stat-value online">{{ onlineUsers }}</span>
          </div>
        </div>
        <button class="add-user-btn" @click="showAddUserModal">
          <PlusIcon />
          添加用户
        </button>
      </div>
    </div>
    
    <!-- 用户管理主体 -->
    <div class="user-content">
      <!-- 筛选和搜索 -->
      <div class="filter-section">
        <div class="filter-left">
          <div class="search-box">
            <MagnifyingGlassIcon class="search-icon" />
            <input 
              v-model="searchQuery"
              type="text" 
              placeholder="搜索用户姓名、部门、手机号..."
              class="search-input"
            />
          </div>
          <div class="filter-controls">
            <select v-model="selectedDepartment" class="filter-select">
              <option value="">全部部门</option>
              <option v-for="dept in departments" :key="dept" :value="dept">
                {{ dept }}
              </option>
            </select>
            <select v-model="selectedRole" class="filter-select">
              <option value="">全部角色</option>
              <option v-for="role in roles" :key="role.key" :value="role.key">
                {{ role.name }}
              </option>
            </select>
            <select v-model="selectedStatus" class="filter-select">
              <option value="">全部状态</option>
              <option value="active">活跃</option>
              <option value="inactive">非活跃</option>
              <option value="locked">已锁定</option>
            </select>
          </div>
        </div>
        <div class="filter-right">
          <button class="filter-btn" @click="resetFilters">
            <RefreshIcon />
            重置筛选
          </button>
          <button class="filter-btn" @click="exportUsers">
            <DocumentArrowDownIcon />
            导出数据
          </button>
        </div>
      </div>
      
      <!-- 用户表格 -->
      <div class="user-table-section">
        <div class="table-header">
          <div class="batch-actions">
            <input 
              type="checkbox" 
              :checked="allSelected"
              @change="toggleSelectAll"
              class="batch-checkbox"
            />
            <span class="selected-count">已选择 {{ selectedUsers.length }} 用户</span>
            <div class="batch-buttons" v-if="selectedUsers.length > 0">
              <button class="batch-btn" @click="batchActivate">
                <CheckIcon />
                批量激活
              </button>
              <button class="batch-btn" @click="batchDeactivate">
                <XMarkIcon />
                批量停用
              </button>
              <button class="batch-btn danger" @click="batchDelete">
                <TrashIcon />
                批量删除
              </button>
            </div>
          </div>
          <div class="table-pagination-info">
            显示 {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, filteredUsers.length) }} 
            / 共 {{ filteredUsers.length }} 条
          </div>
        </div>
        
        <div class="user-table">
          <div class="table-head">
            <div class="table-row">
              <div class="table-cell checkbox">
                <input 
                  type="checkbox" 
                  :checked="allSelected"
                  @change="toggleSelectAll"
                  class="checkbox-input"
                />
              </div>
              <div class="table-cell avatar">头像</div>
              <div class="table-cell name">姓名</div>
              <div class="table-cell department">部门</div>
              <div class="table-cell role">角色</div>
              <div class="table-cell phone">手机号</div>
              <div class="table-cell status">状态</div>
              <div class="table-cell last-login">最后登录</div>
              <div class="table-cell actions">操作</div>
            </div>
          </div>
          
          <div class="table-body">
            <div 
              v-for="user in paginatedUsers"
              :key="user.id"
              class="table-row"
              :class="{ selected: selectedUsers.includes(user.id) }"
            >
              <div class="table-cell checkbox">
                <input 
                  type="checkbox" 
                  :checked="selectedUsers.includes(user.id)"
                  @change="toggleUserSelect(user.id)"
                  class="checkbox-input"
                />
              </div>
              <div class="table-cell avatar">
                <div class="user-avatar">
                  <img v-if="user.avatar" :src="user.avatar" :alt="user.name" />
                  <UserIcon v-else />
                  <div class="online-indicator" v-if="user.online"></div>
                </div>
              </div>
              <div class="table-cell name">
                <div class="user-name">{{ user.name }}</div>
                <div class="user-id">ID: {{ user.id }}</div>
              </div>
              <div class="table-cell department">{{ user.department }}</div>
              <div class="table-cell role">
                <div class="role-badge" :class="user.role">
                  {{ getRoleName(user.role) }}
                </div>
              </div>
              <div class="table-cell phone">{{ user.phone }}</div>
              <div class="table-cell status">
                <div class="status-badge" :class="user.status">
                  {{ getStatusText(user.status) }}
                </div>
              </div>
              <div class="table-cell last-login">
                <div class="login-time">{{ formatTime(user.lastLogin) }}</div>
                <div class="login-from">{{ user.lastLoginFrom }}</div>
              </div>
              <div class="table-cell actions">
                <div class="action-buttons">
                  <button 
                    class="action-btn"
                    @click="viewUser(user)"
                    title="查看详情"
                  >
                    <EyeIcon />
                  </button>
                  <button 
                    class="action-btn"
                    @click="editUser(user)"
                    title="编辑用户"
                  >
                    <PencilIcon />
                  </button>
                  <button 
                    class="action-btn"
                    @click="resetPassword(user)"
                    title="重置密码"
                  >
                    <KeyIcon />
                  </button>
                  <button 
                    class="action-btn danger"
                    @click="deleteUser(user)"
                    title="删除用户"
                  >
                    <TrashIcon />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 分页 -->
        <div class="table-pagination">
          <div class="pagination-info">
            每页显示
            <select v-model="pageSize" @change="currentPage = 1" class="page-size-select">
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
            条
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
    </div>
    
    <!-- 用户详情模态框 -->
    <Transition name="modal">
      <div v-if="showUserDetail" class="user-detail-modal" @click="closeUserDetail">
        <div class="detail-content" @click.stop>
          <div class="detail-header">
            <h3>用户详情</h3>
            <button class="close-detail" @click="closeUserDetail">
              <XMarkIcon />
            </button>
          </div>
          
          <div class="detail-body" v-if="selectedUser">
            <div class="user-profile">
              <div class="profile-avatar">
                <img v-if="selectedUser.avatar" :src="selectedUser.avatar" :alt="selectedUser.name" />
                <UserIcon v-else />
              </div>
              <div class="profile-info">
                <h2>{{ selectedUser.name }}</h2>
                <p class="user-title">{{ selectedUser.department }} - {{ getRoleName(selectedUser.role) }}</p>
                <div class="profile-status">
                  <div class="status-badge" :class="selectedUser.status">
                    {{ getStatusText(selectedUser.status) }}
                  </div>
                  <div class="online-status" v-if="selectedUser.online">
                    <div class="online-dot"></div>
                    <span>在线</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="user-details">
              <div class="detail-section">
                <h4>基本信息</h4>
                <div class="detail-grid">
                  <div class="detail-item">
                    <span class="detail-label">用户ID:</span>
                    <span class="detail-value">{{ selectedUser.id }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">手机号:</span>
                    <span class="detail-value">{{ selectedUser.phone }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">邮箱:</span>
                    <span class="detail-value">{{ selectedUser.email }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">创建时间:</span>
                    <span class="detail-value">{{ formatTime(selectedUser.createdAt) }}</span>
                  </div>
                </div>
              </div>
              
              <div class="detail-section">
                <h4>登录信息</h4>
                <div class="detail-grid">
                  <div class="detail-item">
                    <span class="detail-label">最后登录:</span>
                    <span class="detail-value">{{ formatTime(selectedUser.lastLogin) }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">登录地点:</span>
                    <span class="detail-value">{{ selectedUser.lastLoginFrom }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">登录次数:</span>
                    <span class="detail-value">{{ selectedUser.loginCount }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">设备信息:</span>
                    <span class="detail-value">{{ selectedUser.deviceInfo }}</span>
                  </div>
                </div>
              </div>
              
              <div class="detail-section">
                <h4>权限信息</h4>
                <div class="permissions-list">
                  <div 
                    v-for="permission in selectedUser.permissions"
                    :key="permission"
                    class="permission-item"
                  >
                    <CheckCircleIcon class="permission-icon" />
                    <span>{{ permission }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="detail-actions">
            <button class="detail-action-btn primary" @click="editUser(selectedUser)">
              <PencilIcon />
              编辑用户
            </button>
            <button class="detail-action-btn" @click="resetPassword(selectedUser)">
              <KeyIcon />
              重置密码
            </button>
            <button class="detail-action-btn warning" @click="toggleUserStatus(selectedUser)">
              <component :is="selectedUser.status === 'active' ? StopIcon : PlayIcon" />
              {{ selectedUser.status === 'active' ? '停用用户' : '激活用户' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
    
    <!-- 添加/编辑用户模态框 -->
    <Transition name="modal">
      <div v-if="showUserForm" class="user-form-modal" @click="closeUserForm">
        <div class="form-content" @click.stop>
          <div class="form-header">
            <h3>{{ isEditMode ? '编辑用户' : '添加用户' }}</h3>
            <button class="close-form" @click="closeUserForm">
              <XMarkIcon />
            </button>
          </div>
          
          <div class="form-body">
            <form @submit.prevent="saveUser">
              <div class="form-row">
                <label>姓名:</label>
                <input v-model="userForm.name" type="text" class="form-input" required>
              </div>
              <div class="form-row">
                <label>手机号:</label>
                <input v-model="userForm.phone" type="tel" class="form-input" required>
              </div>
              <div class="form-row">
                <label>邮箱:</label>
                <input v-model="userForm.email" type="email" class="form-input" required>
              </div>
              <div class="form-row">
                <label>部门:</label>
                <select v-model="userForm.department" class="form-select" required>
                  <option value="">请选择部门</option>
                  <option v-for="dept in departments" :key="dept" :value="dept">
                    {{ dept }}
                  </option>
                </select>
              </div>
              <div class="form-row">
                <label>角色:</label>
                <select v-model="userForm.role" class="form-select" required>
                  <option value="">请选择角色</option>
                  <option v-for="role in roles" :key="role.key" :value="role.key">
                    {{ role.name }}
                  </option>
                </select>
              </div>
              <div class="form-actions">
                <button type="button" class="form-btn" @click="closeUserForm">取消</button>
                <button type="submit" class="form-btn primary">{{ isEditMode ? '更新' : '添加' }}</button>
              </div>
            </form>
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
  PlusIcon,
  MagnifyingGlassIcon,
  RefreshIcon,
  DocumentArrowDownIcon,
  CheckIcon,
  XMarkIcon,
  TrashIcon,
  UserIcon,
  EyeIcon,
  PencilIcon,
  KeyIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CheckCircleIcon,
  StopIcon,
  PlayIcon
} from '@element-plus/icons-vue'
import TechBackground from '@/components/effects/TechBackground.vue'
import GlobalToast from '@/components/common/GlobalToast.vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

// Store and router
const userStore = useUserStore()
const router = useRouter()
const toast = ref<InstanceType<typeof GlobalToast>>()

// 组件状态
const searchQuery = ref('')
const selectedDepartment = ref('')
const selectedRole = ref('')
const selectedStatus = ref('')
const selectedUsers = ref<string[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const showUserDetail = ref(false)
const showUserForm = ref(false)
const selectedUser = ref(null)
const isEditMode = ref(false)

// 表单数据
const userForm = ref({
  name: '',
  phone: '',
  email: '',
  department: '',
  role: ''
})

// 基础数据
const departments = ['技术部', '市场部', '财务部', '人事部', '运营部', '客服部']
const roles = [
  { key: 'admin', name: '管理员' },
  { key: 'manager', name: '经理' },
  { key: 'employee', name: '员工' },
  { key: 'guest', name: '访客' }
]

// 模拟用户数据
const users = ref([
  {
    id: 'user_001',
    name: '张三',
    department: '技术部',
    role: 'admin',
    phone: '13800138001',
    email: 'zhangsan@company.com',
    status: 'active',
    online: true,
    lastLogin: new Date(Date.now() - 2 * 60000),
    lastLoginFrom: '北京',
    avatar: '',
    createdAt: new Date('2023-01-15'),
    loginCount: 245,
    deviceInfo: 'Chrome 118.0.0.0',
    permissions: ['用户管理', '系统设置', '数据导出', '报表查看']
  },
  {
    id: 'user_002',
    name: '李四',
    department: '市场部',
    role: 'manager',
    phone: '13800138002',
    email: 'lisi@company.com',
    status: 'active',
    online: false,
    lastLogin: new Date(Date.now() - 30 * 60000),
    lastLoginFrom: '上海',
    avatar: '',
    createdAt: new Date('2023-02-20'),
    loginCount: 189,
    deviceInfo: 'Safari 17.0',
    permissions: ['团队管理', '数据查看', '报表查看']
  },
  {
    id: 'user_003',
    name: '王五',
    department: '财务部',
    role: 'employee',
    phone: '13800138003',
    email: 'wangwu@company.com',
    status: 'inactive',
    online: false,
    lastLogin: new Date(Date.now() - 7 * 24 * 60 * 60000),
    lastLoginFrom: '广州',
    avatar: '',
    createdAt: new Date('2023-03-10'),
    loginCount: 67,
    deviceInfo: 'Edge 118.0.1938.62',
    permissions: ['数据查看']
  },
  {
    id: 'user_004',
    name: '赵六',
    department: '人事部',
    role: 'manager',
    phone: '13800138004',
    email: 'zhaoliu@company.com',
    status: 'locked',
    online: false,
    lastLogin: new Date(Date.now() - 15 * 24 * 60 * 60000),
    lastLoginFrom: '深圳',
    avatar: '',
    createdAt: new Date('2023-01-25'),
    loginCount: 123,
    deviceInfo: 'Firefox 119.0',
    permissions: ['员工管理', '数据查看']
  }
])

// 计算属性
const totalUsers = computed(() => users.value.length)
const activeUsers = computed(() => users.value.filter(u => u.status === 'active').length)
const onlineUsers = computed(() => users.value.filter(u => u.online).length)

const filteredUsers = computed(() => {
  let filtered = users.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(user => 
      user.name.toLowerCase().includes(query) ||
      user.department.toLowerCase().includes(query) ||
      user.phone.includes(query) ||
      user.email.toLowerCase().includes(query)
    )
  }

  // 部门过滤
  if (selectedDepartment.value) {
    filtered = filtered.filter(user => user.department === selectedDepartment.value)
  }

  // 角色过滤
  if (selectedRole.value) {
    filtered = filtered.filter(user => user.role === selectedRole.value)
  }

  // 状态过滤
  if (selectedStatus.value) {
    filtered = filtered.filter(user => user.status === selectedStatus.value)
  }

  return filtered
})

const paginatedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredUsers.value.slice(start, end)
})

const totalPages = computed(() => Math.ceil(filteredUsers.value.length / pageSize.value))

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
  return paginatedUsers.value.length > 0 && 
         paginatedUsers.value.every(user => selectedUsers.value.includes(user.id))
})

// 方法
const goBack = () => {
  router.push('/dashboard/main')
}

const getRoleName = (roleKey: string) => {
  const role = roles.find(r => r.key === roleKey)
  return role ? role.name : roleKey
}

const getStatusText = (status: string) => {
  const statusMap = {
    active: '活跃',
    inactive: '非活跃',
    locked: '已锁定'
  }
  return statusMap[status as keyof typeof statusMap] || status
}

const formatTime = (time: Date) => {
  return time.toLocaleString('zh-CN')
}

const resetFilters = () => {
  searchQuery.value = ''
  selectedDepartment.value = ''
  selectedRole.value = ''
  selectedStatus.value = ''
  currentPage.value = 1
}

const exportUsers = () => {
  toast.value?.info('用户数据导出功能开发中')
}

const toggleSelectAll = () => {
  if (allSelected.value) {
    selectedUsers.value = []
  } else {
    selectedUsers.value = paginatedUsers.value.map(user => user.id)
  }
}

const toggleUserSelect = (userId: string) => {
  const index = selectedUsers.value.indexOf(userId)
  if (index > -1) {
    selectedUsers.value.splice(index, 1)
  } else {
    selectedUsers.value.push(userId)
  }
}

const batchActivate = () => {
  selectedUsers.value.forEach(userId => {
    const user = users.value.find(u => u.id === userId)
    if (user) user.status = 'active'
  })
  selectedUsers.value = []
  toast.value?.success(`已激活 ${selectedUsers.value.length} 个用户`)
}

const batchDeactivate = () => {
  selectedUsers.value.forEach(userId => {
    const user = users.value.find(u => u.id === userId)
    if (user) user.status = 'inactive'
  })
  const count = selectedUsers.value.length
  selectedUsers.value = []
  toast.value?.success(`已停用 ${count} 个用户`)
}

const batchDelete = () => {
  if (confirm(`确认删除选中的 ${selectedUsers.value.length} 个用户吗？`)) {
    const count = selectedUsers.value.length
    selectedUsers.value.forEach(userId => {
      const index = users.value.findIndex(u => u.id === userId)
      if (index > -1) users.value.splice(index, 1)
    })
    selectedUsers.value = []
    toast.value?.success(`已删除 ${count} 个用户`)
  }
}

const changePage = (page: number) => {
  currentPage.value = page
  selectedUsers.value = []
}

const viewUser = (user: any) => {
  selectedUser.value = user
  showUserDetail.value = true
}

const editUser = (user: any) => {
  userForm.value = {
    name: user.name,
    phone: user.phone,
    email: user.email,
    department: user.department,
    role: user.role
  }
  selectedUser.value = user
  isEditMode.value = true
  showUserForm.value = true
  showUserDetail.value = false
}

const deleteUser = (user: any) => {
  if (confirm(`确认删除用户 ${user.name} 吗？`)) {
    const index = users.value.findIndex(u => u.id === user.id)
    if (index > -1) {
      users.value.splice(index, 1)
      toast.value?.success(`已删除用户 ${user.name}`)
    }
  }
}

const resetPassword = (user: any) => {
  if (confirm(`确认重置用户 ${user.name} 的密码吗？`)) {
    toast.value?.success(`已重置用户 ${user.name} 的密码`)
  }
}

const toggleUserStatus = (user: any) => {
  if (user.status === 'active') {
    user.status = 'inactive'
    toast.value?.success(`已停用用户 ${user.name}`)
  } else {
    user.status = 'active'
    toast.value?.success(`已激活用户 ${user.name}`)
  }
}

const showAddUserModal = () => {
  userForm.value = {
    name: '',
    phone: '',
    email: '',
    department: '',
    role: ''
  }
  isEditMode.value = false
  showUserForm.value = true
}

const closeUserDetail = () => {
  showUserDetail.value = false
  selectedUser.value = null
}

const closeUserForm = () => {
  showUserForm.value = false
  selectedUser.value = null
  isEditMode.value = false
}

const saveUser = () => {
  if (isEditMode.value && selectedUser.value) {
    // 编辑用户
    Object.assign(selectedUser.value, userForm.value)
    toast.value?.success(`已更新用户 ${userForm.value.name}`)
  } else {
    // 添加用户
    const newUser = {
      id: `user_${Date.now()}`,
      ...userForm.value,
      status: 'active',
      online: false,
      lastLogin: new Date(),
      lastLoginFrom: '未知',
      avatar: '',
      createdAt: new Date(),
      loginCount: 0,
      deviceInfo: '未知',
      permissions: ['数据查看']
    }
    users.value.unshift(newUser)
    toast.value?.success(`已添加用户 ${userForm.value.name}`)
  }
  closeUserForm()
}

// 生命周期
onMounted(() => {
  console.log('用户管理页面已加载')
})
</script>

<style lang="scss" scoped>
.user-view {
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

.user-stats {
  display: flex;
  gap: var(--spacing-lg);
  
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
      
      &.active {
        color: var(--primary-500);
      }
      
      &.online {
        color: var(--success);
      }
    }
  }
}

.add-user-btn {
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
  
  &:hover {
    background: var(--primary-600);
    transform: translateY(-1px);
  }
}

// ========== 主体内容 ==========
.user-content {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

// ========== 筛选区域 ==========
.filter-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  backdrop-filter: blur(10px);
}

.filter-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  flex: 1;
}

.search-box {
  position: relative;
  width: 300px;
  
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
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-sm) var(--spacing-sm) var(--spacing-xl);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-primary);
    
    &:focus {
      outline: none;
      border-color: var(--primary-500);
    }
    
    &::placeholder {
      color: var(--text-tertiary);
    }
  }
}

.filter-controls {
  display: flex;
  gap: var(--spacing-md);
  
  .filter-select {
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

.filter-right {
  display: flex;
  gap: var(--spacing-sm);
}

.filter-btn {
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
  
  &:hover {
    color: var(--primary-500);
    border-color: var(--primary-500);
    background: rgba(0, 255, 157, 0.1);
  }
}

// ========== 用户表格 ==========
.user-table-section {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-secondary);
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  
  .batch-checkbox {
    margin-right: var(--spacing-sm);
  }
  
  .selected-count {
    font-size: var(--font-sm);
    color: var(--text-secondary);
  }
  
  .batch-buttons {
    display: flex;
    gap: var(--spacing-sm);
  }
  
  .batch-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-sm);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    font-size: var(--font-sm);
    
    &:hover {
      color: var(--primary-500);
      border-color: var(--primary-500);
    }
    
    &.danger:hover {
      color: var(--error);
      border-color: var(--error);
    }
  }
}

.table-pagination-info {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.user-table {
  flex: 1;
  overflow-y: auto;
}

.table-head {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-secondary);
}

.table-row {
  display: grid;
  grid-template-columns: 40px 60px 150px 120px 100px 140px 100px 150px 120px;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  align-items: center;
  border-bottom: 1px solid var(--border-tertiary);
  transition: all var(--duration-fast);
  
  &:hover {
    background: var(--bg-secondary);
  }
  
  &.selected {
    background: rgba(0, 255, 157, 0.1);
  }
}

.table-cell {
  display: flex;
  align-items: center;
  font-size: var(--font-sm);
  
  &.checkbox {
    justify-content: center;
  }
  
  &.avatar {
    justify-content: center;
  }
  
  &.actions {
    justify-content: center;
  }
}

.checkbox-input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.user-avatar {
  position: relative;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  overflow: hidden;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .online-indicator {
    position: absolute;
    top: -2px;
    right: -2px;
    width: 10px;
    height: 10px;
    background: var(--success);
    border: 2px solid var(--bg-card);
    border-radius: 50%;
  }
}

.user-name {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.user-id {
  font-size: var(--font-xs);
  color: var(--text-tertiary);
}

.role-badge,
.status-badge {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-xs);
  font-weight: 500;
  
  &.admin {
    background: rgba(255, 71, 87, 0.2);
    color: #ff4757;
  }
  
  &.manager {
    background: rgba(255, 167, 38, 0.2);
    color: #ffa726;
  }
  
  &.employee {
    background: rgba(66, 165, 245, 0.2);
    color: #42a5f5;
  }
  
  &.guest {
    background: rgba(158, 158, 158, 0.2);
    color: #9e9e9e;
  }
  
  &.active {
    background: rgba(102, 187, 106, 0.2);
    color: #66bb6a;
  }
  
  &.inactive {
    background: rgba(158, 158, 158, 0.2);
    color: #9e9e9e;
  }
  
  &.locked {
    background: rgba(244, 67, 54, 0.2);
    color: #f44336;
  }
}

.login-time {
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.login-from {
  font-size: var(--font-xs);
  color: var(--text-tertiary);
}

.action-buttons {
  display: flex;
  gap: var(--spacing-xs);
}

.action-btn {
  width: 24px;
  height: 24px;
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

// ========== 分页 ==========
.table-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--border-secondary);
}

.pagination-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-sm);
  color: var(--text-secondary);
  
  .page-size-select {
    padding: var(--spacing-xs);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-sm);
    background: var(--bg-secondary);
    color: var(--text-primary);
  }
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

// ========== 用户详情模态框 ==========
.user-detail-modal,
.user-form-modal {
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

.detail-content,
.form-content {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-xl);
  width: 600px;
  max-width: 90vw;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: var(--shadow-2xl);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
}

.detail-header,
.form-header {
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
}

.close-detail,
.close-form {
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

.detail-body,
.form-body {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
}

.user-profile {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
  
  .profile-avatar {
    width: 80px;
    height: 80px;
    border-radius: var(--radius-lg);
    background: var(--bg-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
    font-size: 32px;
    overflow: hidden;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
  
  .profile-info {
    flex: 1;
    
    h2 {
      font-size: var(--font-xl);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 var(--spacing-sm) 0;
    }
    
    .user-title {
      font-size: var(--font-md);
      color: var(--text-secondary);
      margin: 0 0 var(--spacing-md) 0;
    }
    
    .profile-status {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
    }
    
    .online-status {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      font-size: var(--font-sm);
      color: var(--success);
      
      .online-dot {
        width: 8px;
        height: 8px;
        background: var(--success);
        border-radius: 50%;
      }
    }
  }
}

.user-details {
  .detail-section {
    margin-bottom: var(--spacing-xl);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 var(--spacing-md) 0;
    }
  }
  
  .detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-md);
  }
  
  .detail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .detail-label {
      font-size: var(--font-sm);
      color: var(--text-secondary);
    }
    
    .detail-value {
      font-size: var(--font-sm);
      color: var(--text-primary);
      font-family: var(--font-tech);
    }
  }
}

.permissions-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  
  .permission-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--bg-secondary);
    border-radius: var(--radius-sm);
    font-size: var(--font-sm);
    color: var(--text-primary);
    
    .permission-icon {
      width: 14px;
      height: 14px;
      color: var(--success);
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
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-md);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--duration-fast);
    
    &:hover {
      color: var(--primary-500);
      border-color: var(--primary-500);
    }
    
    &.primary {
      background: var(--primary-500);
      color: white;
      border-color: var(--primary-500);
      
      &:hover {
        background: var(--primary-600);
      }
    }
    
    &.warning:hover {
      color: var(--warning);
      border-color: var(--warning);
    }
  }
}

// ========== 表单 ==========
.form-row {
  margin-bottom: var(--spacing-lg);
  
  label {
    display: block;
    font-size: var(--font-sm);
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: var(--spacing-sm);
  }
  
  .form-input,
  .form-select {
    width: 100%;
    padding: var(--spacing-sm);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-primary);
    
    &:focus {
      outline: none;
      border-color: var(--primary-500);
    }
  }
}

.form-actions {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;
  
  .form-btn {
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
@media (max-width: 1024px) {
  .filter-section {
    flex-direction: column;
    gap: var(--spacing-lg);
    align-items: stretch;
  }
  
  .filter-left {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .search-box {
    width: 100%;
  }
  
  .table-row {
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }
  
  .table-cell {
    justify-content: space-between;
    
    &::before {
      content: attr(data-label);
      font-weight: 500;
      color: var(--text-secondary);
    }
  }
}

@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .user-stats {
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }
  
  .detail-content,
  .form-content {
    width: 95vw;
    height: 90vh;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>