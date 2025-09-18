<template>
  <div class="profile-view">
    <div class="view-header">
      <h2 class="view-title">健康档案</h2>
      <div class="header-actions">
        <el-button size="small" @click="editProfile">
          <el-icon><Edit /></el-icon>
          编辑档案
        </el-button>
        <el-button size="small" @click="exportProfile">
          <el-icon><Download /></el-icon>
          导出档案
        </el-button>
      </div>
    </div>

    <div class="profile-content">
      <div class="profile-overview">
        <div class="user-card">
          <div class="user-avatar">
            <el-avatar :size="80" :src="userProfile.avatar">
              <el-icon><User /></el-icon>
            </el-avatar>
          </div>
          <div class="user-info">
            <h3 class="user-name">{{ userProfile.name }}</h3>
            <p class="user-id">ID: {{ userProfile.id }}</p>
            <div class="user-status" :class="userProfile.healthStatus">
              <el-icon><component :is="getStatusIcon(userProfile.healthStatus)" /></el-icon>
              <span>{{ getStatusText(userProfile.healthStatus) }}</span>
            </div>
          </div>
          <div class="health-score">
            <div class="score-circle">
              <svg viewBox="0 0 42 42" class="score-svg">
                <circle
                  cx="21"
                  cy="21"
                  r="15.915"
                  fill="transparent"
                  stroke="var(--bg-secondary)"
                  stroke-width="3"
                />
                <circle
                  cx="21"
                  cy="21"
                  r="15.915"
                  fill="transparent"
                  :stroke="getScoreColor(userProfile.healthScore)"
                  stroke-width="3"
                  stroke-linecap="round"
                  :stroke-dasharray="`${userProfile.healthScore} 100`"
                  transform="rotate(-90 21 21)"
                />
              </svg>
              <div class="score-text">{{ userProfile.healthScore }}</div>
            </div>
            <div class="score-label">健康评分</div>
          </div>
        </div>

        <div class="profile-stats">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ userProfile.age }}岁</div>
              <div class="stat-label">年龄</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon><Scale /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ userProfile.height }}cm</div>
              <div class="stat-label">身高</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon><Scale /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ userProfile.weight }}kg</div>
              <div class="stat-label">体重</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ userProfile.bmi }}</div>
              <div class="stat-label">BMI</div>
            </div>
          </div>
        </div>
      </div>

      <div class="profile-details">
        <div class="details-section basic-info">
          <div class="section-header">
            <h4>基本信息</h4>
            <el-button size="small" type="text" @click="editBasicInfo">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
          </div>
          <div class="info-grid">
            <div class="info-item">
              <label>姓名</label>
              <span>{{ userProfile.name }}</span>
            </div>
            <div class="info-item">
              <label>性别</label>
              <span>{{ userProfile.gender }}</span>
            </div>
            <div class="info-item">
              <label>出生日期</label>
              <span>{{ userProfile.birthDate }}</span>
            </div>
            <div class="info-item">
              <label>血型</label>
              <span>{{ userProfile.bloodType }}</span>
            </div>
            <div class="info-item">
              <label>联系电话</label>
              <span>{{ userProfile.phone }}</span>
            </div>
            <div class="info-item">
              <label>邮箱地址</label>
              <span>{{ userProfile.email }}</span>
            </div>
          </div>
        </div>

        <div class="details-section medical-history">
          <div class="section-header">
            <h4>健康档案</h4>
            <el-button size="small" type="text" @click="addMedicalRecord">
              <el-icon><Plus /></el-icon>
              添加记录
            </el-button>
          </div>
          <div class="medical-records">
            <div class="record-item" v-for="record in medicalHistory" :key="record.id">
              <div class="record-date">{{ formatDate(record.date) }}</div>
              <div class="record-content">
                <div class="record-title">{{ record.title }}</div>
                <div class="record-description">{{ record.description }}</div>
                <div class="record-tags">
                  <el-tag v-for="tag in record.tags" :key="tag" size="small" type="info">
                    {{ tag }}
                  </el-tag>
                </div>
              </div>
              <div class="record-actions">
                <el-button size="small" type="text" @click="viewRecord(record)">
                  <el-icon><View /></el-icon>
                </el-button>
                <el-button size="small" type="text" @click="editRecord(record)">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div class="details-section emergency-contacts">
          <div class="section-header">
            <h4>紧急联系人</h4>
            <el-button size="small" type="text" @click="addEmergencyContact">
              <el-icon><Plus /></el-icon>
              添加联系人
            </el-button>
          </div>
          <div class="contacts-list">
            <div class="contact-item" v-for="contact in emergencyContacts" :key="contact.id">
              <div class="contact-avatar">
                <el-avatar :size="40" :src="contact.avatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
              </div>
              <div class="contact-info">
                <div class="contact-name">{{ contact.name }}</div>
                <div class="contact-relation">{{ contact.relation }}</div>
                <div class="contact-phone">{{ contact.phone }}</div>
              </div>
              <div class="contact-actions">
                <el-button size="small" type="primary" @click="callContact(contact)">
                  <el-icon><Phone /></el-icon>
                  呼叫
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div class="details-section health-goals">
          <div class="section-header">
            <h4>健康目标</h4>
            <el-button size="small" type="text" @click="setHealthGoal">
              <el-icon><Plus /></el-icon>
              设置目标
            </el-button>
          </div>
          <div class="goals-list">
            <div class="goal-item" v-for="goal in healthGoals" :key="goal.id">
              <div class="goal-icon" :class="goal.category">
                <el-icon><component :is="getGoalIcon(goal.category)" /></el-icon>
              </div>
              <div class="goal-content">
                <div class="goal-title">{{ goal.title }}</div>
                <div class="goal-progress">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: goal.progress + '%' }"></div>
                  </div>
                  <span class="progress-text">{{ goal.progress }}%</span>
                </div>
                <div class="goal-target">目标: {{ goal.target }}</div>
              </div>
              <div class="goal-status" :class="getGoalStatus(goal.progress)">
                {{ getGoalStatusText(goal.progress) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Edit, 
  Download, 
  User, 
  Calendar, 
  Scale, 
  DataAnalysis,
  Plus,
  View,
  Phone,
  CircleCheck,
  Warning,
  Timer,
  TrendUp
} from '@element-plus/icons-vue'

const userProfile = ref({
  id: 'U001',
  name: '张健康',
  avatar: '',
  age: 32,
  gender: '男',
  birthDate: '1991-05-15',
  bloodType: 'A型',
  phone: '138****8888',
  email: 'zhang***@email.com',
  height: 175,
  weight: 70,
  bmi: 22.9,
  healthScore: 85,
  healthStatus: 'good'
})

const medicalHistory = ref([
  {
    id: 1,
    date: new Date('2023-12-01'),
    title: '年度体检',
    description: '身体各项指标正常，建议保持当前生活习惯',
    tags: ['体检', '正常']
  },
  {
    id: 2,
    date: new Date('2023-10-15'),
    title: '血压监测',
    description: '血压稍微偏高，建议减少盐分摄入',
    tags: ['血压', '注意']
  },
  {
    id: 3,
    date: new Date('2023-08-20'),
    title: '血糖检查',
    description: '血糖水平正常范围内',
    tags: ['血糖', '正常']
  }
])

const emergencyContacts = ref([
  {
    id: 1,
    name: '李医生',
    relation: '家庭医生',
    phone: '139****1234',
    avatar: ''
  },
  {
    id: 2,
    name: '张小芳',
    relation: '配偶',
    phone: '138****5678',
    avatar: ''
  },
  {
    id: 3,
    name: '张大明',
    relation: '父亲',
    phone: '136****9012',
    avatar: ''
  }
])

const healthGoals = ref([
  {
    id: 1,
    category: 'exercise',
    title: '每周运动150分钟',
    target: '150分钟/周',
    progress: 78
  },
  {
    id: 2,
    category: 'weight',
    title: '减重5公斤',
    target: '65kg',
    progress: 40
  },
  {
    id: 3,
    category: 'sleep',
    title: '保持8小时睡眠',
    target: '8小时/天',
    progress: 92
  },
  {
    id: 4,
    category: 'health',
    title: '血压控制正常',
    target: '<120/80',
    progress: 85
  }
])

const getStatusIcon = (status: string) => {
  const iconMap = {
    excellent: CircleCheck,
    good: CircleCheck,
    warning: Warning,
    poor: Warning
  }
  return iconMap[status as keyof typeof iconMap] || CircleCheck
}

const getStatusText = (status: string) => {
  const textMap = {
    excellent: '健康优秀',
    good: '健康良好',
    warning: '需要关注',
    poor: '需要改善'
  }
  return textMap[status as keyof typeof textMap] || '健康良好'
}

const getScoreColor = (score: number) => {
  if (score >= 85) return 'var(--success-500)'
  if (score >= 70) return 'var(--primary-500)'
  if (score >= 60) return 'var(--warning-500)'
  return 'var(--error-500)'
}

const getGoalIcon = (category: string) => {
  const iconMap = {
    exercise: Timer,
    weight: Scale,
    sleep: User,
    health: TrendUp
  }
  return iconMap[category as keyof typeof iconMap] || Timer
}

const getGoalStatus = (progress: number) => {
  if (progress >= 90) return 'excellent'
  if (progress >= 70) return 'good'
  if (progress >= 50) return 'normal'
  return 'poor'
}

const getGoalStatusText = (progress: number) => {
  if (progress >= 90) return '优秀'
  if (progress >= 70) return '良好'
  if (progress >= 50) return '进行中'
  return '需努力'
}

const formatDate = (date: Date) => {
  return date.toLocaleDateString('zh-CN')
}

const editProfile = () => {
  // 编辑档案逻辑
}

const exportProfile = () => {
  // 导出档案逻辑
}

const editBasicInfo = () => {
  // 编辑基本信息逻辑
}

const addMedicalRecord = () => {
  // 添加医疗记录逻辑
}

const viewRecord = (record: any) => {
  // 查看记录逻辑
}

const editRecord = (record: any) => {
  // 编辑记录逻辑
}

const addEmergencyContact = () => {
  // 添加紧急联系人逻辑
}

const callContact = (contact: any) => {
  // 呼叫联系人逻辑
}

const setHealthGoal = () => {
  // 设置健康目标逻辑
}
</script>

<style lang="scss" scoped>
.profile-view {
  padding: var(--spacing-lg);
  background: var(--bg-primary);
  min-height: 100vh;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
  
  .view-title {
    font-size: var(--font-xl);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  .header-actions {
    display: flex;
    gap: var(--spacing-md);
  }
}

.profile-content {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: var(--spacing-xl);
}

.profile-overview {
  .user-card {
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    padding: var(--spacing-xl);
    margin-bottom: var(--spacing-lg);
    text-align: center;
    
    .user-avatar {
      margin-bottom: var(--spacing-lg);
    }
    
    .user-info {
      margin-bottom: var(--spacing-lg);
      
      .user-name {
        font-size: var(--font-lg);
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 var(--spacing-xs) 0;
      }
      
      .user-id {
        font-size: var(--font-sm);
        color: var(--text-secondary);
        margin: 0 0 var(--spacing-md) 0;
      }
      
      .user-status {
        display: inline-flex;
        align-items: center;
        gap: var(--spacing-xs);
        padding: var(--spacing-xs) var(--spacing-sm);
        border-radius: var(--radius-md);
        font-size: var(--font-sm);
        
        &.excellent,
        &.good {
          background: rgba(76, 175, 80, 0.1);
          color: var(--success-500);
        }
        
        &.warning {
          background: rgba(255, 167, 38, 0.1);
          color: var(--warning-500);
        }
        
        &.poor {
          background: rgba(244, 67, 54, 0.1);
          color: var(--error-500);
        }
      }
    }
    
    .health-score {
      .score-circle {
        position: relative;
        width: 80px;
        height: 80px;
        margin: 0 auto var(--spacing-sm) auto;
        
        .score-svg {
          width: 100%;
          height: 100%;
          transform: rotate(-90deg);
        }
        
        .score-text {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          font-size: var(--font-lg);
          font-weight: 700;
          color: var(--text-primary);
          font-family: var(--font-tech);
        }
      }
      
      .score-label {
        font-size: var(--font-sm);
        color: var(--text-secondary);
      }
    }
  }
  
  .profile-stats {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-md);
    
    .stat-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      background: var(--bg-card);
      border-radius: var(--radius-md);
      
      .stat-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-md);
        background: var(--primary-500);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
      }
      
      .stat-content {
        .stat-value {
          font-size: var(--font-md);
          font-weight: 700;
          color: var(--text-primary);
          font-family: var(--font-tech);
        }
        
        .stat-label {
          font-size: var(--font-xs);
          color: var(--text-secondary);
        }
      }
    }
  }
}

