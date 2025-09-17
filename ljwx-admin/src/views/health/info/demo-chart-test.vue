<script setup lang="ts">
import { ref } from 'vue';
import { NButton, NCard } from 'naive-ui';
import SlowFieldsDetailModal from './modules/slow-fields-detail-modal-charts.vue';

defineOptions({
  name: 'DemoChartTest'
});

const modalVisible = ref(false);
const selectedData = ref<any>(null);

// 基础时间戳 - 最近7天的数据
const baseTime = Date.now();
const generateTimeStamps = (days: number) => {
  return Array.from({ length: days }, (_, i) => baseTime - (days - 1 - i) * 24 * 60 * 60 * 1000);
};

// 1. 基础生命体征数据 - 基于真实API格式
const generateVitalsData = () => {
  const timestamps = generateTimeStamps(7);
  return timestamps.map((timestamp, index) => ({
    altitude: 0.0,
    distance: Math.random() * 5000 + 2000, // 2-7km
    pressure_high: Math.floor(Math.random() * 20) + 115, // 115-135
    latitude: 22.540349 + Math.random() * 0.01,
    deviceSn: 'CRFTQ23409001890',
    bloodOxygen: Math.floor(Math.random() * 5) + 96, // 96-100
    temperature: Math.round((Math.random() * 1.5 + 36.0) * 10) / 10, // 36.0-37.5
    heartRate: Math.floor(Math.random() * 30) + 70, // 70-100
    pressureHigh: Math.floor(Math.random() * 20) + 115,
    pressureLow: Math.floor(Math.random() * 15) + 75, // 75-90
    calorie: Math.floor(Math.random() * 500) + 200, // 200-700
    step: Math.floor(Math.random() * 5000) + 5000, // 5000-10000
    timestamp,
    stress: Math.floor(Math.random() * 40) + 20, // 20-60
    longitude: 114.057868 + Math.random() * 0.01
  }));
};

// 2. 运动健康数据 - 基于真实API格式
const generateExerciseData = () => {
  const timestamps = generateTimeStamps(7);
  return timestamps.map((timestamp, index) => ({
    timestamp,
    step: Math.floor(Math.random() * 8000) + 4000, // 4000-12000步
    calorie: Math.floor(Math.random() * 600) + 300, // 300-900卡路里
    distance: Math.round((Math.random() * 8 + 3) * 100) / 100, // 3-11公里
    deviceSn: 'CRFTQ23409001890',
    userId: 'demo_user_exercise'
  }));
};

// 3. 汇总分析数据 - 睡眠、锻炼记录等
const generateSummaryData = () => {
  const timestamps = generateTimeStamps(7);

  // 睡眠数据
  const sleepData = {
    data: timestamps.map(timestamp => ({
      startTimeStamp: timestamp - 8 * 60 * 60 * 1000, // 8小时前开始
      endTimeStamp: timestamp,
      deepSleep: Math.floor(Math.random() * 120) + 90, // 90-210分钟深睡
      lightSleep: Math.floor(Math.random() * 180) + 180, // 180-360分钟浅睡
      duration: Math.floor(Math.random() * 60) + 420, // 420-480分钟总时长
      efficiency: Math.floor(Math.random() * 20) + 80 // 80-100%效率
    })),
    name: 'sleep',
    type: 'history',
    code: 0
  };

  // 运动记录数据
  const workoutData = {
    code: 0,
    data: timestamps.slice(0, 5).map((timestamp, index) => ({
      calorie: Math.floor(Math.random() * 300) + 200, // 200-500
      distance: Math.floor(Math.random() * 2000) + 1000, // 1-3km
      startTimeStamp: timestamp - 60 * 60 * 1000, // 1小时前开始
      endTimeStamp: timestamp,
      workoutType: [1, 2, 10, 11, 15][index % 5], // 不同运动类型
      duration: Math.floor(Math.random() * 3000) + 1800 // 30-80分钟
    })),
    name: 'workout',
    type: 'history'
  };

  // 每日运动数据
  const dailyData = {
    data: timestamps.map(timestamp => ({
      timeStamps: timestamp,
      totalSteps: Math.floor(Math.random() * 6000) + 6000, // 6000-12000
      totalTime: Math.floor(Math.random() * 120) + 60, // 60-180分钟
      strengthTimes: Math.floor(Math.random() * 30) + 20, // 20-50分钟
      activeTime: Math.floor(Math.random() * 90) + 30 // 30-120分钟
    })),
    name: 'daily',
    type: 'history',
    code: 0
  };

  // 每周运动数据（3周数据）
  const weeklyData = {
    data: Array.from({ length: 3 }, (_, weekIndex) => ({
      timeStamps: baseTime - (2 - weekIndex) * 7 * 24 * 60 * 60 * 1000,
      totalSteps: Math.floor(Math.random() * 20000) + 40000, // 40000-60000
      strengthTimes: Math.floor(Math.random() * 300) + 200, // 200-500分钟
      totalTime: Math.floor(Math.random() * 600) + 400 // 400-1000分钟
    })),
    name: 'weekly',
    type: 'history',
    code: 0
  };

  return { sleepData, workoutData, dailyData, weeklyData };
};

