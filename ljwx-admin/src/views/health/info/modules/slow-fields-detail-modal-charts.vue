<template>
  <NModal v-model:show="modalVisible" :mask-closable="false" preset="card" class="w-95% max-w-7xl">
    <template #header>
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
            <span class="text-blue-600 font-bold text-lg">📊</span>
          </div>
          <div>
            <h3 class="text-xl font-bold text-gray-800">健康数据分析</h3>
            <p class="text-sm text-gray-500" v-if="props.rowData">
              {{ props.rowData.userName }} · {{ props.rowData.orgName }} · {{ formatTime(props.rowData.timestamp) }}
            </p>
          </div>
        </div>
        <NTag type="info" size="large" round>
          数据详情
        </NTag>
      </div>
    </template>

    <div v-if="props.rowData" class="space-y-8">
      <!-- 数据概览卡片 -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <!-- 基础生命体征统计卡片 -->
        <div v-if="vitalsStats" class="bg-red-50 rounded-lg p-4 border-l-4 border-red-400">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-red-600 font-medium">平均心率</p>
              <p class="text-2xl font-bold text-red-800">{{ vitalsStats.avgHeartRate }}</p>
              <p class="text-xs text-red-500">{{ vitalsStats.dataPoints }}次测量</p>
            </div>
            <span class="text-3xl">❤️</span>
          </div>
        </div>

        <div v-if="vitalsStats" class="bg-blue-50 rounded-lg p-4 border-l-4 border-blue-400">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-blue-600 font-medium">平均血氧</p>
              <p class="text-2xl font-bold text-blue-800">{{ vitalsStats.avgBloodOxygen }}%</p>
              <p class="text-xs text-blue-500">血压: {{ vitalsStats.avgPressure }}</p>
            </div>
            <span class="text-3xl">🫁</span>
          </div>
        </div>

        <!-- 运动时序统计卡片 -->
        <div v-if="exerciseTimeSeriesStats" class="bg-green-50 rounded-lg p-4 border-l-4 border-green-400">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-green-600 font-medium">总步数</p>
              <p class="text-2xl font-bold text-green-800">{{ exerciseTimeSeriesStats.totalSteps.toLocaleString() }}</p>
              <p class="text-xs text-green-500">{{ exerciseTimeSeriesStats.activeDays }}活跃天</p>
            </div>
            <span class="text-3xl">👟</span>
          </div>
        </div>

        <div v-if="exerciseTimeSeriesStats" class="bg-orange-50 rounded-lg p-4 border-l-4 border-orange-400">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-orange-600 font-medium">总卡路里</p>
              <p class="text-2xl font-bold text-orange-800">{{ exerciseTimeSeriesStats.totalCalories }}</p>
              <p class="text-xs text-orange-500">{{ exerciseTimeSeriesStats.totalDistance }}km</p>
            </div>
            <span class="text-3xl">🔥</span>
          </div>
        </div>

        <div v-if="sleepStats" class="bg-purple-50 rounded-lg p-4 border-l-4 border-purple-400">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-purple-600 font-medium">睡眠质量</p>
              <p class="text-2xl font-bold text-purple-800">{{ sleepStats.totalHours }}h</p>
              <p class="text-xs text-purple-500">{{ sleepStats.sessions }}次记录</p>
            </div>
            <span class="text-3xl">😴</span>
          </div>
        </div>

        <div v-if="workoutStats" class="bg-orange-50 rounded-lg p-4 border-l-4 border-orange-400">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-orange-600 font-medium">运动强度</p>
              <p class="text-2xl font-bold text-orange-800">{{ workoutStats.totalCalories }}</p>
              <p class="text-xs text-orange-500">{{ workoutStats.sessions }}次运动</p>
            </div>
            <span class="text-3xl">🏃</span>
          </div>
        </div>

        <div v-if="dailyStats" class="bg-cyan-50 rounded-lg p-4 border-l-4 border-cyan-400">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-cyan-600 font-medium">日均步数</p>
              <p class="text-2xl font-bold text-cyan-800">{{ dailyStats.avgSteps }}</p>
              <p class="text-xs text-cyan-500">{{ dailyStats.activeDays }}活跃天</p>
            </div>
            <span class="text-3xl">🚶</span>
          </div>
        </div>

        <div v-if="weeklyStats" class="bg-pink-50 rounded-lg p-4 border-l-4 border-pink-400">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-pink-600 font-medium">周运动量</p>
              <p class="text-2xl font-bold text-pink-800">{{ weeklyStats.avgTime }}min</p>
              <p class="text-xs text-pink-500">{{ weeklyStats.activeWeeks }}活跃周</p>
            </div>
            <span class="text-3xl">📅</span>
          </div>
        </div>
      </div>

      <!-- 基础生命体征图表 -->
      <div v-if="vitalsChartData.length > 0" class="bg-white rounded-xl shadow-sm border p-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
              <span class="text-red-600">❤️</span>
            </div>
            <div>
              <h4 class="text-lg font-bold text-gray-800">基础生命体征</h4>
              <p class="text-sm text-gray-500">心率·血氧·血压·体温·压力时序分析</p>
            </div>
          </div>
          <NTag type="error" size="small">多指标图表</NTag>
        </div>
        <div ref="vitalsChartRef" class="h-80 w-full"></div>
      </div>

      <!-- 运动健康数据图表 -->
      <div v-if="exerciseTimeSeriesData.length > 0" class="bg-white rounded-xl shadow-sm border p-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <span class="text-green-600">🏃</span>
            </div>
            <div>
              <h4 class="text-lg font-bold text-gray-800">运动健康数据</h4>
              <p class="text-sm text-gray-500">步数·卡路里·距离时序分析</p>
            </div>
          </div>
          <NTag type="success" size="small">运动趋势</NTag>
        </div>
        <div ref="exerciseTimeSeriesChartRef" class="h-80 w-full"></div>
      </div>

      <!-- 睡眠数据图表 -->
      <div v-if="sleepChartData.length > 0" class="bg-white rounded-xl shadow-sm border p-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
              <span class="text-purple-600">🌙</span>
            </div>
            <div>
              <h4 class="text-lg font-bold text-gray-800">睡眠分析</h4>
              <p class="text-sm text-gray-500">深度睡眠 vs 浅度睡眠时长对比</p>
            </div>
          </div>
          <NTag type="warning" size="small">时序图表</NTag>
        </div>
        <div ref="sleepChartRef" class="h-80 w-full"></div>
      </div>

      <!-- 运动数据图表 -->
      <div v-if="workoutChartData.length > 0" class="bg-white rounded-xl shadow-sm border p-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
              <span class="text-orange-600">💪</span>
            </div>
            <div>
              <h4 class="text-lg font-bold text-gray-800">运动表现</h4>
              <p class="text-sm text-gray-500">卡路里消耗 & 运动距离趋势</p>
            </div>
          </div>
          <NTag type="success" size="small">双轴图表</NTag>
        </div>
        <div ref="workoutChartRef" class="h-80 w-full"></div>
      </div>

      <!-- 每日运动数据图表 -->
      <div v-if="dailyChartData.length > 0" class="bg-white rounded-xl shadow-sm border p-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-cyan-100 rounded-full flex items-center justify-center">
              <span class="text-cyan-600">📈</span>
            </div>
            <div>
              <h4 class="text-lg font-bold text-gray-800">每日活动</h4>
              <p class="text-sm text-gray-500">步数 & 运动时长日度分析</p>
            </div>
          </div>
          <NTag type="info" size="small">柱状图</NTag>
        </div>
        <div ref="dailyChartRef" class="h-80 w-full"></div>
      </div>

      <!-- 每周运动数据图表 -->
      <div v-if="weeklyChartData.length > 0" class="bg-white rounded-xl shadow-sm border p-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-pink-100 rounded-full flex items-center justify-center">
              <span class="text-pink-600">🎯</span>
            </div>
            <div>
              <h4 class="text-lg font-bold text-gray-800">周度表现</h4>
              <p class="text-sm text-gray-500">多维度运动指标雷达分析</p>
            </div>
          </div>
          <NTag type="error" size="small">雷达图</NTag>
        </div>
        <div ref="weeklyChartRef" class="h-80 w-full"></div>
      </div>

      <!-- 空数据提示 -->
      <div v-if="!hasAnyData" class="text-center py-16">
        <div class="text-6xl mb-4">📊</div>
        <h3 class="text-xl font-semibold text-gray-600 mb-2">暂无详细数据</h3>
        <p class="text-gray-400">该用户在此时间段内暂无慢字段健康数据记录</p>
      </div>
    </div>

    <template #action>
      <NSpace justify="end" size="large">
        <NButton @click="modalVisible = false" size="large">
          关闭
        </NButton>
        <NButton type="primary" @click="exportChartImages" size="large">
          <template #icon>
            <span class="text-base">📸</span>
          </template>
          导出图表
        </NButton>
        <NButton type="info" @click="exportRawData" size="large">
          <template #icon>
            <span class="text-base">📊</span>
          </template>
          导出数据
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch, onUnmounted } from 'vue';
import { convertToBeijingTime } from '@/utils/date';
import { 
  NModal, 
  NSpace, 
  NTag, 
  NButton
} from 'naive-ui';
import * as echarts from 'echarts';

