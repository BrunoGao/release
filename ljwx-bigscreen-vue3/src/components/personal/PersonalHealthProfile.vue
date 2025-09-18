<template>
  <div class="personal-health-profile">
    <div class="profile-header">
      <div class="title-section">
        <el-icon class="header-icon">
          <User />
        </el-icon>
        <h3 class="profile-title">{{ title }}</h3>
      </div>
      
      <div class="profile-actions">
        <el-button size="small" @click="editProfile">
          <el-icon><Edit /></el-icon>
          编辑资料
        </el-button>
        <el-button size="small" @click="exportProfile">
          <el-icon><Download /></el-icon>
          导出档案
        </el-button>
      </div>
    </div>
    
    <!-- 用户基本信息 -->
    <div class="user-basic-info">
      <div class="info-card main-info">
        <div class="user-avatar">
          <el-avatar :size="80" :src="userProfile.avatar">
            <el-icon><User /></el-icon>
          </el-avatar>
          <div class="avatar-actions">
            <el-button size="small" circle @click="changeAvatar">
              <el-icon><Camera /></el-icon>
            </el-button>
          </div>
        </div>
        
        <div class="user-details">
          <div class="user-name">{{ userProfile.name }}</div>
          <div class="user-id">ID: {{ userProfile.id }}</div>
          <div class="user-status" :class="userProfile.healthStatus">
            <span class="status-indicator"></span>
            <span class="status-text">{{ getHealthStatusText() }}</span>
          </div>
        </div>
        
        <div class="profile-stats">
          <div class="stat-item">
            <div class="stat-value">{{ userProfile.age }}</div>
            <div class="stat-label">年龄</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ userProfile.height }}cm</div>
            <div class="stat-label">身高</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ userProfile.weight }}kg</div>
            <div class="stat-label">体重</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ calculateBMI() }}</div>
            <div class="stat-label">BMI</div>
          </div>
        </div>
      </div>
      
      <div class="info-card contact-info">
        <div class="card-header">
          <el-icon><Phone /></el-icon>
          <span>联系信息</span>
        </div>
        <div class="contact-details">
          <div class="contact-item">
            <span class="contact-label">手机号码</span>
            <span class="contact-value">{{ userProfile.phone }}</span>
          </div>
          <div class="contact-item">
            <span class="contact-label">电子邮箱</span>
            <span class="contact-value">{{ userProfile.email }}</span>
          </div>
          <div class="contact-item">
            <span class="contact-label">紧急联系人</span>
            <span class="contact-value">{{ userProfile.emergencyContact }}</span>
          </div>
          <div class="contact-item">
            <span class="contact-label">紧急联系电话</span>
            <span class="contact-value">{{ userProfile.emergencyPhone }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 健康档案 -->
    <div class="health-records">
      <div class="records-header">
        <h4>健康档案</h4>
        <el-button-group size="small">
          <el-button @click="addRecord">
            <el-icon><Plus /></el-icon>
            新增记录
          </el-button>
          <el-button @click="viewHistory">
            <el-icon><Clock /></el-icon>
            查看历史
          </el-button>
        </el-button-group>
      </div>
      
      <div class="records-grid">
        <div class="record-category">
          <div class="category-header">
            <el-icon><Monitor /></el-icon>
            <span>基础指标</span>
          </div>
          <div class="category-content">
            <div 
              v-for="metric in healthMetrics.basic" 
              :key="metric.name"
              class="metric-item"
              :class="metric.status"
            >
              <div class="metric-info">
                <span class="metric-name">{{ metric.name }}</span>
                <span class="metric-unit">{{ metric.unit }}</span>
              </div>
              <div class="metric-value">{{ metric.value }}</div>
              <div class="metric-status">
                <el-tag :type="getMetricTagType(metric.status)" size="small">
                  {{ getMetricStatusText(metric.status) }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
        
        <div class="record-category">
          <div class="category-header">
            <el-icon><FirstAidKit /></el-icon>
            <span>疾病史</span>
          </div>
          <div class="category-content">
            <div 
              v-for="condition in healthRecords.conditions" 
              :key="condition.id"
              class="condition-item"
            >
              <div class="condition-info">
                <div class="condition-name">{{ condition.name }}</div>
                <div class="condition-date">{{ formatDate(condition.diagnosedDate) }}</div>
              </div>
              <div class="condition-status" :class="condition.status">
                {{ getConditionStatusText(condition.status) }}
              </div>
            </div>
          </div>
        </div>
        
        <div class="record-category">
          <div class="category-header">
            <el-icon><Medicine /></el-icon>
            <span>用药记录</span>
          </div>
          <div class="category-content">
            <div 
              v-for="medication in healthRecords.medications" 
              :key="medication.id"
              class="medication-item"
            >
              <div class="medication-info">
                <div class="medication-name">{{ medication.name }}</div>
                <div class="medication-dosage">{{ medication.dosage }}</div>
              </div>
              <div class="medication-frequency">{{ medication.frequency }}</div>
              <div class="medication-status" :class="medication.status">
                {{ getMedicationStatusText(medication.status) }}
              </div>
            </div>
          </div>
        </div>
        
        <div class="record-category">
          <div class="category-header">
            <el-icon><Warning /></el-icon>
            <span>过敏史</span>
          </div>
          <div class="category-content">
            <div 
              v-for="allergy in healthRecords.allergies" 
              :key="allergy.id"
              class="allergy-item"
              :class="allergy.severity"
            >
              <div class="allergy-info">
                <div class="allergy-name">{{ allergy.name }}</div>
                <div class="allergy-type">{{ allergy.type }}</div>
              </div>
              <div class="allergy-severity">
                <el-tag :type="getAllergyTagType(allergy.severity)" size="small">
                  {{ getAllergySeverityText(allergy.severity) }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 生活习惯 -->
    <div class="lifestyle-habits">
      <div class="habits-header">
        <h4>生活习惯</h4>
        <el-button size="small" @click="updateHabits">
          <el-icon><Edit /></el-icon>
          更新习惯
        </el-button>
      </div>
      
      <div class="habits-grid">
        <div class="habit-card exercise">
          <div class="habit-icon">
            <el-icon><TrendUp /></el-icon>
          </div>
          <div class="habit-content">
            <div class="habit-title">运动习惯</div>
            <div class="habit-details">
              <div class="detail-item">
                <span class="detail-label">频率</span>
                <span class="detail-value">{{ lifestyle.exercise.frequency }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">类型</span>
                <span class="detail-value">{{ lifestyle.exercise.type }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">强度</span>
                <span class="detail-value">{{ lifestyle.exercise.intensity }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="habit-card diet">
          <div class="habit-icon">
            <el-icon><Food /></el-icon>
          </div>
          <div class="habit-content">
            <div class="habit-title">饮食习惯</div>
            <div class="habit-details">
              <div class="detail-item">
                <span class="detail-label">饮食类型</span>
                <span class="detail-value">{{ lifestyle.diet.type }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">特殊需求</span>
                <span class="detail-value">{{ lifestyle.diet.special }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">饮水量</span>
                <span class="detail-value">{{ lifestyle.diet.waterIntake }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="habit-card sleep">
          <div class="habit-icon">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="habit-content">
            <div class="habit-title">睡眠习惯</div>
            <div class="habit-details">
              <div class="detail-item">
                <span class="detail-label">就寝时间</span>
                <span class="detail-value">{{ lifestyle.sleep.bedtime }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">起床时间</span>
                <span class="detail-value">{{ lifestyle.sleep.wakeTime }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">睡眠时长</span>
                <span class="detail-value">{{ lifestyle.sleep.duration }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="habit-card social">
          <div class="habit-icon">
            <el-icon><Service /></el-icon>
          </div>
          <div class="habit-content">
            <div class="habit-title">社交习惯</div>
            <div class="habit-details">
              <div class="detail-item">
                <span class="detail-label">社交频率</span>
                <span class="detail-value">{{ lifestyle.social.frequency }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">工作压力</span>
                <span class="detail-value">{{ lifestyle.social.workStress }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">兴趣爱好</span>
                <span class="detail-value">{{ lifestyle.social.hobbies }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 健康目标 -->
    <div class="health-goals">
      <div class="goals-header">
        <h4>健康目标</h4>
        <el-button size="small" @click="setGoals">
          <el-icon><Flag /></el-icon>
          设置目标
        </el-button>
      </div>
      
      <div class="goals-list">
        <div 
          v-for="goal in healthGoals" 
          :key="goal.id"
          class="goal-item"
          :class="goal.priority"
        >
          <div class="goal-info">
            <div class="goal-title">{{ goal.title }}</div>
            <div class="goal-description">{{ goal.description }}</div>
            <div class="goal-timeline">目标期限: {{ formatDate(goal.deadline) }}</div>
          </div>
          <div class="goal-progress">
            <div class="progress-circle">
              <div class="progress-value">{{ goal.progress }}%</div>
            </div>
          </div>
          <div class="goal-status">
            <el-tag :type="getGoalTagType(goal.status)" size="small">
              {{ getGoalStatusText(goal.status) }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  User, 
  Edit, 
  Download, 
  Camera, 
  Phone, 
  Plus, 
  Clock,
  Monitor,
  FirstAidKit,
  Medicine,
  Warning,
  TrendUp,
  Food,
  Service,
  Flag
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  title?: string
  userId?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '个人健康档案',
  userId: ''
})

// 用户资料
const userProfile = reactive({
  id: 'U20240001',
  name: '张三',
  avatar: '',
  age: 28,
  height: 175,
  weight: 70,
  phone: '138****8888',
  email: 'zhangsan@example.com',
  emergencyContact: '李四',
  emergencyPhone: '139****9999',
  healthStatus: 'good' // excellent, good, fair, poor
})

// 健康指标
const healthMetrics = reactive({
  basic: [
    { name: '血压', value: '120/80', unit: 'mmHg', status: 'normal' },
    { name: '心率', value: '72', unit: 'bpm', status: 'normal' },
    { name: '体温', value: '36.5', unit: '°C', status: 'normal' },
    { name: '血氧', value: '98', unit: '%', status: 'normal' },
    { name: '血糖', value: '5.6', unit: 'mmol/L', status: 'normal' },
    { name: '胆固醇', value: '4.2', unit: 'mmol/L', status: 'warning' }
  ]
})

// 健康记录
const healthRecords = reactive({
  conditions: [
    {
      id: 1,
      name: '高血压',
      diagnosedDate: '2022-03-15',
      status: 'controlled'
    },
    {
      id: 2,
      name: '糖尿病前期',
      diagnosedDate: '2023-01-20',
      status: 'monitoring'
    }
  ],
  medications: [
    {
      id: 1,
      name: '降压药',
      dosage: '5mg',
      frequency: '每日一次',
      status: 'active'
    },
    {
      id: 2,
      name: '维生素D',
      dosage: '400IU',
      frequency: '每日一次',
      status: 'active'
    }
  ],
  allergies: [
    {
      id: 1,
      name: '青霉素',
      type: '药物过敏',
      severity: 'high'
    },
    {
      id: 2,
      name: '花生',
      type: '食物过敏',
      severity: 'medium'
    }
  ]
})

// 生活习惯
const lifestyle = reactive({
  exercise: {
    frequency: '每周3-4次',
    type: '有氧运动',
    intensity: '中等强度'
  },
  diet: {
    type: '均衡饮食',
    special: '低盐低脂',
    waterIntake: '每日2L'
  },
  sleep: {
    bedtime: '22:30',
    wakeTime: '06:30',
    duration: '8小时'
  },
  social: {
    frequency: '适中',
    workStress: '中等',
    hobbies: '阅读、游泳'
  }
})

// 健康目标
const healthGoals = ref([
  {
    id: 1,
    title: '减重计划',
    description: '在3个月内减重5kg',
    deadline: '2024-06-30',
    progress: 60,
    status: 'active',
    priority: 'high'
  },
  {
    id: 2,
    title: '血压控制',
    description: '保持血压在正常范围',
    deadline: '2024-12-31',
    progress: 85,
    status: 'active',
    priority: 'medium'
  },
  {
    id: 3,
    title: '运动习惯',
    description: '每周至少运动4次',
    deadline: '2024-12-31',
    progress: 45,
    status: 'active',
    priority: 'medium'
  }
])

// 工具方法
const calculateBMI = () => {
  const bmi = userProfile.weight / ((userProfile.height / 100) ** 2)
  return bmi.toFixed(1)
}

const getHealthStatusText = () => {
  const statusMap = {
    excellent: '健康状况优秀',
    good: '健康状况良好',
    fair: '健康状况一般',
    poor: '需要关注'
  }
  return statusMap[userProfile.healthStatus as keyof typeof statusMap] || '未知'
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const getMetricTagType = (status: string) => {
  const typeMap = {
    normal: 'success',
    warning: 'warning',
    critical: 'danger'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

const getMetricStatusText = (status: string) => {
  const textMap = {
    normal: '正常',
    warning: '注意',
    critical: '异常'
  }
  return textMap[status as keyof typeof textMap] || '未知'
}

const getConditionStatusText = (status: string) => {
  const textMap = {
    controlled: '已控制',
    monitoring: '监测中',
    active: '活跃期',
    resolved: '已治愈'
  }
  return textMap[status as keyof typeof textMap] || '未知'
}

const getMedicationStatusText = (status: string) => {
  const textMap = {
    active: '正在服用',
    paused: '暂停',
    completed: '已完成'
  }
  return textMap[status as keyof typeof textMap] || '未知'
}

const getAllergyTagType = (severity: string) => {
  const typeMap = {
    low: 'info',
    medium: 'warning',
    high: 'danger'
  }
  return typeMap[severity as keyof typeof typeMap] || 'info'
}

const getAllergySeverityText = (severity: string) => {
  const textMap = {
    low: '轻度',
    medium: '中度',
    high: '重度'
  }
  return textMap[severity as keyof typeof textMap] || '未知'
}

const getGoalTagType = (status: string) => {
  const typeMap = {
    active: 'primary',
    completed: 'success',
    paused: 'warning',
    overdue: 'danger'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

const getGoalStatusText = (status: string) => {
  const textMap = {
    active: '进行中',
    completed: '已完成',
    paused: '已暂停',
    overdue: '已逾期'
  }
  return textMap[status as keyof typeof textMap] || '未知'
}

// 事件处理
const editProfile = () => {
  ElMessage.info('打开编辑资料对话框')
}

const exportProfile = () => {
  ElMessage.info('导出健康档案')
}

const changeAvatar = () => {
  ElMessage.info('更换头像')
}

const addRecord = () => {
  ElMessage.info('添加健康记录')
}

const viewHistory = () => {
  ElMessage.info('查看健康历史')
}

const updateHabits = () => {
  ElMessage.info('更新生活习惯')
}

const setGoals = () => {
  ElMessage.info('设置健康目标')
}

onMounted(() => {
  console.log('Personal Health Profile mounted')
})
</script>

<style lang="scss" scoped>
.personal-health-profile {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  
  .title-section {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    
    .header-icon {
      color: var(--primary-500);
      font-size: 20px;
    }
    
    .profile-title {
      font-size: var(--font-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .profile-actions {
    display: flex;
    gap: var(--spacing-sm);
  }
}

.user-basic-info {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  
  .info-card {
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    border: 1px solid var(--border-light);
    
    &.main-info {
      display: flex;
      gap: var(--spacing-lg);
      align-items: center;
      
      .user-avatar {
        position: relative;
        
        .avatar-actions {
          position: absolute;
          bottom: -8px;
          right: -8px;
        }
      }
      
      .user-details {
        flex: 1;
        
        .user-name {
          font-size: var(--font-xl);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .user-id {
          font-size: var(--font-sm);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-sm);
          font-family: var(--font-tech);
        }
        
        .user-status {
          display: flex;
          align-items: center;
          gap: var(--spacing-xs);
          
          .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: var(--radius-full);
          }
          
          &.excellent {
            color: var(--success-500);
            
            .status-indicator {
              background: var(--success-500);
            }
          }
          
          &.good {
            color: var(--primary-500);
            
            .status-indicator {
              background: var(--primary-500);
            }
          }
          
          &.fair {
            color: var(--warning-500);
            
            .status-indicator {
              background: var(--warning-500);
            }
          }
          
          &.poor {
            color: var(--error-500);
            
            .status-indicator {
              background: var(--error-500);
            }
          }
        }
      }
      
      .profile-stats {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: var(--spacing-md);
        
        .stat-item {
          text-align: center;
          
          .stat-value {
            font-size: var(--font-lg);
            font-weight: 700;
            color: var(--text-primary);
            font-family: var(--font-tech);
            margin-bottom: 2px;
          }
          
          .stat-label {
            font-size: var(--font-xs);
            color: var(--text-secondary);
          }
        }
      }
    }
    
    &.contact-info {
      .card-header {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
        margin-bottom: var(--spacing-md);
        color: var(--primary-500);
        font-size: var(--font-sm);
        font-weight: 600;
      }
      
      .contact-details {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-sm);
        
        .contact-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          
          .contact-label {
            font-size: var(--font-sm);
            color: var(--text-secondary);
          }
          
          .contact-value {
            font-size: var(--font-sm);
            color: var(--text-primary);
            font-weight: 500;
          }
        }
      }
    }
  }
}

.health-records {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .records-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .records-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-lg);
    
    .record-category {
      .category-header {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
        margin-bottom: var(--spacing-md);
        color: var(--primary-500);
        font-size: var(--font-sm);
        font-weight: 600;
        
        .el-icon {
          font-size: 16px;
        }
      }
      
      .category-content {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-sm);
        
        .metric-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--spacing-sm);
          background: var(--bg-secondary);
          border-radius: var(--radius-sm);
          
          .metric-info {
            display: flex;
            align-items: baseline;
            gap: var(--spacing-xs);
            
            .metric-name {
              font-size: var(--font-sm);
              color: var(--text-primary);
            }
            
            .metric-unit {
              font-size: var(--font-xs);
              color: var(--text-secondary);
            }
          }
          
          .metric-value {
            font-size: var(--font-sm);
            font-weight: 600;
            color: var(--text-primary);
            font-family: var(--font-tech);
          }
        }
        
        .condition-item,
        .medication-item,
        .allergy-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--spacing-sm);
          background: var(--bg-secondary);
          border-radius: var(--radius-sm);
          
          .condition-info,
          .medication-info,
          .allergy-info {
            .condition-name,
            .medication-name,
            .allergy-name {
              font-size: var(--font-sm);
              color: var(--text-primary);
              font-weight: 500;
              margin-bottom: 2px;
            }
            
            .condition-date,
            .medication-dosage,
            .allergy-type {
              font-size: var(--font-xs);
              color: var(--text-secondary);
            }
          }
          
          .condition-status,
          .medication-frequency,
          .medication-status {
            font-size: var(--font-xs);
            color: var(--text-primary);
          }
        }
      }
    }
  }
}

.lifestyle-habits {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  margin-bottom: var(--spacing-lg);
  
  .habits-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .habits-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-lg);
    
    .habit-card {
      display: flex;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      
      .habit-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-sm);
        background: var(--primary-500);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
        flex-shrink: 0;
      }
      
      .habit-content {
        flex: 1;
        
        .habit-title {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-sm);
        }
        
        .habit-details {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-xs);
          
          .detail-item {
            display: flex;
            justify-content: space-between;
            
            .detail-label {
              font-size: var(--font-xs);
              color: var(--text-secondary);
            }
            
            .detail-value {
              font-size: var(--font-xs);
              color: var(--text-primary);
              font-weight: 500;
            }
          }
        }
      }
    }
  }
}

.health-goals {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  
  .goals-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    
    h4 {
      font-size: var(--font-md);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  .goals-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    
    .goal-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-lg);
      padding: var(--spacing-md);
      background: var(--bg-secondary);
      border-radius: var(--radius-sm);
      
      .goal-info {
        flex: 1;
        
        .goal-title {
          font-size: var(--font-sm);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .goal-description {
          font-size: var(--font-xs);
          color: var(--text-secondary);
          margin-bottom: var(--spacing-xs);
        }
        
        .goal-timeline {
          font-size: var(--font-xs);
          color: var(--primary-500);
        }
      }
      
      .goal-progress {
        .progress-circle {
          width: 50px;
          height: 50px;
          border-radius: var(--radius-full);
          background: conic-gradient(var(--primary-500) calc(var(--progress) * 1%), var(--bg-card) 0%);
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          
          &::before {
            content: '';
            position: absolute;
            width: 70%;
            height: 70%;
            background: var(--bg-secondary);
            border-radius: var(--radius-full);
          }
          
          .progress-value {
            position: relative;
            z-index: 1;
            font-size: var(--font-xs);
            font-weight: 600;
            color: var(--text-primary);
            font-family: var(--font-tech);
          }
        }
      }
      
      &.high {
        border-left: 3px solid var(--error-500);
      }
      
      &.medium {
        border-left: 3px solid var(--warning-500);
      }
      
      &.low {
        border-left: 3px solid var(--info-500);
      }
    }
  }
}

@media (max-width: 1024px) {
  .user-basic-info {
    grid-template-columns: 1fr;
  }
  
  .records-grid,
  .habits-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .main-info {
    flex-direction: column;
    text-align: center;
  }
}
</style>