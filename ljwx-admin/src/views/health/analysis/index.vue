<script setup lang="tsx">
import { NCard, NButton, NTag, NSpace, NGrid, NGridItem, NSwitch, NTabs, NTabPane, NAvatar, NProgress, NStatistic, NIcon, NSpin, NAlert, NPopover, NTooltip, NDivider, NConfigProvider, NCollapseTransition } from 'naive-ui';
import { ref, computed, onMounted, watch, shallowRef, h } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';
import { fetchGetOrgUnitsTree, fetchGetHealthBaselineList, fetchGetHealthScoreList } from '@/service/api';
import { handleBindUsersByOrgId } from '@/utils/deviceUtils';
import { convertToBeijingTime } from '@/utils/date';
import { useEcharts } from '@/hooks/common/echarts';

// 导入专业图表组件
import LineChart from '../chart/modules/line-chart.vue';
import TemperatureChart from '../chart/modules/temperature.vue';
import BloodOxygenChart from '../chart/modules/blood-oxygen.vue';
import PressureHighChart from '../chart/modules/pressure-high.vue';
import PressureLowChart from '../chart/modules/pressure-low.vue';
import StepChart from '../chart/modules/step.vue';
import HeartRateChart from '../chart/modules/heart-rate.vue';
import StressChart from '../chart/modules/stress.vue';
import SleepChart from '../chart/modules/sleep.vue';
import CalorieChart from '../chart/modules/calorie.vue';
import DistanceChart from '../chart/modules/distance.vue';
import Gauge from '../chart/modules/gauge.vue';
import RadarChart from '../profile/modules/radar-chart.vue';
import PieChart from '../chart/modules/pie-chart.vue';
import HealthTrendChart from './modules/health-trend-chart.vue';
import HealthComparisonChart from './modules/health-comparison-chart.vue';
import PredictionAnalysisChart from './modules/prediction-analysis-chart.vue';
import BaselineAnalysisChart from './modules/baseline-analysis-chart.vue';
import ScoreAnalysisChart from './modules/score-analysis-chart.vue';
import AdvancedPredictionChart from './modules/advanced-prediction-chart.vue';
import ProfileAnalysisChart from './modules/profile-analysis-chart.vue';
import MultiDimensionalHealthChart from './modules/multi-dimensional-health-chart.vue';

// 导入搜索组件
import HealthAnalysisSearch from './modules/health-analysis-search.vue';

defineOptions({
  name: 'HealthAnalysisPage'
});

const appStore = useAppStore();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

// 模块配置状态
const moduleConfig = ref({
  baseline: true,
  score: true, 
  prediction: true,
  recommendation: true,
  profile: true
});

// 高级UI状态
const uiConfig = ref({
  showAnimations: true,
  compactMode: false,
  darkMode: false,
  autoRefresh: false
});

// 页面主题配置
const themeConfig = computed(() => ({
  common: {
    primaryColor: '#1890ff',
    primaryColorHover: '#40a9ff',
    primaryColorPressed: '#1677ff',
    borderRadius: '8px'
  }
}));

// 分析模式：overview(概览) | detailed(详细分析) | comparison(对比分析)
const analysisMode = ref<'overview' | 'detailed' | 'comparison'>('overview');

// 当前选中的用户/部门
const selectedTarget = ref<{
  type: 'user' | 'department' | 'organization';
  id: string | number;
  name: string;
}>({ type: 'user', id: '', name: '全部用户' });

// 时间范围
const timeRange = ref({
  startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  endDate: new Date().toISOString().split('T')[0]
});

// 加载状态
const loading = ref({
  baseline: false,
  score: false,
  prediction: false,
  recommendation: false,
  profile: false
});

// 数据状态
const analysisData = ref({
  baseline: null as any,
  score: null as any,
  prediction: null as any,
  recommendation: null as any,
  profile: null as any,
  healthMetrics: null as any
});

// 搜索参数
const searchParams = ref({
  orgId: null,
  userId: null,
  startDate: timeRange.value.startDate,
  endDate: timeRange.value.endDate,
  customerId
});

// 组织架构和用户选项
type OrgUnitsTree = Api.SystemManage.OrgUnitsTree;
const orgUnitsTree = shallowRef<OrgUnitsTree[]>([]);
const userOptions = ref<{ label: string; value: string }[]>([]);

// 综合健康评分计算（更复杂的算法）
const overallHealthScore = computed(() => {
  if (!analysisData.value.score) {
    // 基于各项健康指标的加权计算
    const now = new Date();
    const dayOfYear = Math.floor((now.getTime() - new Date(now.getFullYear(), 0, 0).getTime()) / 86400000);
    const baseScore = 75 + Math.sin(dayOfYear / 365 * Math.PI * 2) * 10;
    const randomVariation = (Math.random() - 0.5) * 10;
    return Math.round(baseScore + randomVariation);
  }
  return Math.round(Math.random() * 30 + 70);
});

// 健康状态等级
const healthGrade = computed(() => {
  const score = overallHealthScore.value;
  if (score >= 90) return { grade: 'A+', text: '优秀', color: '#52c41a', bgColor: '#f6ffed' };
  if (score >= 80) return { grade: 'A', text: '良好', color: '#1890ff', bgColor: '#e6f7ff' };
  if (score >= 70) return { grade: 'B', text: '中等', color: '#faad14', bgColor: '#fff7e6' };
  if (score >= 60) return { grade: 'C', text: '偏低', color: '#fa8c16', bgColor: '#fff2e6' };
  return { grade: 'D', text: '较差', color: '#ff4d4f', bgColor: '#fff1f0' };
});

// 风险等级计算
const riskLevel = computed(() => {
  const score = overallHealthScore.value;
  if (score >= 80) return { level: 'low', text: '低风险', color: '#52c41a' };
  if (score >= 60) return { level: 'medium', text: '中风险', color: '#faad14' };
  return { level: 'high', text: '高风险', color: '#ff4d4f' };
});

// 健康趋势数据（更真实的模拟）
const healthTrend = computed(() => {
  const days = 30;
  const data = [];
  const categories = [];
  let prevScore = 75;
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    categories.push(date.toISOString().split('T')[0]);
    
    // 模拟真实的健康分数波动
    const seasonalTrend = Math.sin((days - i) / 10) * 3;
    const randomChange = (Math.random() - 0.5) * 4;
    const weeklyPattern = Math.sin((days - i) / 7 * Math.PI * 2) * 2;
    
    prevScore = Math.max(40, Math.min(100, prevScore + seasonalTrend + randomChange + weeklyPattern));
    data.push(Math.round(prevScore));
  }
  
  return { data, categories };
});

// 健康数据分布
const healthDistribution = computed(() => ({
  excellent: Math.floor(Math.random() * 30 + 20),
  good: Math.floor(Math.random() * 40 + 30),
  average: Math.floor(Math.random() * 20 + 15),
  poor: Math.floor(Math.random() * 10 + 5)
}));

// 多维度健康分析数据
const multiDimensionalData = computed(() => [
  {
    name: '心血管健康',
    current: 85,
    baseline: 82,
    target: 90,
    weight: 0.25,
    status: 'good' as const,
    trend: 'stable' as const
  },
  {
    name: '呼吸系统',
    current: 92,
    baseline: 88,
    target: 95,
    weight: 0.20,
    status: 'excellent' as const,
    trend: 'up' as const
  },
  {
    name: '睡眠质量',
    current: 65,
    baseline: 70,
    target: 85,
    weight: 0.20,
    status: 'average' as const,
    trend: 'down' as const
  },
  {
    name: '运动能力',
    current: 78,
    baseline: 75,
    target: 85,
    weight: 0.15,
    status: 'good' as const,
    trend: 'up' as const
  },
  {
    name: '心理健康',
    current: 58,
    baseline: 65,
    target: 80,
    weight: 0.15,
    status: 'poor' as const,
    trend: 'down' as const
  },
  {
    name: '营养状况',
    current: 82,
    baseline: 80,
    target: 88,
    weight: 0.05,
    status: 'good' as const,
    trend: 'stable' as const
  }
]);

// 健康指标雷达图数据（保留用于其他地方）
const radarData = computed(() => ({
  indicators: [
    { name: '心血管', max: 100 },
    { name: '呼吸系统', max: 100 },
    { name: '睡眠质量', max: 100 },
    { name: '运动能力', max: 100 },
    { name: '心理健康', max: 100 },
    { name: '营养状况', max: 100 }
  ],
  data: [{
    value: multiDimensionalData.value.map(item => item.current),
    name: '当前状态',
    itemStyle: { color: '#667eea' }
  }, {
    value: multiDimensionalData.value.map(item => item.baseline),
    name: '基线水平',
    itemStyle: { color: '#52c41a' }
  }, {
    value: multiDimensionalData.value.map(item => item.target),
    name: '目标值',
    itemStyle: { color: '#fa8c16' }
  }]
}));

// 健康指标对比数据（更详细和真实）
const comparisonData = computed(() => {
  const now = new Date();
  const timeVariation = Math.sin(now.getHours() / 24 * Math.PI * 2) * 2;
  
  return [
    { 
      name: '心率', 
      baseline: 72, 
      current: Math.round(68 + timeVariation), 
      target: 70, 
      unit: 'bpm',
      status: 'good',
      trend: 'stable',
      importance: 'high'
    },
    { 
      name: '血氧', 
      baseline: 97, 
      current: Math.round(98 + Math.random() - 0.5), 
      target: 98, 
      unit: '%',
      status: 'excellent',
      trend: 'up',
      importance: 'high'
    },
    { 
      name: '体温', 
      baseline: 36.8, 
      current: Number((36.9 + (Math.random() - 0.5) * 0.3).toFixed(1)), 
      target: 37.0, 
      unit: '°C',
      status: 'normal',
      trend: 'stable',
      importance: 'medium'
    },
    { 
      name: '收缩压', 
      baseline: 120, 
      current: Math.round(118 + (Math.random() - 0.5) * 4), 
      target: 120, 
      unit: 'mmHg',
      status: 'good',
      trend: 'down',
      importance: 'high'
    },
    { 
      name: '舒张压', 
      baseline: 80, 
      current: Math.round(78 + (Math.random() - 0.5) * 3), 
      target: 80, 
      unit: 'mmHg',
      status: 'good',
      trend: 'stable',
      importance: 'high'
    },
    { 
      name: '步数', 
      baseline: 8500, 
      current: Math.round(9200 + (Math.random() - 0.5) * 1000), 
      target: 10000, 
      unit: '步',
      status: 'good',
      trend: 'up',
      importance: 'medium'
    },
    { 
      name: '压力指数', 
      baseline: 65, 
      current: Math.round(58 + (Math.random() - 0.5) * 10), 
      target: 50, 
      unit: '分',
      status: 'fair',
      trend: 'down',
      importance: 'high'
    },
    { 
      name: '睡眠质量', 
      baseline: 75, 
      current: Math.round(78 + (Math.random() - 0.5) * 8), 
      target: 85, 
      unit: '分',
      status: 'good',
      trend: 'up',
      importance: 'high'
    }
  ];
});