interface Props {
  visible: boolean;
  rowData: any;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  rowData: null
});

const emit = defineEmits<{
  'update:visible': [visible: boolean];
}>();

const modalVisible = computed({
  get: () => props.visible,
  set: (visible: boolean) => emit('update:visible', visible)
});

// Chart refs
const vitalsChartRef = ref<HTMLDivElement>();
const exerciseTimeSeriesChartRef = ref<HTMLDivElement>();
const sleepChartRef = ref<HTMLDivElement>();
const workoutChartRef = ref<HTMLDivElement>();
const dailyChartRef = ref<HTMLDivElement>();
const weeklyChartRef = ref<HTMLDivElement>();

// Chart instances
let vitalsChart: echarts.ECharts | null = null;
let exerciseTimeSeriesChart: echarts.ECharts | null = null;
let sleepChart: echarts.ECharts | null = null;
let workoutChart: echarts.ECharts | null = null;
let dailyChart: echarts.ECharts | null = null;
let weeklyChart: echarts.ECharts | null = null;

// 格式化时间
const formatTime = (timestamp: number) => {
  return convertToBeijingTime(timestamp);
};

// 数据解析和计算
const sleepChartData = computed(() => {
  if (!props.rowData?.sleepData) return [];
  let data = props.rowData.sleepData;
  if (typeof data === 'string') {
    try { data = JSON.parse(data); } catch (e) { return []; }
  }
  return Array.isArray(data.data) ? data.data : [];
});

