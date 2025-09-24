<script setup lang="ts">
import { computed, onMounted, ref, shallowRef, watch, nextTick } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';
import { 
  fetchGetHealthDataBasicList,
  fetchUserHealthData, 
  fetchHealthMetrics, 
  fetchHealthScore, 
  fetchHealthRecommendations, 
  fetchHealthTrends,
  fetchComprehensiveAnalysis 
} from '@/service/api';
import { fetchGetOrgUnitsTree } from '@/service/api';
import { useEcharts } from '@/hooks/common/echarts';
import { handleBindUsersByOrgId } from '@/utils/deviceUtils';
import HealthChartSearch from './modules/health-search.vue';
import HealthMetricsOverview from './components/HealthMetricsOverview.vue';
import ProfessionalChart from './components/ProfessionalChart.vue';
import HealthInsights from './components/HealthInsights.vue';
import ComparisonAnalysis from './components/ComparisonAnalysis.vue';
import ProfessionalMedicalDashboard from './components/ProfessionalMedicalDashboard.vue';
import MedicalChart from './components/MedicalChart.vue';

const appStore = useAppStore();
const authStore = useAuthStore();

const today = new Date();
const startDate = new Date(today.setHours(0, 0, 0, 0)).getTime();
const endDate = new Date(today.setHours(23, 59, 59, 999)).getTime();

const customerId = authStore.userInfo?.customerId;
const loading = ref(false);
const selectedUser = ref<any>(null);
const viewMode = ref<'overview' | 'detailed' | 'medical'>('medical');
const activeMetric = ref<string>('heart_rate');

const searchParams = ref({
  page: 1,
  pageSize: 10,
  orgId: null,
  userId: null,
  startDate,
  endDate,
  timeType: 'day',
  customerId,
  dataType: 'heart_rate'
});

type HealthData = {
  bloodOxygen: number[];
  heartRate: number[];
  pressureHigh: number[];
  pressureLow: number[];
  step: number[];
  temperature: number[];
  timestamps: string[];
  sleep: number[];
  stress: number[];
  calorie: number[];
  distance: number[];
};

type HealthMetrics = {
  current: Record<string, number>;
  average: Record<string, number>;
  trend: Record<string, 'up' | 'down' | 'stable'>;
  status: Record<string, 'normal' | 'warning' | 'danger'>;
  recommendations: string[];
};

const healthData = ref<HealthData>({
  bloodOxygen: [],
  heartRate: [],
  pressureHigh: [],
  pressureLow: [],
  step: [],
  temperature: [],
  timestamps: [],
  sleep: [],
  stress: [],
  calorie: [],
  distance: []
});

const healthMetrics = ref<HealthMetrics>({
  current: {},
  average: {},
  trend: {},
  status: {},
  recommendations: []
});