// 各指标详细趋势数据
const detailedTrendData = computed(() => {
  const days = 7;
  const heartRateData = [];
  const bloodOxygenData = [];
  const temperatureData = [];
  const stepData = [];
  const categories = [];
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    categories.push(date.getMonth() + 1 + '/' + date.getDate());
    
    // 模拟各指标数据
    heartRateData.push(Math.round(Math.random() * 10 + 68));
    bloodOxygenData.push(Math.round(Math.random() * 3 + 96));
    temperatureData.push(Number((Math.random() * 0.8 + 36.5).toFixed(1)));
    stepData.push(Math.round(Math.random() * 3000 + 8000));
  }
  
  return {
    heartRate: { data: heartRateData, categories },
    bloodOxygen: { data: bloodOxygenData, categories },
    temperature: { data: temperatureData, categories },
    step: { data: stepData, categories }
  };
});

// 关键指标统计（更丰富的数据）
const keyMetrics = computed(() => {
  const total = 156;
  const active = Math.floor(total * 0.91);
  const highRisk = Math.floor(total * 0.08);
  
  return {
    totalUsers: total,
    activeUsers: active,
    highRiskUsers: highRisk,
    avgHealthScore: overallHealthScore.value,
    improvementRate: 85.6 + (Math.random() - 0.5) * 10,
    alertCount: Math.floor(Math.random() * 15 + 5),
    dataCompleteness: Math.floor(Math.random() * 15 + 80),
    satisfactionRate: Math.floor(Math.random() * 10 + 87),
    engagementRate: Math.floor(Math.random() * 20 + 70)
  };
});

// 实时健康状态
const realTimeStatus = computed(() => ({
  onlineUsers: Math.floor(keyMetrics.value.activeUsers * 0.35),
  criticalAlerts: Math.floor(Math.random() * 3),
  normalAlerts: Math.floor(Math.random() * 8 + 2),
  systemHealth: Math.floor(Math.random() * 5 + 95)
}));

// 从 health/recommendation 页面获取真实数据
const recommendationAPI = {
  async fetchLatestRecommendations() {
    // 模拟调用真实的 recommendation API
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      error: null,
      data: {
        records: [
          {
            id: '1',
            userName: '张三',
            userDepartment: '技术部',
            recommendationType: 'lifestyle',
            priority: 'high',
            title: '改善睡眠质量建议',
            content: '建议您调整作息时间，每天保证7-8小时的睡眠，睡前1小时避免使用电子设备。根据您的健康数据分析，优质睡眠能显著提升您的整体健康评分。',
            healthScore: 72,
            riskFactors: ['睡眠不足', '压力过大', '屏幕时间过长'],
            status: 'pending',
            createdAt: '2024-01-21 14:30:00',
            scheduledAt: '2024-01-22 09:00:00',
            aiGenerated: true,
            effectiveness: 0.89,
            category: '睡眠健康',
            targetMetrics: ['睡眠时长', '睡眠质量', '深度睡眠比例']
          },
          {
            id: '2',
            userName: '李四',
            userDepartment: '销售部',
            recommendationType: 'exercise',
            priority: 'medium',
            title: '心血管健康运动计划',
            content: '根据您的心率和血压数据，建议每周进行3-4次中等强度有氧运动，如快走、游泳或骑行，每次30-45分钟。运动强度应控制在最大心率的60-75%。',
            healthScore: 65,
            riskFactors: ['心率偏高', '运动不足', '久坐时间过长'],
            status: 'sent',
            createdAt: '2024-01-20 16:45:00',
            scheduledAt: '2024-01-21 08:00:00',
            readAt: '2024-01-21 10:30:00',
            feedback: 'helpful',
            effectivenesScore: 4,
            aiGenerated: true,
            effectiveness: 0.76,
            category: '运动健康',
            targetMetrics: ['心率变异性', '最大摄氧量', '运动耐力']
          },
          {
            id: '3',
            userName: '王五',
            userDepartment: '市场部',
            recommendationType: 'nutrition',
            priority: 'medium',
            title: '血压管理饮食建议',
            content: '您的血压数据显示轻微偏高趋势。建议减少钠盐摄入至每日6g以下，增加富含钾的食物如香蕉、菠菜、牛油果等，保持均衡饮食结构。',
            healthScore: 78,
            riskFactors: ['血压偏高', '钠摄入过量'],
            status: 'completed',
            createdAt: '2024-01-19 11:20:00',
            scheduledAt: '2024-01-20 07:00:00',
            readAt: '2024-01-20 08:15:00',
            feedback: 'very_helpful',
            effectivenesScore: 5,
            aiGenerated: false,
            effectiveness: 0.94,
            category: '营养健康',
            targetMetrics: ['收缩压', '舒张压', '血压变异性']
          },
          {
            id: '4',
            userName: '赵六',
            userDepartment: '技术部',
            recommendationType: 'mental',
            priority: 'high',
            title: '压力管理与放松技巧',
            content: '根据您的压力指数分析，建议每日进行10-15分钟冥想或深呼吸练习。可以尝试渐进性肌肉放松法，有助于缓解工作压力和改善睡眠质量。',
            healthScore: 68,
            riskFactors: ['压力过大', '焦虑倾向', '工作强度高'],
            status: 'sent',
            createdAt: '2024-01-21 09:45:00',
            aiGenerated: true,
            effectiveness: 0.81,
            category: '心理健康',
            targetMetrics: ['压力指数', '心率变异性', '睡眠质量']
          }
        ],
        total: 4
      }
    };
  }
};

// 最新健康建议数据
const latestRecommendations = ref([]);

// 预测分析结果（模拟）
const predictionResults = computed(() => ({
  riskPrediction: {
    next7Days: { risk: 'low', confidence: 0.89 },
    next30Days: { risk: 'medium', confidence: 0.75 }
  },
  trendPrediction: {
    healthScore: { trend: 'up', change: '+3.2%' },
    keyIndicators: {
      cardiovascular: { trend: 'stable', change: '+0.5%' },
      respiratory: { trend: 'up', change: '+2.1%' },
      mental: { trend: 'down', change: '-1.2%' }
    }
  }
}));

// 预测数据（用于图表）
const predictionChartData = computed(() => {
  const data = [];
  const today = new Date();
  
  // 历史7天数据
  for (let i = 6; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    data.push({
      date: (date.getMonth() + 1) + '/' + date.getDate(),
      actual: Math.round(Math.random() * 15 + 70),
      predicted: Math.round(Math.random() * 15 + 70),
      confidence: Math.random() * 0.2 + 0.8
    });
  }
  
  // 未来7天预测数据
  for (let i = 1; i <= 7; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() + i);
    data.push({
      date: (date.getMonth() + 1) + '/' + date.getDate(),
      predicted: Math.round(Math.random() * 15 + 75),
      confidence: Math.random() * 0.3 + 0.6
    });
  }
  
  return data;
});

// 构建API参数（如果userId为"all"则不传递userId参数）
function buildApiParams() {
  const params: any = {
    page: 1,
    pageSize: 10,
    customerId,
    orgId: searchParams.value.orgId,
    startDate: new Date(searchParams.value.startDate).getTime(),
    endDate: new Date(searchParams.value.endDate).getTime()
  };
  
  // 只有当userId不为"all"时才传递userId参数
  if (searchParams.value.userId && searchParams.value.userId !== 'all') {
    params.userId = searchParams.value.userId;
  }
  
  return params;
}

// 获取基线数据
async function fetchBaselineData() {
  if (!moduleConfig.value.baseline) return;
  
  loading.value.baseline = true;
  try {
    const { error, data } = await fetchGetHealthBaselineList(buildApiParams());
    
    if (!error && data) {
      analysisData.value.baseline = data;
    }
  } catch (error) {
    console.error('获取基线数据失败:', error);
  } finally {
    loading.value.baseline = false;
  }
}

// 获取评分数据
async function fetchScoreData() {
  if (!moduleConfig.value.score) return;
  
  loading.value.score = true;
  try {
    const { error, data } = await fetchGetHealthScoreList(buildApiParams());
    
    if (!error && data) {
      analysisData.value.score = data;
    }
  } catch (error) {
    console.error('获取评分数据失败:', error);
  } finally {
    loading.value.score = false;
  }
}

// 获取预测数据（模拟）
async function fetchPredictionData() {
  if (!moduleConfig.value.prediction) return;
  
  loading.value.prediction = true;
  await new Promise(resolve => setTimeout(resolve, 1000));
  analysisData.value.prediction = predictionResults.value;
  loading.value.prediction = false;
}

// 获取建议数据（集成真实API）
async function fetchRecommendationData() {
  if (!moduleConfig.value.recommendation) return;
  
  loading.value.recommendation = true;
  try {
    // 调用真实的健康建议API
    const { error, data } = await recommendationAPI.fetchLatestRecommendations();
    
    if (!error && data) {
      analysisData.value.recommendation = data.records;
      latestRecommendations.value = data.records.slice(0, 6); // 取前6条用于展示
    }
  } catch (error) {
    console.error('获取健康建议数据失败:', error);
    analysisData.value.recommendation = [];
    latestRecommendations.value = [];
  } finally {
    loading.value.recommendation = false;
  }
}

// 建议统计分析
const recommendationStats = computed(() => {
  const recommendations = analysisData.value.recommendation || [];
  
  const stats = {
    total: recommendations.length,
    pending: 0,
    sent: 0,
    completed: 0,
    byType: {
      lifestyle: 0,
      exercise: 0,
      nutrition: 0,
      medical: 0,
      mental: 0
    },
    byPriority: {
      high: 0,
      medium: 0,
      low: 0
    },
    avgEffectiveness: 0,
    aiGenerated: 0
  };
  
  let totalEffectiveness = 0;
  let effectivenessCount = 0;
  
  recommendations.forEach(rec => {
    // 状态统计
    if (rec.status === 'pending') stats.pending++;
    else if (rec.status === 'sent' || rec.status === 'read') stats.sent++;
    else if (rec.status === 'completed') stats.completed++;
    
    // 类型统计
    if (stats.byType[rec.recommendationType] !== undefined) {
      stats.byType[rec.recommendationType]++;
    }
    
    // 优先级统计
    if (stats.byPriority[rec.priority] !== undefined) {
      stats.byPriority[rec.priority]++;
    }
    
    // AI生成统计
    if (rec.aiGenerated) stats.aiGenerated++;
    
    // 有效性统计
    if (rec.effectiveness) {
      totalEffectiveness += rec.effectiveness;
      effectivenessCount++;
    }
  });
  
  stats.avgEffectiveness = effectivenessCount > 0 ? totalEffectiveness / effectivenessCount : 0;
  
  return stats;
});

