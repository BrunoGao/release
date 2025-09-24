<template>
  <div class="medical-dashboard">
    <!-- 专业医疗头部 -->
    <div class="medical-header">
      <div class="hospital-branding">
        <div class="logo-section">
          <NIcon size="32" color="#0066cc">
            <i class="i-material-symbols:local-hospital"></i>
          </NIcon>
          <div class="hospital-info">
            <h1>智慧健康监护系统</h1>
            <p>Professional Health Monitoring System</p>
          </div>
        </div>
        <div class="system-status">
          <NTag type="success" size="small">
            <template #icon>
              <NIcon><i class="i-material-symbols:check-circle"></i></NIcon>
            </template>
            系统正常运行
          </NTag>
          <span class="timestamp">{{ currentTime }}</span>
        </div>
      </div>
      <div class="patient-info-bar" v-if="selectedPatient">
        <div class="patient-card">
          <div class="patient-avatar">
            <NIcon size="24" color="#666">
              <i class="i-material-symbols:person"></i>
            </NIcon>
          </div>
          <div class="patient-details">
            <h3>{{ selectedPatient.name || '患者' }}</h3>
            <div class="patient-meta">
              <span>ID: {{ selectedPatient.id }}</span>
              <span>年龄: {{ calculateAge(selectedPatient.birthDate) }}岁</span>
              <span>性别: {{ selectedPatient.gender === 'M' ? '男' : '女' }}</span>
            </div>
          </div>
          <div class="patient-status">
            <NTag :type="getPatientStatusType(overallRiskLevel)" size="medium">
              {{ overallRiskLevel }}
            </NTag>
          </div>
        </div>
      </div>
    </div>

    <!-- 关键生命体征监控 -->
    <div class="vital-signs-panel">
      <NCard title="生命体征监控 (Vital Signs)" class="vital-signs-card">
        <template #header-extra>
          <NSpace>
            <NButton size="small" @click="toggleRealtime">
              <template #icon>
                <NIcon><i :class="isRealtime ? 'i-material-symbols:pause' : 'i-material-symbols:play-arrow'"></i></NIcon>
              </template>
              {{ isRealtime ? '暂停' : '开始' }}实时监控
            </NButton>
            <NButton size="small" @click="exportReport">
              <template #icon>
                <NIcon><i class="i-material-symbols:download"></i></NIcon>
              </template>
              导出报告
            </NButton>
          </NSpace>
        </template>

        <div class="vital-signs-grid">
          <!-- 心率监控 -->
          <div class="vital-sign-item critical">
            <div class="vital-header">
              <div class="vital-icon heart-rate">
                <NIcon size="20"><i class="i-material-symbols:favorite"></i></NIcon>
              </div>
              <div class="vital-info">
                <h4>心率 (HR)</h4>
                <span class="unit">beats/min</span>
              </div>
              <div class="status-indicator" :class="getVitalStatus('heartRate')"></div>
            </div>
            <div class="vital-value">
              <span class="current-value">{{ currentVitals.heartRate || '--' }}</span>
              <span class="reference-range">正常: 60-100</span>
            </div>
            <div class="vital-chart">
              <div ref="heartRateChart" class="mini-chart"></div>
            </div>
            <div class="vital-alerts" v-if="getAlerts('heartRate').length">
              <NAlert 
                v-for="alert in getAlerts('heartRate')" 
                :key="alert.id"
                :type="alert.type"
                size="small"
                :title="alert.message"
                closable
              />
            </div>
          </div>

          <!-- 血压监控 -->
          <div class="vital-sign-item critical">
            <div class="vital-header">
              <div class="vital-icon blood-pressure">
                <NIcon size="20"><i class="i-material-symbols:monitor-heart"></i></NIcon>
              </div>
              <div class="vital-info">
                <h4>血压 (BP)</h4>
                <span class="unit">mmHg</span>
              </div>
              <div class="status-indicator" :class="getVitalStatus('bloodPressure')"></div>
            </div>
            <div class="vital-value">
              <span class="current-value">
                {{ currentVitals.systolic || '--' }}/{{ currentVitals.diastolic || '--' }}
              </span>
              <span class="reference-range">正常: &lt;120/80</span>
            </div>
            <div class="blood-pressure-categories">
              <div class="bp-category" :class="{ active: getBPCategory() === 'normal' }">
                <span class="category-dot normal"></span>正常
              </div>
              <div class="bp-category" :class="{ active: getBPCategory() === 'elevated' }">
                <span class="category-dot elevated"></span>偏高
              </div>
              <div class="bp-category" :class="{ active: getBPCategory() === 'high' }">
                <span class="category-dot high"></span>高血压
              </div>
            </div>
          </div>

          <!-- 血氧饱和度 -->
          <div class="vital-sign-item critical">
            <div class="vital-header">
              <div class="vital-icon oxygen">
                <NIcon size="20"><i class="i-material-symbols:air"></i></NIcon>
              </div>
              <div class="vital-info">
                <h4>血氧饱和度 (SpO₂)</h4>
                <span class="unit">%</span>
              </div>
              <div class="status-indicator" :class="getVitalStatus('oxygenSaturation')"></div>
            </div>
            <div class="vital-value">
              <span class="current-value">{{ currentVitals.oxygenSaturation || '--' }}</span>
              <span class="reference-range">正常: ≥95%</span>
            </div>
            <div class="oxygen-gauge">
              <NProgress
                type="circle"
                :percentage="currentVitals.oxygenSaturation || 0"
                :stroke-width="8"
                :color="getOxygenColor(currentVitals.oxygenSaturation)"
                :size="60"
              />
            </div>
          </div>

          <!-- 体温 -->
          <div class="vital-sign-item">
            <div class="vital-header">
              <div class="vital-icon temperature">
                <NIcon size="20"><i class="i-material-symbols:device-thermostat"></i></NIcon>
              </div>
              <div class="vital-info">
                <h4>体温 (Temp)</h4>
                <span class="unit">°C</span>
              </div>
              <div class="status-indicator" :class="getVitalStatus('temperature')"></div>
            </div>
            <div class="vital-value">
              <span class="current-value">{{ currentVitals.temperature || '--' }}</span>
              <span class="reference-range">正常: 36.1-37.2</span>
            </div>
            <div class="temperature-scale">
              <div class="temp-bar">
                <div 
                  class="temp-indicator" 
                  :style="{ left: getTempPosition(currentVitals.temperature) + '%' }"
                ></div>
              </div>
              <div class="temp-labels">
                <span>35°C</span>
                <span>37°C</span>
                <span>39°C</span>
              </div>
            </div>
          </div>
        </div>
      </NCard>
    </div>

    <!-- 详细分析面板 -->
    <div class="analysis-panels">
      <!-- 趋势分析 -->
      <NCard title="趋势分析 (Trend Analysis)" class="trend-analysis">
        <template #header-extra>
          <NSelect
            v-model:value="trendPeriod"
            :options="trendPeriodOptions"
            size="small"
            style="width: 120px"
          />
        </template>
        <div ref="trendChart" class="trend-chart"></div>
      </NCard>

      <!-- 风险评估 -->
      <NCard title="风险评估 (Risk Assessment)" class="risk-assessment">
        <div class="risk-matrix">
          <div class="risk-item" v-for="risk in riskAssessment" :key="risk.category">
            <div class="risk-header">
              <span class="risk-category">{{ risk.category }}</span>
              <NTag :type="getRiskTagType(risk.level)" size="small">
                {{ risk.level }}
              </NTag>
            </div>
            <div class="risk-score">
              <NProgress
                :percentage="risk.score"
                :color="getRiskColor(risk.level)"
                :show-indicator="false"
                :height="6"
              />
              <span class="score-text">{{ risk.score }}/100</span>
            </div>
            <p class="risk-description">{{ risk.description }}</p>
          </div>
        </div>
      </NCard>
    </div>

    <!-- 专业医疗指标 -->
    <div class="medical-indicators">
      <NCard title="专业医疗指标 (Clinical Indicators)">
        <div class="indicators-grid">
          <!-- 心血管指标 -->
          <div class="indicator-section">
            <h5>心血管系统</h5>
            <div class="indicator-list">
              <div class="indicator-item">
                <span class="indicator-name">平均动脉压 (MAP)</span>
                <span class="indicator-value">{{ calculateMAP() }} mmHg</span>
                <span class="indicator-status" :class="getMAPStatus()">
                  {{ getMAPStatusText() }}
                </span>
              </div>
              <div class="indicator-item">
                <span class="indicator-name">脉压 (PP)</span>
                <span class="indicator-value">{{ calculatePP() }} mmHg</span>
                <span class="indicator-status" :class="getPPStatus()">
                  {{ getPPStatusText() }}
                </span>
              </div>
            </div>
          </div>

          <!-- 呼吸系统指标 -->
          <div class="indicator-section">
            <h5>呼吸系统</h5>
            <div class="indicator-list">
              <div class="indicator-item">
                <span class="indicator-name">氧合指数</span>
                <span class="indicator-value">{{ currentVitals.oxygenSaturation || '--' }}%</span>
                <span class="indicator-status" :class="getOxygenStatus()">
                  {{ getOxygenStatusText() }}
                </span>
              </div>
            </div>
          </div>

          <!-- 代谢指标 -->
          <div class="indicator-section">
            <h5>代谢系统</h5>
            <div class="indicator-list">
              <div class="indicator-item">
                <span class="indicator-name">基础代谢率</span>
                <span class="indicator-value">{{ calculateBMR() }} kcal/day</span>
                <span class="indicator-status normal">正常</span>
              </div>
            </div>
          </div>
        </div>
      </NCard>
    </div>

    <!-- 医疗建议 -->
    <div class="medical-recommendations">
      <NCard title="医疗建议 (Medical Recommendations)">
        <div class="recommendations-list">
          <div 
            v-for="(rec, index) in medicalRecommendations" 
            :key="index"
            class="recommendation-item"
            :class="rec.priority"
          >
            <div class="recommendation-icon">
              <NIcon :size="20" :color="getRecommendationColor(rec.priority)">
                <i :class="getRecommendationIcon(rec.priority)"></i>
              </NIcon>
            </div>
            <div class="recommendation-content">
              <h6>{{ rec.title }}</h6>
              <p>{{ rec.description }}</p>
              <div class="recommendation-meta">
                <span class="recommendation-type">{{ rec.type }}</span>
                <span class="recommendation-time">{{ rec.timestamp }}</span>
              </div>
            </div>
          </div>
        </div>
      </NCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';