// 健康指标配置
const metricsConfig = {
  heart_rate: {
    name: '心率',
    unit: 'bpm',
    icon: 'i-material-symbols:favorite',
    color: '#FF6B6B',
    normal: { min: 60, max: 100 },
    format: (val: number) => `${val} bpm`
  },
  blood_oxygen: {
    name: '血氧',
    unit: '%',
    icon: 'i-material-symbols:air',
    color: '#4ECDC4',
    normal: { min: 95, max: 100 },
    format: (val: number) => `${val}%`
  },
  temperature: {
    name: '体温',
    unit: '°C',
    icon: 'i-material-symbols:device-thermostat',
    color: '#45B7D1',
    normal: { min: 36.1, max: 37.2 },
    format: (val: number) => `${val}°C`
  },
  pressure_high: {
    name: '收缩压',
    unit: 'mmHg',
    icon: 'i-material-symbols:monitor-heart',
    color: '#96CEB4',
    normal: { min: 90, max: 140 },
    format: (val: number) => `${val} mmHg`
  },
  pressure_low: {
    name: '舒张压',
    unit: 'mmHg',
    icon: 'i-material-symbols:monitor-heart-outline',
    color: '#FFEAA7',
    normal: { min: 60, max: 90 },
    format: (val: number) => `${val} mmHg`
  },
  step: {
    name: '步数',
    unit: '步',
    icon: 'i-material-symbols:directions-walk',
    color: '#DDA0DD',
    normal: { min: 6000, max: 15000 },
    format: (val: number) => `${val.toLocaleString()} 步`
  },
  sleep: {
    name: '睡眠',
    unit: '小时',
    icon: 'i-material-symbols:bedtime',
    color: '#98D8C8',
    normal: { min: 7, max: 9 },
    format: (val: number) => `${val} 小时`
  },
  stress: {
    name: '压力指数',
    unit: '',
    icon: 'i-material-symbols:psychology',
    color: '#F7DC6F',
    normal: { min: 0, max: 30 },
    format: (val: number) => `${val}`
  },
  calorie: {
    name: '卡路里',
    unit: 'kcal',
    icon: 'i-material-symbols:local-fire-department',
    color: '#FF9F43',
    normal: { min: 1200, max: 2500 },
    format: (val: number) => `${val} kcal`
  },
  distance: {
    name: '距离',
    unit: 'km',
    icon: 'i-material-symbols:route',
    color: '#6C5CE7',
    normal: { min: 3, max: 10 },
    format: (val: number) => `${val} km`
  }
};

function processYearlyMonthlyData(data: any, acc: HealthData, timeKey: string) {
  acc.heartRate.push(Number(data.heartRate) || 0);
  acc.bloodOxygen.push(Number(data.bloodOxygen) || 0);
  acc.pressureHigh.push(Number(data.pressureHigh) || 0);
  acc.pressureLow.push(Number(data.pressureLow) || 0);
  acc.step.push(Number(data.step) || 0);
  acc.temperature.push(Number(data.temperature) || 0);
  acc.sleep.push(Number(data.sleep) || 0);
  acc.stress.push(Number(data.stress) || 0);
  acc.calorie.push(Number(data.calorie) || 0);
  acc.distance.push(Number(data.distance) || 0);
  acc.timestamps.push(String(timeKey || ''));
}

function processDetailedData(data: any, acc: HealthData, timeKey: string) {
  const subKeys = Object.keys(data);
  subKeys.forEach(subTimeKey => {
    const subData = data[subTimeKey];
    if (subData && typeof subData === 'object') {
      acc.heartRate.push(Number(subData.heartRate) || 0);
      acc.bloodOxygen.push(Number(subData.bloodOxygen) || 0);
      acc.pressureHigh.push(Number(subData.pressureHigh) || 0);
      acc.pressureLow.push(Number(subData.pressureLow) || 0);
      acc.step.push(Number(subData.step) || 0);
      acc.temperature.push(Number(subData.temperature) || 0);
      acc.sleep.push(Number(subData.sleep) || 0);
      acc.stress.push(Number(subData.stress) || 0);
      acc.calorie.push(Number(subData.calorie) || 0);
      acc.distance.push(Number(subData.distance) || 0);
      acc.timestamps.push(`${timeKey} ${subTimeKey}`);
    }
  });
}

function initializeHealthDataArrays(acc: HealthData) {
  if (!Array.isArray(acc.heartRate)) acc.heartRate = [];
  if (!Array.isArray(acc.bloodOxygen)) acc.bloodOxygen = [];
  if (!Array.isArray(acc.pressureHigh)) acc.pressureHigh = [];
  if (!Array.isArray(acc.pressureLow)) acc.pressureLow = [];
  if (!Array.isArray(acc.step)) acc.step = [];
  if (!Array.isArray(acc.temperature)) acc.temperature = [];
  if (!Array.isArray(acc.sleep)) acc.sleep = [];
  if (!Array.isArray(acc.stress)) acc.stress = [];
  if (!Array.isArray(acc.calorie)) acc.calorie = [];
  if (!Array.isArray(acc.distance)) acc.distance = [];
  if (!Array.isArray(acc.timestamps)) acc.timestamps = [];
}

