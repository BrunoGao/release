<script setup lang="ts">
import { computed, ref } from 'vue';

defineOptions({
  name: 'HealthInsights'
});

interface Props {
  healthMetrics: any;
  healthScore: number;
  overallStatus: any;
}

const props = defineProps<Props>();

const activeTab = ref<'recommendations' | 'trends' | 'alerts'>('recommendations');

// 健康建议
const healthRecommendations = computed(() => {
  return props.healthMetrics.recommendations || [];
});

// 趋势分析
const trendAnalysis = computed(() => {
  const trends = [];
  const metrics = props.healthMetrics;
  
  Object.keys(metrics.trend || {}).forEach(key => {
    const trend = metrics.trend[key];
    const status = metrics.status[key];
    const current = metrics.current[key];
    
    let analysis = '';
    let severity = 'info';
    
    if (trend === 'up') {
      if (key === 'heart_rate' && status === 'danger') {
        analysis = '心率持续上升，可能存在心血管压力，建议减少剧烈活动';
        severity = 'warning';
      } else if (key === 'step' && status === 'normal') {
        analysis = '运动量呈上升趋势，保持良好的运动习惯';
        severity = 'success';
      } else if (key === 'stress' && status !== 'normal') {
        analysis = '压力指数上升，建议进行放松训练或寻求心理支持';
        severity = 'warning';
      }
    } else if (trend === 'down') {
      if (key === 'blood_oxygen' && status === 'danger') {
        analysis = '血氧饱和度下降，可能存在呼吸系统问题，建议就医检查';
        severity = 'error';
      } else if (key === 'step' && status === 'warning') {
        analysis = '运动量减少，建议增加日常活动和锻炼';
        severity = 'warning';
      } else if (key === 'sleep' && status !== 'normal') {
        analysis = '睡眠质量下降，建议调整作息时间和睡眠环境';
        severity = 'warning';
      }
    }
    
    if (analysis) {
      trends.push({
        key,
        trend,
        analysis,
        severity,
        value: current
      });
    }
  });
  
  return trends;
});

// 健康警报
const healthAlerts = computed(() => {
  const alerts = [];
  const metrics = props.healthMetrics;
  
  Object.keys(metrics.status || {}).forEach(key => {
    const status = metrics.status[key];
    const current = metrics.current[key];
    
    if (status === 'danger') {
      alerts.push({
        key,
        type: 'danger',
        title: getAlertTitle(key, status),
        description: getAlertDescription(key, current),
        action: getAlertAction(key),
        timestamp: new Date().toLocaleString()
      });
    } else if (status === 'warning') {
      alerts.push({
        key,
        type: 'warning',
        title: getAlertTitle(key, status),
        description: getAlertDescription(key, current),
        action: getAlertAction(key),
        timestamp: new Date().toLocaleString()
      });
    }
  });
  
  return alerts.sort((a, b) => a.type === 'danger' ? -1 : 1);
});

function getAlertTitle(key: string, status: string) {
  const names = {
    heart_rate: '心率',
    blood_oxygen: '血氧',
    temperature: '体温',
    pressure_high: '收缩压',
    pressure_low: '舒张压',
    sleep: '睡眠',
    stress: '压力',
    step: '运动量'
  };
  
  return `${names[key as keyof typeof names] || key}${status === 'danger' ? '异常' : '警告'}`;
}

function getAlertDescription(key: string, value: number) {
  const descriptions = {
    heart_rate: `当前心率 ${value} bpm，${value > 100 ? '过快' : '过慢'}`,
    blood_oxygen: `当前血氧 ${value}%，低于正常范围`,
    temperature: `当前体温 ${value}°C，${value > 37.5 ? '偏高' : '偏低'}`,
    pressure_high: `当前收缩压 ${value} mmHg，${value > 140 ? '偏高' : '偏低'}`,
    pressure_low: `当前舒张压 ${value} mmHg，${value > 90 ? '偏高' : '偏低'}`,
    sleep: `睡眠时间 ${value} 小时，${value < 7 ? '不足' : '过多'}`,
    stress: `压力指数 ${value}，${value > 50 ? '过高' : ''}`,
    step: `日步数 ${value} 步，运动量不足`
  };
  
  return descriptions[key as keyof typeof descriptions] || `数值: ${value}`;
}