import * as echarts from 'echarts';

// Props
interface Props {
  healthData?: any;
  healthMetrics?: any;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
});

// 响应式数据
const currentTime = ref(new Date().toLocaleString());
const isRealtime = ref(false);
const trendPeriod = ref('24h');
const selectedPatient = ref({
  id: 'P001',
  name: '张三',
  birthDate: '1985-06-15',
  gender: 'M'
});

// 当前生命体征数据
const currentVitals = ref({
  heartRate: 72,
  systolic: 118,
  diastolic: 76,
  oxygenSaturation: 98,
  temperature: 36.8,
  respiratoryRate: 16
});

// 时间更新
let timeInterval: NodeJS.Timeout;
onMounted(() => {
  timeInterval = setInterval(() => {
    currentTime.value = new Date().toLocaleString();
  }, 1000);
  
  // 初始化图表
  nextTick(() => {
    initCharts();
  });
});

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval);
  }
});

// 趋势周期选项
const trendPeriodOptions = [
  { label: '最近24小时', value: '24h' },
  { label: '最近7天', value: '7d' },
  { label: '最近30天', value: '30d' }
];

// 总体风险级别
const overallRiskLevel = computed(() => {
  const vitals = currentVitals.value;
  let riskScore = 0;
  
  // 心率风险评估
  if (vitals.heartRate < 60 || vitals.heartRate > 100) riskScore += 2;
  else if (vitals.heartRate < 65 || vitals.heartRate > 90) riskScore += 1;
  
  // 血压风险评估
  if (vitals.systolic > 140 || vitals.diastolic > 90) riskScore += 3;
  else if (vitals.systolic > 120 || vitals.diastolic > 80) riskScore += 1;
  
  // 血氧风险评估
  if (vitals.oxygenSaturation < 95) riskScore += 3;
  else if (vitals.oxygenSaturation < 97) riskScore += 1;
  
  if (riskScore >= 5) return '高风险';
  if (riskScore >= 3) return '中风险';
  if (riskScore >= 1) return '低风险';
  return '正常';
});