async function fetchHealthData() {
  loading.value = true;
  try {
    const apiParams = {
      customerId: searchParams.value.customerId,
      orgId: searchParams.value.orgId || '',
      userId: searchParams.value.userId,
      startDate: searchParams.value.startDate,
      endDate: searchParams.value.endDate,
      timeType: searchParams.value.timeType,
      dataType: searchParams.value.dataType
    };

    // 并行获取所有需要的数据
    const [chartDataResponse, metricsResponse, scoreResponse, recommendationsResponse] = await Promise.allSettled([
      fetchGetHealthDataBasicList(apiParams),
      fetchHealthMetrics(apiParams),
      fetchHealthScore(apiParams),
      fetchHealthRecommendations(apiParams)
    ]);

    // 处理图表数据
    if (chartDataResponse.status === 'fulfilled') {
      const response = chartDataResponse.value;
      if (response && response.data && response.data.records) {
        const records = response.data.records;
        
        // 初始化健康数据数组
        const newHealthData = {
          bloodOxygen: [] as number[],
          heartRate: [] as number[],
          pressureHigh: [] as number[],
          pressureLow: [] as number[],
          step: [] as number[],
          temperature: [] as number[],
          timestamps: [] as string[],
          sleep: [] as number[],
          stress: [] as number[],
          calorie: [] as number[],
          distance: [] as number[]
        };

        // 处理记录数据
        records.forEach((record: any) => {
          // 添加所有数据点，即使为0
          newHealthData.heartRate.push(Number(record.heartRate) || 0);
          newHealthData.bloodOxygen.push(Number(record.bloodOxygen) || 0);
          newHealthData.pressureHigh.push(Number(record.pressureHigh) || 0);
          newHealthData.pressureLow.push(Number(record.pressureLow) || 0);
          newHealthData.step.push(Number(record.step) || 0);
          newHealthData.temperature.push(Number(record.temperature) || 0);
          newHealthData.sleep.push(Number(record.sleep) || 0);
          newHealthData.stress.push(Number(record.stress) || 0);
          newHealthData.calorie.push(Number(record.calorie) || 0);
          newHealthData.distance.push(Number(record.distance) || 0);
          
          // 处理时间戳 - 格式化为简短显示
          const timestamp = record.timestamp ? 
            new Date(record.timestamp).toLocaleString('zh-CN', {
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            }) : '';
          newHealthData.timestamps.push(timestamp);
        });

        Object.assign(healthData.value, newHealthData);
        
        console.log('健康数据处理完成:', {
          recordsCount: records.length,
          healthData: newHealthData
        });
      }
    }

    // 处理健康指标数据
    if (metricsResponse.status === 'fulfilled' && metricsResponse.value?.data) {
      Object.assign(healthMetrics.value, metricsResponse.value.data);
    } else {
      console.log('API获取指标失败，使用本地计算');
      // 如果新API失败，使用本地计算
      calculateHealthMetrics();
    }
    
    // 确保总是执行本地计算作为兜底
    if (!healthMetrics.value.current || Object.keys(healthMetrics.value.current).length === 0) {
      calculateHealthMetrics();
    }

    console.log('健康数据获取完成:', {
      chartData: chartDataResponse.status,
      metrics: metricsResponse.status,
      score: scoreResponse.status,
      recommendations: recommendationsResponse.status
    });

  } catch (error) {
    console.error('Failed to fetch health data:', error);
    window.$message?.error('获取健康数据失败');
    resetHealthData();
    // 降级到本地计算
    calculateHealthMetrics();
  } finally {
    loading.value = false;
    
    // 最终确保指标计算完成
    console.log('最终健康指标状态:', {
      healthData: healthData.value,
      healthMetrics: healthMetrics.value,
      dataLength: {
        heartRate: healthData.value.heartRate?.length || 0,
        bloodOxygen: healthData.value.bloodOxygen?.length || 0,
        timestamps: healthData.value.timestamps?.length || 0
      }
    });
  }
}

