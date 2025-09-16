<script setup lang="tsx">
import { NCard, NSpace, NButton, NTag, NSkeleton, NEmpty, NGrid, NGridItem } from 'naive-ui';
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue';
import { fetchGetHealthDataBasicList } from '@/service/api';
import * as echarts from 'echarts';

interface Props {
  healthData?: any; // 来自父组件的完整健康数据
  visible?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  healthData: null,
  visible: true
});

// 图表引用
const sleepChartRef = ref<HTMLElement>();
const exerciseChartRef = ref<HTMLElement>();
const cardioChartRef = ref<HTMLElement>();
const activityChartRef = ref<HTMLElement>();

// 从props中提取各类数据
const sleepData = computed(() => props.healthData?.sleepData || []);
const workoutData = computed(() => props.healthData?.workoutData || []);
const scientificSleepData = computed(() => props.healthData?.scientificSleepData || []);
const exerciseDailyData = computed(() => props.healthData?.exerciseDailyData || []);
const exerciseWeekData = computed(() => props.healthData?.exerciseWeekData || []);
const records = computed(() => props.healthData?.records || []);

// ECharts 实例
let sleepChart: echarts.ECharts | null = null;
let exerciseChart: echarts.ECharts | null = null;
let cardioChart: echarts.ECharts | null = null;
let activityChart: echarts.ECharts | null = null;

// 统计信息
const chartStats = computed(() => {
  if (!props.healthData) return null;
  
  // 从睡眠数据计算平均睡眠时长
  const sleepAvgDuration = sleepData.value.length > 0 
    ? sleepData.value.reduce((sum, item) => sum + (parseFloat(item.processed?.value || 0)), 0) / sleepData.value.length
    : 0;
  
  // 从基础数据计算心血管和活动数据
  const recordsData = records.value;
  const validHeartRates = recordsData.filter(r => r.heartRate).map(r => r.heartRate);
  const avgHeartRate = validHeartRates.length > 0 
    ? validHeartRates.reduce((a, b) => a + b, 0) / validHeartRates.length 
    : 0;
  
  const totalSteps = recordsData.reduce((sum, r) => sum + (r.step || 0), 0);
  const totalCalories = recordsData.reduce((sum, r) => sum + (r.calorie || 0), 0);
  
  return {
    sleepAvgDuration: sleepAvgDuration,
    sleepQuality: 85, // 临时固定值，后续可以从processed数据中计算
    exerciseTypes: workoutData.value.length + exerciseDailyData.value.length,
    avgHeartRate: Math.round(avgHeartRate),
    totalSteps: totalSteps,
    totalCalories: Math.round(totalCalories)
  };
});

// 渲染图表
const renderCharts = async () => {
  if (!props.healthData) return;
  
  // 等待DOM更新后渲染图表
  await nextTick();
  renderAllCharts();
};

// 渲染所有图表
const renderAllCharts = () => {
  if (props.healthData) {
    renderSleepChart();
    renderExerciseChart();
    renderCardioChart();
    renderActivityChart();
  }
};

