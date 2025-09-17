<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';

interface BaselineData {
  feature: string;
  baseline: number;
  current: number;
  deviation: number;
  status: 'normal' | 'warning' | 'danger';
  unit: string;
  trend: 'up' | 'down' | 'stable';
}

interface Props {
  data: BaselineData[];
  title?: string;
  chartType?: 'line' | 'bar' | 'mixed';
}

const props = withDefaults(defineProps<Props>(), {
  title: '健康基线分析',
  chartType: 'mixed'
});

const chartRef = ref<HTMLElement>();
const { domRef, updateOptions } = useEcharts(chartRef, {
  darkMode: false,
  size: { width: '100%', height: '100%' }
});

const chartColors = {
  baseline: '#52c41a',
  current: '#1890ff',
  deviation: '#faad14',
  warning: '#ff7875',
  danger: '#ff4d4f'
};

const processedData = computed(() => {
  if (!props.data || props.data.length === 0) return null;
  
  return {
    categories: props.data.map(item => item.feature),
    baseline: props.data.map(item => item.baseline),
    current: props.data.map(item => item.current),
    deviation: props.data.map(item => Math.abs(item.deviation)),
    status: props.data.map(item => item.status)
  };
});

watch(
  () => props.data,
  (newData) => {
    if (newData && newData.length > 0) {
      updateChart();
    }
  },
  { immediate: true }
);

function updateChart() {
  if (!processedData.value) return;

  const { categories, baseline, current, deviation, status } = processedData.value;

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
      formatter: function(params: any) {
        let result = `<div style="padding: 8px;">`;
        result += `<div style="font-weight: 600; margin-bottom: 8px;">${params[0].name}</div>`;
        
        params.forEach((param: any, index: number) => {
          const dataItem = props.data[param.dataIndex];
          if (param.value !== null && param.value !== undefined) {
            result += `
              <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="display: inline-block; width: 10px; height: 10px; background-color: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>
                <span>${param.seriesName}: ${param.value}${dataItem.unit}</span>
              </div>
            `;
          }
        });
        
        const dataItem = props.data[params[0].dataIndex];
        result += `
          <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e7eb;">
            <div style="font-size: 12px; color: #6b7280;">
              偏差: ${dataItem.deviation > 0 ? '+' : ''}${dataItem.deviation.toFixed(1)}${dataItem.unit}
            </div>
            <div style="font-size: 12px; color: ${getStatusColor(dataItem.status)};">
              状态: ${getStatusText(dataItem.status)}
            </div>
          </div>
        `;
        
        result += `</div>`;
        return result;
      }
    },
    legend: {
      data: ['基线值', '当前值', '偏差程度'],
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
    xAxis: [
      {
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
          interval: 0,
          rotate: categories.length > 6 ? 30 : 0
        },
        axisTick: {
          show: false
        }
      }
    ],
    yAxis: [
      {
        type: 'value',
        name: '数值',
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
          fontSize: 11
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
        name: '偏差',
        nameTextStyle: {
          color: '#6b7280',
          fontSize: 12
        },
        position: 'right',
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
        name: '基线值',
        type: 'line',
        data: baseline,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          color: chartColors.baseline,
          width: 3
        },
        itemStyle: {
          color: chartColors.baseline,
          borderColor: '#ffffff',
          borderWidth: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: chartColors.baseline + '40' },
              { offset: 1, color: chartColors.baseline + '10' }
            ]
          }
        }
      },
      {
        name: '当前值',
        type: 'line',
        data: current,
        smooth: true,
        symbol: 'diamond',
        symbolSize: 8,
        lineStyle: {
          color: chartColors.current,
          width: 3,
          type: 'solid'
        },
        itemStyle: {
          color: chartColors.current,
          borderColor: '#ffffff',
          borderWidth: 2
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: chartColors.current + '60'
          }
        }
      },
      {
        name: '偏差程度',
        type: 'bar',
        yAxisIndex: 1,
        data: deviation.map((value, index) => ({
          value: value,
          itemStyle: {
            color: getDeviationColor(status[index])
          }
        })),
        barWidth: '40%',
        emphasis: {
          itemStyle: {
            opacity: 0.8
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

function getStatusColor(status: string) {
  switch (status) {
    case 'normal': return '#52c41a';
    case 'warning': return '#faad14';
    case 'danger': return '#ff4d4f';
    default: return '#6b7280';
  }
}

function getStatusText(status: string) {
  switch (status) {
    case 'normal': return '正常';
    case 'warning': return '警告';
    case 'danger': return '异常';
    default: return '未知';
  }
}

function getDeviationColor(status: string) {
  switch (status) {
    case 'normal': return chartColors.baseline;
    case 'warning': return chartColors.deviation;
    case 'danger': return chartColors.danger;
    default: return '#d9d9d9';
  }
}

onMounted(() => {
  if (props.data && props.data.length > 0) {
    updateChart();
  }
});
</script>

<template>
  <div ref="chartRef" class="w-full h-full min-h-80" />
</template>

<style scoped>
/* Chart container styling */
</style>