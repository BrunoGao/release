<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';

interface PredictionPoint {
  date: string;
  actual?: number;
  predicted: number;
  confidence: number;
  upperBound?: number;
  lowerBound?: number;
  trend?: 'increasing' | 'decreasing' | 'stable';
  anomaly?: boolean;
}

interface Props {
  data: PredictionPoint[];
  title?: string;
  yAxisName?: string;
  unit?: string;
  showConfidenceInterval?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  title: '高级健康预测分析',
  yAxisName: '数值',
  unit: '',
  showConfidenceInterval: true
});

const chartRef = ref<HTMLElement>();
const { domRef, updateOptions } = useEcharts(chartRef, {
  darkMode: false,
  size: { width: '100%', height: '100%' }
});

// 计算预测统计信息
const predictionStats = computed(() => {
  if (!props.data || props.data.length === 0) return null;

  const actualData = props.data.filter(item => item.actual !== undefined);
  const predictedData = props.data.filter(item => item.actual === undefined);

  const avgActual = actualData.reduce((sum, item) => sum + (item.actual || 0), 0) / actualData.length;
  const avgPredicted = predictedData.reduce((sum, item) => sum + item.predicted, 0) / predictedData.length;
  const avgConfidence = props.data.reduce((sum, item) => sum + item.confidence, 0) / props.data.length;

  const trend = avgPredicted > avgActual ? 'increasing' : avgPredicted < avgActual ? 'decreasing' : 'stable';

  return {
    avgActual: Math.round(avgActual * 10) / 10,
    avgPredicted: Math.round(avgPredicted * 10) / 10,
    avgConfidence: Math.round(avgConfidence * 100) / 100,
    trend,
    changePercent: Math.round(((avgPredicted - avgActual) / avgActual) * 100 * 10) / 10,
    accuracy: Math.round((avgConfidence / 100) * 100)
  };
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

  // 计算置信区间
  const upperBoundData = props.data.map((item, index) => {
    if (index >= splitIndex - 1 && item.predicted !== null) {
      const confidence = item.confidence;
      return Math.round(item.predicted + item.predicted * (1 - confidence) * 0.3);
    }
    return null;
  });

  const lowerBoundData = props.data.map((item, index) => {
    if (index >= splitIndex - 1 && item.predicted !== null) {
      const confidence = item.confidence;
      return Math.round(item.predicted - item.predicted * (1 - confidence) * 0.3);
    }
    return null;
  });

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
          if (param.value !== null && param.seriesName !== '置信度上限' && param.seriesName !== '置信度下限') {
            result += `
              <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="display: inline-block; width: 10px; height: 10px; background-color: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>
                <span>${param.seriesName}: ${param.value}${props.unit}</span>
              </div>
            `;
          }
        });

        // 添加预测统计信息
        if (predictionStats.value && params[0].dataIndex >= splitIndex - 1) {
          result += `
            <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e7eb;">
              <div style="font-size: 12px; color: #6b7280; margin-bottom: 4px;">预测趋势: ${getTrendText(predictionStats.value.trend)}</div>
              <div style="font-size: 12px; color: #6b7280;">置信度: ${props.data[params[0].dataIndex].confidence * 100}%</div>
            </div>
          `;
        }

        result += `</div>`;
        return result;
      }
    },
    legend: {
      data: ['历史数据', '预测数据', '置信区间', '异常检测'],
      top: '8%',
      textStyle: {
        color: '#6b7280'
      }
    },
    grid: {
      top: '20%',
      left: '5%',
      right: '15%',
      bottom: '20%',
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
      }
    ],
    series: [
      // 置信区间（背景）
      {
        name: '置信度上限',
        type: 'line',
        data: upperBoundData,
        lineStyle: {
          opacity: 0
        },
        itemStyle: {
          opacity: 0
        },
        showSymbol: false,
        silent: true
      },
      {
        name: '置信度下限',
        type: 'line',
        data: lowerBoundData,
        lineStyle: {
          opacity: 0
        },
        itemStyle: {
          opacity: 0
        },
        showSymbol: false,
        silent: true,
        areaStyle: {
          color: '#f59e0b20'
        },
        stack: 'confidence'
      },
      // 历史数据
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
        connectNulls: false,
        markPoint: {
          data: [
            {
              type: 'max',
              name: '最大值',
              itemStyle: {
                color: '#3b82f6'
              }
            },
            {
              type: 'min',
              name: '最小值',
              itemStyle: {
                color: '#3b82f6'
              }
            }
          ]
        },
        markLine: {
          silent: true,
          data: [
            {
              type: 'average',
              name: '历史平均',
              lineStyle: {
                color: '#3b82f680',
                type: 'dashed'
              }
            }
          ]
        }
      },
      // 预测数据
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
        },
        markArea: {
          silent: true,
          itemStyle: {
            color: '#f59e0b10'
          },
          data: [
            [
              {
                name: '预测区间',
                xAxis: categories[Math.max(0, splitIndex - 1)]
              },
              {
                xAxis: categories[categories.length - 1]
              }
            ]
          ]
        }
      },
      // 异常点检测
      {
        name: '异常检测',
        type: 'scatter',
        data: props.data
          .map((item, index) => {
            if (item.anomaly) {
              return [index, item.actual || item.predicted];
            }
            return null;
          })
          .filter(item => item !== null),
        symbol: 'triangle',
        symbolSize: 12,
        itemStyle: {
          color: '#ff4d4f',
          borderColor: '#ffffff',
          borderWidth: 2
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: '#ff4d4f60'
          }
        }
      }
    ],
    graphic: [
      {
        type: 'text',
        left: 'center',
        bottom: '3%',
        style: {
          text: predictionStats.value
            ? `预测趋势: ${getTrendText(predictionStats.value.trend)} | 平均置信度: ${predictionStats.value.avgConfidence.toFixed(1)}% | 预期变化: ${predictionStats.value.changePercent > 0 ? '+' : ''}${predictionStats.value.changePercent}%`
            : '',
          fontSize: 12,
          fill: '#6b7280'
        }
      }
    ],
    animation: true,
    animationDuration: 2000,
    animationEasing: 'elasticOut'
  };

  updateOptions(option);
}

function getTrendText(trend: string) {
  switch (trend) {
    case 'increasing':
      return '⬆ 上升';
    case 'decreasing':
      return '⬇ 下降';
    case 'stable':
      return '➡ 稳定';
    default:
      return '❓ 未知';
  }
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