function resetHealthData() {
  healthData.value = {
    bloodOxygen: [],
    heartRate: [],
    pressureHigh: [],
    pressureLow: [],
    step: [],
    temperature: [],
    timestamps: [],
    sleep: [],
    stress: [],
    calorie: [],
    distance: []
  };
  healthMetrics.value = {
    current: {},
    average: {},
    trend: {},
    status: {},
    recommendations: [],
    apiScore: undefined,
    apiStatus: undefined
  };
}

// 计算健康指标
function calculateHealthMetrics() {
  const metrics = healthMetrics.value;
  
  Object.keys(metricsConfig).forEach(key => {
    const data = healthData.value[key as keyof HealthData] as number[];
    if (data && data.length > 0) {
      const validData = data.filter(val => val > 0);
      if (validData.length > 0) {
        const current = validData[validData.length - 1];
        const average = validData.reduce((sum, val) => sum + val, 0) / validData.length;
        const config = metricsConfig[key as keyof typeof metricsConfig];
        
        metrics.current[key] = current;
        metrics.average[key] = average;
        
        // 计算趋势
        if (validData.length >= 2) {
          const recent = validData.slice(-3).reduce((sum, val) => sum + val, 0) / Math.min(3, validData.length);
          const earlier = validData.slice(0, -3).reduce((sum, val) => sum + val, 0) / Math.max(1, validData.length - 3);
          const change = recent - earlier;
          metrics.trend[key] = Math.abs(change) < average * 0.05 ? 'stable' : (change > 0 ? 'up' : 'down');
        } else {
          metrics.trend[key] = 'stable';
        }
        
        // 计算状态
        if (current >= config.normal.min && current <= config.normal.max) {
          metrics.status[key] = 'normal';
        } else if (current < config.normal.min * 0.8 || current > config.normal.max * 1.2) {
          metrics.status[key] = 'danger';
        } else {
          metrics.status[key] = 'warning';
        }
      }
    }
  });
  
  generateRecommendations();
}

// 生成健康建议
function generateRecommendations() {
  const recommendations: string[] = [];
  const metrics = healthMetrics.value;
  
  Object.keys(metrics.status).forEach(key => {
    const status = metrics.status[key];
    const config = metricsConfig[key as keyof typeof metricsConfig];
    const current = metrics.current[key];
    
    if (status === 'danger') {
      if (key === 'heart_rate') {
        if (current > config.normal.max) {
          recommendations.push('心率偏高，建议减少剧烈运动，保持情绪稳定');
        } else {
          recommendations.push('心率偏低，建议适当增加有氧运动');
        }
      } else if (key === 'blood_oxygen' && current < config.normal.min) {
        recommendations.push('血氧偏低，建议进行深呼吸练习，如有持续请就医');
      } else if (key === 'sleep' && current < config.normal.min) {
        recommendations.push('睡眠不足，建议保持规律作息，每晚7-9小时睡眠');
      } else if (key === 'step' && current < config.normal.min) {
        recommendations.push('运动量不足，建议每天至少6000步，增加日常活动');
      }
    } else if (status === 'warning') {
      recommendations.push(`${config.name}需要关注，建议保持健康生活方式`);
    }
  });
  
  if (recommendations.length === 0) {
    recommendations.push('各项健康指标正常，继续保持良好的生活习惯！');
  }
  
  metrics.recommendations = recommendations;
}

// 选择指标
function selectMetric(metricKey: string) {
  activeMetric.value = metricKey;
  searchParams.value.dataType = metricKey;
}

// 切换视图模式
function toggleViewMode() {
  viewMode.value = viewMode.value === 'overview' ? 'detailed' : 'overview';
}

