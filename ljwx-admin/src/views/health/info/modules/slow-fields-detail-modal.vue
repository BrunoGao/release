<template>
  <NModal v-model:show="modalVisible" :mask-closable="false" preset="card" class="w-90% max-w-5xl">
    <template #header>
      <NSpace align="center">
        <span class="text-lg font-semibold">健康数据详情</span>
        <NTag v-if="props.rowData" type="info" size="small">
          {{ props.rowData.userName }} - {{ props.rowData.orgName }}
        </NTag>
      </NSpace>
    </template>

    <div v-if="props.rowData" class="space-y-6">
      <!-- 基本信息 -->
      <NCard size="small" :bordered="false" class="bg-gray-50">
        <template #header>
          基本信息
        </template>
        <NDescriptions :column="4" size="small" label-placement="left">
          <NDescriptionsItem label="用户">{{ props.rowData.userName }}</NDescriptionsItem>
          <NDescriptionsItem label="部门">{{ props.rowData.orgName }}</NDescriptionsItem>
          <NDescriptionsItem label="记录时间">{{ convertToBeijingTime(props.rowData.timestamp) }}</NDescriptionsItem>
          <NDescriptionsItem label="用户ID">{{ props.rowData.userId }}</NDescriptionsItem>
        </NDescriptions>
      </NCard>

      <!-- 睡眠数据 -->
      <div v-if="sleepChartData" class="space-y-4">
        <NCard size="small" :bordered="false">
          <template #header>
            <NSpace align="center">
              <span>睡眠数据</span>
              <NTag type="warning" size="small">{{ sleepChartData.name }}</NTag>
            </NSpace>
          </template>
          
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 睡眠图表 -->
            <div class="h-80">
              <canvas ref="sleepChartRef"></canvas>
            </div>
            
            <!-- 睡眠统计 -->
            <div class="space-y-4">
              <NStatistic label="总睡眠时长" :value="sleepStats.totalSleep" suffix="小时" />
              <NStatistic label="深度睡眠" :value="sleepStats.deepSleep" suffix="小时" />
              <NStatistic label="浅度睡眠" :value="sleepStats.lightSleep" suffix="小时" />
              <NStatistic label="睡眠效率" :value="sleepStats.efficiency" suffix="%" />
            </div>
          </div>
        </NCard>
      </div>

      <!-- 运动数据 -->
      <div v-if="workoutChartData" class="space-y-4">
        <NCard size="small" :bordered="false">
          <template #header>
            <NSpace align="center">
              <span>运动数据</span>
              <NTag type="success" size="small">{{ workoutChartData.name }}</NTag>
            </NSpace>
          </template>
          
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 运动图表 -->
            <div class="h-80">
              <canvas ref="workoutChartRef"></canvas>
            </div>
            
            <!-- 运动统计 -->
            <div class="space-y-4">
              <NStatistic label="总运动时长" :value="workoutStats.totalTime" suffix="分钟" />
              <NStatistic label="总消耗卡路里" :value="workoutStats.totalCalorie" suffix="卡" />
              <NStatistic label="总距离" :value="workoutStats.totalDistance" suffix="米" />
              <NStatistic label="运动次数" :value="workoutStats.workoutCount" suffix="次" />
            </div>
          </div>
        </NCard>
      </div>

      <!-- 每日运动数据 -->
      <div v-if="exerciseDailyChartData" class="space-y-4">
        <NCard size="small" :bordered="false">
          <template #header>
            <NSpace align="center">
              <span>每日运动数据</span>
              <NTag type="info" size="small">{{ exerciseDailyChartData.name }}</NTag>
            </NSpace>
          </template>
          
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 每日运动图表 -->
            <div class="h-80">
              <canvas ref="exerciseDailyChartRef"></canvas>
            </div>
            
            <!-- 每日运动统计 -->
            <div class="space-y-4">
              <NStatistic label="平均步数" :value="exerciseDailyStats.avgSteps" suffix="步" />
              <NStatistic label="平均运动时长" :value="exerciseDailyStats.avgTime" suffix="分钟" />
              <NStatistic label="活跃天数" :value="exerciseDailyStats.activeDays" suffix="天" />
              <NStatistic label="数据覆盖天数" :value="exerciseDailyStats.totalDays" suffix="天" />
            </div>
          </div>
        </NCard>
      </div>

      <!-- 每周运动数据 -->
      <div v-if="exerciseWeekChartData" class="space-y-4">
        <NCard size="small" :bordered="false">
          <template #header>
            <NSpace align="center">
              <span>每周运动数据</span>
              <NTag type="error" size="small">{{ exerciseWeekChartData.name }}</NTag>
            </NSpace>
          </template>
          
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 每周运动图表 -->
            <div class="h-80">
              <canvas ref="exerciseWeekChartRef"></canvas>
            </div>
            
            <!-- 每周运动统计 -->
            <div class="space-y-4">
              <NStatistic label="周平均步数" :value="exerciseWeekStats.avgSteps" suffix="步" />
              <NStatistic label="周平均强度时长" :value="exerciseWeekStats.avgStrengthTime" suffix="分钟" />
              <NStatistic label="周平均总时长" :value="exerciseWeekStats.avgTotalTime" suffix="分钟" />
              <NStatistic label="活跃周数" :value="exerciseWeekStats.activeWeeks" suffix="周" />
            </div>
          </div>
        </NCard>
      </div>

      <!-- 空数据提示 -->
      <NEmpty v-if="!hasAnyData" description="暂无详细数据" class="py-12" />
    </div>

    <template #action>
      <NSpace justify="end">
        <NButton @click="modalVisible = false">关闭</NButton>
        <NButton type="primary" @click="exportData">
          导出数据
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue';
import { Chart, registerables } from 'chart.js';
import { convertToBeijingTime } from '@/utils/date';
import { 
  NModal, 
  NCard, 
  NSpace, 
  NIcon, 
  NTag, 
  NDescriptions, 
  NDescriptionsItem, 
  NStatistic,
  NButton,
  NEmpty
} from 'naive-ui';