// 新增：基础生命体征数据
const vitalsChartData = computed(() => {
  if (!props.rowData?.vitalsTimeSeries) return [];
  return Array.isArray(props.rowData.vitalsTimeSeries) ? props.rowData.vitalsTimeSeries : [];
});

// 新增：运动时序数据
const exerciseTimeSeriesData = computed(() => {
  if (!props.rowData?.exerciseTimeSeries) return [];
  return Array.isArray(props.rowData.exerciseTimeSeries) ? props.rowData.exerciseTimeSeries : [];
});

const workoutChartData = computed(() => {
  if (!props.rowData?.workoutData) return [];
  let data = props.rowData.workoutData;
  if (typeof data === 'string') {
    try { data = JSON.parse(data); } catch (e) { return []; }
  }
  return Array.isArray(data.data) ? data.data : [];
});

const dailyChartData = computed(() => {
  if (!props.rowData?.exerciseDailyData) return [];
  let data = props.rowData.exerciseDailyData;
  if (typeof data === 'string') {
    try { data = JSON.parse(data); } catch (e) { return []; }
  }
  return Array.isArray(data.data) ? data.data.filter((item: any) => item.timeStamps > 0) : [];
});

const weeklyChartData = computed(() => {
  if (!props.rowData?.exerciseWeekData) return [];
  let data = props.rowData.exerciseWeekData;
  if (typeof data === 'string') {
    try { data = JSON.parse(data); } catch (e) { return []; }
  }
  return Array.isArray(data.data) ? data.data.filter((item: any) => item.timeStamps > 0) : [];
});

// 统计数据
const sleepStats = computed(() => {
  if (sleepChartData.value.length === 0) return null;
  const totalMinutes = sleepChartData.value.reduce((sum: number, item: any) => 
    sum + (item.deepSleep || 0) + (item.lightSleep || 0), 0);
  return {
    totalHours: Math.round(totalMinutes / 60 * 10) / 10,
    sessions: sleepChartData.value.length
  };
});