// 风险评估数据
const riskAssessment = computed(() => [
  {
    category: '心血管风险',
    level: getBPCategory() === 'high' ? '高风险' : '低风险',
    score: getBPCategory() === 'high' ? 85 : 25,
    description: getBPCategory() === 'high' ? '血压偏高，建议密切监控' : '心血管指标正常'
  },
  {
    category: '呼吸系统风险',
    level: currentVitals.value.oxygenSaturation < 95 ? '高风险' : '低风险',
    score: currentVitals.value.oxygenSaturation < 95 ? 90 : 15,
    description: currentVitals.value.oxygenSaturation < 95 ? '血氧饱和度偏低，需要关注' : '呼吸系统功能良好'
  },
  {
    category: '整体健康风险',
    level: overallRiskLevel.value === '高风险' ? '高风险' : '低风险',
    score: overallRiskLevel.value === '高风险' ? 75 : 30,
    description: '基于当前生命体征的综合评估'
  }
]);

// 医疗建议
const medicalRecommendations = computed(() => {
  const recommendations = [];
  const vitals = currentVitals.value;
  
  if (vitals.systolic > 140 || vitals.diastolic > 90) {
    recommendations.push({
      title: '血压偏高警告',
      description: '建议立即复查血压，必要时联系医生调整治疗方案',
      type: '紧急建议',
      priority: 'urgent',
      timestamp: new Date().toLocaleTimeString()
    });
  }
  
  if (vitals.oxygenSaturation < 95) {
    recommendations.push({
      title: '血氧饱和度异常',
      description: '血氧饱和度偏低，建议进行深呼吸训练或吸氧治疗',
      type: '医疗建议',
      priority: 'high',
      timestamp: new Date().toLocaleTimeString()
    });
  }
  
  if (vitals.heartRate > 100) {
    recommendations.push({
      title: '心率偏快提醒',
      description: '建议减少活动，保持心情平静，必要时服用降心率药物',
      type: '日常建议',
      priority: 'medium',
      timestamp: new Date().toLocaleTimeString()
    });
  }
  
  if (recommendations.length === 0) {
    recommendations.push({
      title: '健康状态良好',
      description: '各项生命体征正常，继续保持良好的生活习惯',
      type: '健康提醒',
      priority: 'normal',
      timestamp: new Date().toLocaleTimeString()
    });
  }
  
  return recommendations;
});