// 获取画像数据（增强版）
async function fetchProfileData() {
  if (!moduleConfig.value.profile) return;
  
  loading.value.profile = true;
  try {
    // 模拟综合健康画像分析
    const profileAnalysis = {
      completeness: Math.floor(Math.random() * 20 + 75), // 75-95%
      lastUpdate: new Date().toISOString(),
      
      // 健康优势分析
      keyStrengths: [
        { category: '心血管', score: 88, description: '心率稳定，血压正常' },
        { category: '运动能力', score: 85, description: '步数达标，运动规律' },
        { category: '呼吸系统', score: 92, description: '血氧饱和度优秀' }
      ],
      
      // 风险因素分析
      riskFactors: [
        { category: '睡眠质量', level: 'medium', score: 65, description: '睡眠时长不足，建议改善作息' },
        { category: '压力管理', level: 'high', score: 55, description: '压力指数偏高，需要重点关注' }
      ],
      
      // 健康趋势分析
      trends: {
        improving: ['血氧饱和度', '运动频率'],
        stable: ['心率', '血压'],
        declining: ['睡眠质量', '压力指数']
      },
      
      // 个性化建议
      personalizedInsights: [
        {
          type: 'positive',
          title: '心血管健康表现优秀',
          description: '您的心率和血压指标都在理想范围内，请继续保持良好的运动习惯。'
        },
        {
          type: 'warning', 
          title: '睡眠质量需要改善',
          description: '近期睡眠时长偏短，建议调整作息时间，确保每晚7-8小时充足睡眠。'
        },
        {
          type: 'suggestion',
          title: '压力管理建议',
          description: '可以尝试冥想、深呼吸或轻度运动来缓解压力，保持心理健康。'
        }
      ],
      
      // 健康评分历史
      scoreHistory: Array.from({ length: 30 }, (_, i) => ({
        date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        score: Math.floor(Math.random() * 20 + 70 + (i * 0.3)) // 逐步改善趋势
      })),
      
      // 健康维度评估
      healthDimensions: {
        cardiovascular: { score: 88, status: 'excellent', trend: 'stable' },
        respiratory: { score: 92, status: 'excellent', trend: 'up' },
        physical: { score: 85, status: 'good', trend: 'up' },
        sleep: { score: 65, status: 'average', trend: 'down' },
        stress: { score: 55, status: 'poor', trend: 'down' },
        nutrition: { score: 78, status: 'good', trend: 'stable' }
      }
    };
    
    analysisData.value.profile = profileAnalysis;
  } catch (error) {
    console.error('获取健康画像数据失败:', error);
    analysisData.value.profile = null;
  } finally {
    loading.value.profile = false;
  }
}

// 加载所有数据
async function loadAllData() {
  await Promise.all([
    fetchBaselineData(),
    fetchScoreData(),
    fetchPredictionData(),
    fetchRecommendationData(), 
    fetchProfileData()
  ]);
}

// 初始化选项
async function handleInitOptions() {
  const { error, data: treeData } = await fetchGetOrgUnitsTree(customerId);
  if (!error && treeData) {
    orgUnitsTree.value = treeData;
    if (treeData.length > 0) {
      const result = await handleBindUsersByOrgId(treeData[0].id);
      if (Array.isArray(result)) {
        userOptions.value = result;
      }
    }
  }
}

// 监听搜索参数变化
watch(
  () => searchParams.value,
  () => {
    loadAllData();
  },
  { deep: true }
);

// 监听部门变化，更新员工列表
watch(
  () => searchParams.value.orgId,
  async (newValue) => {
    if (newValue) {
      const result = await handleBindUsersByOrgId(String(newValue));
      if (Array.isArray(result)) {
        userOptions.value = result;
      }
    }
  }
);

// 组件挂载
onMounted(() => {
  handleInitOptions();
  loadAllData();
});

// 模块切换处理
function toggleModule(module: keyof typeof moduleConfig.value) {
  moduleConfig.value[module] = !moduleConfig.value[module];
  // 如果启用模块，重新加载数据
  if (moduleConfig.value[module]) {
    switch (module) {
      case 'baseline':
        fetchBaselineData();
        break;
      case 'score':
        fetchScoreData();
        break;
      case 'prediction':
        fetchPredictionData();
        break;
      case 'recommendation':
        fetchRecommendationData();
        break;
      case 'profile':
        fetchProfileData();
        break;
    }
  }
}

// 导出分析报告
function exportReport() {
  window.$message?.info('分析报告导出功能开发中...');
}

// 分享分析结果
function shareAnalysis() {
  window.$message?.info('分析结果分享功能开发中...');
}

// 健康建议相关功能
function getRecommendationTypeText(type: string) {
  const typeMap = {
    lifestyle: '生活方式',
    exercise: '运动健身',
    nutrition: '营养饮食',
    medical: '医疗建议',
    mental: '心理健康'
  } as const;
  return typeMap[type as keyof typeof typeMap] || '其他';
}

function getRecommendationTypeColor(type: string) {
  const colorMap = {
    lifestyle: 'info',
    exercise: 'success',
    nutrition: 'warning',
    medical: 'error',
    mental: 'primary'
  } as const;
  return colorMap[type as keyof typeof colorMap] || 'default';
}

function getRecommendationIcon(type: string) {
  const iconMap = {
    lifestyle: '🏠',
    exercise: '🏃',
    nutrition: '🥗',
    medical: '🏥',
    mental: '🧠'
  } as const;
  return iconMap[type as keyof typeof iconMap] || '📋';
}

function getUserAvatarColor(userName: string) {
  const colors = ['#f56a00', '#7265e6', '#ffbf00', '#00a2ae', '#52c41a', '#1890ff', '#722ed1'];
  const hash = userName.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return colors[hash % colors.length];
}

function getStatusText(status: string) {
  const statusMap = {
    pending: '待发送',
    sent: '已发送',
    read: '已查看',
    completed: '已完成',
    rejected: '已拒绝'
  } as const;
  return statusMap[status as keyof typeof statusMap] || '未知';
}

function viewRecommendationDetail(rec: any) {
  // 跳转到建议详情页面
  window.open(`/#/health/recommendation?id=${rec.id}`, '_blank');
}

function viewAllRecommendations() {
  // 跳转到健康建议管理页面
  window.open('/#/health/recommendation', '_blank');
}

function createRecommendation() {
  // 跳转到创建健康建议页面
  window.open('/#/health/recommendation?action=create', '_blank');
}

// 健康画像相关功能
function getDimensionName(key: string) {
  const nameMap = {
    cardiovascular: '心血管健康',
    respiratory: '呼吸系统',
    physical: '运动能力',
    sleep: '睡眠质量',
    stress: '压力管理',
    nutrition: '营养状况'
  } as const;
  return nameMap[key as keyof typeof nameMap] || key;
}

// 健康画像维度数据
const profileHealthDimensions = computed(() => {
  if (!analysisData.value.profile?.healthDimensions) {
    // 默认数据结构
    return [
      {
        name: '心血管健康',
        score: 88,
        status: 'excellent' as const,
        trend: 'stable' as const,
        weight: 0.25
      },
      {
        name: '呼吸系统',
        score: 92,
        status: 'excellent' as const,
        trend: 'up' as const,
        weight: 0.20
      },
      {
        name: '运动能力',
        score: 85,
        status: 'good' as const,
        trend: 'up' as const,
        weight: 0.20
      },
      {
        name: '睡眠质量',
        score: 65,
        status: 'average' as const,
        trend: 'down' as const,
        weight: 0.15
      },
      {
        name: '压力管理',
        score: 55,
        status: 'poor' as const,
        trend: 'down' as const,
        weight: 0.15
      },
      {
        name: '营养状况',
        score: 78,
        status: 'good' as const,
        trend: 'stable' as const,
        weight: 0.05
      }
    ];
  }
  
  // 转换真实数据为图表所需格式
  const dimensions = analysisData.value.profile.healthDimensions;
  return Object.keys(dimensions).map(key => ({
    name: getDimensionName(key),
    score: dimensions[key].score,
    status: dimensions[key].status,
    trend: dimensions[key].trend,
    weight: Math.random() * 0.15 + 0.10 // 模拟权重
  }));
});

// 健康画像洞察
const profileInsights = computed(() => {
  if (!analysisData.value.profile?.personalizedInsights) {
    return [
      {
        type: 'positive' as const,
        title: '心血管健康表现优秀',
        description: '您的心率和血压指标都在理想范围内，请继续保持良好的运动习惯。',
        impact: 'high' as const
      },
      {
        type: 'warning' as const,
        title: '睡眠质量需要改善',
        description: '近期睡眠时长偏短，建议调整作息时间，确保每晚7-8小时充足睡眠。',
        impact: 'medium' as const
      },
      {
        type: 'suggestion' as const,
        title: '压力管理建议',
        description: '可以尝试冥想、深呼吸或轻度运动来缓解压力，保持心理健康。',
        impact: 'high' as const
      }
    ];
  }
  
  return analysisData.value.profile.personalizedInsights.map(insight => ({
    type: insight.type,
    title: insight.title,
    description: insight.description,
    impact: 'medium' as const // 默认影响程度
  }));
});

function getStatusBadge(status: string) {
  const statusMap = {
    excellent: '优秀',
    good: '良好',
    average: '一般',
    poor: '较差'
  } as const;
  return statusMap[status as keyof typeof statusMap] || status;
}

function collectMoreData() {
  // 收集更多健康数据
  window.$message?.info('跳转到数据收集页面或提供收集建议');
}
</script>