// 注册 Chart.js 组件
Chart.register(...registerables);

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
const sleepChartRef = ref<HTMLCanvasElement>();
const workoutChartRef = ref<HTMLCanvasElement>();
const exerciseDailyChartRef = ref<HTMLCanvasElement>();
const exerciseWeekChartRef = ref<HTMLCanvasElement>();

// Chart instances
let sleepChart: Chart | null = null;
let workoutChart: Chart | null = null;
let exerciseDailyChart: Chart | null = null;
let exerciseWeekChart: Chart | null = null;

// 处理数据格式，适配你提供的示例
const sleepChartData = computed(() => {
  if (!props.rowData?.sleepData) return null;
  
  let data = props.rowData.sleepData;
  if (typeof data === 'string') {
    try {
      data = JSON.parse(data);
    } catch (e) {
      return null;
    }
  }
  
  return data;
});

const workoutChartData = computed(() => {
  if (!props.rowData?.workoutData) return null;
  
  let data = props.rowData.workoutData;
  if (typeof data === 'string') {
    try {
      data = JSON.parse(data);
    } catch (e) {
      return null;
    }
  }
  
  return data;
});

const exerciseDailyChartData = computed(() => {
  if (!props.rowData?.exerciseDailyData) return null;
  
  let data = props.rowData.exerciseDailyData;
  if (typeof data === 'string') {
    try {
      data = JSON.parse(data);
    } catch (e) {
      return null;
    }
  }
  
  return data;
});

const exerciseWeekChartData = computed(() => {
  if (!props.rowData?.exerciseWeekData) return null;
  
  let data = props.rowData.exerciseWeekData;
  if (typeof data === 'string') {
    try {
      data = JSON.parse(data);
    } catch (e) {
      return null;
    }
  }
  
  return data;
});

// 统计数据计算
const sleepStats = computed(() => {
  if (!sleepChartData.value?.data) return { totalSleep: 0, deepSleep: 0, lightSleep: 0, efficiency: 0 };
  
  const data = sleepChartData.value.data;
  const totalSleep = data.reduce((sum: number, item: any) => sum + (item.duration || 0), 0) / 60; // 转换为小时
  const deepSleep = data.reduce((sum: number, item: any) => sum + (item.deepSleep || 0), 0) / 60;
  const lightSleep = data.reduce((sum: number, item: any) => sum + (item.lightSleep || 0), 0) / 60;
  const efficiency = totalSleep > 0 ? Math.round((deepSleep / totalSleep) * 100) : 0;
  
  return {
    totalSleep: Math.round(totalSleep * 10) / 10,
    deepSleep: Math.round(deepSleep * 10) / 10,
    lightSleep: Math.round(lightSleep * 10) / 10,
    efficiency
  };
});