// 工具函数
const calculateAge = (birthDate: string) => {
  const today = new Date();
  const birth = new Date(birthDate);
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  
  return age;
};

const getPatientStatusType = (riskLevel: string) => {
  switch (riskLevel) {
    case '高风险': return 'error';
    case '中风险': return 'warning';
    case '低风险': return 'info';
    default: return 'success';
  }
};

const getVitalStatus = (vitalType: string) => {
  const vitals = currentVitals.value;
  
  switch (vitalType) {
    case 'heartRate':
      if (vitals.heartRate < 60 || vitals.heartRate > 100) return 'critical';
      if (vitals.heartRate < 65 || vitals.heartRate > 90) return 'warning';
      return 'normal';
    
    case 'bloodPressure':
      if (vitals.systolic > 140 || vitals.diastolic > 90) return 'critical';
      if (vitals.systolic > 120 || vitals.diastolic > 80) return 'warning';
      return 'normal';
    
    case 'oxygenSaturation':
      if (vitals.oxygenSaturation < 95) return 'critical';
      if (vitals.oxygenSaturation < 97) return 'warning';
      return 'normal';
    
    case 'temperature':
      if (vitals.temperature < 36.0 || vitals.temperature > 37.5) return 'warning';
      return 'normal';
    
    default:
      return 'normal';
  }
};

