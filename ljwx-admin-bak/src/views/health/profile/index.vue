<script setup lang="ts">
import { ref } from 'vue';
import LineChart from './modules/line-chart.vue';
import RadarChart from './modules/radar-chart.vue';

interface Props {
  id: string;
}

defineProps<Props>();

// 健康指标数据
const healthMetrics = ref([
  {
    key: 'bloodPressure',
    title: '血压',
    value: '133/80',
    unit: 'mmHg',
    status: 'excellent'
  },
  {
    key: 'heartRate',
    title: '心率',
    value: '99',
    unit: '次/分钟',
    status: 'normal'
  },
  {
    key: 'bloodOxygen',
    title: '血氧',
    value: '100',
    unit: '%',
    status: 'normal'
  },
  {
    key: 'pulseRate',
    title: '脉搏率',
    value: '97',
    unit: '次/分钟',
    status: 'normal'
  },
  {
    key: 'respiratoryRate',
    title: '呼吸率',
    value: '10',
    unit: '次/分钟',
    status: 'normal'
  },
  {
    key: 'hemoglobin',
    title: '血红蛋白',
    value: '130.86',
    unit: 'g/L',
    status: 'normal'
  },
  {
    key: 'comprehensiveScore',
    title: '综合反映',
    value: '89',
    unit: '分',
    status: 'good'
  }
]);

// 详细指标数据
const detailedMetrics = ref([
  {
    name: '血压',
    value: '133/80',
    range: '90-139,50-89',
    unit: 'mmHg'
  },
  {
    name: '血氧',
    value: '100',
    range: '95-99',
    unit: '%'
  },
  {
    name: '血红蛋白',
    value: '130.86',
    range: '120-160',
    unit: 'g/L'
  }
]);

// 心率变异性趋势数据
const hrvTrendData = ref({
  labels: ['1秒', '2秒', '3秒', '4秒', '5秒', '6秒', '7秒', '8秒', '9秒', '10秒', '11秒', '12秒', '13秒', '14秒', '15秒'],
  datasets: [
    {
      data: [65, 70, 68, 72, 69, 71, 70, 73, 68, 74, 71, 69, 72, 70, 71],
      borderColor: '#3B82F6',
      fill: true,
      backgroundColor: 'rgba(59, 130, 246, 0.1)'
    }
  ]
});

// 心率变异性分析结果
const hrvAnalysis = ref({
  environmentRisk: {
    status: 'normal',
    description: '您当前没有生心血管相关疾病的风险 轻微，请继续保持。'
  },
  emotionalRisk: {
    status: 'warning',
    description: '您的情绪风险等级为 轻度，其中 LF/HF、CVNN升高，SDNN、RMSSD下降。'
  }
});

// 心率变异性趋势描述
const hrvTrendDescription = ref('心率变异性趋势描述');

// 雷达图数据
const hrvRadarData = ref({
  labels: ['产量', '压力', '疲劳', '紧张', '恢复', '睡眠'],
  datasets: [
    {
      data: [80, 70, 60, 65, 75, 85],
      backgroundColor: 'rgba(59, 130, 246, 0.2)',
      borderColor: '#3B82F6'
    }
  ]
});

const analysisResult = ref('分析结果');

// 健康建议
const healthSuggestions = ref({
  heart: [
    '均衡膳食，重人天足的膳食纤维，维生素和蛋白质',
    '保持规律的生活习惯，戒烟限酒，避免熬夜不良嗜好，规律作息',
    '坚持适度的有氧运动，提高身体代谢能力，避免肥胖'
  ],
  emotion: [
    '正确认识和对待负面情绪，尝试通过倾诉、冥想等方式缓解',
    '舍己、轻松、某些等食物能够促进身体产生多巴胺，有助于改善情绪',
    '如果这种情绪持续时间较长甚至开始影响生活应考虑咨询专业人士寻求帮助'
  ]
});

// 获取指标状态对应的样式类
function getMetricClass(status: string) {
  return {
    'bg-green-100 text-green-800': status === 'excellent',
    'bg-blue-100 text-blue-800': status === 'normal',
    'bg-yellow-100 text-yellow-800': status === 'warning',
    'bg-red-100 text-red-800': status === 'danger'
  };
}

// 获取状态对应的样式类
function getStatusClass(status: string) {
  return {
    'text-green-600': status === 'normal',
    'text-yellow-600': status === 'warning',
    'text-red-600': status === 'danger'
  };
}
</script>

