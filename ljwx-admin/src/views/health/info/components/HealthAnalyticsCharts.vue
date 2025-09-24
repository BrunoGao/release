<script setup lang="tsx">
import { NButton, NCard, NEmpty, NGrid, NGridItem, NSkeleton, NSpace, NTag } from 'naive-ui';
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import * as echarts from 'echarts';
import { fetchGetHealthDataBasicList } from '@/service/api';

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
  const sleepAvgDuration =
    sleepData.value.length > 0
      ? sleepData.value.reduce((sum, item) => sum + Number.parseFloat(item.processed?.value || 0), 0) / sleepData.value.length
      : 0;

  // 从基础数据计算心血管和活动数据
  const recordsData = records.value;
  const validHeartRates = recordsData.filter(r => r.heartRate).map(r => r.heartRate);
  const avgHeartRate = validHeartRates.length > 0 ? validHeartRates.reduce((a, b) => a + b, 0) / validHeartRates.length : 0;

  const totalSteps = recordsData.reduce((sum, r) => sum + (r.step || 0), 0);
  const totalCalories = recordsData.reduce((sum, r) => sum + (r.calorie || 0), 0);

  return {
    sleepAvgDuration,
    sleepQuality: 85, // 临时固定值，后续可以从processed数据中计算
    exerciseTypes: workoutData.value.length + exerciseDailyData.value.length,
    avgHeartRate: Math.round(avgHeartRate),
    totalSteps,
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
      duration: Number.parseFloat(item.processed?.value || 0),
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
      text: '睡眠质量分析',
      subtext: '多用户睡眠时长趋势对比',
      left: 'center',
      textStyle: { 
        fontSize: 18, 
        fontWeight: 'bold',
        color: '#2c3e50'
      },
      subtextStyle: {
        fontSize: 12,
        color: '#7f8c8d'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#409EFF',
      borderWidth: 1,
      textStyle: {
        color: '#fff',
        fontSize: 12
      },
      formatter: (params: any) => {
        let result = `<div style="padding: 8px;">`;
        result += `<div style="margin-bottom: 6px; font-weight: bold; color: #409EFF;">📅 ${params[0].name}</div>`;
        params.forEach((param: any) => {
          const qualityScore = param.value >= 7 ? '优质' : param.value >= 6 ? '良好' : param.value >= 5 ? '一般' : '较差';
          const qualityColor = param.value >= 7 ? '#67C23A' : param.value >= 6 ? '#E6A23C' : param.value >= 5 ? '#F56C6C' : '#909399';
          result += `<div style="margin: 4px 0; display: flex; align-items: center;">`;
          result += `<span style="display: inline-block; width: 10px; height: 10px; background: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>`;
          result += `<span style="margin-right: 8px;">${param.seriesName}:</span>`;
          result += `<span style="font-weight: bold; margin-right: 8px;">${param.value.toFixed(1)}小时</span>`;
          result += `<span style="color: ${qualityColor}; font-size: 10px; padding: 1px 4px; background: rgba(255,255,255,0.1); border-radius: 3px;">${qualityScore}</span>`;
          result += `</div>`;
        });
        result += `</div>`;
        return result;
      }
    },
    legend: {
      data: series.map(s => s.name),
      top: '12%',
      type: 'scroll',
      textStyle: {
        fontSize: 12,
        color: '#606266'
      },
      itemWidth: 14,
      itemHeight: 8
    },
    xAxis: {
      type: 'category',
      data: allDates,
      axisLabel: {
        rotate: 30,
        color: '#606266',
        fontSize: 11,
        formatter: (value: string) => {
          return value.substring(5);
        }
      },
      axisLine: {
        lineStyle: {
          color: '#E4E7ED'
        }
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      name: '睡眠时长(小时)',
      nameTextStyle: {
        color: '#606266',
        fontSize: 12
      },
      min: 0,
      max: 12,
      splitNumber: 6,
      axisLabel: {
        color: '#606266',
        fontSize: 11,
        formatter: (value: number) => `${value}h`
      },
      axisLine: {
        show: false
      },
      splitLine: {
        lineStyle: {
          color: '#F5F7FA',
          type: 'dashed'
        }
      }
    },
    series: series.map(s => ({
      ...s,
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: {
        width: 3,
        shadowColor: 'rgba(0,0,0,0.1)',
        shadowBlur: 4,
        shadowOffsetY: 2
      },
      areaStyle: {
        opacity: 0.1
      }
    })),
    grid: { 
      left: '8%', 
      right: '5%', 
      bottom: '15%', 
      top: '25%',
      containLabel: true
    },
    graphic: allDates.length === 0 ? {
      type: 'text',
      left: 'center',
      top: 'middle',
      style: {
        text: '🌙 暂无睡眠数据',
        fontSize: 16,
        fill: '#C0C4CC'
      }
    } : null
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
        userName,
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
      text: '运动类型分布',
      subtext: '用户运动偏好统计分析',
      left: 'center',
      textStyle: { 
        fontSize: 18, 
        fontWeight: 'bold',
        color: '#2c3e50'
      },
      subtextStyle: {
        fontSize: 12,
        color: '#7f8c8d'
      }
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#67C23A',
      borderWidth: 1,
      textStyle: {
        color: '#fff',
        fontSize: 12
      },
      formatter: (params: any) => {
        return `<div style="padding: 8px;">
          <div style="margin-bottom: 6px; font-weight: bold; color: #67C23A;">🏃 ${params.name}</div>
          <div style="display: flex; align-items: center;">
            <span style="display: inline-block; width: 10px; height: 10px; background: ${params.color}; border-radius: 50%; margin-right: 8px;"></span>
            <span>运动次数: <strong>${params.value}次</strong></span>
          </div>
          <div style="margin-top: 4px; color: #E6A23C;">占比: <strong>${params.percent}%</strong></div>
        </div>`;
      }
    },
    legend: {
      orient: 'vertical',
      left: '5%',
      top: '20%',
      type: 'scroll',
      textStyle: { 
        fontSize: 11,
        color: '#606266'
      },
      itemWidth: 12,
      itemHeight: 8,
      itemGap: 8
    },
    series: [
      {
        name: '运动统计',
        type: 'pie',
        radius: ['45%', '75%'],
        center: ['65%', '55%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 3,
          shadowColor: 'rgba(0,0,0,0.1)',
          shadowBlur: 8,
          shadowOffsetY: 2
        },
        label: {
          show: true,
          position: 'outside',
          fontSize: 11,
          color: '#606266',
          formatter: (params: any) => {
            return params.percent >= 5 ? `${params.percent}%` : '';
          }
        },
        labelLine: {
          show: true,
          length: 15,
          length2: 8,
          lineStyle: {
            color: '#C0C4CC'
          }
        },
        emphasis: {
          scale: true,
          scaleSize: 5,
          itemStyle: {
            shadowBlur: 15,
            shadowColor: 'rgba(0,0,0,0.3)'
          }
        },
        data: pieData.length > 0 ? pieData : [
          { name: '暂无数据', value: 1, itemStyle: { color: '#E4E7ED' } }
        ]
      }
    ],
    graphic: pieData.length === 0 ? {
      type: 'text',
      left: 'center',
      top: 'middle',
      style: {
        text: '🏃 暂无运动数据',
        fontSize: 16,
        fill: '#C0C4CC'
      }
    } : null
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
        userName,
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
      text: '心血管健康监测',
      subtext: '心率与血压趋势分析',
      left: 'center',
      textStyle: { 
        fontSize: 18, 
        fontWeight: 'bold',
        color: '#2c3e50'
      },
      subtextStyle: {
        fontSize: 12,
        color: '#7f8c8d'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#F56C6C',
      borderWidth: 1,
      textStyle: {
        color: '#fff',
        fontSize: 12
      },
      formatter: (params: any) => {
        let result = `<div style="padding: 8px;">`;
        result += `<div style="margin-bottom: 6px; font-weight: bold; color: #F56C6C;">❤️ ${params[0].name}</div>`;
        params.forEach((param: any) => {
          if (param.value !== null) {
            const unit = param.seriesName.includes('心率') ? 'bpm' : 'mmHg';
            const isHeartRate = param.seriesName.includes('心率');
            const status = isHeartRate 
              ? (param.value >= 60 && param.value <= 100 ? '正常' : '异常')
              : (param.value <= 120 ? '正常' : param.value <= 140 ? '偏高' : '高血压');
            const statusColor = isHeartRate
              ? (param.value >= 60 && param.value <= 100 ? '#67C23A' : '#F56C6C')
              : (param.value <= 120 ? '#67C23A' : param.value <= 140 ? '#E6A23C' : '#F56C6C');
            
            result += `<div style="margin: 4px 0; display: flex; align-items: center;">`;
            result += `<span style="display: inline-block; width: 10px; height: 10px; background: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>`;
            result += `<span style="margin-right: 8px;">${param.seriesName}:</span>`;
            result += `<span style="font-weight: bold; margin-right: 8px;">${param.value}${unit}</span>`;
            result += `<span style="color: ${statusColor}; font-size: 10px; padding: 1px 4px; background: rgba(255,255,255,0.1); border-radius: 3px;">${status}</span>`;
            result += `</div>`;
          }
        });
        result += `</div>`;
        return result;
      }
    },
    legend: {
      data: allSeries.map(s => s.name),
      top: '12%',
      type: 'scroll',
      textStyle: { 
        fontSize: 11,
        color: '#606266'
      },
      itemWidth: 14,
      itemHeight: 8
    },
    xAxis: {
      type: 'category',
      data: sortedDates,
      axisLabel: {
        rotate: 30,
        color: '#606266',
        fontSize: 11,
        formatter: (value: string) => value.substring(5)
      },
      axisLine: {
        lineStyle: {
          color: '#E4E7ED'
        }
      },
      axisTick: {
        show: false
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '心率(bpm)',
        nameTextStyle: {
          color: '#F56C6C',
          fontSize: 12
        },
        position: 'left',
        min: 50,
        max: 120,
        splitNumber: 7,
        axisLabel: {
          color: '#606266',
          fontSize: 11,
          formatter: (value: number) => `${value}`
        },
        axisLine: {
          show: false
        },
        splitLine: {
          lineStyle: {
            color: '#F5F7FA',
            type: 'dashed'
          }
        }
      },
      {
        type: 'value',
        name: '血压(mmHg)',
        nameTextStyle: {
          color: '#E6A23C',
          fontSize: 12
        },
        position: 'right',
        min: 80,
        max: 160,
        splitNumber: 8,
        axisLabel: {
          color: '#606266',
          fontSize: 11,
          formatter: (value: number) => `${value}`
        },
        axisLine: {
          show: false
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: allSeries.map(s => ({
      ...s,
      smooth: true,
      symbolSize: s.name.includes('心率') ? 6 : 8,
      lineStyle: {
        width: s.name.includes('心率') ? 3 : 2,
        shadowColor: 'rgba(0,0,0,0.1)',
        shadowBlur: 4,
        shadowOffsetY: 2
      }
    })),
    grid: { 
      left: '8%', 
      right: '8%', 
      bottom: '15%', 
      top: '25%',
      containLabel: true
    },
    graphic: sortedDates.length === 0 ? {
      type: 'text',
      left: 'center',
      top: 'middle',
      style: {
        text: '❤️ 暂无心血管数据',
        fontSize: 16,
        fill: '#C0C4CC'
      }
    } : null
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
        userName,
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
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: userColor },
            { offset: 1, color: `${userColor}80` }
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
      text: '日常活动量统计',
      subtext: '步数与卡路里消耗分析',
      left: 'center',
      textStyle: { 
        fontSize: 18, 
        fontWeight: 'bold',
        color: '#2c3e50'
      },
      subtextStyle: {
        fontSize: 12,
        color: '#7f8c8d'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#67C23A',
      borderWidth: 1,
      textStyle: {
        color: '#fff',
        fontSize: 12
      },
      formatter: (params: any) => {
        let result = `<div style="padding: 8px;">`;
        result += `<div style="margin-bottom: 6px; font-weight: bold; color: #67C23A;">🚶 ${params[0].name}</div>`;
        params.forEach((param: any) => {
          if (param.value > 0) {
            const unit = param.seriesName.includes('步数') ? '步' : 'kcal';
            const isSteps = param.seriesName.includes('步数');
            const target = isSteps ? 10000 : 2000; // 目标步数10000步，目标卡路里2000kcal
            const achievement = Math.min((param.value / target) * 100, 100);
            const achievementColor = achievement >= 80 ? '#67C23A' : achievement >= 60 ? '#E6A23C' : '#F56C6C';
            
            result += `<div style="margin: 4px 0; display: flex; align-items: center;">`;
            result += `<span style="display: inline-block; width: 10px; height: 10px; background: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>`;
            result += `<span style="margin-right: 8px;">${param.seriesName}:</span>`;
            result += `<span style="font-weight: bold; margin-right: 8px;">${param.value.toLocaleString()}${unit}</span>`;
            if (isSteps) {
              result += `<span style="color: ${achievementColor}; font-size: 10px; padding: 1px 4px; background: rgba(255,255,255,0.1); border-radius: 3px;">${achievement.toFixed(0)}%目标</span>`;
            }
            result += `</div>`;
          }
        });
        result += `</div>`;
        return result;
      }
    },
    legend: {
      data: allSeries.map(s => s.name),
      top: '12%',
      type: 'scroll',
      textStyle: { 
        fontSize: 11,
        color: '#606266'
      },
      itemWidth: 14,
      itemHeight: 8
    },
    xAxis: {
      type: 'category',
      data: sortedDates,
      axisLabel: {
        rotate: 30,
        color: '#606266',
        fontSize: 11,
        formatter: (value: string) => value.substring(5)
      },
      axisLine: {
        lineStyle: {
          color: '#E4E7ED'
        }
      },
      axisTick: {
        show: false
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '步数',
        nameTextStyle: {
          color: '#67C23A',
          fontSize: 12
        },
        position: 'left',
        min: 0,
        axisLabel: {
          color: '#606266',
          fontSize: 11,
          formatter: (value: number) => (value >= 1000 ? `${(value / 1000).toFixed(0)}k` : value)
        },
        axisLine: {
          show: false
        },
        splitLine: {
          lineStyle: {
            color: '#F5F7FA',
            type: 'dashed'
          }
        }
      },
      {
        type: 'value',
        name: '卡路里(kcal)',
        nameTextStyle: {
          color: '#E6A23C',
          fontSize: 12
        },
        position: 'right',
        min: 0,
        axisLabel: {
          color: '#606266',
          fontSize: 11,
          formatter: (value: number) => `${value}`
        },
        axisLine: {
          show: false
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: allSeries.map(s => {
      if (s.name.includes('步数')) {
        return {
          ...s,
          itemStyle: {
            ...s.itemStyle,
            borderRadius: [4, 4, 0, 0],
            shadowColor: 'rgba(0,0,0,0.1)',
            shadowBlur: 4,
            shadowOffsetY: 2
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 8,
              shadowColor: 'rgba(0,0,0,0.3)'
            }
          }
        };
      } else {
        return {
          ...s,
          smooth: true,
          symbolSize: 8,
          lineStyle: {
            width: 3,
            shadowColor: 'rgba(0,0,0,0.1)',
            shadowBlur: 4,
            shadowOffsetY: 2
          },
          areaStyle: {
            opacity: 0.1
          }
        };
      }
    }),
    grid: { 
      left: '8%', 
      right: '8%', 
      bottom: '15%', 
      top: '25%',
      containLabel: true
    },
    graphic: sortedDates.length === 0 ? {
      type: 'text',
      left: 'center',
      top: 'middle',
      style: {
        text: '🚶 暂无活动数据',
        fontSize: 16,
        fill: '#C0C4CC'
      }
    } : null
  };

  activityChart.setOption(option);
};

// 获取运动类型颜色
const getExerciseTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    跑步: '#FF6B6B',
    走路: '#4ECDC4',
    骑行: '#45B7D1',
    游泳: '#96CEB4',
    力量训练: '#FFEAA7',
    瑜伽: '#DDA0DD',
    其他: '#95A5A6'
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
watch(
  () => props.healthData,
  newHealthData => {
    if (newHealthData) {
      renderCharts();
    }
  },
  { deep: true }
);

// 监听可见性变化
watch(
  () => props.visible,
  visible => {
    if (visible && props.healthData) {
      renderCharts();
    }
  }
);

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
  <div v-show="visible" class="health-analytics-charts">
    <!-- 分析概览 -->
    <NCard :bordered="false" class="mb-4">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-lg font-medium">📊 健康数据分析概览</span>
            <NTag v-if="records && records.length > 0" type="info" size="small">{{ records.length }} 条记录</NTag>
          </div>
          <NButton size="small" @click="refreshCharts">刷新分析</NButton>
        </div>
      </template>

      <div v-if="chartStats && (chartStats.sleepAvgDuration > 0 || chartStats.avgHeartRate > 0 || chartStats.totalSteps > 0)">
        <NGrid :cols="6" :x-gap="16" :y-gap="16" responsive="screen">
          <NGridItem>
            <div class="rounded-lg bg-blue-50 p-3 text-center">
              <div class="text-xl text-blue-600 font-bold">{{ chartStats.sleepAvgDuration.toFixed(1) }}h</div>
              <div class="mt-1 text-xs text-blue-500">平均睡眠</div>
            </div>
          </NGridItem>

          <NGridItem>
            <div class="rounded-lg bg-green-50 p-3 text-center">
              <div class="text-xl text-green-600 font-bold">{{ chartStats.sleepQuality.toFixed(0) }}分</div>
              <div class="mt-1 text-xs text-green-500">睡眠质量</div>
            </div>
          </NGridItem>

          <NGridItem>
            <div class="rounded-lg bg-purple-50 p-3 text-center">
              <div class="text-xl text-purple-600 font-bold">{{ chartStats.exerciseTypes }}</div>
              <div class="mt-1 text-xs text-purple-500">运动类型</div>
            </div>
          </NGridItem>

          <NGridItem>
            <div class="rounded-lg bg-red-50 p-3 text-center">
              <div class="text-xl text-red-600 font-bold">{{ chartStats.avgHeartRate.toFixed(0) }}bpm</div>
              <div class="mt-1 text-xs text-red-500">平均心率</div>
            </div>
          </NGridItem>

          <NGridItem>
            <div class="rounded-lg bg-orange-50 p-3 text-center">
              <div class="text-xl text-orange-600 font-bold">{{ chartStats.totalSteps.toLocaleString() }}</div>
              <div class="mt-1 text-xs text-orange-500">总步数</div>
            </div>
          </NGridItem>

          <NGridItem>
            <div class="rounded-lg bg-yellow-50 p-3 text-center">
              <div class="text-xl text-yellow-600 font-bold">{{ chartStats.totalCalories.toFixed(0) }}</div>
              <div class="mt-1 text-xs text-yellow-500">总卡路里</div>
            </div>
          </NGridItem>
        </NGrid>
      </div>
      <div v-else class="py-8 text-center">
        <NEmpty description="暂无分析数据" />
      </div>
    </NCard>

    <!-- 图表区域 -->
    <div v-if="!props.healthData" class="flex justify-center py-8">
      <NEmpty description="暂无健康数据，无法生成分析图表" />
    </div>

    <div v-else class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <!-- 睡眠分析图表 -->
      <NCard :bordered="false" class="chart-card">
        <template #header>
          <div class="flex items-center gap-2">
            <span class="text-base font-medium">🌙 睡眠质量分析</span>
            <NTag type="info" size="small">日常监测</NTag>
          </div>
        </template>
        <div v-if="sleepData && sleepData.length > 0" ref="sleepChartRef" class="chart-container"></div>
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
        <div
          v-if="(workoutData && workoutData.length > 0) || (exerciseDailyData && exerciseDailyData.length > 0)"
          ref="exerciseChartRef"
          class="chart-container"
        ></div>
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
        <div v-if="records && records.length > 0" ref="cardioChartRef" class="chart-container"></div>
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
        <div v-if="records && records.length > 0" ref="activityChartRef" class="chart-container"></div>
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