const workoutStats = computed(() => {
  if (!workoutChartData.value?.data) return { totalTime: 0, totalCalorie: 0, totalDistance: 0, workoutCount: 0 };
  
  const data = workoutChartData.value.data;
  const totalTime = data.reduce((sum: number, item: any) => sum + (item.duration || 0), 0);
  const totalCalorie = data.reduce((sum: number, item: any) => sum + (item.calorie || 0), 0);
  const totalDistance = data.reduce((sum: number, item: any) => sum + (item.distance || 0), 0);
  const workoutCount = data.filter((item: any) => item.duration > 0).length;
  
  return {
    totalTime,
    totalCalorie,
    totalDistance,
    workoutCount
  };
});

const exerciseDailyStats = computed(() => {
  if (!exerciseDailyChartData.value?.data) return { avgSteps: 0, avgTime: 0, activeDays: 0, totalDays: 0 };
  
  const data = exerciseDailyChartData.value.data;
  const validData = data.filter((item: any) => item.timeStamps > 0);
  const activeData = validData.filter((item: any) => item.totalSteps > 0);
  
  const avgSteps = validData.length > 0 ? Math.round(validData.reduce((sum: number, item: any) => sum + (item.totalSteps || 0), 0) / validData.length) : 0;
  const avgTime = validData.length > 0 ? Math.round(validData.reduce((sum: number, item: any) => sum + (item.totalTime || 0), 0) / validData.length) : 0;
  
  return {
    avgSteps,
    avgTime,
    activeDays: activeData.length,
    totalDays: validData.length
  };
});

const exerciseWeekStats = computed(() => {
  if (!exerciseWeekChartData.value?.data) return { avgSteps: 0, avgStrengthTime: 0, avgTotalTime: 0, activeWeeks: 0 };
  
  const data = exerciseWeekChartData.value.data;
  const validData = data.filter((item: any) => item.timeStamps > 0);
  const activeData = validData.filter((item: any) => item.totalSteps > 0);
  
  const avgSteps = validData.length > 0 ? Math.round(validData.reduce((sum: number, item: any) => sum + (item.totalSteps || 0), 0) / validData.length) : 0;
  const avgStrengthTime = validData.length > 0 ? Math.round(validData.reduce((sum: number, item: any) => sum + (item.strengthTimes || 0), 0) / validData.length) : 0;
  const avgTotalTime = validData.length > 0 ? Math.round(validData.reduce((sum: number, item: any) => sum + (item.totalTime || 0), 0) / validData.length) : 0;
  
  return {
    avgSteps,
    avgStrengthTime,
    avgTotalTime,
    activeWeeks: activeData.length
  };
});

const hasAnyData = computed(() => {
  return !!(sleepChartData.value || workoutChartData.value || exerciseDailyChartData.value || exerciseWeekChartData.value);
});

// 创建图表
function createSleepChart() {
  if (!sleepChartRef.value || !sleepChartData.value?.data) return;
  
  const data = sleepChartData.value.data;
  const labels = data.map((item: any) => {
    const date = new Date(item.startTimeStamp || item.timeStamps);
    return date.toLocaleDateString('zh-CN');
  });
  
  sleepChart = new Chart(sleepChartRef.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: '深度睡眠(分钟)',
          data: data.map((item: any) => item.deepSleep || 0),
          backgroundColor: 'rgba(114, 46, 209, 0.8)',
          borderColor: 'rgba(114, 46, 209, 1)',
          borderWidth: 1
        },
        {
          label: '浅度睡眠(分钟)',
          data: data.map((item: any) => item.lightSleep || 0),
          backgroundColor: 'rgba(114, 46, 209, 0.4)',
          borderColor: 'rgba(114, 46, 209, 0.6)',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: '时长(分钟)'
          }
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top'
        }
      }
    }
  });
}

function createWorkoutChart() {
  if (!workoutChartRef.value || !workoutChartData.value?.data) return;
  
  const data = workoutChartData.value.data;
  const labels = data.map((item: any) => {
    const date = new Date(item.startTimeStamp || item.timeStamps);
    return date.toLocaleDateString('zh-CN');
  });
  
  workoutChart = new Chart(workoutChartRef.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: '卡路里',
          data: data.map((item: any) => item.calorie || 0),
          backgroundColor: 'rgba(250, 84, 28, 0.2)',
          borderColor: 'rgba(250, 84, 28, 1)',
          borderWidth: 2,
          yAxisID: 'y'
        },
        {
          label: '距离(米)',
          data: data.map((item: any) => item.distance || 0),
          backgroundColor: 'rgba(19, 194, 194, 0.2)',
          borderColor: 'rgba(19, 194, 194, 1)',
          borderWidth: 2,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: {
            display: true,
            text: '卡路里'
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: {
            display: true,
            text: '距离(米)'
          },
          grid: {
            drawOnChartArea: false
          }
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top'
        }
      }
    }
  });
}