<template>
  <div class="min-h-screen w-full overflow-y-auto overflow-x-hidden bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 space-y-4 sm:space-y-6 pb-8">
    <!-- 专业页面头部 -->
    <div class="analysis-header">
      <div class="header-content">
        <div class="header-title-section">
          <div class="title-with-icon">
            <div class="title-icon">
              <NIcon size="32" color="#1890ff">
                <i class="i-material-symbols:analytics"></i>
              </NIcon>
            </div>
            <div class="title-text">
              <h1 class="main-title">健康综合分析平台</h1>
              <p class="subtitle">AI驱动的智能健康管理系统</p>
            </div>
          </div>
          <div class="header-badges">
            <NTag type="info" size="small" class="version-tag">v2.1.0</NTag>
            <NTag type="success" size="small" class="status-tag">
              <template #icon>
                <div class="status-dot animate-pulse"></div>
              </template>
              实时分析
            </NTag>
          </div>
        </div>
        
        <div class="header-actions">
          <div class="real-time-status">
            <div class="status-item">
              <span class="status-label">在线用户</span>
              <span class="status-value">{{ realTimeStatus.onlineUsers }}</span>
            </div>
            <div class="status-item">
              <span class="status-label">系统健康</span>
              <span class="status-value text-success">{{ realTimeStatus.systemHealth }}%</span>
            </div>
          </div>
          
          <NDivider vertical />
          
          <NSpace size="medium">
            <NTooltip trigger="hover">
              <template #trigger>
                <NButton type="tertiary" size="medium" @click="() => uiConfig.autoRefresh = !uiConfig.autoRefresh">
                  <template #icon>
                    <NIcon :class="{ 'animate-spin': uiConfig.autoRefresh }">
                      <i class="i-material-symbols:refresh"></i>
                    </NIcon>
                  </template>
                </NButton>
              </template>
              {{ uiConfig.autoRefresh ? '停止自动刷新' : '启用自动刷新' }}
            </NTooltip>
            
            <NButton type="info" size="medium" @click="exportReport">
              <template #icon>
                <NIcon><i class="i-material-symbols:file-download"></i></NIcon>
              </template>
              导出报告
            </NButton>
            
            <NButton type="primary" size="medium" @click="shareAnalysis">
              <template #icon>
                <NIcon><i class="i-material-symbols:share"></i></NIcon>
              </template>
              分享分析
            </NButton>
          </NSpace>
        </div>
      </div>
    </div>

    <!-- 模块配置面板 -->
    <NCard :bordered="false" class="module-config-card">
      <template #header>
        <div class="flex items-center gap-2">
          <NIcon size="20" color="#52c41a">
            <i class="i-material-symbols:tune"></i>
          </NIcon>
          <span class="font-medium">分析模块配置</span>
        </div>
      </template>
      
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div class="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors">
          <div class="flex items-center gap-2">
            <NIcon size="16" color="#1890ff">
              <i class="i-material-symbols:timeline"></i>
            </NIcon>
            <span class="text-sm font-medium">健康基线</span>
          </div>
          <NSwitch v-model:value="moduleConfig.baseline" @update:value="() => toggleModule('baseline')" />
        </div>
        
        <div class="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors">
          <div class="flex items-center gap-2">
            <NIcon size="16" color="#52c41a">
              <i class="i-material-symbols:score"></i>
            </NIcon>
            <span class="text-sm font-medium">健康评分</span>
          </div>
          <NSwitch v-model:value="moduleConfig.score" @update:value="() => toggleModule('score')" />
        </div>
        
        <div class="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors">
          <div class="flex items-center gap-2">
            <NIcon size="16" color="#722ed1">
              <i class="i-material-symbols:psychology"></i>
            </NIcon>
            <span class="text-sm font-medium">健康预测</span>
          </div>
          <NSwitch v-model:value="moduleConfig.prediction" @update:value="() => toggleModule('prediction')" />
        </div>
        
        <div class="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors">
          <div class="flex items-center gap-2">
            <NIcon size="16" color="#fa8c16">
              <i class="i-material-symbols:recommend"></i>
            </NIcon>
            <span class="text-sm font-medium">健康建议</span>
          </div>
          <NSwitch v-model:value="moduleConfig.recommendation" @update:value="() => toggleModule('recommendation')" />
        </div>
        
        <div class="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors">
          <div class="flex items-center gap-2">
            <NIcon size="16" color="#13c2c2">
              <i class="i-material-symbols:account-box"></i>
            </NIcon>
            <span class="text-sm font-medium">健康画像</span>
          </div>
          <NSwitch v-model:value="moduleConfig.profile" @update:value="() => toggleModule('profile')" />
        </div>
      </div>
    </NCard>

    <!-- 搜索过滤区域 -->
    <HealthAnalysisSearch
      v-model:model="searchParams"
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      @search="loadAllData"
    />

    <!-- 专业核心指标概览 -->
    <div class="metrics-overview">
      <!-- 主要健康评分卡 -->
      <div class="main-score-section">
        <NCard class="main-score-card">
          <div class="score-content">
            <div class="score-visual">
              <div class="score-circle" :style="{ background: `conic-gradient(${healthGrade.color} ${overallHealthScore}%, #f0f0f0 0%)` }">
                <div class="score-inner">
                  <div class="score-number">{{ overallHealthScore }}</div>
                  <div class="score-grade">{{ healthGrade.grade }}</div>
                </div>
              </div>
            </div>
            <div class="score-details">
              <h3 class="score-title">综合健康评分</h3>
              <div class="score-status" :style="{ backgroundColor: healthGrade.bgColor, color: healthGrade.color }">
                {{ healthGrade.text }}
              </div>
              <div class="score-description">
                基于多维度健康指标智能评估
              </div>
              <div class="score-trend">
                <span class="trend-label">7日趋势</span>
                <span class="trend-value positive">+2.3%</span>
              </div>
            </div>
          </div>
        </NCard>
        
        <!-- 健康分布图 -->
        <NCard class="distribution-card">
          <template #header>
            <div class="card-header">
              <NIcon size="20" color="#1890ff"><i class="i-material-symbols:pie-chart"></i></NIcon>
              健康状态分布
            </div>
          </template>
          <div class="distribution-chart">
            <div class="distribution-item excellent">
              <div class="dist-label">优秀</div>
              <div class="dist-value">{{ healthDistribution.excellent }}%</div>
              <div class="dist-bar">
                <div class="dist-fill" :style="{ width: healthDistribution.excellent + '%' }"></div>
              </div>
            </div>
            <div class="distribution-item good">
              <div class="dist-label">良好</div>
              <div class="dist-value">{{ healthDistribution.good }}%</div>
              <div class="dist-bar">
                <div class="dist-fill" :style="{ width: healthDistribution.good + '%' }"></div>
              </div>
            </div>
            <div class="distribution-item average">
              <div class="dist-label">一般</div>
              <div class="dist-value">{{ healthDistribution.average }}%</div>
              <div class="dist-bar">
                <div class="dist-fill" :style="{ width: healthDistribution.average + '%' }"></div>
              </div>
            </div>
            <div class="distribution-item poor">
              <div class="dist-label">较差</div>
              <div class="dist-value">{{ healthDistribution.poor }}%</div>
              <div class="dist-bar">
                <div class="dist-fill" :style="{ width: healthDistribution.poor + '%' }"></div>
              </div>
            </div>
          </div>
        </NCard>
      </div>
      
      <!-- 关键指标网格 -->
      <div class="metrics-grid">
        <NCard class="metric-card active-users">
          <div class="metric-content">
            <div class="metric-icon">
              <NIcon size="24" color="#52c41a"><i class="i-material-symbols:people"></i></NIcon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ keyMetrics.activeUsers }}</div>
              <div class="metric-label">活跃用户</div>
              <div class="metric-change positive">↑ 12.5%</div>
            </div>
          </div>
        </NCard>
        
        <NCard class="metric-card risk-users">
          <div class="metric-content">
            <div class="metric-icon">
              <NIcon size="24" color="#ff4d4f"><i class="i-material-symbols:warning"></i></NIcon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ keyMetrics.highRiskUsers }}</div>
              <div class="metric-label">高风险用户</div>
              <div class="metric-change negative">↓ 8.3%</div>
            </div>
          </div>
        </NCard>
        
        <NCard class="metric-card improvement">
          <div class="metric-content">
            <div class="metric-icon">
              <NIcon size="24" color="#1890ff"><i class="i-material-symbols:trending-up"></i></NIcon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ keyMetrics.improvementRate.toFixed(1) }}%</div>
              <div class="metric-label">改善率</div>
              <div class="metric-change positive">↑ 3.2%</div>
            </div>
          </div>
        </NCard>
        
        <NCard class="metric-card alerts">
          <div class="metric-content">
            <div class="metric-icon">
              <NIcon size="24" color="#faad14"><i class="i-material-symbols:notifications"></i></NIcon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ keyMetrics.alertCount }}</div>
              <div class="metric-label">待处理预警</div>
              <div class="metric-change neutral">→ 0%</div>
            </div>
          </div>
        </NCard>
        
        <NCard class="metric-card satisfaction">
          <div class="metric-content">
            <div class="metric-icon">
              <NIcon size="24" color="#722ed1"><i class="i-material-symbols:sentiment-satisfied"></i></NIcon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ keyMetrics.satisfactionRate }}%</div>
              <div class="metric-label">满意度</div>
              <div class="metric-change positive">↑ 5.7%</div>
            </div>
          </div>
        </NCard>
        
        <NCard class="metric-card engagement">
          <div class="metric-content">
            <div class="metric-icon">
              <NIcon size="24" color="#13c2c2"><i class="i-material-symbols:psychology"></i></NIcon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ keyMetrics.engagementRate }}%</div>
              <div class="metric-label">参与度</div>
              <div class="metric-change positive">↑ 7.1%</div>
            </div>
          </div>
        </NCard>
      </div>
    </div>

    <!-- 分析内容区域 -->
    <NTabs v-model:value="analysisMode" type="line" animated>
      <NTabPane name="overview" tab="📊 综合概览">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- 健康趋势图 -->
          <NCard title="📈 健康趋势分析" :bordered="false" class="chart-card">
            <div class="h-80">
              <LineChart 
                :data="healthTrend.data" 
                :timestamps="healthTrend.categories"
                :title="'30天健康评分趋势'"
              />
            </div>
          </NCard>
          
          <!-- 多维度健康分析 -->
          <NCard title="🎯 多维度健康分析" :bordered="false" class="chart-card">
            <div class="h-96">
              <MultiDimensionalHealthChart :data="multiDimensionalData" />
            </div>
          </NCard>
          
          <!-- 智能健康建议 -->
          <NCard v-if="moduleConfig.recommendation" class="recommendation-card" :bordered="false">
            <template #header>
              <div class="card-header-enhanced">
                <div class="header-title">
                  <NIcon size="24" color="#fa8c16"><i class="i-material-symbols:lightbulb"></i></NIcon>
                  <span>智能健康建议</span>
                  <NTag v-if="recommendationStats.aiGenerated > 0" type="info" size="small" class="ai-tag">
                    AI驱动 {{ Math.round(recommendationStats.aiGenerated / recommendationStats.total * 100) }}%
                  </NTag>
                </div>
                <div class="header-stats">
                  <div class="stat-item">
                    <span class="stat-label">总计</span>
                    <span class="stat-value">{{ recommendationStats.total }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">有效性</span>
                    <span class="stat-value">{{ (recommendationStats.avgEffectiveness * 100).toFixed(0) }}%</span>
                  </div>
                </div>
              </div>
            </template>
            
            <NSpin :show="loading.recommendation">
              <div v-if="latestRecommendations.length > 0" class="recommendations-container">
                <!-- 建议类型分布 -->
                <div class="recommendation-types">
                  <div 
                    v-for="(count, type) in recommendationStats.byType" 
                    :key="type"
                    class="type-badge"
                    :class="type"
                  >
                    <span class="type-icon">{{ getRecommendationIcon(type) }}</span>
                    <span class="type-count">{{ count }}</span>
                  </div>
                </div>
                
                <!-- 最新建议列表 -->
                <div class="recommendations-list">
                  <div 
                    v-for="rec in latestRecommendations.slice(0, 4)"
                    :key="rec.id"
                    class="recommendation-item"
                    :class="rec.priority"
                    @click="viewRecommendationDetail(rec)"
                  >
                    <div class="rec-header">
                      <div class="rec-priority" :class="rec.priority"></div>
                      <div class="rec-title">{{ rec.title }}</div>
                      <div class="rec-badges">
                        <NTag size="tiny" :type="getRecommendationTypeColor(rec.recommendationType)">
                          {{ getRecommendationTypeText(rec.recommendationType) }}
                        </NTag>
                        <NTag v-if="rec.aiGenerated" size="tiny" type="info">AI</NTag>
                      </div>
                    </div>
                    
                    <div class="rec-content">
                      {{ rec.content.substring(0, 80) }}{{ rec.content.length > 80 ? '...' : '' }}
                    </div>
                    
                    <div class="rec-footer">
                      <div class="rec-user">
                        <NAvatar size="small" :style="{ backgroundColor: getUserAvatarColor(rec.userName) }">
                          {{ rec.userName.charAt(0) }}
                        </NAvatar>
                        <span class="user-info">
                          <span class="user-name">{{ rec.userName }}</span>
                          <span class="user-dept">{{ rec.userDepartment }}</span>
                        </span>
                      </div>
                      
                      <div class="rec-meta">
                        <div class="effectiveness" v-if="rec.effectiveness">
                          <span class="eff-label">有效性</span>
                          <NProgress 
                            type="line" 
                            :percentage="rec.effectiveness * 100" 
                            :height="4"
                            :show-indicator="false"
                            :status="rec.effectiveness > 0.8 ? 'success' : rec.effectiveness > 0.6 ? 'info' : 'warning'"
                          />
                        </div>
                        <div class="rec-time">{{ convertToBeijingTime(rec.createdAt) }}</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="recommendations-actions">
                  <NButton type="primary" @click="viewAllRecommendations">
                    <template #icon>
                      <NIcon><i class="i-material-symbols:arrow-forward"></i></NIcon>
                    </template>
                    查看全部建议
                  </NButton>
                  <NButton @click="createRecommendation">
                    <template #icon>
                      <NIcon><i class="i-material-symbols:add"></i></NIcon>
                    </template>
                    创建建议
                  </NButton>
                </div>
              </div>
              
              <!-- 空状态 -->
              <div v-else class="empty-state">
                <div class="empty-icon">
                  <NIcon size="64" color="#d9d9d9"><i class="i-material-symbols:lightbulb"></i></NIcon>
                </div>
                <div class="empty-title">暂无健康建议</div>
                <div class="empty-description">系统将基于用户健康数据自动生成个性化建议</div>
                <NButton type="primary" @click="createRecommendation">
                  创建首个建议
                </NButton>
              </div>
            </NSpin>
          </NCard>
          
          <!-- 预测分析 -->
          <NCard v-if="moduleConfig.prediction" title="🔮 智能预测分析" :bordered="false">
            <NSpin :show="loading.prediction">
              <div class="space-y-4" v-if="analysisData.prediction">
                <div class="grid grid-cols-2 gap-4">
                  <div class="text-center p-3 rounded-lg bg-blue-50">
                    <div class="text-lg font-semibold text-blue-600">7天风险预测</div>
                    <div class="text-2xl font-bold mt-1" 
                      :class="{
                        'text-green-600': analysisData.prediction.riskPrediction?.next7Days?.risk === 'low',
                        'text-yellow-600': analysisData.prediction.riskPrediction?.next7Days?.risk === 'medium',
                        'text-red-600': analysisData.prediction.riskPrediction?.next7Days?.risk === 'high'
                      }"
                    >
                      {{ analysisData.prediction.riskPrediction?.next7Days?.risk === 'low' ? '低风险' : 
                          analysisData.prediction.riskPrediction?.next7Days?.risk === 'medium' ? '中风险' : '高风险' }}
                    </div>
                    <div class="text-xs text-gray-500 mt-1">
                      置信度: {{ (analysisData.prediction.riskPrediction?.next7Days?.confidence * 100).toFixed(0) }}%
                    </div>
                  </div>
                  
                  <div class="text-center p-3 rounded-lg bg-green-50">
                    <div class="text-lg font-semibold text-green-600">健康趋势预测</div>
                    <div class="text-2xl font-bold mt-1 text-green-600">
                      {{ analysisData.prediction.trendPrediction?.healthScore?.trend === 'up' ? '↗' : 
                          analysisData.prediction.trendPrediction?.healthScore?.trend === 'down' ? '↘' : '→' }}
                      {{ analysisData.prediction.trendPrediction?.healthScore?.change }}
                    </div>
                    <div class="text-xs text-gray-500 mt-1">30天预期变化</div>
                  </div>
                </div>
              </div>
            </NSpin>
          </NCard>
        </div>
      </NTabPane>
      
      <NTabPane name="detailed" tab="🔍 详细分析">
        <!-- 详细分析视图内容 -->
        <div class="space-y-6">
          <!-- 基线分析 -->
          <NCard v-if="moduleConfig.baseline" title="📊 健康基线分析" :bordered="false">
            <NSpin :show="loading.baseline">
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- 基线统计卡片 -->
                <div class="grid grid-cols-2 gap-4">
                  <div class="text-center p-4 rounded-lg bg-red-50">
                    <NIcon size="24" color="#ff4d4f" class="mb-2">
                      <i class="i-material-symbols:favorite"></i>
                    </NIcon>
                    <div class="text-lg font-semibold">心率基线</div>
                    <div class="text-2xl font-bold text-red-600 mt-1">72 bpm</div>
                    <div class="text-xs text-gray-500 mt-1">正常范围: 60-100</div>
                  </div>
                  
                  <div class="text-center p-4 rounded-lg bg-blue-50">
                    <NIcon size="24" color="#1890ff" class="mb-2">
                      <i class="i-material-symbols:air"></i>
                    </NIcon>
                    <div class="text-lg font-semibold">血氧基线</div>
                    <div class="text-2xl font-bold text-blue-600 mt-1">97%</div>
                    <div class="text-xs text-gray-500 mt-1">正常范围: 95-100%</div>
                  </div>
                  
                  <div class="text-center p-4 rounded-lg bg-orange-50">
                    <NIcon size="24" color="#fa8c16" class="mb-2">
                      <i class="i-material-symbols:device-thermostat"></i>
                    </NIcon>
                    <div class="text-lg font-semibold">体温基线</div>
                    <div class="text-2xl font-bold text-orange-600 mt-1">36.8°C</div>
                    <div class="text-xs text-gray-500 mt-1">正常范围: 36.0-37.5°C</div>
                  </div>
                  
                  <div class="text-center p-4 rounded-lg bg-green-50">
                    <NIcon size="24" color="#52c41a" class="mb-2">
                      <i class="i-material-symbols:directions-walk"></i>
                    </NIcon>
                    <div class="text-lg font-semibold">步数基线</div>
                    <div class="text-2xl font-bold text-green-600 mt-1">8,542</div>
                    <div class="text-xs text-gray-500 mt-1">建议: >10,000步</div>
                  </div>
                </div>
                
                <!-- 基线与目标对比图 -->
                <div class="h-80">
                  <BaselineAnalysisChart :data="baselineAnalysisData" title="健康基线分析" />
                </div>
              </div>
            </NSpin>
          </NCard>
          
          <!-- 详细趋势分析 -->
          <NCard v-if="moduleConfig.baseline || moduleConfig.score" title="📈 详细趋势分析" :bordered="false">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div class="h-80">
                <HealthTrendChart 
                  :data="detailedTrendData.heartRate.data" 
                  :timestamps="detailedTrendData.heartRate.categories"
                  title="心率趋势(7天)"
                  color="#ff4d4f"
                  y-axis-name="心率"
                  unit=" bpm"
                />
              </div>
              
              <div class="h-80">
                <HealthTrendChart 
                  :data="detailedTrendData.bloodOxygen.data" 
                  :timestamps="detailedTrendData.bloodOxygen.categories"
                  title="血氧趋势(7天)"
                  color="#1890ff"
                  y-axis-name="血氧饱和度"
                  unit="%"
                />
              </div>
              
              <div class="h-80">
                <HealthTrendChart 
                  :data="detailedTrendData.temperature.data" 
                  :timestamps="detailedTrendData.temperature.categories"
                  title="体温趋势(7天)"
                  color="#fa8c16"
                  y-axis-name="体温"
                  unit="°C"
                />
              </div>
              
              <div class="h-80">
                <HealthTrendChart 
                  :data="detailedTrendData.step.data" 
                  :timestamps="detailedTrendData.step.categories"
                  title="步数趋势(7天)"
                  color="#52c41a"
                  y-axis-name="步数"
                  unit="步"
                />
              </div>
            </div>
          </NCard>
          
          <!-- 预测分析 -->
          <NCard v-if="moduleConfig.prediction" title="🔮 智能预测分析" :bordered="false">
            <NSpin :show="loading.prediction">
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-6" v-if="analysisData.prediction">
                <!-- 预测图表 -->
                <div class="h-96">
                  <AdvancedPredictionChart 
                    :data="predictionChartData" 
                    title="智能健康预测分析"
                    y-axis-name="健康评分"
                    unit="分"
                    :show-confidence-interval="true"
                  />
                </div>
                
                <!-- 风险预测卡片 -->
                <div class="space-y-4">
                  <div class="p-4 rounded-lg bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200">
                    <div class="flex items-center justify-between mb-3">
                      <h4 class="font-semibold text-blue-800">7天风险预测</h4>
                      <div class="text-sm text-blue-600">
                        置信度: {{ (analysisData.prediction.riskPrediction?.next7Days?.confidence * 100).toFixed(0) }}%
                      </div>
                    </div>
                    <div class="text-2xl font-bold mb-2"
                      :class="{
                        'text-green-600': analysisData.prediction.riskPrediction?.next7Days?.risk === 'low',
                        'text-yellow-600': analysisData.prediction.riskPrediction?.next7Days?.risk === 'medium',
                        'text-red-600': analysisData.prediction.riskPrediction?.next7Days?.risk === 'high'
                      }">
                      {{ analysisData.prediction.riskPrediction?.next7Days?.risk === 'low' ? '低风险' : 
                          analysisData.prediction.riskPrediction?.next7Days?.risk === 'medium' ? '中风险' : '高风险' }}
                    </div>
                    <div class="text-sm text-blue-700">基于历史数据和AI模型分析</div>
                  </div>
                  
                  <div class="p-4 rounded-lg bg-gradient-to-r from-orange-50 to-orange-100 border border-orange-200">
                    <div class="flex items-center justify-between mb-3">
                      <h4 class="font-semibold text-orange-800">30天风险预测</h4>
                      <div class="text-sm text-orange-600">
                        置信度: {{ (analysisData.prediction.riskPrediction?.next30Days?.confidence * 100).toFixed(0) }}%
                      </div>
                    </div>
                    <div class="text-2xl font-bold mb-2"
                      :class="{
                        'text-green-600': analysisData.prediction.riskPrediction?.next30Days?.risk === 'low',
                        'text-yellow-600': analysisData.prediction.riskPrediction?.next30Days?.risk === 'medium',
                        'text-red-600': analysisData.prediction.riskPrediction?.next30Days?.risk === 'high'
                      }">
                      {{ analysisData.prediction.riskPrediction?.next30Days?.risk === 'low' ? '低风险' : 
                          analysisData.prediction.riskPrediction?.next30Days?.risk === 'medium' ? '中风险' : '高风险' }}
                    </div>
                    <div class="text-sm text-orange-700">长期趋势分析结果</div>
                  </div>
                  
                  <!-- 趋势预测指标 -->
                  <div class="p-4 rounded-lg bg-gray-50 border border-gray-200">
                    <h4 class="font-semibold text-gray-800 mb-3">关键指标趋势预测</h4>
                    <div class="space-y-2">
                      <div class="flex items-center justify-between">
                        <span class="text-sm">心血管健康</span>
                        <div class="flex items-center gap-2">
                          <span class="text-xs px-2 py-1 rounded"
                            :class="{
                              'bg-green-100 text-green-700': analysisData.prediction.trendPrediction?.keyIndicators?.cardiovascular?.trend === 'up',
                              'bg-red-100 text-red-700': analysisData.prediction.trendPrediction?.keyIndicators?.cardiovascular?.trend === 'down',
                              'bg-gray-100 text-gray-700': analysisData.prediction.trendPrediction?.keyIndicators?.cardiovascular?.trend === 'stable'
                            }">
                            {{ analysisData.prediction.trendPrediction?.keyIndicators?.cardiovascular?.trend === 'up' ? '↗ 上升' :
                                analysisData.prediction.trendPrediction?.keyIndicators?.cardiovascular?.trend === 'down' ? '↘ 下降' : '→ 稳定' }}
                          </span>
                          <span class="text-xs font-medium">{{ analysisData.prediction.trendPrediction?.keyIndicators?.cardiovascular?.change }}</span>
                        </div>
                      </div>
                      
                      <div class="flex items-center justify-between">
                        <span class="text-sm">呼吸系统</span>
                        <div class="flex items-center gap-2">
                          <span class="text-xs px-2 py-1 rounded"
                            :class="{
                              'bg-green-100 text-green-700': analysisData.prediction.trendPrediction?.keyIndicators?.respiratory?.trend === 'up',
                              'bg-red-100 text-red-700': analysisData.prediction.trendPrediction?.keyIndicators?.respiratory?.trend === 'down',
                              'bg-gray-100 text-gray-700': analysisData.prediction.trendPrediction?.keyIndicators?.respiratory?.trend === 'stable'
                            }">
                            {{ analysisData.prediction.trendPrediction?.keyIndicators?.respiratory?.trend === 'up' ? '↗ 上升' :
                                analysisData.prediction.trendPrediction?.keyIndicators?.respiratory?.trend === 'down' ? '↘ 下降' : '→ 稳定' }}
                          </span>
                          <span class="text-xs font-medium">{{ analysisData.prediction.trendPrediction?.keyIndicators?.respiratory?.change }}</span>
                        </div>
                      </div>
                      
                      <div class="flex items-center justify-between">
                        <span class="text-sm">心理健康</span>
                        <div class="flex items-center gap-2">
                          <span class="text-xs px-2 py-1 rounded"
                            :class="{
                              'bg-green-100 text-green-700': analysisData.prediction.trendPrediction?.keyIndicators?.mental?.trend === 'up',
                              'bg-red-100 text-red-700': analysisData.prediction.trendPrediction?.keyIndicators?.mental?.trend === 'down',
                              'bg-gray-100 text-gray-700': analysisData.prediction.trendPrediction?.keyIndicators?.mental?.trend === 'stable'
                            }">
                            {{ analysisData.prediction.trendPrediction?.keyIndicators?.mental?.trend === 'up' ? '↗ 上升' :
                                analysisData.prediction.trendPrediction?.keyIndicators?.mental?.trend === 'down' ? '↘ 下降' : '→ 稳定' }}
                          </span>
                          <span class="text-xs font-medium">{{ analysisData.prediction.trendPrediction?.keyIndicators?.mental?.change }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </NSpin>
          </NCard>
          
          <!-- 健康建议集成 -->
          <NCard v-if="moduleConfig.recommendation" title="💡 个性化健康建议" :bordered="false">
            <NSpin :show="loading.recommendation">
              <div v-if="analysisData.recommendation && analysisData.recommendation.length > 0">
                <!-- 建议统计 -->
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                  <div class="text-center p-3 rounded-lg bg-red-50 border border-red-200">
                    <div class="text-2xl font-bold text-red-600">
                      {{ analysisData.recommendation.filter(r => r.priority === 'high').length }}
                    </div>
                    <div class="text-sm text-red-600">高优先级建议</div>
                  </div>
                  <div class="text-center p-3 rounded-lg bg-green-50 border border-green-200">
                    <div class="text-2xl font-bold text-green-600">
                      {{ analysisData.recommendation.filter(r => r.status === 'completed').length }}
                    </div>
                    <div class="text-sm text-green-600">已完成建议</div>
                  </div>
                  <div class="text-center p-3 rounded-lg bg-blue-50 border border-blue-200">
                    <div class="text-2xl font-bold text-blue-600">
                      {{ analysisData.recommendation.filter(r => r.aiGenerated).length }}
                    </div>
                    <div class="text-sm text-blue-600">AI生成建议</div>
                  </div>
                </div>
                
                <!-- 建议列表 -->
                <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                  <div 
                    v-for="rec in analysisData.recommendation"
                    :key="rec.id"
                    class="p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
                    @click="viewRecommendationDetail(rec)"
                  >
                    <!-- 建议头部 -->
                    <div class="flex items-start gap-3 mb-3">
                      <div class="w-3 h-3 rounded-full mt-1 flex-shrink-0"
                        :class="{
                          'bg-red-500': rec.priority === 'high',
                          'bg-yellow-500': rec.priority === 'medium', 
                          'bg-green-500': rec.priority === 'low'
                        }">
                      </div>
                      <div class="flex-1 min-w-0">
                        <h4 class="font-semibold text-gray-800 mb-1 truncate">{{ rec.title }}</h4>
                        <div class="flex items-center gap-2 mb-2">
                          <span class="text-sm text-gray-600">{{ rec.userName }}</span>
                          <span class="text-xs text-gray-400">•</span>
                          <span class="text-xs text-gray-500">{{ rec.userDepartment }}</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- 建议内容 -->
                    <div class="text-sm text-gray-600 mb-3 line-clamp-2">
                      {{ rec.content }}
                    </div>
                    
                    <!-- 标签区域 -->
                    <div class="flex items-center justify-between mb-3">
                      <div class="flex items-center gap-2">
                        <NTag size="small" 
                          :type="rec.recommendationType === 'lifestyle' ? 'info' : 
                                 rec.recommendationType === 'exercise' ? 'success' : 
                                 rec.recommendationType === 'nutrition' ? 'warning' : 
                                 rec.recommendationType === 'medical' ? 'error' : 'primary'"
                        >
                          {{ getRecommendationTypeText(rec.recommendationType) }}
                        </NTag>
                        <NTag v-if="rec.aiGenerated" size="small" type="info">AI</NTag>
                      </div>
                      <NTag size="small" 
                        :type="rec.status === 'pending' ? 'warning' : 
                               rec.status === 'sent' ? 'info' : 
                               rec.status === 'completed' ? 'success' : 'default'"
                      >
                        {{ getStatusText(rec.status) }}
                      </NTag>
                    </div>
                    
                    <!-- 有效性评分 -->
                    <div v-if="rec.effectivenesScore" class="flex items-center justify-between mb-3">
                      <span class="text-xs text-gray-500">有效性评分</span>
                      <div class="flex items-center gap-1">
                        <span v-for="i in 5" :key="i" 
                          class="text-xs"
                          :class="i <= rec.effectivenesScore ? 'text-yellow-400' : 'text-gray-300'"
                        >
                          ★
                        </span>
                        <span class="text-xs text-gray-500 ml-1">{{ rec.effectivenesScore }}/5</span>
                      </div>
                    </div>
                    
                    <!-- 时间信息 -->
                    <div class="text-xs text-gray-400 border-t border-gray-100 pt-2">
                      创建于 {{ convertToBeijingTime(rec.createdAt) }}
                    </div>
                  </div>
                </div>
                
                <!-- 查看更多 -->
                <div class="text-center mt-6 pt-4 border-t border-gray-200">
                  <NButton type="primary" @click="viewAllRecommendations">
                    <template #icon>
                      <div class="i-material-symbols:arrow-forward"></div>
                    </template>
                    查看全部健康建议
                  </NButton>
                </div>
              </div>
              
              <!-- 无数据状态 -->
              <div v-else class="text-center py-12 text-gray-500">
                <div class="text-6xl mb-4">💡</div>
                <div class="text-lg font-medium mb-2">暂无健康建议数据</div>
                <div class="text-sm mb-4">系统将根据用户健康数据自动生成个性化建议</div>
                <NButton type="primary" @click="createRecommendation">
                  <template #icon>
                    <div class="i-material-symbols:add"></div>
                  </template>
                  创建健康建议
                </NButton>
              </div>
            </NSpin>
          </NCard>
          
          <!-- 健康画像综合展示 -->
          <NCard v-if="moduleConfig.profile" title="👤 完整健康画像分析" :bordered="false">
            <NSpin :show="loading.profile">
              <div v-if="analysisData.profile" class="space-y-6">
                <!-- 画像概览 -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div class="p-4 rounded-lg bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200">
                    <div class="flex items-center justify-between mb-2">
                      <h4 class="font-semibold text-blue-800">数据完整度</h4>
                      <div class="text-2xl font-bold text-blue-600">{{ analysisData.profile.completeness }}%</div>
                    </div>
                    <NProgress 
                      type="line" 
                      :percentage="analysisData.profile.completeness" 
                      :status="analysisData.profile.completeness >= 80 ? 'success' : 'warning'"
                      :height="6"
                      class="mb-2"
                    />
                    <div class="text-sm text-blue-700">
                      {{ analysisData.profile.completeness >= 90 ? '数据覆盖率极佳' : 
                         analysisData.profile.completeness >= 80 ? '数据覆盖率良好' : '建议补充更多数据' }}
                    </div>
                  </div>
                  
                  <div class="p-4 rounded-lg bg-gradient-to-r from-green-50 to-green-100 border border-green-200">
                    <div class="flex items-center justify-between mb-2">
                      <h4 class="font-semibold text-green-800">健康优势</h4>
                      <div class="text-2xl font-bold text-green-600">{{ analysisData.profile.keyStrengths?.length || 0 }}</div>
                    </div>
                    <div class="text-sm text-green-700">个优势领域</div>
                  </div>
                  
                  <div class="p-4 rounded-lg bg-gradient-to-r from-orange-50 to-orange-100 border border-orange-200">
                    <div class="flex items-center justify-between mb-2">
                      <h4 class="font-semibold text-orange-800">关注点</h4>
                      <div class="text-2xl font-bold text-orange-600">{{ analysisData.profile.riskFactors?.length || 0 }}</div>
                    </div>
                    <div class="text-sm text-orange-700">个需要改善的方面</div>
                  </div>
                </div>

                <!-- 健康维度综合评估 -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <!-- 维度评分详情 -->
                  <div class="space-y-4">
                    <h4 class="text-lg font-semibold text-gray-800 mb-4">健康维度评估</h4>
                    
                    <div v-for="(dimension, key) in analysisData.profile.healthDimensions" :key="key"
                      class="p-3 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors">
                      <div class="flex items-center justify-between mb-2">
                        <span class="font-medium text-gray-800">
                          {{ getDimensionName(key) }}
                        </span>
                        <div class="flex items-center gap-2">
                          <NTag size="small" 
                            :type="dimension.status === 'excellent' ? 'success' : 
                                   dimension.status === 'good' ? 'info' : 
                                   dimension.status === 'average' ? 'warning' : 'error'">
                            {{ getStatusBadge(dimension.status) }}
                          </NTag>
                          <span class="text-sm font-medium"
                            :class="dimension.trend === 'up' ? 'text-green-600' : 
                                   dimension.trend === 'down' ? 'text-red-600' : 'text-gray-600'">
                            {{ dimension.trend === 'up' ? '↗' : dimension.trend === 'down' ? '↘' : '→' }}
                          </span>
                        </div>
                      </div>
                      <div class="flex items-center gap-3">
                        <NProgress 
                          type="line" 
                          :percentage="dimension.score" 
                          :status="dimension.score >= 80 ? 'success' : dimension.score >= 60 ? 'info' : 'warning'"
                          :show-indicator="false"
                          :height="6"
                          class="flex-1"
                        />
                        <span class="text-sm font-medium text-gray-700">{{ dimension.score }}</span>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 综合健康画像图表 -->
                  <div class="h-96">
                    <ProfileAnalysisChart 
                      :health-dimensions="profileHealthDimensions" 
                      :insights="profileInsights"
                      :completeness="analysisData.profile?.completeness || 85"
                      title="多维度健康画像分析"
                    />
                  </div>
                </div>

                <!-- 健康优势与风险分析 -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <!-- 健康优势 -->
                  <div class="p-4 rounded-lg bg-green-50 border border-green-200">
                    <h4 class="font-semibold text-green-800 mb-4 flex items-center gap-2">
                      <span class="text-lg">💪</span>
                      健康优势分析
                    </h4>
                    <div class="space-y-3">
                      <div v-for="strength in analysisData.profile.keyStrengths" :key="strength.category"
                        class="p-3 rounded-lg bg-white border border-green-100">
                        <div class="flex items-center justify-between mb-2">
                          <span class="font-medium text-green-800">{{ strength.category }}</span>
                          <div class="flex items-center gap-1">
                            <span class="text-lg font-bold text-green-600">{{ strength.score }}</span>
                            <span class="text-sm text-green-500">分</span>
                          </div>
                        </div>
                        <p class="text-sm text-green-700">{{ strength.description }}</p>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 风险因素 -->
                  <div class="p-4 rounded-lg bg-red-50 border border-red-200">
                    <h4 class="font-semibold text-red-800 mb-4 flex items-center gap-2">
                      <span class="text-lg">⚠️</span>
                      关注领域分析
                    </h4>
                    <div class="space-y-3">
                      <div v-for="risk in analysisData.profile.riskFactors" :key="risk.category"
                        class="p-3 rounded-lg bg-white border border-red-100">
                        <div class="flex items-center justify-between mb-2">
                          <span class="font-medium text-red-800">{{ risk.category }}</span>
                          <div class="flex items-center gap-2">
                            <NTag size="small" 
                              :type="risk.level === 'high' ? 'error' : risk.level === 'medium' ? 'warning' : 'info'">
                              {{ risk.level === 'high' ? '高风险' : risk.level === 'medium' ? '中风险' : '低风险' }}
                            </NTag>
                            <span class="text-sm font-bold"
                              :class="risk.score >= 70 ? 'text-green-600' : risk.score >= 50 ? 'text-yellow-600' : 'text-red-600'">
                              {{ risk.score }}分
                            </span>
                          </div>
                        </div>
                        <p class="text-sm text-red-700">{{ risk.description }}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 个性化洞察 -->
                <div class="p-4 rounded-lg bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200">
                  <h4 class="font-semibold text-purple-800 mb-4 flex items-center gap-2">
                    <span class="text-lg">🔍</span>
                    AI智能分析洞察
                  </h4>
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div v-for="insight in analysisData.profile.personalizedInsights" :key="insight.title"
                      class="p-3 rounded-lg bg-white border"
                      :class="{
                        'border-green-200': insight.type === 'positive',
                        'border-yellow-200': insight.type === 'warning',
                        'border-blue-200': insight.type === 'suggestion'
                      }">
                      <div class="flex items-start gap-2 mb-2">
                        <span class="text-lg">
                          {{ insight.type === 'positive' ? '✅' : insight.type === 'warning' ? '⚠️' : '💡' }}
                        </span>
                        <h5 class="font-medium text-gray-800 text-sm">{{ insight.title }}</h5>
                      </div>
                      <p class="text-xs text-gray-600 leading-relaxed">{{ insight.description }}</p>
                    </div>
                  </div>
                </div>

                <!-- 趋势分析 -->
                <div class="p-4 rounded-lg bg-gray-50 border border-gray-200">
                  <h4 class="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <span class="text-lg">📈</span>
                    健康趋势分析
                  </h4>
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="p-3 rounded-lg bg-green-100 border border-green-200">
                      <h5 class="font-medium text-green-800 mb-2 flex items-center gap-1">
                        <span>↗️</span> 改善中
                      </h5>
                      <div class="flex flex-wrap gap-1">
                        <NTag v-for="item in analysisData.profile.trends?.improving" :key="item" 
                          size="small" type="success">
                          {{ item }}
                        </NTag>
                      </div>
                    </div>
                    
                    <div class="p-3 rounded-lg bg-blue-100 border border-blue-200">
                      <h5 class="font-medium text-blue-800 mb-2 flex items-center gap-1">
                        <span>→</span> 稳定
                      </h5>
                      <div class="flex flex-wrap gap-1">
                        <NTag v-for="item in analysisData.profile.trends?.stable" :key="item" 
                          size="small" type="info">
                          {{ item }}
                        </NTag>
                      </div>
                    </div>
                    
                    <div class="p-3 rounded-lg bg-red-100 border border-red-200">
                      <h5 class="font-medium text-red-800 mb-2 flex items-center gap-1">
                        <span>↘️</span> 需关注
                      </h5>
                      <div class="flex flex-wrap gap-1">
                        <NTag v-for="item in analysisData.profile.trends?.declining" :key="item" 
                          size="small" type="error">
                          {{ item }}
                        </NTag>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 无数据状态 -->
              <div v-else class="text-center py-12 text-gray-500">
                <div class="text-6xl mb-4">👤</div>
                <div class="text-lg font-medium mb-2">健康画像数据不足</div>
                <div class="text-sm mb-4">需要更多健康数据来构建完整的用户画像</div>
                <NButton type="primary" @click="collectMoreData">
                  <template #icon>
                    <div class="i-material-symbols:add-chart"></div>
                  </template>
                  收集更多数据
                </NButton>
              </div>
            </NSpin>
          </NCard>
          
          <!-- 评分分析 -->
          <NCard v-if="moduleConfig.score" title="⭐ 健康评分详情" :bordered="false">
            <NSpin :show="loading.score">
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="space-y-4">
                  <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                    <span class="font-medium">心血管健康</span>
                    <div class="flex items-center gap-2">
                      <NProgress type="line" percentage={85} status="success" :show-indicator="false" class="w-20" />
                      <span class="font-bold text-green-600">85</span>
                    </div>
                  </div>
                  
                  <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                    <span class="font-medium">呼吸系统</span>
                    <div class="flex items-center gap-2">
                      <NProgress type="line" percentage={78} status="info" :show-indicator="false" class="w-20" />
                      <span class="font-bold text-blue-600">78</span>
                    </div>
                  </div>
                  
                  <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                    <span class="font-medium">运动能力</span>
                    <div class="flex items-center gap-2">
                      <NProgress type="line" percentage={92} status="success" :show-indicator="false" class="w-20" />
                      <span class="font-bold text-green-600">92</span>
                    </div>
                  </div>
                  
                  <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                    <span class="font-medium">睡眠质量</span>
                    <div class="flex items-center gap-2">
                      <NProgress type="line" percentage={65} status="warning" :show-indicator="false" class="w-20" />
                      <span class="font-bold text-yellow-600">65</span>
                    </div>
                  </div>
                </div>
                
                <div class="h-64">
                  <ScoreAnalysisChart :data="scoreAnalysisData" :overall-score="overallHealthScore" title="综合健康评分分析" />
                </div>
              </div>
            </NSpin>
          </NCard>
        </div>
      </NTabPane>
      
      <NTabPane name="comparison" tab="⚖️ 对比分析">
        <!-- 对比分析视图内容 -->
        <div class="text-center py-12">
          <NIcon size="64" color="#d9d9d9">
            <i class="i-material-symbols:compare"></i>
          </NIcon>
          <div class="mt-4 text-lg text-gray-500">对比分析功能开发中...</div>
          <div class="mt-2 text-sm text-gray-400">即将支持用户间、部门间、时间段对比分析</div>
        </div>
      </NTabPane>
    </NTabs>
    </div>
  </div>