const getBPCategory = () => {
  const { systolic, diastolic } = currentVitals.value;
  
  if (systolic >= 140 || diastolic >= 90) return 'high';
  if (systolic >= 120 && systolic < 140) return 'elevated';
  return 'normal';
};

const getOxygenColor = (value: number) => {
  if (value < 95) return '#f5222d';
  if (value < 97) return '#faad14';
  return '#52c41a';
};

const getTempPosition = (temp: number) => {
  // 35-39°C 范围映射到 0-100%
  return Math.max(0, Math.min(100, ((temp - 35) / 4) * 100));
};

// 专业医疗指标计算
const calculateMAP = () => {
  // 平均动脉压 = (收缩压 + 2*舒张压) / 3
  const { systolic, diastolic } = currentVitals.value;
  return Math.round((systolic + 2 * diastolic) / 3);
};

const calculatePP = () => {
  // 脉压 = 收缩压 - 舒张压
  const { systolic, diastolic } = currentVitals.value;
  return systolic - diastolic;
};

const calculateBMR = () => {
  // 基础代谢率计算（Harris-Benedict方程）
  const age = calculateAge(selectedPatient.value.birthDate);
  const isMale = selectedPatient.value.gender === 'M';
  
  // 假设体重70kg，身高170cm
  const weight = 70;
  const height = 170;
  
  if (isMale) {
    return Math.round(88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age));
  } else {
    return Math.round(447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age));
  }
};

const getMAPStatus = () => {
  const map = calculateMAP();
  if (map < 70 || map > 105) return 'abnormal';
  return 'normal';
};

const getMAPStatusText = () => {
  const map = calculateMAP();
  if (map < 70) return '偏低';
  if (map > 105) return '偏高';
  return '正常';
};

const getPPStatus = () => {
  const pp = calculatePP();
  if (pp < 30 || pp > 60) return 'abnormal';
  return 'normal';
};

const getPPStatusText = () => {
  const pp = calculatePP();
  if (pp < 30) return '偏低';
  if (pp > 60) return '偏高';
  return '正常';
};

const getOxygenStatus = () => {
  const oxygen = currentVitals.value.oxygenSaturation;
  if (oxygen < 95) return 'critical';
  if (oxygen < 97) return 'warning';
  return 'normal';
};

const getOxygenStatusText = () => {
  const oxygen = currentVitals.value.oxygenSaturation;
  if (oxygen < 95) return '危险';
  if (oxygen < 97) return '注意';
  return '正常';
};

// 告警和风险相关
const getAlerts = (vitalType: string) => {
  const alerts = [];
  
  if (vitalType === 'heartRate' && currentVitals.value.heartRate > 100) {
    alerts.push({
      id: 1,
      type: 'warning',
      message: '心率超过正常范围，建议休息'
    });
  }
  
  return alerts;
};

const getRiskTagType = (level: string) => {
  switch (level) {
    case '高风险': return 'error';
    case '中风险': return 'warning';
    case '低风险': return 'info';
    default: return 'default';
  }
};