// 新增：基础生命体征统计
const vitalsStats = computed(() => {
  if (vitalsChartData.value.length === 0) return null;
  const data = vitalsChartData.value;
  return {
    avgHeartRate: Math.round(data.reduce((sum: number, item: any) => sum + (item.heartRate || 0), 0) / data.length),
    avgBloodOxygen: Math.round(data.reduce((sum: number, item: any) => sum + (item.bloodOxygen || 0), 0) / data.length),
    avgTemperature: Math.round(data.reduce((sum: number, item: any) => sum + (item.temperature || 0), 0) / data.length * 10) / 10,
    avgPressure: Math.round(data.reduce((sum: number, item: any) => sum + (item.pressureHigh || 0), 0) / data.length) + '/' + 
                Math.round(data.reduce((sum: number, item: any) => sum + (item.pressureLow || 0), 0) / data.length),
    dataPoints: data.length
  };
});

// 新增：运动时序统计
const exerciseTimeSeriesStats = computed(() => {
  if (exerciseTimeSeriesData.value.length === 0) return null;
  const data = exerciseTimeSeriesData.value;
  return {
    totalSteps: data.reduce((sum: number, item: any) => sum + (item.step || 0), 0),
    totalCalories: data.reduce((sum: number, item: any) => sum + (item.calorie || 0), 0),
    totalDistance: Math.round(data.reduce((sum: number, item: any) => sum + (item.distance || 0), 0) * 10) / 10,
    activeDays: data.filter((item: any) => (item.step || 0) > 1000).length
  };
});

const workoutStats = computed(() => {
  if (workoutChartData.value.length === 0) return null;
  return {
    totalCalories: workoutChartData.value.reduce((sum: number, item: any) => sum + (item.calorie || 0), 0),
    sessions: workoutChartData.value.length
  };
});

const dailyStats = computed(() => {
  if (dailyChartData.value.length === 0) return null;
  const validData = dailyChartData.value.filter((item: any) => item.totalSteps > 0);
  return {
    avgSteps: validData.length > 0 ? Math.round(
      validData.reduce((sum: number, item: any) => sum + (item.totalSteps || 0), 0) / validData.length
    ) : 0,
    activeDays: validData.length
  };
});

const weeklyStats = computed(() => {
  if (weeklyChartData.value.length === 0) return null;
  const validData = weeklyChartData.value.filter((item: any) => item.totalTime > 0);
  return {
    avgTime: validData.length > 0 ? Math.round(
      validData.reduce((sum: number, item: any) => sum + (item.totalTime || 0), 0) / validData.length
    ) : 0,
    activeWeeks: validData.length
  };
});

const hasAnyData = computed(() => {
  return sleepChartData.value.length > 0 || 
         workoutChartData.value.length > 0 || 
         dailyChartData.value.length > 0 || 
         weeklyChartData.value.length > 0 ||
         vitalsChartData.value.length > 0 ||
         exerciseTimeSeriesData.value.length > 0;
});

