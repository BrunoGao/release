<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';

interface PredictionPoint {
  date: string;
  actual?: number;
  predicted: number;
  confidence: number;
}

interface Props {
  data: PredictionPoint[];
  title?: string;
  yAxisName?: string;
  unit?: string;
}

const props = withDefaults(defineProps<Props>(), {
  title: '健康预测分析',
  yAxisName: '数值',
  unit: ''
});

const chartRef = ref<HTMLElement>();
const { domRef, updateOptions } = useEcharts(chartRef, {
  darkMode: false,
  size: { width: '100%', height: '100%' }
});

watch(
  () => props.data,
  newData => {
    if (newData && newData.length > 0) {
      updateChart();
    }
  },
  { immediate: true }
);

function updateChart() {
  const categories = props.data.map(item => item.date);
  const actualData = props.data.map(item => item.actual || null);
  const predictedData = props.data.map(item => item.predicted);
  const confidenceData = props.data.map(item => item.confidence * 100);

  // 分离历史数据和预测数据
  const splitIndex = props.data.findIndex(item => item.actual === undefined);
  const historyCategories = categories.slice(0, splitIndex);
  const predictionCategories = categories.slice(splitIndex - 1);
  const historyActual = actualData.slice(0, splitIndex);
  const predictionData = predictedData.slice(splitIndex - 1);

  const option = {
    title: {
      text: props.title,
      left: 'center',
      textStyle: {
        color: '#1f2937',
        fontSize: 16,
        fontWeight: '600'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#374151'
      },
      formatter(params: any) {
        let result = `<div style="padding: 8px;">`;
        result += `<div style="font-weight: 600; margin-bottom: 8px;">${params[0].name}</div>`;

        params.forEach((param: any) => {
          if (param.value !== null) {
            result += `
              <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="display: inline-block; width: 10px; height: 10px; background-color: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>
                <span>${param.seriesName}: ${param.value}${props.unit}</span>
              </div>
            `;
          }
        });

        result += `</div>`;
        return result;
      }
    },
    legend: {
      data: ['历史数据', '预测数据', '置信度'],
      top: '8%',
      textStyle: {
        color: '#6b7280'
      }
    },
    grid: {
      top: '20%',
      left: '5%',
      right: '15%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLine: {
        lineStyle: {
          color: '#e5e7eb'
        }
      },
      axisLabel: {
        color: '#6b7280',
        fontSize: 11,
        rotate: categories.length > 10 ? 45 : 0
      },
      axisTick: {
        show: false
      }
    },
    yAxis: [
      {
        type: 'value',
        name: props.yAxisName,
        nameTextStyle: {
          color: '#6b7280',
          fontSize: 12
        },
        axisLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        axisLabel: {
          color: '#6b7280',
          fontSize: 11,
          formatter: `{value}${props.unit}`
        },
        splitLine: {
          lineStyle: {
            color: '#f3f4f6',
            type: 'dashed'
          }
        }
      },
      {
        type: 'value',
        name: '置信度(%)',
        nameTextStyle: {
          color: '#6b7280',
          fontSize: 12
        },
        position: 'right',
        min: 0,
        max: 100,
        axisLabel: {
          color: '#6b7280',
          fontSize: 11,
          formatter: '{value}%'
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: '历史数据',
        type: 'line',
        data: actualData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          color: '#3b82f6',
          width: 3
        },
        itemStyle: {
          color: '#3b82f6',
          borderColor: '#ffffff',
          borderWidth: 2
        },
        connectNulls: false
      },
      {
        name: '预测数据',
        type: 'line',
        data: predictedData.map((value, index) => (index >= splitIndex - 1 ? value : null)),
        smooth: true,
        symbol: 'diamond',
        symbolSize: 8,
        lineStyle: {
          color: '#f59e0b',
          width: 3,
          type: 'dashed'
        },
        itemStyle: {
          color: '#f59e0b',
          borderColor: '#ffffff',
          borderWidth: 2
        },
        connectNulls: false,
        emphasis: {
          itemStyle: {
            color: '#d97706',
            shadowBlur: 10,
            shadowColor: '#f59e0b60'
          }
        }
      },
      {
        name: '置信度',
        type: 'bar',
        yAxisIndex: 1,
        data: confidenceData.map((value, index) => (index >= splitIndex - 1 ? value : null)),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#10b98160' },
              { offset: 1, color: '#10b98120' }
            ]
          }
        },
        barWidth: '40%',
        emphasis: {
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#059669' },
                { offset: 1, color: '#05966940' }
              ]
            }
          }
        }
      }
    ],
    animation: true,
    animationDuration: 1500,
    animationEasing: 'cubicOut'
  };

  updateOptions(option);
}

onMounted(() => {
  if (props.data && props.data.length > 0) {
    updateChart();
  }
});
</script>

<template>
  <div ref="chartRef" class="h-full min-h-80 w-full" />
</template>

<style scoped>
/* Chart container styling */
</style>