const getRiskColor = (level: string) => {
  switch (level) {
    case '高风险': return '#f5222d';
    case '中风险': return '#faad14';
    case '低风险': return '#1890ff';
    default: return '#52c41a';
  }
};

const getRecommendationColor = (priority: string) => {
  switch (priority) {
    case 'urgent': return '#f5222d';
    case 'high': return '#faad14';
    case 'medium': return '#1890ff';
    default: return '#52c41a';
  }
};

const getRecommendationIcon = (priority: string) => {
  switch (priority) {
    case 'urgent': return 'i-material-symbols:warning';
    case 'high': return 'i-material-symbols:priority-high';
    case 'medium': return 'i-material-symbols:info';
    default: return 'i-material-symbols:check-circle';
  }
};

// 图表相关
const heartRateChart = ref();
const trendChart = ref();

const initCharts = () => {
  // 初始化心率图表
  if (heartRateChart.value) {
    const chart = echarts.init(heartRateChart.value);
    chart.setOption({
      grid: { top: 10, right: 10, bottom: 10, left: 10 },
      xAxis: { show: false, type: 'category' },
      yAxis: { show: false, type: 'value' },
      series: [{
        data: [72, 74, 71, 73, 75, 72, 70],
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#f5222d', width: 2 }
      }]
    });
  }
  
  // 初始化趋势图表
  if (trendChart.value) {
    const chart = echarts.init(trendChart.value);
    chart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['心率', '收缩压', '舒张压', '血氧'] },
      grid: { top: 40, right: 20, bottom: 40, left: 60 },
      xAxis: {
        type: 'category',
        data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
      },
      yAxis: { type: 'value' },
      series: [
        {
          name: '心率',
          type: 'line',
          data: [68, 72, 75, 78, 74, 70],
          smooth: true,
          itemStyle: { color: '#f5222d' }
        },
        {
          name: '收缩压',
          type: 'line',
          data: [115, 118, 122, 125, 120, 116],
          smooth: true,
          itemStyle: { color: '#1890ff' }
        },
        {
          name: '舒张压',
          type: 'line',
          data: [72, 76, 78, 82, 79, 74],
          smooth: true,
          itemStyle: { color: '#52c41a' }
        },
        {
          name: '血氧',
          type: 'line',
          data: [98, 97, 98, 99, 98, 97],
          smooth: true,
          itemStyle: { color: '#faad14' }
        }
      ]
    });
  }
};

// 操作函数
const toggleRealtime = () => {
  isRealtime.value = !isRealtime.value;
  // TODO: 实现实时数据更新逻辑
};

const exportReport = () => {
  // TODO: 实现报告导出功能
  window.$message?.success('报告导出功能开发中...');
};
</script>

<style scoped>
.medical-dashboard {
  background: #f5f7fa;
  min-height: 100vh;
  padding: 16px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 专业医疗头部 */
.medical-header {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  margin-bottom: 20px;
}

.hospital-branding {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hospital-info h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
  letter-spacing: -0.5px;
}

.hospital-info p {
  font-size: 14px;
  color: #666;
  margin: 4px 0 0 0;
  font-weight: 400;
}

.system-status {
  display: flex;
  align-items: center;
  gap: 16px;
}

.timestamp {
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 14px;
  color: #666;
}

.patient-info-bar {
  padding: 16px 24px;
}

.patient-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #e6f4ff;
}

.patient-avatar {
  width: 48px;
  height: 48px;
  background: #e6f4ff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.patient-details h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 4px 0;
}

.patient-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #666;
}

/* 生命体征面板 */
.vital-signs-panel {
  margin-bottom: 20px;
}

.vital-signs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.vital-sign-item {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #f0f0f0;
  transition: all 0.2s ease;
}

.vital-sign-item.critical {
  border-left: 4px solid #f5222d;
}

.vital-sign-item:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.vital-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.vital-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.vital-icon.heart-rate {
  background: #fff2f0;
  color: #f5222d;
}