// 获取指标键名映射
function getMetricKey(metric: string): keyof HealthData {
  const keyMap: Record<string, keyof HealthData> = {
    'heart_rate': 'heartRate',
    'blood_oxygen': 'bloodOxygen', 
    'temperature': 'temperature',
    'pressure_high': 'pressureHigh',
    'pressure_low': 'pressureLow',
    'step': 'step',
    'stress': 'stress',
    'calorie': 'calorie',
    'distance': 'distance',
    'sleep': 'sleep'
  };
  return keyMap[metric] || 'heartRate';
}

// 获取健康评分（优先使用API数据，降级到本地计算）
const healthScore = computed(() => {
  // 如果有API返回的评分数据，优先使用
  if (healthMetrics.value.apiScore !== undefined) {
    return healthMetrics.value.apiScore;
  }
  
  // 降级到本地计算
  const metrics = healthMetrics.value;
  if (!metrics.status || Object.keys(metrics.status).length === 0) {
    return 0;
  }
  
  const scores = Object.keys(metrics.status).map(key => {
    const status = metrics.status[key];
    switch (status) {
      case 'normal': return 100;
      case 'warning': return 70;
      case 'danger': return 30;
      default: return 50;
    }
  });
  
  return scores.length > 0 ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length) : 0;
});

// 获取总体健康状态（优先使用API数据）
const overallStatus = computed(() => {
  // 如果有API返回的状态数据，优先使用
  if (healthMetrics.value.apiStatus) {
    return healthMetrics.value.apiStatus;
  }
  
  // 降级到本地计算
  const score = healthScore.value;
  if (score >= 90) return { text: '优秀', color: '#52c41a', level: 'excellent' };
  if (score >= 75) return { text: '良好', color: '#1890ff', level: 'good' };
  if (score >= 60) return { text: '一般', color: '#faad14', level: 'fair' };
  return { text: '需改善', color: '#f5222d', level: 'poor' };
});

console.log('Initial dataType:', searchParams.value.dataType);
watch(
  () => searchParams.value.dataType,
  (newValue, oldValue) => {
    console.log(`dataType changed from ${oldValue} to ${newValue}`);
  }
);

console.log('searchParams.value.dataType', searchParams.value.dataType);

type OrgUnitsTree = Api.SystemManage.OrgUnitsTree;

/** org units tree data */
const orgUnitsTree = shallowRef<OrgUnitsTree[]>([]);
const userOptions = ref<{ label: string; value: string }[]>([]);

async function handleInitOptions() {
  fetchGetOrgUnitsTree(customerId).then(({ error, data: treeData }) => {
    if (!error && treeData) {
      orgUnitsTree.value = treeData;
      // 初始化时获取第一个部门的员工列表
      if (treeData.length > 0) {
        handleBindUsersByOrgId(treeData[0].id).then(result => {
          if (Array.isArray(result)) {
            userOptions.value = result;
          }
        });
      }
    }
  });
}

// 监听部门变化，更新员工列表
watch(
  () => searchParams.value.orgId,
  async newValue => {
    if (newValue) {
      const result = await handleBindUsersByOrgId(String(newValue));
      if (Array.isArray(result)) {
        userOptions.value = result;
      }
    }
  }
);

// console.log('healthData2', healthData.value);
onMounted(() => {
  handleInitOptions();
  fetchHealthData();
});
</script>