// 创建基础生命体征图表
function createVitalsChart() {
  if (!vitalsChartRef.value || vitalsChartData.value.length === 0) return;
  
  vitalsChart = echarts.init(vitalsChartRef.value);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: (params: any) => {
        const date = new Date(params[0].name).toLocaleString();
        let result = `<div style="padding: 8px"><strong>${date}</strong><br/>`;
        params.forEach((param: any) => {
          result += `<div style="margin: 4px 0">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: ${param.color}; margin-right: 8px"></span>
            ${param.seriesName}: ${param.value}${param.seriesName.includes('心率') ? ' BPM' : 
                                                 param.seriesName.includes('血氧') ? '%' : 
                                                 param.seriesName.includes('体温') ? '°C' : 
                                                 param.seriesName.includes('压力') ? '' : ''}
          </div>`;
        });
        return result + '</div>';
      }
    },
    legend: {
      data: ['心率', '血氧', '体温', '压力指数'],
      top: 10
    },
    grid: {
      left: '3%', right: '4%', bottom: '3%', containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: vitalsChartData.value.map((item: any) => item.timestamp),
      axisLabel: {
        formatter: (value: number) => new Date(value).toLocaleDateString('zh-CN', {
          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        })
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '心率/血氧',
        position: 'left',
        axisLabel: { formatter: '{value}' },
        axisLine: { lineStyle: { color: '#ff4d4f' } },
        min: 60,
        max: 120
      },
      {
        type: 'value',
        name: '体温/压力',
        position: 'right',
        axisLabel: { formatter: '{value}' },
        axisLine: { lineStyle: { color: '#52c41a' } }
      }
    ],
    series: [
      {
        name: '心率',
        type: 'line',
        yAxisIndex: 0,
        data: vitalsChartData.value.map((item: any) => item.heartRate || 0),
        smooth: true,
        itemStyle: { color: '#ff4d4f' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255, 77, 79, 0.3)' },
            { offset: 1, color: 'rgba(255, 77, 79, 0.1)' }
          ])
        }
      },
      {
        name: '血氧',
        type: 'line',
        yAxisIndex: 0,
        data: vitalsChartData.value.map((item: any) => item.bloodOxygen || 0),
        smooth: true,
        itemStyle: { color: '#1890ff' }
      },
      {
        name: '体温',
        type: 'line',
        yAxisIndex: 1,
        data: vitalsChartData.value.map((item: any) => item.temperature || 0),
        smooth: true,
        itemStyle: { color: '#52c41a' }
      },
      {
        name: '压力指数',
        type: 'line',
        yAxisIndex: 1,
        data: vitalsChartData.value.map((item: any) => item.stress || 0),
        smooth: true,
        itemStyle: { color: '#faad14' }
      }
    ]
  };
  
  vitalsChart.setOption(option);
}

// 创建运动时序图表
function createExerciseTimeSeriesChart() {
  if (!exerciseTimeSeriesChartRef.value || exerciseTimeSeriesData.value.length === 0) return;
  
  exerciseTimeSeriesChart = echarts.init(exerciseTimeSeriesChartRef.value);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['步数', '卡路里', '距离'],
      top: 10
    },
    grid: {
      left: '3%', right: '4%', bottom: '3%', containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: exerciseTimeSeriesData.value.map((item: any) => item.timestamp),
      axisLabel: {
        formatter: (value: number) => new Date(value).toLocaleDateString('zh-CN', {
          month: 'short', day: 'numeric'
        })
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '步数',
        position: 'left',
        axisLabel: { formatter: '{value} 步' },
        axisLine: { lineStyle: { color: '#52c41a' } }
      },
      {
        type: 'value',
        name: '卡路里/距离',
        position: 'right',
        axisLabel: { formatter: '{value}' },
        axisLine: { lineStyle: { color: '#faad14' } }
      }
    ],
    series: [
      {
        name: '步数',
        type: 'bar',
        yAxisIndex: 0,
        data: exerciseTimeSeriesData.value.map((item: any) => item.step || 0),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#73d13d' },
            { offset: 1, color: '#36cfc9' }
          ])
        }
      },
      {
        name: '卡路里',
        type: 'line',
        yAxisIndex: 1,
        data: exerciseTimeSeriesData.value.map((item: any) => item.calorie || 0),
        smooth: true,
        itemStyle: { color: '#faad14' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(250, 173, 20, 0.3)' },
            { offset: 1, color: 'rgba(250, 173, 20, 0.1)' }
          ])
        }
      },
      {
        name: '距离',
        type: 'line',
        yAxisIndex: 1,
        data: exerciseTimeSeriesData.value.map((item: any) => item.distance || 0),
        smooth: true,
        itemStyle: { color: '#f759ab' }
      }
    ]
  };
  
  exerciseTimeSeriesChart.setOption(option);
}