// 睡眠分析图表 - 多用户对比
const renderSleepChart = () => {
  if (!sleepChartRef.value || sleepData.value.length === 0) return;
  
  sleepChart = echarts.init(sleepChartRef.value);
  
  console.log('渲染睡眠图表，数据:', sleepData.value);
  
  // 按用户分组数据
  const userGroups = new Map();
  sleepData.value.forEach(item => {
    const userId = item.userId;
    if (!userGroups.has(userId)) {
      userGroups.set(userId, {
        userName: item.userName,
        orgName: item.orgName,
        data: []
      });
    }
    userGroups.get(userId).data.push({
      date: item.date,
      duration: parseFloat(item.processed?.value || 0),
      quality: 85 // 临时固定值，可以从processed数据中解析
    });
  });
  
  // 获取所有日期并排序
  const allDates = [...new Set(sleepData.value.map(item => item.date))].sort();
  
  // 为每个用户构建系列数据
  const series = [];
  const colors = ['#5B8FF9', '#FF6B6B', '#5AD8A6', '#F7D794', '#9C88FF', '#F8B4CB'];
  let colorIndex = 0;
  
  userGroups.forEach((userInfo, userId) => {
    const durations = allDates.map(date => {
      const found = userInfo.data.find(d => d.date === date);
      return found ? found.duration : 0;
    });
    
    series.push({
      name: userInfo.userName,
      type: 'line',
      data: durations,
      itemStyle: { color: colors[colorIndex % colors.length] },
      smooth: true,
      symbol: 'circle',
      symbolSize: 6
    });
    
    colorIndex++;
  });
  
  const option = {
    title: {
      text: '睡眠质量分析 - 多用户对比',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        let result = `日期: ${params[0].name}<br/>`;
        params.forEach((param: any) => {
          result += `${param.seriesName}: ${param.value.toFixed(1)}小时<br/>`;
        });
        return result;
      }
    },
    legend: {
      data: series.map(s => s.name),
      top: '10%',
      type: 'scroll'
    },
    xAxis: {
      type: 'category',
      data: allDates,
      axisLabel: { 
        rotate: 45,
        formatter: (value: string) => {
          // 格式化日期显示
          return value.substring(5); // 只显示月-日
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '睡眠时长(小时)',
      min: 0,
      max: 12
    },
    series: series,
    grid: { left: '10%', right: '10%', bottom: '20%', top: '20%' }
  };
  
  sleepChart.setOption(option);
};

// 运动分布图表 - 多用户运动类型统计
const renderExerciseChart = () => {
  if (!exerciseChartRef.value) return;
  
  exerciseChart = echarts.init(exerciseChartRef.value);
  
  console.log('渲染运动图表，数据:', {
    workoutData: workoutData.value,
    exerciseDailyData: exerciseDailyData.value
  });
  
  // 合并所有运动数据
  const allExerciseData = [...workoutData.value, ...exerciseDailyData.value];
  
  if (allExerciseData.length === 0) {
    // 显示空数据图表
    const option = {
      title: {
        text: '运动类型分布',
        left: 'center',
        textStyle: { fontSize: 16, fontWeight: 'bold' }
      },
      graphic: {
        type: 'text',
        left: 'center',
        top: 'middle',
        style: {
          text: '暂无运动数据',
          fontSize: 16,
          fill: '#999'
        }
      }
    };
    exerciseChart.setOption(option);
    return;
  }
  
  // 按用户统计运动类型
  const userExerciseStats = new Map();
  
  allExerciseData.forEach(item => {
    const userId = item.userId;
    const userName = item.userName;
    
    if (!userExerciseStats.has(userId)) {
      userExerciseStats.set(userId, {
        userName: userName,
        exercises: new Map()
      });
    }
    
    // 解析运动数据 - 这里需要根据实际的数据结构调整
    // 假设processed数据包含运动类型信息
    const exerciseType = item.processed?.type || '一般运动';
    const userStats = userExerciseStats.get(userId);
    
    if (!userStats.exercises.has(exerciseType)) {
      userStats.exercises.set(exerciseType, 0);
    }
    userStats.exercises.set(exerciseType, userStats.exercises.get(exerciseType) + 1);
  });
  
  // 构建饼图数据
  const pieData = [];
  const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'];
  let colorIndex = 0;
  
  userExerciseStats.forEach((userInfo, userId) => {
    userInfo.exercises.forEach((count, exerciseType) => {
      pieData.push({
        name: `${userInfo.userName} - ${exerciseType}`,
        value: count,
        itemStyle: {
          color: colors[colorIndex % colors.length]
        }
      });
      colorIndex++;
    });
  });
  
  const option = {
    title: {
      text: '运动类型分布 - 用户对比',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}次 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: '15%',
      type: 'scroll',
      textStyle: { fontSize: 12 }
    },
    series: [
      {
        name: '运动统计',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '55%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '14',
            fontWeight: 'bold'
          }
        },
        labelLine: { show: false },
        data: pieData
      }
    ]
  };
  
  exerciseChart.setOption(option);
};