function createExerciseDailyChart() {
  if (!exerciseDailyChartRef.value || !exerciseDailyChartData.value?.data) return;
  
  const data = exerciseDailyChartData.value.data.filter((item: any) => item.timeStamps > 0);
  const labels = data.map((item: any) => {
    const date = new Date(item.timeStamps);
    return date.toLocaleDateString('zh-CN');
  });
  
  exerciseDailyChart = new Chart(exerciseDailyChartRef.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: '步数',
          data: data.map((item: any) => item.totalSteps || 0),
          backgroundColor: 'rgba(19, 194, 194, 0.8)',
          borderColor: 'rgba(19, 194, 194, 1)',
          borderWidth: 1,
          yAxisID: 'y'
        },
        {
          label: '运动时长(分钟)',
          data: data.map((item: any) => item.totalTime || 0),
          backgroundColor: 'rgba(235, 47, 150, 0.8)',
          borderColor: 'rgba(235, 47, 150, 1)',
          borderWidth: 1,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: {
            display: true,
            text: '步数'
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: {
            display: true,
            text: '时长(分钟)'
          },
          grid: {
            drawOnChartArea: false
          }
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top'
        }
      }
    }
  });
}

function createExerciseWeekChart() {
  if (!exerciseWeekChartRef.value || !exerciseWeekChartData.value?.data) return;
  
  const data = exerciseWeekChartData.value.data.filter((item: any) => item.timeStamps > 0);
  const labels = data.map((item: any, index: number) => `第${index + 1}周`);
  
  exerciseWeekChart = new Chart(exerciseWeekChartRef.value, {
    type: 'radar',
    data: {
      labels: ['步数', '强度训练(分钟)', '总时长(分钟)'],
      datasets: data.map((item: any, index: number) => ({
        label: `第${index + 1}周`,
        data: [
          (item.totalSteps || 0) / 1000, // 转换为千步
          item.strengthTimes || 0,
          item.totalTime || 0
        ],
        backgroundColor: `hsla(${index * 60}, 70%, 50%, 0.2)`,
        borderColor: `hsla(${index * 60}, 70%, 50%, 1)`,
        borderWidth: 2
      }))
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          beginAtZero: true,
          title: {
            display: true,
            text: '运动指标'
          }
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top'
        }
      }
    }
  });
}

// 监听模态框显示状态
watch(() => props.visible, async (visible) => {
  if (visible && props.rowData) {
    await nextTick();
    
    // 销毁现有图表
    sleepChart?.destroy();
    workoutChart?.destroy();
    exerciseDailyChart?.destroy();
    exerciseWeekChart?.destroy();
    
    // 创建新图表
    setTimeout(() => {
      createSleepChart();
      createWorkoutChart();
      createExerciseDailyChart();
      createExerciseWeekChart();
    }, 100);
  }
});

// 导出数据
function exportData() {
  const exportData = {
    userInfo: {
      userId: props.rowData.userId,
      userName: props.rowData.userName,
      orgName: props.rowData.orgName,
      timestamp: props.rowData.timestamp
    },
    sleepData: sleepChartData.value,
    workoutData: workoutChartData.value,
    exerciseDailyData: exerciseDailyChartData.value,
    exerciseWeekData: exerciseWeekChartData.value
  };
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `健康数据详情_${props.rowData.userName}_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<style scoped>
.grid {
  display: grid;
}

.grid-cols-1 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

@media (min-width: 1024px) {
  .lg\:grid-cols-2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.gap-6 {
  gap: 1.5rem;
}

.space-y-4 > * + * {
  margin-top: 1rem;
}

.space-y-6 > * + * {
  margin-top: 1.5rem;
}

.h-80 {
  height: 20rem;
}

.py-12 {
  padding-top: 3rem;
  padding-bottom: 3rem;
}

.w-90\% {
  width: 90%;
}

.max-w-5xl {
  max-width: 64rem;
}
</style>