// 显示基础生命体征图表
function showVitalsData() {
  const vitalsData = generateVitalsData();
  selectedData.value = {
    userId: 'demo_user_vitals',
    userName: '张医生',
    orgName: '心血管科',
    timestamp: Date.now(),
    vitalsTimeSeries: vitalsData, // 新增：生命体征时序数据
    sleepData: null,
    workoutData: null,
    exerciseDailyData: null,
    exerciseWeekData: null
  };
  modalVisible.value = true;
}

// 显示运动健康数据图表
function showExerciseData() {
  const exerciseData = generateExerciseData();
  selectedData.value = {
    userId: 'demo_user_exercise',
    userName: '李教练',
    orgName: '运动科学部',
    timestamp: Date.now(),
    exerciseTimeSeries: exerciseData, // 新增：运动时序数据
    sleepData: null,
    workoutData: null,
    exerciseDailyData: null,
    exerciseWeekData: null
  };
  modalVisible.value = true;
}

// 显示汇总分析数据图表
function showSummaryData() {
  const summaryData = generateSummaryData();
  selectedData.value = {
    userId: 'demo_user_summary',
    userName: '王分析师',
    orgName: '健康数据中心',
    timestamp: Date.now(),
    sleepData: summaryData.sleepData,
    workoutData: summaryData.workoutData,
    exerciseDailyData: summaryData.dailyData,
    exerciseWeekData: summaryData.weeklyData
  };
  modalVisible.value = true;
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="mx-auto max-w-6xl">
      <div class="mb-8 text-center">
        <h1 class="mb-2 text-3xl text-gray-800 font-bold">🏥 健康数据可视化演示</h1>
        <p class="text-gray-600">展示慢字段数据的优雅可视化效果</p>
      </div>

      <div class="grid grid-cols-1 mb-8 gap-6 md:grid-cols-3">
        <NCard class="transition-shadow hover:shadow-lg">
          <template #header>
            <div class="flex items-center space-x-2">
              <span class="text-2xl">❤️</span>
              <span class="font-semibold">基础生命体征</span>
            </div>
          </template>
          <NButton type="primary" size="large" block class="h-12" @click="showVitalsData">心率·血氧·血压·体温·压力</NButton>
        </NCard>

        <NCard class="transition-shadow hover:shadow-lg">
          <template #header>
            <div class="flex items-center space-x-2">
              <span class="text-2xl">🏃</span>
              <span class="font-semibold">运动健康数据</span>
            </div>
          </template>
          <NButton type="success" size="large" block class="h-12" @click="showExerciseData">卡路里·距离·步数</NButton>
        </NCard>

        <NCard class="transition-shadow hover:shadow-lg">
          <template #header>
            <div class="flex items-center space-x-2">
              <span class="text-2xl">📊</span>
              <span class="font-semibold">汇总分析数据</span>
            </div>
          </template>
          <NButton type="info" size="large" block class="h-12" @click="showSummaryData">睡眠·锻炼·每日·每周</NButton>
        </NCard>
      </div>

      <div class="grid grid-cols-1 mb-8 gap-6 md:grid-cols-3">
        <NCard class="border-red-200 bg-red-50">
          <template #header>
            <span class="text-red-700 font-semibold">❤️ 基础生命体征数据</span>
          </template>
          <div class="text-sm">
            <div class="mb-2 rounded bg-red-100 p-3">
              <strong>数据来源：</strong>
              <ul class="mt-2 text-red-700 space-y-1">
                <li>• 实时健康监测设备</li>
                <li>• 心率: 83 BPM</li>
                <li>• 血压: 124/85 mmHg</li>
                <li>• 体温: 36.5°C</li>
              </ul>
            </div>
            <div class="border rounded bg-white p-3">
              <strong>可视化方式：</strong>
              <ul class="mt-2 text-gray-700 space-y-1">
                <li>📈 时序折线图</li>
                <li>🎯 多指标雷达图</li>
                <li>📊 实时监控面板</li>
              </ul>
            </div>
          </div>
        </NCard>

        <NCard class="border-green-200 bg-green-50">
          <template #header>
            <span class="text-green-700 font-semibold">🏃 运动健康数据</span>
          </template>
          <div class="text-sm">
            <div class="mb-2 rounded bg-green-100 p-3">
              <strong>数据来源：</strong>
              <ul class="mt-2 text-green-700 space-y-1">
                <li>• 智能穿戴设备</li>
                <li>• 步数: 8,250 步</li>
                <li>• 距离: 6.2 公里</li>
                <li>• 卡路里: 380 千卡</li>
              </ul>
            </div>
            <div class="border rounded bg-white p-3">
              <strong>可视化方式：</strong>
              <ul class="mt-2 text-gray-700 space-y-1">
                <li>📊 双轴柱状图</li>
                <li>📈 运动趋势分析</li>
                <li>🔥 卡路里燃烧曲线</li>
              </ul>
            </div>
          </div>
        </NCard>

        <NCard class="border-blue-200 bg-blue-50">
          <template #header>
            <span class="text-blue-700 font-semibold">📊 汇总分析数据</span>
          </template>
          <div class="text-sm">
            <div class="mb-2 rounded bg-blue-100 p-3">
              <strong>数据来源：</strong>
              <ul class="mt-2 text-blue-700 space-y-1">
                <li>• 长期健康数据聚合</li>
                <li>• 睡眠: 7.5小时/天</li>
                <li>• 锻炼: 3次/周</li>
                <li>• 活跃: 5天/周</li>
              </ul>
            </div>
            <div class="border rounded bg-white p-3">
              <strong>可视化方式：</strong>
              <ul class="mt-2 text-gray-700 space-y-1">
                <li>🌙 睡眠质量图表</li>
                <li>💪 运动强度分析</li>
                <li>📅 每日/周度对比</li>
              </ul>
            </div>
          </div>
        </NCard>
      </div>

      <!-- 演示模态框 -->
      <SlowFieldsDetailModal v-model:visible="modalVisible" :row-data="selectedData" />
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
}

