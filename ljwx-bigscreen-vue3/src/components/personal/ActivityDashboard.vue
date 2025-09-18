<template>
  <div class="activity-dashboard">
    <div class="dashboard-header">
      <h3>活动仪表板</h3>
      <div class="activity-score">{{ activityScore }}/100</div>
    </div>
    
    <div class="activity-cards">
      <div class="activity-card steps">
        <div class="card-icon"><el-icon><Walking /></el-icon></div>
        <div class="card-content">
          <div class="card-value">{{ todayData.steps }}</div>
          <div class="card-label">今日步数</div>
        </div>
      </div>
      
      <div class="activity-card calories">
        <div class="card-icon"><el-icon><Lightning /></el-icon></div>
        <div class="card-content">
          <div class="card-value">{{ todayData.calories }}</div>
          <div class="card-label">卡路里</div>
        </div>
      </div>
      
      <div class="activity-card distance">
        <div class="card-icon"><el-icon><Position /></el-icon></div>
        <div class="card-content">
          <div class="card-value">{{ todayData.distance }}km</div>
          <div class="card-label">运动距离</div>
        </div>
      </div>
    </div>
    
    <div class="activity-trends">
      <h4>活动趋势</h4>
      <div class="trend-chart" ref="chartRef"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Walking, Lightning, Position } from '@element-plus/icons-vue'

const activityScore = ref(85)
const todayData = reactive({
  steps: 8520,
  calories: 420,
  distance: 6.8
})

const chartRef = ref<HTMLElement>()

onMounted(() => {
  console.log('Activity Dashboard mounted')
})
</script>

<style lang="scss" scoped>
.activity-dashboard {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  
  h3 {
    margin: 0;
    color: var(--text-primary);
  }
  
  .activity-score {
    font-size: var(--font-xl);
    font-weight: 700;
    color: var(--primary-500);
  }
}

.activity-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  
  .activity-card {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    
    .card-icon {
      width: 40px;
      height: 40px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 18px;
    }
    
    .card-content {
      .card-value {
        font-size: var(--font-lg);
        font-weight: 700;
        color: var(--text-primary);
      }
      
      .card-label {
        font-size: var(--font-sm);
        color: var(--text-secondary);
      }
    }
    
    &.steps .card-icon {
      background: linear-gradient(135deg, #66bb6a, #4caf50);
    }
    
    &.calories .card-icon {
      background: linear-gradient(135deg, #ff6b6b, #f44336);
    }
    
    &.distance .card-icon {
      background: linear-gradient(135deg, #42a5f5, #2196f3);
    }
  }
}

.activity-trends {
  h4 {
    margin: 0 0 var(--spacing-md) 0;
    color: var(--text-primary);
  }
  
  .trend-chart {
    height: 200px;
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
  }
}

@media (max-width: 768px) {
  .activity-cards {
    grid-template-columns: 1fr;
  }
}
</style>