// 创建睡眠图表
function createSleepChart() {
  if (!sleepChartRef.value || sleepChartData.value.length === 0) return;
  
  sleepChart = echarts.init(sleepChartRef.value);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: (params: any) => {
        const date = new Date(params[0].name).toLocaleDateString();
        let result = `<div style="padding: 8px"><strong>${date}</strong><br/>`;
        params.forEach((param: any) => {
          result += `<div style="margin: 4px 0">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: ${param.color}; margin-right: 8px"></span>
            ${param.seriesName}: ${param.value} 分钟
          </div>`;
        });
        return result + '</div>';
      }
    },
    legend: {
      data: ['深度睡眠', '浅度睡眠'],
      top: 10
    },
    grid: {
      left: '3%', right: '4%', bottom: '3%', containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: sleepChartData.value.map((item: any) => 
        item.startTimeStamp || item.timeStamps
      ),
      axisLabel: {
        formatter: (value: number) => new Date(value).toLocaleDateString('zh-CN', {
          month: 'short', day: 'numeric'
        })
      }
    },
    yAxis: {
      type: 'value',
      name: '睡眠时长 (分钟)',
      axisLabel: { formatter: '{value} min' }
    },
    series: [
      {
        name: '深度睡眠',
        type: 'area',
        stack: 'sleep',
        data: sleepChartData.value.map((item: any) => item.deepSleep || 0),
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(138, 43, 226, 0.8)' },
            { offset: 1, color: 'rgba(138, 43, 226, 0.1)' }
          ])
        },
        itemStyle: { color: '#8a2be2' }
      },
      {
        name: '浅度睡眠',
        type: 'area',
        stack: 'sleep',
        data: sleepChartData.value.map((item: any) => item.lightSleep || 0),
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(186, 85, 211, 0.6)' },
            { offset: 1, color: 'rgba(186, 85, 211, 0.1)' }
          ])
        },
        itemStyle: { color: '#ba55d3' }
      }
    ]
  };
  
  sleepChart.setOption(option);
}

// 创建运动图表
function createWorkoutChart() {
  if (!workoutChartRef.value || workoutChartData.value.length === 0) return;
  
  workoutChart = echarts.init(workoutChartRef.value);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['卡路里', '距离'],
      top: 10
    },
    grid: {
      left: '3%', right: '4%', bottom: '3%', containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: workoutChartData.value.map((item: any) => 
        item.startTimeStamp || item.timeStamps
      ),
      axisLabel: {
        formatter: (value: number) => new Date(value).toLocaleDateString('zh-CN', {
          month: 'short', day: 'numeric'
        })
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '卡路里',
        position: 'left',
        axisLabel: { formatter: '{value} cal' },
        axisLine: { lineStyle: { color: '#ff7f50' } }
      },
      {
        type: 'value',
        name: '距离 (米)',
        position: 'right',
        axisLabel: { formatter: '{value} m' },
        axisLine: { lineStyle: { color: '#20b2aa' } }
      }
    ],
    series: [
      {
        name: '卡路里',
        type: 'line',
        yAxisIndex: 0,
        data: workoutChartData.value.map((item: any) => item.calorie || 0),
        smooth: true,
        itemStyle: { color: '#ff7f50' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255, 127, 80, 0.3)' },
            { offset: 1, color: 'rgba(255, 127, 80, 0.1)' }
          ])
        }
      },
      {
        name: '距离',
        type: 'line',
        yAxisIndex: 1,
        data: workoutChartData.value.map((item: any) => item.distance || 0),
        smooth: true,
        itemStyle: { color: '#20b2aa' }
      }
    ]
  };
  
  workoutChart.setOption(option);
}

// 创建每日运动图表
function createDailyChart() {
  if (!dailyChartRef.value || dailyChartData.value.length === 0) return;
  
  dailyChart = echarts.init(dailyChartRef.value);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['步数', '运动时长'],
      top: 10
    },
    grid: {
      left: '3%', right: '4%', bottom: '3%', containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dailyChartData.value.map((item: any, index: number) => 
        `第${index + 1}天`
      )
    },
    yAxis: [
      {
        type: 'value',
        name: '步数',
        position: 'left',
        axisLabel: { formatter: '{value} 步' },
        axisLine: { lineStyle: { color: '#1890ff' } }
      },
      {
        type: 'value',
        name: '时长 (分钟)',
        position: 'right',
        axisLabel: { formatter: '{value} min' },
        axisLine: { lineStyle: { color: '#52c41a' } }
      }
    ],
    series: [
      {
        name: '步数',
        type: 'bar',
        yAxisIndex: 0,
        data: dailyChartData.value.map((item: any) => item.totalSteps || 0),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#1890ff' },
            { offset: 1, color: '#69c0ff' }
          ])
        }
      },
      {
        name: '运动时长',
        type: 'line',
        yAxisIndex: 1,
        data: dailyChartData.value.map((item: any) => item.totalTime || 0),
        smooth: true,
        itemStyle: { color: '#52c41a' }
      }
    ]
  };
  
  dailyChart.setOption(option);
}