// 心血管监测图表 - 基于基础数据的多用户对比
const renderCardioChart = () => {
  if (!cardioChartRef.value || records.value.length === 0) return;
  
  cardioChart = echarts.init(cardioChartRef.value);
  
  console.log('渲染心血管图表，数据:', records.value);
  
  // 按用户和日期分组数据
  const userCardioData = new Map();
  
  records.value.forEach(record => {
    const userId = record.userId;
    const userName = record.userName;
    const date = new Date(record.timestamp).toISOString().split('T')[0]; // 转换为日期字符串
    
    if (!userCardioData.has(userId)) {
      userCardioData.set(userId, {
        userName: userName,
        dailyData: new Map()
      });
    }
    
    const userData = userCardioData.get(userId);
    if (!userData.dailyData.has(date)) {
      userData.dailyData.set(date, {
        heartRates: [],
        systolicPressures: []
      });
    }
    
    const dayData = userData.dailyData.get(date);
    if (record.heartRate) dayData.heartRates.push(record.heartRate);
    if (record.pressureHigh) dayData.systolicPressures.push(record.pressureHigh);
  });
  
  // 计算每天的平均值
  const allDates = new Set();
  userCardioData.forEach(userData => {
    userData.dailyData.forEach((_, date) => allDates.add(date));
  });
  const sortedDates = Array.from(allDates).sort();
  
  // 构建系列数据
  const heartRateSeries = [];
  const bloodPressureSeries = [];
  const colors = ['#FF6B6B', '#5B8FF9', '#5AD8A6', '#F7D794', '#9C88FF', '#F8B4CB'];
  let colorIndex = 0;
  
  userCardioData.forEach((userData, userId) => {
    const heartRateData = sortedDates.map(date => {
      const dayData = userData.dailyData.get(date);
      if (dayData && dayData.heartRates.length > 0) {
        return Math.round(dayData.heartRates.reduce((a, b) => a + b, 0) / dayData.heartRates.length);
      }
      return null;
    });
    
    const pressureData = sortedDates.map(date => {
      const dayData = userData.dailyData.get(date);
      if (dayData && dayData.systolicPressures.length > 0) {
        return Math.round(dayData.systolicPressures.reduce((a, b) => a + b, 0) / dayData.systolicPressures.length);
      }
      return null;
    });
    
    const userColor = colors[colorIndex % colors.length];
    
    heartRateSeries.push({
      name: `${userData.userName} - 心率`,
      type: 'line',
      data: heartRateData,
      itemStyle: { color: userColor },
      yAxisIndex: 0,
      smooth: true,
      connectNulls: false,
      symbol: 'circle',
      symbolSize: 6
    });
    
    bloodPressureSeries.push({
      name: `${userData.userName} - 收缩压`,
      type: 'line',
      data: pressureData,
      itemStyle: { color: userColor, opacity: 0.7 },
      lineStyle: { type: 'dashed' },
      yAxisIndex: 1,
      smooth: true,
      connectNulls: false,
      symbol: 'diamond',
      symbolSize: 6
    });
    
    colorIndex++;
  });
  
  const allSeries = [...heartRateSeries, ...bloodPressureSeries];
  
  const option = {
    title: {
      text: '心血管健康监测 - 多用户对比',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        let result = `日期: ${params[0].name}<br/>`;
        params.forEach((param: any) => {
          if (param.value !== null) {
            const unit = param.seriesName.includes('心率') ? 'bpm' : 'mmHg';
            result += `${param.seriesName}: ${param.value}${unit}<br/>`;
          }
        });
        return result;
      }
    },
    legend: {
      data: allSeries.map(s => s.name),
      top: '10%',
      type: 'scroll',
      textStyle: { fontSize: 12 }
    },
    xAxis: {
      type: 'category',
      data: sortedDates,
      axisLabel: { 
        rotate: 45,
        formatter: (value: string) => value.substring(5) // 只显示月-日
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '心率(bpm)',
        position: 'left',
        min: 50,
        max: 120
      },
      {
        type: 'value',
        name: '血压(mmHg)',
        position: 'right',
        min: 80,
        max: 160
      }
    ],
    series: allSeries,
    grid: { left: '10%', right: '10%', bottom: '20%', top: '25%' }
  };
  
  cardioChart.setOption(option);
};