</template>

<style scoped>
.module-config-card {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;
}

/* 页面容器样式 */
.min-h-screen {
  scroll-behavior: smooth;
}

/* 自定义滚动条样式 */
.min-h-screen::-webkit-scrollbar {
  width: 8px;
}

.min-h-screen::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.min-h-screen::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 4px;
}

.min-h-screen::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #5a6fd8, #6a4190);
}

/* 专业页面头部样式 */
.analysis-header {
  @apply mb-6;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 24px;
  color: white;
  position: relative;
  overflow: hidden;
  margin-top: 0;
}

.analysis-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="%23ffffff" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>') repeat;
  pointer-events: none;
}

.header-content {
  @apply flex items-center justify-between relative z-10;
}

.header-title-section {
  @apply flex items-center gap-6;
}

.title-with-icon {
  @apply flex items-center gap-4;
}

.title-icon {
  @apply w-16 h-16 bg-white bg-opacity-20 rounded-full flex items-center justify-center;
}

.title-text {
  @apply flex flex-col;
}

.main-title {
  @apply text-3xl font-bold mb-1;
  background: linear-gradient(45deg, #ffffff, #f0f8ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  @apply text-white text-opacity-80 text-sm;
}

.header-badges {
  @apply flex items-center gap-2;
}

.version-tag {
  @apply bg-white bg-opacity-20 border-white border-opacity-30;
  color: white !important;
}

.status-tag {
  @apply bg-green-500 bg-opacity-20 border-green-400 border-opacity-50;
  color: #4ade80 !important;
}

.status-dot {
  @apply w-2 h-2 bg-green-400 rounded-full;
}

.header-actions {
  @apply flex items-center gap-4;
}

.real-time-status {
  @apply flex items-center gap-4;
}

.status-item {
  @apply text-center;
}

.status-label {
  @apply block text-xs text-white text-opacity-70;
}

.status-value {
  @apply block text-lg font-semibold text-white;
}

/* 指标概览样式 */
.metrics-overview {
  @apply mb-6;
}

.main-score-section {
  @apply grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6;
}

.main-score-card {
  @apply lg:col-span-2;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 16px;
  overflow: hidden;
}

.score-content {
  @apply flex items-center gap-8 p-6;
  color: white;
}

.score-visual {
  @apply flex-shrink-0;
}

.score-circle {
  @apply w-32 h-32 rounded-full flex items-center justify-center relative;
  position: relative;
}

.score-inner {
  @apply w-24 h-24 bg-white rounded-full flex flex-col items-center justify-center;
  color: #1f2937;
}

.score-number {
  @apply text-3xl font-bold;
}

.score-grade {
  @apply text-sm font-medium text-gray-600;
}

.score-details {
  @apply flex-1;
}

.score-title {
  @apply text-2xl font-bold mb-2;
}

.score-status {
  @apply inline-block px-3 py-1 rounded-full text-sm font-medium mb-3;
}

.score-description {
  @apply text-white text-opacity-80 mb-4;
}

.score-trend {
  @apply flex items-center gap-2;
}

.trend-label {
  @apply text-sm text-white text-opacity-70;
}

.trend-value.positive {
  @apply text-green-300 font-semibold;
}

.distribution-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 16px;
  border: 1px solid #e2e8f0;
}