<template>
  <div class="health-dashboard">
    <!-- SVG 渐变定义 -->
    <svg width="0" height="0" style="position: absolute;">
      <defs>
        <linearGradient id="neon-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style="stop-color:#00f5ff;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#ff00aa;stop-opacity:1" />
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge> 
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>
    </svg>

    <!-- 顶部操作栏 -->
    <div class="dashboard-header">
      <div class="header-left">
        <div class="title-section">
          <h1 class="dashboard-title">
            <NIcon size="28" color="#1890ff">
              <i class="i-material-symbols:monitor-heart"></i>
            </NIcon>
            健康数据监控中心
          </h1>
          <p class="dashboard-subtitle">专业健康数据分析与监控平台</p>
        </div>
      </div>
      <div class="header-right">
        <NSpace>
          <NButton
            :type="viewMode === 'medical' ? 'primary' : 'default'"
            @click="viewMode = 'medical'"
          >
            <template #icon>
              <NIcon><i class="i-material-symbols:local-hospital"></i></NIcon>
            </template>
            医疗级监控
          </NButton>
          <NButton
            :type="viewMode === 'overview' ? 'primary' : 'default'"
            @click="viewMode = 'overview'"
          >
            <template #icon>
              <NIcon><i class="i-material-symbols:dashboard"></i></NIcon>
            </template>
            概览模式
          </NButton>
          <NButton
            :type="viewMode === 'detailed' ? 'primary' : 'default'"
            @click="viewMode = 'detailed'"
          >
            <template #icon>
              <NIcon><i class="i-material-symbols:analytics"></i></NIcon>
            </template>
            详细分析
          </NButton>
          <NButton :loading="loading" @click="fetchHealthData">
            <template #icon>
              <NIcon><i class="i-material-symbols:refresh"></i></NIcon>
            </template>
            刷新数据
          </NButton>
        </NSpace>
      </div>
    </div>

    <!-- 搜索条件 -->
    <HealthChartSearch
      v-model:model="searchParams"
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      :customer-id="customerId"
      @search="fetchHealthData"
    />

    <!-- 健康概览卡片 -->
    <div class="health-overview">
      <NCard class="health-score-card">
        <div class="score-content">
          <div class="score-circle">
            <NProgress
              type="circle"
              :percentage="healthScore"
              :stroke-width="8"
              :color="overallStatus.color"
              class="score-progress"
            >
              <div class="score-text">
                <div class="score-number">{{ healthScore }}</div>
                <div class="score-label">健康评分</div>
              </div>
            </NProgress>
          </div>
          <div class="score-info">
            <div class="status-tag">
              <NTag :color="{ color: overallStatus.color, textColor: '#fff' }" size="large">
                {{ overallStatus.text }}
              </NTag>
            </div>
            <div class="score-details">
              <div class="detail-item">
                <span class="label">监测指标</span>
                <span class="value">{{ Object.keys(healthMetrics.current).length }}</span>
              </div>
              <div class="detail-item">
                <span class="label">正常指标</span>
                <span class="value">
                  {{ Object.values(healthMetrics.status).filter(s => s === 'normal').length }}
                </span>
              </div>
              <div class="detail-item">
                <span class="label">异常指标</span>
                <span class="value danger">
                  {{ Object.values(healthMetrics.status).filter(s => s === 'danger').length }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </NCard>

      <!-- 快速指标 -->
      <div class="quick-metrics">
        <div
          v-for="(config, key) in metricsConfig"
          :key="key"
          class="metric-card"
          :class="{ active: activeMetric === key }"
          @click="selectMetric(key)"
        >
          <div class="metric-icon" :style="{ background: config.color }">
            <NIcon size="20" color="white">
              <i :class="config.icon"></i>
            </NIcon>
          </div>
          <div class="metric-content">
            <div class="metric-name">{{ config.name }}</div>
            <div class="metric-value">
              <span v-if="healthMetrics.current[key]" class="current-value">
                {{ config.format(healthMetrics.current[key]) }}
              </span>
              <span v-else class="no-data">暂无数据</span>
            </div>
            <div class="metric-status">
              <NIcon 
                v-if="healthMetrics.trend[key]"
                :color="
                  healthMetrics.trend[key] === 'up' ? '#52c41a' : 
                  healthMetrics.trend[key] === 'down' ? '#f5222d' : '#faad14'
                "
                size="14"
              >
                <i v-if="healthMetrics.trend[key] === 'up'" class="i-material-symbols:trending-up"></i>
                <i v-else-if="healthMetrics.trend[key] === 'down'" class="i-material-symbols:trending-down"></i>
                <i v-else class="i-material-symbols:trending-flat"></i>
              </NIcon>
              <NTag
                :type="
                  healthMetrics.status[key] === 'normal' ? 'success' :
                  healthMetrics.status[key] === 'warning' ? 'warning' : 'error'
                "
                size="small"
              >
                {{ 
                  healthMetrics.status[key] === 'normal' ? '正常' :
                  healthMetrics.status[key] === 'warning' ? '注意' : '异常'
                }}
              </NTag>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="dashboard-content">
      <!-- 医疗级监控模式 -->
      <template v-if="viewMode === 'medical'">
        <div class="medical-layout">
          <!-- 专业医疗监控面板 -->
          <ProfessionalMedicalDashboard
            :health-data="healthData"
            :health-metrics="healthMetrics"
            :loading="loading"
          />
          
          <!-- 专业医疗图表 -->
          <div class="medical-charts-grid">
            <MedicalChart
              v-for="metric in ['heart_rate', 'blood_oxygen', 'temperature', 'pressure_high']"
              :key="metric"
              :data="healthData[getMetricKey(metric)]"
              :timestamps="healthData.timestamps"
              :metric="metric"
              :loading="loading"
              :height="280"
              :realtime="true"
            />
          </div>
        </div>
      </template>

      <!-- 概览模式 -->
      <template v-else-if="viewMode === 'overview'">
        <div class="overview-layout">
          <!-- 指标概览 -->
          <HealthMetricsOverview
            :health-data="healthData"
            :health-metrics="healthMetrics"
            :metrics-config="metricsConfig"
            :loading="loading"
          />

          <!-- 健康洞察 -->
          <HealthInsights
            :health-metrics="healthMetrics"
            :health-score="healthScore"
            :overall-status="overallStatus"
          />
        </div>
      </template>

      <!-- 详细分析模式 -->
      <template v-else>
        <div class="detailed-layout">
          <!-- 专业图表 -->
          <ProfessionalChart
            :health-data="healthData"
            :active-metric="activeMetric"
            :metrics-config="metricsConfig"
            :loading="loading"
            @metric-change="selectMetric"
          />

          <!-- 对比分析 -->
          <ComparisonAnalysis
            :health-data="healthData"
            :health-metrics="healthMetrics"
            :metrics-config="metricsConfig"
            :search-params="searchParams"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.health-dashboard {
  padding: 24px;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3a 25%, #2d1b69 50%, #6b46c1 100%);
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.health-dashboard::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 40% 80%, rgba(99, 102, 241, 0.2) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.health-dashboard > * {
  position: relative;
  z-index: 1;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px 32px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  backdrop-filter: blur(20px);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.title-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dashboard-title {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 32px;
  font-weight: 800;
  margin: 0;
  background: linear-gradient(135deg, #00f5ff, #ff00aa, #00f5ff);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradientShift 3s ease-in-out infinite;
  text-shadow: 0 0 30px rgba(0, 245, 255, 0.5);
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.dashboard-subtitle {
  color: rgba(255, 255, 255, 0.7);
  font-size: 16px;
  margin: 8px 0 0 48px;
  font-weight: 300;
  letter-spacing: 0.5px;
}

.health-overview {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.health-score-card {
  background: linear-gradient(135deg, rgba(15, 15, 35, 0.8) 0%, rgba(45, 27, 105, 0.9) 100%);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  overflow: hidden;
  backdrop-filter: blur(20px);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
}

.health-score-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.1) 0%, rgba(255, 0, 170, 0.1) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.health-score-card:hover::before {
  opacity: 1;
}

.score-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
  gap: 20px;
}

.score-circle {
  position: relative;
}

.score-text {
  text-align: center;
}

.score-number {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 4px;
}

.score-info {
  width: 100%;
  text-align: center;
}

.status-tag {
  margin-bottom: 16px;
}

.score-details {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.detail-item .label {
  font-size: 12px;
  opacity: 0.8;
}

.detail-item .value {
  font-size: 18px;
  font-weight: 600;
}

.detail-item .value.danger {
  color: #ff7875;
}

.quick-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(20px);
  position: relative;
  overflow: hidden;
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.1) 0%, rgba(255, 0, 170, 0.1) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.metric-card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.3),
    0 0 20px rgba(0, 245, 255, 0.2);
  border-color: rgba(0, 245, 255, 0.5);
}

.metric-card:hover::before {
  opacity: 1;
}

.metric-card.active {
  border-color: rgba(0, 245, 255, 0.8);
  background: rgba(0, 245, 255, 0.1);
  box-shadow: 
    0 12px 32px rgba(0, 0, 0, 0.3),
    0 0 20px rgba(0, 245, 255, 0.3);
}

.metric-card.active::before {
  opacity: 0.5;
}

.metric-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0.1) 100%);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.metric-card:hover .metric-icon {
  transform: scale(1.1) rotate(5deg);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
}