// 活动量统计图表 - 基于基础数据的多用户对比
const renderActivityChart = () => {
  if (!activityChartRef.value || records.value.length === 0) return;
  
  activityChart = echarts.init(activityChartRef.value);
  
  console.log('渲染活动量图表，数据:', records.value);
  
  // 按用户和日期分组数据
  const userActivityData = new Map();
  
  records.value.forEach(record => {
    const userId = record.userId;
    const userName = record.userName;
    const date = new Date(record.timestamp).toISOString().split('T')[0];
    
    if (!userActivityData.has(userId)) {
      userActivityData.set(userId, {
        userName: userName,
        dailyData: new Map()
      });
    }
    
    const userData = userActivityData.get(userId);
    if (!userData.dailyData.has(date)) {
      userData.dailyData.set(date, {
        steps: [],
        calories: [],
        distances: []
      });
    }
    
    const dayData = userData.dailyData.get(date);
    if (record.step) dayData.steps.push(record.step);
    if (record.calorie) dayData.calories.push(record.calorie);
    if (record.distance) dayData.distances.push(record.distance);
  });
  
  // 计算每天的平均值或总和
  const allDates = new Set();
  userActivityData.forEach(userData => {
    userData.dailyData.forEach((_, date) => allDates.add(date));
  });
  const sortedDates = Array.from(allDates).sort();
  
  // 构建系列数据
  const stepsSeries = [];
  const caloriesSeries = [];
  const colors = ['#91CC75', '#FAC858', '#EE6666', '#73C0DE', '#3BA272', '#FC8452'];
  let colorIndex = 0;
  
  userActivityData.forEach((userData, userId) => {
    const stepsData = sortedDates.map(date => {
      const dayData = userData.dailyData.get(date);
      if (dayData && dayData.steps.length > 0) {
        // 使用最大值作为当天步数
        return Math.max(...dayData.steps);
      }
      return 0;
    });
    
    const caloriesData = sortedDates.map(date => {
      const dayData = userData.dailyData.get(date);
      if (dayData && dayData.calories.length > 0) {
        // 使用最大值作为当天卡路里
        return Math.max(...dayData.calories);
      }
      return 0;
    });
    
    const userColor = colors[colorIndex % colors.length];
    
    stepsSeries.push({
      name: `${userData.userName} - 步数`,
      type: 'bar',
      data: stepsData,
      itemStyle: { 
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: userColor },
            { offset: 1, color: userColor + '80' }
          ]
        }
      },
      yAxisIndex: 0
    });
    
    caloriesSeries.push({
      name: `${userData.userName} - 卡路里`,
      type: 'line',
      data: caloriesData,
      itemStyle: { color: userColor },
      lineStyle: { width: 3 },
      yAxisIndex: 1,
      smooth: true,
      symbol: 'circle',
      symbolSize: 8
    });
    
    colorIndex++;
  });
  
  const allSeries = [...stepsSeries, ...caloriesSeries];
  
  const option = {
    title: {
      text: '日常活动量统计 - 多用户对比',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        let result = `日期: ${params[0].name}<br/>`;
        params.forEach((param: any) => {
          if (param.value > 0) {
            const unit = param.seriesName.includes('步数') ? '步' : 'kcal';
            result += `${param.seriesName}: ${param.value.toLocaleString()}${unit}<br/>`;
          }
        });
        return result;
      }
    },
    legend: {
      data: allSeries.map(s => s.name),
      top: '10%',
      type: 'scroll',
      textStyle: { fontSize: 12 }
    },
    xAxis: {
      type: 'category',
      data: sortedDates,
      axisLabel: { 
        rotate: 45,
        formatter: (value: string) => value.substring(5) // 只显示月-日
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '步数',
        position: 'left',
        min: 0,
        axisLabel: {
          formatter: (value: number) => value >= 1000 ? (value/1000).toFixed(0) + 'k' : value
        }
      },
      {
        type: 'value',
        name: '卡路里(kcal)',
        position: 'right',
        min: 0
      }
    ],
    series: allSeries,
    grid: { left: '12%', right: '12%', bottom: '20%', top: '25%' }
  };
  
  activityChart.setOption(option);
};