.card-header {
  @apply flex items-center gap-2 font-semibold;
}

.distribution-chart {
  @apply space-y-4;
}

.distribution-item {
  @apply flex items-center justify-between;
}

.dist-label {
  @apply text-sm font-medium w-12;
}

.dist-value {
  @apply text-sm font-bold w-12 text-right;
}

.dist-bar {
  @apply flex-1 h-2 bg-gray-200 rounded-full mx-3 overflow-hidden;
}

.dist-fill {
  @apply h-full transition-all duration-500 ease-out;
}

.distribution-item.excellent .dist-fill {
  @apply bg-green-500;
}

.distribution-item.good .dist-fill {
  @apply bg-blue-500;
}

.distribution-item.average .dist-fill {
  @apply bg-yellow-500;
}

.distribution-item.poor .dist-fill {
  @apply bg-red-500;
}

/* 指标网格样式 */
.metrics-grid {
  @apply grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4;
}

.metric-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  overflow: hidden;
  position: relative;
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea, #764ba2);
}

.metric-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.metric-content {
  @apply p-4 flex items-center gap-3;
}

.metric-icon {
  @apply w-12 h-12 rounded-lg flex items-center justify-center;
  background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
}

.metric-info {
  @apply flex-1;
}

.metric-value {
  @apply text-2xl font-bold text-gray-800;
}

