<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';

interface ComparisonData {
  name: string;
  baseline: number;
  current: number;
  target?: number;
}

interface Props {
  data: ComparisonData[];
  title?: string;
}

const props = withDefaults(defineProps<Props>(), {
  title: '健康指标对比分析'
});

const chartRef = ref<HTMLElement>();
const { domRef, updateOptions } = useEcharts(chartRef, {
  darkMode: false,
  size: { width: '100%', height: '100%' }
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
  const categories = props.data.map(item => item.name);
  const baselineData = props.data.map(item => item.baseline);
  const currentData = props.data.map(item => item.current);
  const targetData = props.data.map(item => item.target || null);

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
        type: 'shadow'
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
        
        params.forEach((param: any) => {
          if (param.value !== null) {
            result += `
              <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="display: inline-block; width: 10px; height: 10px; background-color: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>
                <span>${param.seriesName}: ${param.value}</span>
              </div>
            `;
          }
        });
        
        result += `</div>`;
        return result;
      }
    },
    legend: {
      data: ['基线值', '当前值', '目标值'],
      top: '8%',
      textStyle: {
        color: '#6b7280'
      }
    },
    grid: {
      top: '20%',
      left: '5%',
      right: '5%',
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
        interval: 0,
        rotate: categories.length > 6 ? 45 : 0
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
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
    series: [
      {
        name: '基线值',
        type: 'bar',
        data: baselineData,
        itemStyle: {
          color: '#94a3b8',
          borderRadius: [4, 4, 0, 0]
        },
        emphasis: {
          itemStyle: {
            color: '#64748b'
          }
        }
      },
      {
        name: '当前值',
        type: 'bar',
        data: currentData,
        itemStyle: {
          color: '#3b82f6',
          borderRadius: [4, 4, 0, 0]
        },
        emphasis: {
          itemStyle: {
            color: '#2563eb'
          }
        }
      },
      {
        name: '目标值',
        type: 'line',
        data: targetData,
        lineStyle: {
          color: '#10b981',
          width: 2,
          type: 'dashed'
        },
        itemStyle: {
          color: '#10b981'
        },
        symbol: 'diamond',
        symbolSize: 8,
        emphasis: {
          itemStyle: {
            color: '#059669',
            shadowBlur: 10,
            shadowColor: '#10b98160'
          }
        }
      }
    ],
    animation: true,
    animationDuration: 1200,
    animationEasing: 'elasticOut',
    animationDelay: function(idx: number) {
      return idx * 100;
    }
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
  <div ref="chartRef" class="w-full h-full min-h-80" />
</template>

<style scoped>
/* Chart container styling */
</style>