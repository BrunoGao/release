<template>
  <div class="department-ranking">
    <div class="ranking-header">
      <h4 class="ranking-title">{{ title }}</h4>
      <div class="ranking-controls">
        <el-select v-model="sortBy" size="small" @change="updateRanking">
          <el-option label="e·Ä" value="healthScore" />
          <el-option label="Âºp" value="participants" />
          <el-option label="9„‡" value="improvement" />
        </el-select>
      </div>
    </div>
    
    <div class="ranking-list">
      <div 
        v-for="(dept, index) in rankedDepartments" 
        :key="dept.id"
        class="ranking-item"
        :class="getRankClass(index)"
      >
        <div class="rank-number" :class="getRankClass(index)">
          {{ index + 1 }}
        </div>
        
        <div class="dept-info">
          <div class="dept-name">{{ dept.name }}</div>
          <div class="dept-meta">
            <span class="participant-count">{{ dept.participants }}º</span>
            <span class="improvement-rate">9„‡: {{ dept.improvement }}%</span>
          </div>
        </div>
        
        <div class="dept-score">
          <div class="score-value" :class="getScoreClass(dept.score)">
            {{ dept.score }}
          </div>
          <div class="score-bar">
            <div 
              class="score-fill" 
              :style="{ width: dept.score + '%' }"
              :class="getScoreClass(dept.score)"
            ></div>
          </div>
        </div>
        
        <div class="rank-change" :class="getTrendClass(dept.trend)">
          <el-icon>
            <component :is="getTrendIcon(dept.trend)" />
          </el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { TrendingUp, TrendingDown, Minus } from '@element-plus/icons-vue'

interface Department {
  id: string
  name: string
  score: number
  participants: number
  improvement: number
  trend: 'up' | 'down' | 'stable'
}

interface Props {
  title?: string
  departments?: Department[]
}

const props = withDefaults(defineProps<Props>(), {
  title: 'èèe·’L',
  departments: () => [
    { id: '1', name: '€/è', score: 92, participants: 45, improvement: 12, trend: 'up' },
    { id: '2', name: '§Áè', score: 88, participants: 32, improvement: 8, trend: 'up' },
    { id: '3', name: 'Ð%è', score: 85, participants: 28, improvement: 5, trend: 'stable' },
    { id: '4', name: '¾¡è', score: 83, participants: 24, improvement: 3, trend: 'down' },
    { id: '5', name: ':è', score: 80, participants: 35, improvement: -2, trend: 'down' }
  ]
})

const sortBy = ref('healthScore')

const rankedDepartments = computed(() => {
  const depts = [...props.departments]
  
  switch (sortBy.value) {
    case 'healthScore':
      return depts.sort((a, b) => b.score - a.score)
    case 'participants':
      return depts.sort((a, b) => b.participants - a.participants)
    case 'improvement':
      return depts.sort((a, b) => b.improvement - a.improvement)
    default:
      return depts
  }
})

const updateRanking = () => {
  console.log('ô°’L:', sortBy.value)
}

const getRankClass = (index: number) => {
  if (index === 0) return 'first'
  if (index === 1) return 'second'
  if (index === 2) return 'third'
  return 'normal'
}

const getScoreClass = (score: number) => {
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 70) return 'fair'
  return 'poor'
}

const getTrendClass = (trend: string) => {
  return `trend-${trend}`
}

const getTrendIcon = (trend: string) => {
  const iconMap = {
    up: TrendingUp,
    down: TrendingDown,
    stable: Minus
  }
  return iconMap[trend as keyof typeof iconMap]
}
</script>

<style lang="scss" scoped>
.department-ranking {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow: hidden;
}

.ranking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  
  .ranking-title {
    font-size: var(--font-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
}

.ranking-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  
  .ranking-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-lg);
    padding: var(--spacing-lg);
    background: var(--bg-elevated);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateX(4px);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }
    
    .rank-number {
      width: 40px;
      height: 40px;
      border-radius: var(--radius-full);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: var(--font-lg);
      font-weight: 700;
      font-family: var(--font-tech);
      
      &.first {
        background: linear-gradient(135deg, #ffd700, #ffb300);
        color: #fff;
        box-shadow: 0 4px 12px rgba(255, 215, 0, 0.4);
      }
      
      &.second {
        background: linear-gradient(135deg, #c0c0c0, #9e9e9e);
        color: #fff;
        box-shadow: 0 4px 12px rgba(192, 192, 192, 0.4);
      }
      
      &.third {
        background: linear-gradient(135deg, #cd7f32, #a0522d);
        color: #fff;
        box-shadow: 0 4px 12px rgba(205, 127, 50, 0.4);
      }
      
      &.normal {
        background: var(--bg-secondary);
        color: var(--text-secondary);
      }
    }
    
    .dept-info {
      flex: 1;
      
      .dept-name {
        font-size: var(--font-md);
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: var(--spacing-xs);
      }
      
      .dept-meta {
        display: flex;
        gap: var(--spacing-md);
        font-size: var(--font-sm);
        color: var(--text-secondary);
        
        .improvement-rate {
          font-weight: 500;
        }
      }
    }
    
    .dept-score {
      text-align: right;
      min-width: 80px;
      
      .score-value {
        font-size: var(--font-lg);
        font-weight: 700;
        font-family: var(--font-tech);
        margin-bottom: var(--spacing-xs);
        
        &.excellent { color: var(--success-500); }
        &.good { color: var(--primary-500); }
        &.fair { color: var(--warning-500); }
        &.poor { color: var(--error-500); }
      }
      
      .score-bar {
        width: 60px;
        height: 6px;
        background: var(--bg-secondary);
        border-radius: var(--radius-full);
        overflow: hidden;
        
        .score-fill {
          height: 100%;
          border-radius: var(--radius-full);
          transition: width 0.8s ease;
          
          &.excellent { background: var(--success-500); }
          &.good { background: var(--primary-500); }
          &.fair { background: var(--warning-500); }
          &.poor { background: var(--error-500); }
        }
      }
    }
    
    .rank-change {
      font-size: 20px;
      
      &.trend-up { color: var(--success-500); }
      &.trend-down { color: var(--error-500); }
      &.trend-stable { color: var(--text-secondary); }
    }
    
    &.first {
      border-color: #ffd700;
      background: linear-gradient(135deg, var(--bg-elevated) 0%, rgba(255, 215, 0, 0.05) 100%);
    }
    
    &.second {
      border-color: #c0c0c0;
      background: linear-gradient(135deg, var(--bg-elevated) 0%, rgba(192, 192, 192, 0.05) 100%);
    }
    
    &.third {
      border-color: #cd7f32;
      background: linear-gradient(135deg, var(--bg-elevated) 0%, rgba(205, 127, 50, 0.05) 100%);
    }
  }
}

@media (max-width: 768px) {
  .ranking-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }
  
  .ranking-item {
    .dept-meta {
      flex-direction: column;
      gap: var(--spacing-xs);
    }
  }
}
</style>