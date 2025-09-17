<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';

interface Props {
  data: number[];
  timestamps: string[];
  title?: string;
  color?: string;
  yAxisName?: string;
  unit?: string;
}

const props = withDefaults(defineProps<Props>(), {
  title: '健康趋势',
  color: '#1890ff',
  yAxisName: '数值',
  unit: ''
});

const chartRef = ref<HTMLElement>();
const { domRef, updateOptions } = useEcharts(chartRef, {
  darkMode: false,
  size: { width: '100%', height: '100%' }
});

watch(
  [() => props.data, () => props.timestamps],
  ([newData, newTimestamps]) => {
    if (newData.length > 0 && newTimestamps.length > 0) {
      updateChart();
    }
  },
  { immediate: true }
);

function updateChart() {
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
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#374151'
      },
      formatter: function(params: any) {
        const point = params[0];
        return `
          <div style="padding: 8px;">
            <div style="font-weight: 600; margin-bottom: 4px;">
              ${point.name}
            </div>
            <div style="display: flex; align-items: center;">
              <span style="display: inline-block; width: 10px; height: 10px; background-color: ${props.color}; border-radius: 50%; margin-right: 8px;"></span>
              <span>${props.yAxisName}: ${point.value}${props.unit}</span>
            </div>
          </div>
        `;
      }
    },
    grid: {
      top: '15%',
      left: '5%',
      right: '5%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: props.timestamps,
      axisLine: {
        lineStyle: {
          color: '#e5e7eb'
        }
      },
      axisLabel: {
        color: '#6b7280',
        fontSize: 11,
        rotate: props.timestamps.length > 10 ? 45 : 0
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
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
    series: [
      {
        data: props.data,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          color: props.color,
          width: 3
        },
        itemStyle: {
          color: props.color,
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
              {
                offset: 0,
                color: props.color + '40'
              },
              {
                offset: 1,
                color: props.color + '10'
              }
            ]
          }
        },
        emphasis: {
          itemStyle: {
            color: props.color,
            borderColor: '#ffffff',
            borderWidth: 3,
            shadowBlur: 10,
            shadowColor: props.color + '60'
          }
        }
      }
    ],
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut'
  };
  
  updateOptions(option);
}

onMounted(() => {
  if (props.data.length > 0 && props.timestamps.length > 0) {
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