function getAlertAction(key: string) {
  const actions = {
    heart_rate: '建议休息并监测心率变化，必要时就医',
    blood_oxygen: '建议深呼吸或吸氧，持续异常请立即就医',
    temperature: '建议测量体温并观察症状变化',
    pressure_high: '建议控制饮食，减少盐分摄入',
    pressure_low: '建议监测血压变化，注意补充水分',
    sleep: '建议调整作息时间，创造良好睡眠环境',
    stress: '建议进行放松训练，如深呼吸、冥想等',
    step: '建议增加日常活动，每天至少6000步'
  };
  
  return actions[key as keyof typeof actions] || '建议咨询医生';
}

// 获取健康等级
const healthLevel = computed(() => {
  const score = props.healthScore;
  if (score >= 90) return { level: 5, text: '优秀', color: '#52c41a', description: '您的健康状况非常好，请继续保持' };
  if (score >= 80) return { level: 4, text: '良好', color: '#1890ff', description: '健康状况良好，注意保持良好习惯' };
  if (score >= 70) return { level: 3, text: '一般', color: '#faad14', description: '健康状况一般，需要适当改善' };
  if (score >= 60) return { level: 2, text: '较差', color: '#fa8c16', description: '健康状况需要改善，建议调整生活方式' };
  return { level: 1, text: '差', color: '#f5222d', description: '健康状况需要重点关注，建议咨询医生' };
});

// 获取图标
function getMetricIcon(key: string) {
  const icons = {
    heart_rate: 'i-material-symbols:favorite',
    blood_oxygen: 'i-material-symbols:air',
    temperature: 'i-material-symbols:device-thermostat',
    pressure_high: 'i-material-symbols:monitor-heart',
    pressure_low: 'i-material-symbols:monitor-heart-outline',
    sleep: 'i-material-symbols:bedtime',
    stress: 'i-material-symbols:psychology',
    step: 'i-material-symbols:directions-walk'
  };
  
  return icons[key as keyof typeof icons] || 'i-material-symbols:health-and-safety';
}

function getMetricColor(key: string) {
  const colors = {
    heart_rate: '#FF6B6B',
    blood_oxygen: '#4ECDC4',
    temperature: '#45B7D1',
    pressure_high: '#96CEB4',
    pressure_low: '#FFEAA7',
    sleep: '#98D8C8',
    stress: '#F7DC6F',
    step: '#DDA0DD'
  };
  
  return colors[key as keyof typeof colors] || '#999';
}
</script>

<template>
  <div class="health-insights">
    <!-- 健康等级卡片 -->
    <NCard class="health-level-card">
      <div class="level-content">
        <div class="level-icon">
          <div class="level-circle" :style="{ borderColor: healthLevel.color }">
            <NIcon size="32" :color="healthLevel.color">
              <i class="i-material-symbols:health-and-safety"></i>
            </NIcon>
          </div>
          <div class="level-stars">
            <NIcon 
              v-for="i in 5" 
              :key="i"
              size="14"
              :color="i <= healthLevel.level ? '#fadb14' : '#d9d9d9'"
            >
              <i class="i-material-symbols:star"></i>
            </NIcon>
          </div>
        </div>
        <div class="level-info">
          <div class="level-text">
            <span class="level-title">健康等级</span>
            <span class="level-value" :style="{ color: healthLevel.color }">
              {{ healthLevel.text }}
            </span>
          </div>
          <div class="level-description">{{ healthLevel.description }}</div>
        </div>
      </div>
    </NCard>

    <!-- 主要内容区域 -->
    <NCard class="insights-main">
      <template #header>
        <div class="insights-header">
          <h3>健康洞察分析</h3>
          <NTabs v-model:value="activeTab" type="line" size="small">
            <NTab name="recommendations" tab="健康建议" />
            <NTab name="trends" tab="趋势分析" />
            <NTab name="alerts" tab="健康警报" />
          </NTabs>
        </div>
      </template>

      <!-- 健康建议 -->
      <div v-if="activeTab === 'recommendations'" class="recommendations-content">
        <div v-if="healthRecommendations.length > 0" class="recommendations-list">
          <div 
            v-for="(recommendation, index) in healthRecommendations" 
            :key="index"
            class="recommendation-item"
          >
            <div class="recommendation-icon">
              <NIcon size="18" color="#1890ff">
                <i class="i-material-symbols:lightbulb"></i>
              </NIcon>
            </div>
            <div class="recommendation-text">{{ recommendation }}</div>
          </div>
        </div>
        <NEmpty v-else description="暂无健康建议" />
      </div>

      <!-- 趋势分析 -->
      <div v-if="activeTab === 'trends'" class="trends-content">
        <div v-if="trendAnalysis.length > 0" class="trends-list">
          <div 
            v-for="trend in trendAnalysis" 
            :key="trend.key"
            class="trend-item"
            :class="trend.severity"
          >
            <div class="trend-header">
              <div class="trend-metric">
                <NIcon size="16" :color="getMetricColor(trend.key)">
                  <i :class="getMetricIcon(trend.key)"></i>
                </NIcon>
                <span class="metric-name">{{ trend.key }}</span>
              </div>
              <div class="trend-direction">
                <NIcon 
                  size="16" 
                  :color="trend.trend === 'up' ? '#f5222d' : '#52c41a'"
                >
                  <i v-if="trend.trend === 'up'" class="i-material-symbols:trending-up"></i>
                  <i v-else class="i-material-symbols:trending-down"></i>
                </NIcon>
                <span>{{ trend.trend === 'up' ? '上升' : '下降' }}</span>
              </div>
            </div>
            <div class="trend-analysis">{{ trend.analysis }}</div>
          </div>
        </div>
        <NEmpty v-else description="暂无趋势分析" />
      </div>

      <!-- 健康警报 -->
      <div v-if="activeTab === 'alerts'" class="alerts-content">
        <div v-if="healthAlerts.length > 0" class="alerts-list">
          <div 
            v-for="alert in healthAlerts" 
            :key="alert.key"
            class="alert-item"
            :class="alert.type"
          >
            <div class="alert-icon">
              <NIcon 
                size="20" 
                :color="alert.type === 'danger' ? '#f5222d' : '#faad14'"
              >
                <i v-if="alert.type === 'danger'" class="i-material-symbols:warning"></i>
                <i v-else class="i-material-symbols:info"></i>
              </NIcon>
            </div>
            <div class="alert-content">
              <div class="alert-header">
                <span class="alert-title">{{ alert.title }}</span>
                <span class="alert-time">{{ alert.timestamp }}</span>
              </div>
              <div class="alert-description">{{ alert.description }}</div>
              <div class="alert-action">
                <NTag :type="alert.type === 'danger' ? 'error' : 'warning'" size="small">
                  建议: {{ alert.action }}
                </NTag>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="no-alerts">
          <NResult status="success" title="无健康警报" description="所有健康指标正常">
            <template #icon>
              <NIcon size="48" color="#52c41a">
                <i class="i-material-symbols:check-circle"></i>
              </NIcon>
            </template>
          </NResult>
        </div>
      </div>
    </NCard>
  </div>