<template>
  <div class="health-data-card">
    <!-- 用户基本信息 -->
    <div class="user-info mb-4 flex items-center gap-4">
      <div class="size-72px shrink-0 overflow-hidden rd-1/2">
        <img src="@/assets/imgs/soybean.jpg" class="size-full" />
      </div>
      <div class="user-details">
        <div>姓名: 灵境万象</div>
        <div>性别: 男</div>
      </div>
    </div>

    <!-- 健康指标网格 -->
    <div class="health-metrics grid grid-cols-4 mb-6 gap-4">
      <div v-for="metric in healthMetrics" :key="metric.key" class="metric-card rounded-lg p-4" :class="getMetricClass(metric.status)">
        <div class="metric-title mb-2 text-sm">{{ metric.title }}</div>
        <div class="flex items-end gap-2">
          <span class="text-xl font-bold">{{ metric.value }}</span>
          <span class="text-sm">{{ metric.unit }}</span>
        </div>
      </div>
    </div>

    <!-- 分析结果 -->
    <div class="analysis-result mb-6 rounded-lg bg-blue-50 p-4">
      <h3 class="mb-2 text-lg font-bold">分析结果</h3>
      <p class="text-sm">{{ analysisResult }}</p>
    </div>

    <!-- 详细指标表格 -->
    <div class="metrics-table mb-6 w-full">
      <table class="w-full">
        <thead>
          <tr class="bg-gray-50">
            <th class="p-2">指标</th>
            <th class="p-2">测量值</th>
            <th class="p-2">参考范围</th>
            <th class="p-2">单位</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in detailedMetrics" :key="item.name">
            <td class="p-2">{{ item.name }}</td>
            <td class="p-2">{{ item.value }}</td>
            <td class="p-2">{{ item.range }}</td>
            <td class="p-2">{{ item.unit }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 心率变异性分析部分 -->
    <div class="hrv-analysis mb-6">
      <!-- 标题 -->
      <h3 class="mb-4 text-lg font-bold">心率变异性及相关指标分析</h3>

      <!-- 心率变异性综合趋势图 -->
      <div class="trend-chart mb-6">
        <h4 class="text-md mb-2 font-bold">心率变异性综合趋势图</h4>

        <!-- 趋势说明 -->
        <div class="trend-description mt-2 text-sm text-gray-600">
          {{ hrvTrendDescription }}
        </div>
      </div>

      <!-- 心率变异性说明 -->
      <div class="hrv-description mb-6">
        <h4 class="text-md mb-2 font-bold">心率变异性说明</h4>
        <div class="rounded-lg bg-blue-50 p-4">
          <div class="mb-2">
            <span class="font-bold">心脏及外部环境分析:</span>
            <span :class="getStatusClass(hrvAnalysis.environmentRisk.status)">
              {{ hrvAnalysis.environmentRisk.description }}
            </span>
          </div>
          <div>
            <span class="font-bold">情绪心理分析:</span>
            <span :class="getStatusClass(hrvAnalysis.emotionalRisk.status)">
              {{ hrvAnalysis.emotionalRisk.description }}
            </span>
          </div>
        </div>
      </div>

      <!-- 雷达图 -->
      <div class="radar-chart mb-6">
        <h4 class="text-md mb-2 font-bold">心率变异性指标雷达图</h4>
      </div>

      <!-- 健康建议 -->
      <div class="health-suggestions">
        <h4 class="text-md mb-2 font-bold">建议</h4>
        <div class="grid grid-cols-2 gap-4">
          <div class="suggestion-card rounded-lg bg-green-50 p-4">
            <h5 class="mb-2 font-bold">心脏建议:</h5>
            <ul class="list-disc list-inside text-sm">
              <li v-for="(item, index) in healthSuggestions.heart" :key="index">
                {{ item }}
              </li>
            </ul>
          </div>
          <div class="suggestion-card rounded-lg bg-blue-50 p-4">
            <h5 class="mb-2 font-bold">情绪建议:</h5>
            <ul class="list-disc list-inside text-sm">
              <li v-for="(item, index) in healthSuggestions.emotion" :key="index">
                {{ item }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.health-data-card {
  @apply p-6 bg-white rounded-xl shadow;
}

.metric-card {
  @apply transition-all duration-300 hover:shadow-md;
}

.metrics-table {
  @apply border border-gray-200 rounded-lg overflow-hidden;
}

.metrics-table th,
.metrics-table td {
  @apply border border-gray-200;
}

.chart-container {
  @apply border border-gray-200 rounded-lg p-4;
}

.suggestion-card {
  @apply transition-all duration-300 hover:shadow-md;
}
</style>