.profile-details {
  .details-section {
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    margin-bottom: var(--spacing-lg);
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--spacing-lg);
      
      h4 {
        font-size: var(--font-md);
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
      }
    }
    
    &.basic-info {
      .info-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: var(--spacing-lg);
        
        .info-item {
          label {
            display: block;
            font-size: var(--font-sm);
            color: var(--text-secondary);
            margin-bottom: var(--spacing-xs);
          }
          
          span {
            font-size: var(--font-sm);
            color: var(--text-primary);
            font-weight: 500;
          }
        }
      }
    }
    
    &.medical-history {
      .medical-records {
        .record-item {
          display: flex;
          gap: var(--spacing-md);
          padding: var(--spacing-md);
          margin-bottom: var(--spacing-md);
          background: var(--bg-elevated);
          border-radius: var(--radius-md);
          border: 1px solid var(--border-light);
          
          &:last-child {
            margin-bottom: 0;
          }
          
          .record-date {
            font-size: var(--font-xs);
            color: var(--text-secondary);
            min-width: 80px;
          }
          
          .record-content {
            flex: 1;
            
            .record-title {
              font-size: var(--font-sm);
              font-weight: 600;
              color: var(--text-primary);
              margin-bottom: var(--spacing-xs);
            }
            
            .record-description {
              font-size: var(--font-xs);
              color: var(--text-secondary);
              margin-bottom: var(--spacing-sm);
            }
            
            .record-tags {
              display: flex;
              gap: var(--spacing-xs);
            }
          }
          
          .record-actions {
            display: flex;
            gap: var(--spacing-xs);
          }
        }
      }
    }
    
    &.emergency-contacts {
      .contacts-list {
        .contact-item {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);
          padding: var(--spacing-md);
          margin-bottom: var(--spacing-md);
          background: var(--bg-elevated);
          border-radius: var(--radius-md);
          border: 1px solid var(--border-light);
          
          &:last-child {
            margin-bottom: 0;
          }
          
          .contact-info {
            flex: 1;
            
            .contact-name {
              font-size: var(--font-sm);
              font-weight: 600;
              color: var(--text-primary);
              margin-bottom: 2px;
            }
            
            .contact-relation {
              font-size: var(--font-xs);
              color: var(--text-secondary);
              margin-bottom: 2px;
            }
            
            .contact-phone {
              font-size: var(--font-xs);
              color: var(--text-secondary);
            }
          }
        }
      }
    }
    
    &.health-goals {
      .goals-list {
        .goal-item {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);
          padding: var(--spacing-md);
          margin-bottom: var(--spacing-md);
          background: var(--bg-elevated);
          border-radius: var(--radius-md);
          border: 1px solid var(--border-light);
          
          &:last-child {
            margin-bottom: 0;
          }
          
          .goal-icon {
            width: 40px;
            height: 40px;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 18px;
            
            &.exercise {
              background: var(--primary-500);
            }
            
            &.weight {
              background: var(--warning-500);
            }
            
            &.sleep {
              background: var(--success-500);
            }
            
            &.health {
              background: var(--error-500);
            }
          }
          
          .goal-content {
            flex: 1;
            
            .goal-title {
              font-size: var(--font-sm);
              font-weight: 600;
              color: var(--text-primary);
              margin-bottom: var(--spacing-xs);
            }
            
            .goal-progress {
              display: flex;
              align-items: center;
              gap: var(--spacing-sm);
              margin-bottom: var(--spacing-xs);
              
              .progress-bar {
                flex: 1;
                height: 6px;
                background: var(--bg-secondary);
                border-radius: var(--radius-full);
                overflow: hidden;
                
                .progress-fill {
                  height: 100%;
                  background: var(--primary-500);
                  border-radius: var(--radius-full);
                  transition: width 0.3s ease;
                }
              }
              
              .progress-text {
                font-size: var(--font-xs);
                font-family: var(--font-tech);
                color: var(--text-primary);
                min-width: 35px;
              }
            }
            
            .goal-target {
              font-size: var(--font-xs);
              color: var(--text-secondary);
            }
          }
          
          .goal-status {
            font-size: var(--font-xs);
            font-weight: 600;
            padding: 2px 6px;
            border-radius: var(--radius-sm);
            
            &.excellent {
              background: rgba(76, 175, 80, 0.2);
              color: var(--success-500);
            }
            
            &.good {
              background: rgba(66, 165, 245, 0.2);
              color: var(--primary-500);
            }
            
            &.normal {
              background: rgba(255, 167, 38, 0.2);
              color: var(--warning-500);
            }
            
            &.poor {
              background: rgba(244, 67, 54, 0.2);
              color: var(--error-500);
            }
          }
        }
      }
    }
  }
}

@media (max-width: 1024px) {
  .profile-content {
    grid-template-columns: 1fr;
  }
  
  .profile-stats {
    grid-template-columns: 1fr;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
}
</style>