</template>

<style scoped>
.health-insights {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
}

.health-level-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 16px;
}

.level-content {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px;
}

.level-icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.level-circle {
  width: 64px;
  height: 64px;
  border: 3px solid;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
}

.level-stars {
  display: flex;
  gap: 2px;
}

.level-info {
  flex: 1;
}

.level-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.level-title {
  font-size: 14px;
  opacity: 0.9;
}

.level-value {
  font-size: 24px;
  font-weight: 700;
}

.level-description {
  font-size: 14px;
  opacity: 0.8;
  line-height: 1.5;
}

.insights-main {
  flex: 1;
  background: rgba(255, 255, 255, 0.95);
  border: none;
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.insights-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.insights-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.recommendations-list,
.trends-list,
.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.recommendation-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #1890ff;
}

.recommendation-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.recommendation-text {
  flex: 1;
  line-height: 1.6;
  color: #262626;
}

.trend-item {
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid;
}

.trend-item.success {
  background: #f6ffed;
  border-left-color: #52c41a;
}

.trend-item.warning {
  background: #fffbe6;
  border-left-color: #faad14;
}

.trend-item.error {
  background: #fff2f0;
  border-left-color: #f5222d;
}

.trend-item.info {
  background: #f0f5ff;
  border-left-color: #1890ff;
}

.trend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.trend-metric {
  display: flex;
  align-items: center;
  gap: 8px;
}

.metric-name {
  font-size: 14px;
  font-weight: 500;
}

.trend-direction {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.trend-analysis {
  color: #595959;
  line-height: 1.6;
  font-size: 14px;
}

.alert-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid;
}

.alert-item.danger {
  background: #fff2f0;
  border-left-color: #f5222d;
}

.alert-item.warning {
  background: #fffbe6;
  border-left-color: #faad14;
}

.alert-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.alert-content {
  flex: 1;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.alert-title {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.alert-time {
  font-size: 12px;
  color: #8c8c8c;
}

.alert-description {
  color: #595959;
  margin-bottom: 8px;
  line-height: 1.5;
}

.alert-action {
  margin-top: 8px;
}

.no-alerts {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .level-content {
    flex-direction: column;
    text-align: center;
  }
  
  .insights-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .trend-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .alert-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>