.metric-content {
  flex: 1;
  min-width: 0;
}

.metric-name {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 6px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin-bottom: 8px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.metric-value .no-data {
  color: rgba(255, 255, 255, 0.5);
  font-size: 16px;
  font-weight: 400;
}

.metric-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dashboard-content {
  min-height: 600px;
}

.overview-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 28px;
  animation: fadeInUp 0.6s ease-out;
}

.detailed-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 28px;
  animation: fadeInUp 0.6s ease-out;
}

.medical-layout {
  display: flex;
  flex-direction: column;
  gap: 20px;
  animation: fadeInUp 0.6s ease-out;
}

.medical-charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
  gap: 20px;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 为所有卡片添加现代化玻璃态样式 */
:deep(.n-card) {
  background: rgba(255, 255, 255, 0.1) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  border-radius: 20px !important;
  backdrop-filter: blur(20px) !important;
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
  position: relative;
  overflow: hidden;
}

:deep(.n-card):hover {
  transform: translateY(-2px);
  box-shadow: 
    0 20px 50px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    0 0 30px rgba(0, 245, 255, 0.2) !important;
}

:deep(.n-card::before) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.05) 0%, rgba(255, 0, 170, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
  z-index: 0;
}

:deep(.n-card:hover::before) {
  opacity: 1;
}