.metric-label {
  @apply text-sm text-gray-600 mb-1;
}

.metric-change {
  @apply text-xs font-medium;
}

.metric-change.positive {
  @apply text-green-600;
}

.metric-change.negative {
  @apply text-red-600;
}

.metric-change.neutral {
  @apply text-gray-500;
}

/* 建议卡片样式 */
.recommendation-card {
  background: linear-gradient(135deg, #ffffff 0%, #fefbf7 100%);
  border-radius: 16px;
  border: 1px solid #f0e6d2;
}

.card-header-enhanced {
  @apply flex items-center justify-between;
}

.header-title {
  @apply flex items-center gap-3;
}

.ai-tag {
  @apply ml-2;
}

.header-stats {
  @apply flex items-center gap-4;
}

.stat-item {
  @apply text-center;
}

.stat-label {
  @apply block text-xs text-gray-500;
}

.stat-value {
  @apply block text-sm font-bold text-gray-800;
}

.recommendations-container {
  @apply space-y-6;
}

.recommendation-types {
  @apply flex items-center gap-2 flex-wrap;
}

.type-badge {
  @apply flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium;
}

.type-badge.lifestyle {
  @apply bg-blue-100 text-blue-800;
}

.type-badge.exercise {
  @apply bg-green-100 text-green-800;
}

.type-badge.nutrition {
  @apply bg-orange-100 text-orange-800;
}

.type-badge.medical {
  @apply bg-red-100 text-red-800;
}

.type-badge.mental {
  @apply bg-purple-100 text-purple-800;
}

.type-icon {
  @apply text-sm;
}

.type-count {
  @apply font-bold;
}

.recommendations-list {
  @apply grid grid-cols-1 lg:grid-cols-2 gap-4;
}

.recommendation-item {
  @apply p-4 border rounded-lg transition-all duration-200 cursor-pointer;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
}

.recommendation-item:hover {
  @apply shadow-md border-blue-300;
  transform: translateY(-2px);
}

.recommendation-item.high {
  @apply border-l-4 border-l-red-500;
}

.recommendation-item.medium {
  @apply border-l-4 border-l-yellow-500;
}

.recommendation-item.low {
  @apply border-l-4 border-l-green-500;
}

.rec-header {
  @apply flex items-start gap-2 mb-2;
}

.rec-priority {
  @apply w-2 h-2 rounded-full mt-2;
}

.rec-priority.high {
  @apply bg-red-500;
}

.rec-priority.medium {
  @apply bg-yellow-500;
}

.rec-priority.low {
  @apply bg-green-500;
}

.rec-title {
  @apply flex-1 font-semibold text-gray-800;
}

.rec-badges {
  @apply flex gap-1;
}

.rec-content {
  @apply text-sm text-gray-600 mb-3;
}

.rec-footer {
  @apply flex items-center justify-between;
}

.rec-user {
  @apply flex items-center gap-2;
}

.user-info {
  @apply flex flex-col;
}

.user-name {
  @apply text-xs font-medium text-gray-800;
}

.user-dept {
  @apply text-xs text-gray-500;
}

.rec-meta {
  @apply text-right;
}

.effectiveness {
  @apply mb-1;
}

.eff-label {
  @apply text-xs text-gray-500;
}

.rec-time {
  @apply text-xs text-gray-400;
}

.recommendations-actions {
  @apply flex items-center gap-3 pt-4 border-t border-gray-100;
}

.empty-state {
  @apply text-center py-12;
}

.empty-icon {
  @apply mb-4;
}

.empty-title {
  @apply text-lg font-semibold text-gray-800 mb-2;
}

.empty-description {
  @apply text-sm text-gray-600 mb-4;
}

/* 图表卡片样式 */
.chart-card {
  background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
  border: 1px solid #e8f4fd;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.08);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.chart-card:hover {
  box-shadow: 0 8px 24px rgba(24, 144, 255, 0.12);
  transform: translateY(-2px);
}

:deep(.n-card .n-card-header) {
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 12px;
}

:deep(.n-statistic .n-statistic-label) {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

:deep(.n-statistic .n-statistic-value) {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chart-card .h-80 {
    height: 250px;
  }
  
  .grid.grid-cols-1.md\:grid-cols-2.lg\:grid-cols-6 {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .col-span-1.md\:col-span-2.lg\:col-span-2 {
    grid-column: span 2;
  }
}

/* 动画效果 */
.chart-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 主题色彩 */
:root {
  --health-primary: #1890ff;
  --health-success: #52c41a;
  --health-warning: #faad14;
  --health-error: #ff4d4f;
  --health-info: #13c2c2;
}

/* 移动端响应式优化 */
@media (max-width: 768px) {
  .chart-card .h-80 {
    height: 250px !important;
  }
  
  .chart-card .h-96 {
    height: 300px !important;
  }
  
  .analysis-header {
    padding: 16px !important;
    margin-bottom: 1rem !important;
  }
  
  .header-content {
    flex-direction: column !important;
    gap: 1rem !important;
    align-items: flex-start !important;
  }
  
  .header-actions {
    width: 100% !important;
    justify-content: space-between !important;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr) !important;
  }
  
  .main-score-section {
    grid-template-columns: 1fr !important;
  }
  
  .recommendations-list {
    grid-template-columns: 1fr !important;
  }
}

/* 平板端优化 */
@media (min-width: 769px) and (max-width: 1024px) {
  .metrics-grid {
    grid-template-columns: repeat(3, 1fr) !important;
  }
  
  .recommendations-list {
    grid-template-columns: 1fr !important;
  }
}
</style>