// 创建每周运动图表
function createWeeklyChart() {
  if (!weeklyChartRef.value || weeklyChartData.value.length === 0) return;
  
  weeklyChart = echarts.init(weeklyChartRef.value);
  
  const maxValues = weeklyChartData.value.reduce((max: any, item: any) => ({
    steps: Math.max(max.steps, item.totalSteps || 0),
    strength: Math.max(max.strength, item.strengthTimes || 0),
    time: Math.max(max.time, item.totalTime || 0)
  }), { steps: 0, strength: 0, time: 0 });
  
  const option = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      data: weeklyChartData.value.map((_: any, index: number) => `第${index + 1}周`),
      top: 10
    },
    radar: {
      indicator: [
        { name: '步数', max: maxValues.steps * 1.2 },
        { name: '强度训练(分钟)', max: maxValues.strength * 1.2 },
        { name: '总时长(分钟)', max: maxValues.time * 1.2 }
      ],
      center: ['50%', '55%'],
      radius: 120
    },
    series: [{
      type: 'radar',
      data: weeklyChartData.value.map((item: any, index: number) => ({
        value: [
          item.totalSteps || 0,
          item.strengthTimes || 0,
          item.totalTime || 0
        ],
        name: `第${index + 1}周`,
        itemStyle: {
          color: `hsl(${index * 60}, 70%, 50%)`
        },
        areaStyle: {
          color: `hsla(${index * 60}, 70%, 50%, 0.2)`
        }
      }))
    }]
  };
  
  weeklyChart.setOption(option);
}

// 监听模态框显示状态
watch(() => props.visible, async (visible) => {
  if (visible && props.rowData) {
    await nextTick();
    
    // 销毁现有图表
    [vitalsChart, exerciseTimeSeriesChart, sleepChart, workoutChart, dailyChart, weeklyChart].forEach(chart => {
      if (chart) chart.dispose();
    });
    
    // 延迟创建新图表，确保DOM已渲染
    setTimeout(() => {
      createVitalsChart();
      createExerciseTimeSeriesChart();
      createSleepChart();
      createWorkoutChart();
      createDailyChart();
      createWeeklyChart();
    }, 200);
  }
});

// 组件卸载时清理图表
onUnmounted(() => {
  [vitalsChart, exerciseTimeSeriesChart, sleepChart, workoutChart, dailyChart, weeklyChart].forEach(chart => {
    if (chart) chart.dispose();
  });
});

// 导出图表图片
function exportChartImages() {
  const charts = [
    { chart: vitalsChart, name: '基础生命体征' },
    { chart: exerciseTimeSeriesChart, name: '运动健康数据' },
    { chart: sleepChart, name: '睡眠分析' },
    { chart: workoutChart, name: '运动表现' },
    { chart: dailyChart, name: '每日活动' },
    { chart: weeklyChart, name: '周度表现' }
  ];
  
  charts.forEach(({ chart, name }, index) => {
    if (chart) {
      const canvas = chart.getCanvasPaintAble();
      const url = canvas.toDataURL('image/png');
      const a = document.createElement('a');
      a.href = url;
      a.download = `${name}_${props.rowData.userName}_${Date.now() + index}.png`;
      a.click();
    }
  });
}