:deep(.n-card > *) {
  position: relative;
  z-index: 1;
}

/* 为按钮添加科技感样式 */
:deep(.n-button) {
  border-radius: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  position: relative !important;
  overflow: hidden !important;
}

:deep(.n-button--primary-type) {
  background: linear-gradient(135deg, #00f5ff, #ff00aa) !important;
  border: none !important;
  box-shadow: 0 4px 15px rgba(0, 245, 255, 0.3) !important;
}

:deep(.n-button--primary-type:hover) {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 25px rgba(0, 245, 255, 0.4) !important;
}

:deep(.n-button--default-type) {
  background: rgba(255, 255, 255, 0.1) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: rgba(255, 255, 255, 0.9) !important;
  backdrop-filter: blur(10px) !important;
}

:deep(.n-button--default-type:hover) {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(0, 245, 255, 0.5) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2) !important;
}

/* 为卡片标题添加科技感 */
:deep(.n-card-header__main) {
  color: rgba(255, 255, 255, 0.95) !important;
  font-weight: 700 !important;
  font-size: 18px !important;
  letter-spacing: 0.5px !important;
}

:deep(.n-card-header) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
  backdrop-filter: blur(10px) !important;
}

/* 为进度条添加科技感 */
:deep(.n-progress) {
  --n-fill-color: linear-gradient(90deg, #00f5ff, #ff00aa) !important;
}

:deep(.n-progress .n-progress-graph-circle-fill) {
  stroke: url(#neon-gradient) !important;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .health-overview {
    grid-template-columns: 1fr;
  }
  
  .quick-metrics {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }
  
  .overview-layout {
    grid-template-columns: 1fr;
  }
  
  .medical-charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .health-dashboard {
    padding: 16px;
  }
  
  .dashboard-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .dashboard-title {
    font-size: 24px;
  }
  
  .quick-metrics {
    grid-template-columns: 1fr;
  }
  
  .score-details {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