// 获取运动类型颜色
const getExerciseTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    '跑步': '#FF6B6B',
    '走路': '#4ECDC4', 
    '骑行': '#45B7D1',
    '游泳': '#96CEB4',
    '力量训练': '#FFEAA7',
    '瑜伽': '#DDA0DD',
    '其他': '#95A5A6'
  };
  return colorMap[type] || '#95A5A6';
};

// 图表自适应
const resizeCharts = () => {
  sleepChart?.resize();
  exerciseChart?.resize();
  cardioChart?.resize();
  activityChart?.resize();
};

// 清理图表
const disposeCharts = () => {
  sleepChart?.dispose();
  exerciseChart?.dispose();
  cardioChart?.dispose();
  activityChart?.dispose();
  
  sleepChart = null;
  exerciseChart = null;
  cardioChart = null;
  activityChart = null;
};

// 刷新图表数据
const refreshCharts = () => {
  renderCharts();
};

// 监听健康数据变化
watch(() => props.healthData, (newHealthData) => {
  if (newHealthData) {
    renderCharts();
  }
}, { deep: true });

// 监听可见性变化
watch(() => props.visible, (visible) => {
  if (visible && props.healthData) {
    renderCharts();
  }
});

// 窗口大小变化监听
window.addEventListener('resize', resizeCharts);

onMounted(() => {
  if (props.healthData) {
    renderCharts();
  }
});

// 组件卸载时清理
onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts);
  disposeCharts();
});

// 暴露方法给父组件
defineExpose({
  refresh: refreshCharts,
  dispose: disposeCharts
});
</script>