// 导出原始数据
function exportRawData() {
  const exportData = {
    userInfo: {
      userId: props.rowData.userId,
      userName: props.rowData.userName,
      orgName: props.rowData.orgName,
      timestamp: props.rowData.timestamp
    },
    statistics: {
      vitals: vitalsStats.value,
      exerciseTimeSeries: exerciseTimeSeriesStats.value,
      sleep: sleepStats.value,
      workout: workoutStats.value,
      daily: dailyStats.value,
      weekly: weeklyStats.value
    },
    rawData: {
      vitalsTimeSeries: vitalsChartData.value,
      exerciseTimeSeries: exerciseTimeSeriesData.value,
      sleepData: sleepChartData.value,
      workoutData: workoutChartData.value,
      exerciseDailyData: dailyChartData.value,
      exerciseWeekData: weeklyChartData.value
    }
  };
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `健康数据分析_${props.rowData.userName}_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<style scoped>
.space-y-8 > * + * {
  margin-top: 2rem;
}

.space-y-3 > * + * {
  margin-top: 0.75rem;
}

.space-x-3 > * + * {
  margin-left: 0.75rem;
}

.grid {
  display: grid;
}

.grid-cols-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (min-width: 768px) {
  .md\:grid-cols-4 {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.gap-4 {
  gap: 1rem;
}

.w-95\% {
  width: 95%;
}

.max-w-7xl {
  max-width: 80rem;
}

.h-80 {
  height: 20rem;
}

.w-full {
  width: 100%;
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.justify-between {
  justify-content: space-between;
}

.rounded-xl {
  border-radius: 0.75rem;
}

.rounded-lg {
  border-radius: 0.5rem;
}

.rounded-full {
  border-radius: 9999px;
}

.shadow-sm {
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}

.border {
  border-width: 1px;
  border-color: #e5e7eb;
}

.border-l-4 {
  border-left-width: 4px;
}

.border-purple-400 {
  border-color: #c084fc;
}

.border-orange-400 {
  border-color: #fb923c;
}

.border-cyan-400 {
  border-color: #22d3ee;
}

.border-pink-400 {
  border-color: #f472b6;
}

.p-4 {
  padding: 1rem;
}

.p-6 {
  padding: 1.5rem;
}

.py-16 {
  padding-top: 4rem;
  padding-bottom: 4rem;
}

.mb-2 {
  margin-bottom: 0.5rem;
}

.mb-4 {
  margin-bottom: 1rem;
}

.mb-6 {
  margin-bottom: 1.5rem;
}

.w-8 {
  width: 2rem;
}

.h-8 {
  height: 2rem;
}

.w-10 {
  width: 2.5rem;
}

.h-10 {
  height: 2.5rem;
}

.text-center {
  text-align: center;
}

.text-xs {
  font-size: 0.75rem;
  line-height: 1rem;
}

.text-sm {
  font-size: 0.875rem;
  line-height: 1.25rem;
}

.text-base {
  font-size: 1rem;
  line-height: 1.5rem;
}

.text-lg {
  font-size: 1.125rem;
  line-height: 1.75rem;
}

.text-xl {
  font-size: 1.25rem;
  line-height: 1.75rem;
}

.text-2xl {
  font-size: 1.5rem;
  line-height: 2rem;
}

.text-6xl {
  font-size: 3.75rem;
  line-height: 1;
}

.font-medium {
  font-weight: 500;
}

.font-semibold {
  font-weight: 600;
}

.font-bold {
  font-weight: 700;
}

.bg-white {
  background-color: white;
}

.bg-purple-50 {
  background-color: #faf5ff;
}

.bg-purple-100 {
  background-color: #f3e8ff;
}

.bg-orange-50 {
  background-color: #fff7ed;
}

.bg-orange-100 {
  background-color: #fed7aa;
}

.bg-cyan-50 {
  background-color: #ecfeff;
}

.bg-cyan-100 {
  background-color: #cffafe;
}

.bg-pink-50 {
  background-color: #fdf2f8;
}

.bg-pink-100 {
  background-color: #fce7f3;
}

.bg-blue-100 {
  background-color: #dbeafe;
}

.text-purple-500 {
  color: #a855f7;
}

.text-purple-600 {
  color: #9333ea;
}

.text-purple-800 {
  color: #6b21a8;
}

.text-orange-500 {
  color: #f97316;
}

.text-orange-600 {
  color: #ea580c;
}

.text-orange-800 {
  color: #9a3412;
}

.text-cyan-500 {
  color: #06b6d4;
}

.text-cyan-600 {
  color: #0891b2;
}

.text-cyan-800 {
  color: #155e75;
}

.text-pink-500 {
  color: #ec4899;
}

.text-pink-600 {
  color: #db2777;
}

.text-pink-800 {
  color: #9d174d;
}

.text-blue-600 {
  color: #2563eb;
}

.text-gray-400 {
  color: #9ca3af;
}

.text-gray-500 {
  color: #6b7280;
}

.text-gray-600 {
  color: #4b5563;
}

.text-gray-800 {
  color: #1f2937;
}
</style>