.grid-cols-1 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

@media (min-width: 768px) {
  .md\:grid-cols-2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .md\:grid-cols-3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.gap-6 {
  gap: 1.5rem;
}

.space-x-2 > * + * {
  margin-left: 0.5rem;
}

.space-y-1 > * + * {
  margin-top: 0.25rem;
}

.max-w-6xl {
  max-width: 72rem;
}

.mx-auto {
  margin-left: auto;
  margin-right: auto;
}

.p-6 {
  padding: 1.5rem;
}

.p-3 {
  padding: 0.75rem;
}

.mb-8 {
  margin-bottom: 2rem;
}

.mb-2 {
  margin-bottom: 0.5rem;
}

.mt-2 {
  margin-top: 0.5rem;
}

.h-12 {
  height: 3rem;
}

.min-h-screen {
  min-height: 100vh;
}

.text-center {
  text-align: center;
}

.text-3xl {
  font-size: 1.875rem;
  line-height: 2.25rem;
}

.text-2xl {
  font-size: 1.5rem;
  line-height: 2rem;
}

.text-sm {
  font-size: 0.875rem;
  line-height: 1.25rem;
}

.font-bold {
  font-weight: 700;
}

.font-semibold {
  font-weight: 600;
}

.bg-gray-50 {
  background-color: #f9fafb;
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

.bg-white {
  background-color: white;
}

.text-gray-800 {
  color: #1f2937;
}

.text-gray-600 {
  color: #4b5563;
}

.text-gray-700 {
  color: #374151;
}

.text-purple-700 {
  color: #7c3aed;
}

.text-orange-700 {
  color: #c2410c;
}

.text-red-700 {
  color: #b91c1c;
}

.text-green-700 {
  color: #15803d;
}

.text-blue-700 {
  color: #1d4ed8;
}

.border {
  border-width: 1px;
  border-color: #e5e7eb;
}

.border-purple-200 {
  border-color: #e9d5ff;
}

.border-orange-200 {
  border-color: #fed7aa;
}

.border-red-200 {
  border-color: #fecaca;
}

.border-green-200 {
  border-color: #bbf7d0;
}

.border-blue-200 {
  border-color: #bfdbfe;
}

.bg-red-50 {
  background-color: #fef2f2;
}

.bg-red-100 {
  background-color: #fee2e2;
}

.bg-green-50 {
  background-color: #f0fdf4;
}

.bg-green-100 {
  background-color: #dcfce7;
}

.bg-blue-50 {
  background-color: #eff6ff;
}

.bg-blue-100 {
  background-color: #dbeafe;
}

.rounded {
  border-radius: 0.25rem;
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.hover\:shadow-lg:hover {
  box-shadow:
    0 10px 15px -3px rgb(0 0 0 / 0.1),
    0 4px 6px -4px rgb(0 0 0 / 0.1);
}

.transition-shadow {
  transition-property: box-shadow;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}
</style>