.vital-icon.blood-pressure {
  background: #e6f4ff;
  color: #1890ff;
}

.vital-icon.oxygen {
  background: #f6ffed;
  color: #52c41a;
}

.vital-icon.temperature {
  background: #fff7e6;
  color: #faad14;
}

.vital-info h4 {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.vital-info .unit {
  font-size: 12px;
  color: #999;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-left: auto;
}

.status-indicator.normal {
  background: #52c41a;
}

.status-indicator.warning {
  background: #faad14;
}

.status-indicator.critical {
  background: #f5222d;
}

.vital-value {
  margin-bottom: 16px;
}

.current-value {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a1a;
  display: block;
  line-height: 1;
  margin-bottom: 4px;
}

.reference-range {
  font-size: 12px;
  color: #666;
}

.mini-chart {
  height: 60px;
  margin-bottom: 12px;
}

.blood-pressure-categories {
  display: flex;
  gap: 12px;
}

.bp-category {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.bp-category.active {
  color: #1a1a1a;
  background: #f0f0f0;
}

.category-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.category-dot.normal {
  background: #52c41a;
}

.category-dot.elevated {
  background: #faad14;
}

.category-dot.high {
  background: #f5222d;
}

.oxygen-gauge {
  display: flex;
  justify-content: center;
  align-items: center;
}

.temperature-scale {
  margin-top: 16px;
}

.temp-bar {
  height: 6px;
  background: linear-gradient(to right, #1890ff, #52c41a, #faad14, #f5222d);
  border-radius: 3px;
  position: relative;
  margin-bottom: 8px;
}

.temp-indicator {
  position: absolute;
  top: -2px;
  width: 10px;
  height: 10px;
  background: white;
  border: 2px solid #1a1a1a;
  border-radius: 50%;
  transform: translateX(-50%);
}

.temp-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #999;
}

/* 分析面板 */
.analysis-panels {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.trend-chart {
  height: 300px;
}

.risk-matrix {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.risk-item {
  padding: 16px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.risk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.risk-category {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
}

.risk-score {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.score-text {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  min-width: 40px;
}

.risk-description {
  font-size: 12px;
  color: #666;
  margin: 0;
  line-height: 1.4;
}

/* 医疗指标 */
.medical-indicators {
  margin-bottom: 20px;
}

.indicators-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
}

.indicator-section h5 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e6f4ff;
}

.indicator-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.indicator-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #fafbfc;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
}

.indicator-name {
  font-size: 13px;
  color: #666;
  flex: 1;
}

.indicator-value {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 12px;
}

.indicator-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.indicator-status.normal {
  background: #f6ffed;
  color: #52c41a;
}

.indicator-status.abnormal {
  background: #fff2f0;
  color: #f5222d;
}

.indicator-status.warning {
  background: #fff7e6;
  color: #faad14;
}

/* 医疗建议 */
.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recommendation-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  border-left: 4px solid #1890ff;
}

.recommendation-item.urgent {
  border-left-color: #f5222d;
  background: #fff2f0;
}

.recommendation-item.high {
  border-left-color: #faad14;
  background: #fff7e6;
}

.recommendation-item.medium {
  border-left-color: #1890ff;
  background: #e6f4ff;
}

.recommendation-item.normal {
  border-left-color: #52c41a;
  background: #f6ffed;
}

.recommendation-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.recommendation-content h6 {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
}

.recommendation-content p {
  font-size: 13px;
  color: #666;
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.recommendation-meta {
  display: flex;
  gap: 16px;
}

.recommendation-type,
.recommendation-time {
  font-size: 11px;
  color: #999;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .analysis-panels {
    grid-template-columns: 1fr;
  }
  
  .indicators-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .medical-dashboard {
    padding: 12px;
  }
  
  .hospital-branding {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .vital-signs-grid {
    grid-template-columns: 1fr;
  }
  
  .patient-meta {
    flex-direction: column;
    gap: 4px;
  }
}
</style>