<template>
  <div class="health-analytics-charts" v-show="visible">
    <!-- 分析概览 -->
    <NCard :bordered="false" class="mb-4">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-lg font-medium">📊 健康数据分析概览</span>
            <NTag v-if="records && records.length > 0" type="info" size="small">
              {{ records.length }} 条记录
            </NTag>
          </div>
          <NButton size="small" @click="refreshCharts">
            刷新分析
          </NButton>
        </div>
      </template>
      
      <div v-if="chartStats && (chartStats.sleepAvgDuration > 0 || chartStats.avgHeartRate > 0 || chartStats.totalSteps > 0)">
        <NGrid :cols="6" :x-gap="16" :y-gap="16" responsive="screen">
          <NGridItem>
            <div class="text-center p-3 bg-blue-50 rounded-lg">
              <div class="text-xl font-bold text-blue-600">{{ chartStats.sleepAvgDuration.toFixed(1) }}h</div>
              <div class="text-xs text-blue-500 mt-1">平均睡眠</div>
            </div>
          </NGridItem>
        
          <NGridItem>
            <div class="text-center p-3 bg-green-50 rounded-lg">
              <div class="text-xl font-bold text-green-600">{{ chartStats.sleepQuality.toFixed(0) }}分</div>
              <div class="text-xs text-green-500 mt-1">睡眠质量</div>
            </div>
          </NGridItem>
          
          <NGridItem>
            <div class="text-center p-3 bg-purple-50 rounded-lg">
              <div class="text-xl font-bold text-purple-600">{{ chartStats.exerciseTypes }}</div>
              <div class="text-xs text-purple-500 mt-1">运动类型</div>
            </div>
          </NGridItem>
          
          <NGridItem>
            <div class="text-center p-3 bg-red-50 rounded-lg">
              <div class="text-xl font-bold text-red-600">{{ chartStats.avgHeartRate.toFixed(0) }}bpm</div>
              <div class="text-xs text-red-500 mt-1">平均心率</div>
            </div>
          </NGridItem>
          
          <NGridItem>
            <div class="text-center p-3 bg-orange-50 rounded-lg">
              <div class="text-xl font-bold text-orange-600">{{ chartStats.totalSteps.toLocaleString() }}</div>
              <div class="text-xs text-orange-500 mt-1">总步数</div>
            </div>
          </NGridItem>
          
          <NGridItem>
            <div class="text-center p-3 bg-yellow-50 rounded-lg">
              <div class="text-xl font-bold text-yellow-600">{{ chartStats.totalCalories.toFixed(0) }}</div>
              <div class="text-xs text-yellow-500 mt-1">总卡路里</div>
            </div>
          </NGridItem>
        </NGrid>
      </div>
      <div v-else class="text-center py-8">
        <NEmpty description="暂无分析数据" />
      </div>
    </NCard>

    <!-- 图表区域 -->
    <div v-if="!props.healthData" class="flex justify-center py-8">
      <NEmpty description="暂无健康数据，无法生成分析图表" />
    </div>
    
    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 睡眠分析图表 -->
      <NCard :bordered="false" class="chart-card">
        <template #header>
          <div class="flex items-center gap-2">
            <span class="text-base font-medium">🌙 睡眠质量分析</span>
            <NTag type="info" size="small">日常监测</NTag>
          </div>
        </template>
        <div v-if="sleepData && sleepData.length > 0" 
             ref="sleepChartRef" class="chart-container"></div>
        <div v-else class="chart-container flex items-center justify-center">
          <NEmpty description="暂无睡眠数据" />
        </div>
      </NCard>

      <!-- 运动分布图表 -->
      <NCard :bordered="false" class="chart-card">
        <template #header>
          <div class="flex items-center gap-2">
            <span class="text-base font-medium">🏃 运动类型分布</span>
            <NTag type="success" size="small">活动统计</NTag>
          </div>
        </template>
        <div v-if="(workoutData && workoutData.length > 0) || (exerciseDailyData && exerciseDailyData.length > 0)" 
             ref="exerciseChartRef" class="chart-container"></div>
        <div v-else class="chart-container flex items-center justify-center">
          <NEmpty description="暂无运动数据" />
        </div>
      </NCard>

      <!-- 心血管监测图表 -->
      <NCard :bordered="false" class="chart-card">
        <template #header>
          <div class="flex items-center gap-2">
            <span class="text-base font-medium">❤️ 心血管健康</span>
            <NTag type="error" size="small">生命体征</NTag>
          </div>
        </template>
        <div v-if="records && records.length > 0" 
             ref="cardioChartRef" class="chart-container"></div>
        <div v-else class="chart-container flex items-center justify-center">
          <NEmpty description="暂无心血管数据" />
        </div>
      </NCard>

      <!-- 活动量统计图表 -->
      <NCard :bordered="false" class="chart-card">
        <template #header>
          <div class="flex items-center gap-2">
            <span class="text-base font-medium">🚶 日常活动量</span>
            <NTag type="warning" size="small">运动指标</NTag>
          </div>
        </template>
        <div v-if="records && records.length > 0" 
             ref="activityChartRef" class="chart-container"></div>
        <div v-else class="chart-container flex items-center justify-center">
          <NEmpty description="暂无活动数据" />
        </div>
      </NCard>
    </div>
  </div>
</template>

<style scoped>
.health-analytics-charts {
  .chart-card {
    height: 450px;
    
    .chart-container {
      height: 380px;
      width: 100%;
    }
    
    :deep(.n-card-header) {
      padding-bottom: 12px;
      border-bottom: 1px solid #f0f0f0;
    }
  }
  
  /* 响应式适配 */
  @media (max-width: 1024px) {
    .grid-cols-1.lg\\:grid-cols-2 {
      grid-template-columns: 1fr;
    }
    
    .chart-card {
      height: 400px;
      
      .chart-container {
        height: 330px;
      }
    }
  }
  
  @media (max-width: 768px) {
    .chart-card {
      height: 350px;
      
      .chart-container {
        height: 280px;
      }
    }
  }
}

/* 概览卡片响应式 */
:deep(.n-grid-item) {
  @media (max-width: 768px) {
    grid-column: span 2;
  }
  
  @media (max-width: 480px) {
    grid-column: span 3;
  }
}
</style>