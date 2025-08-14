<script setup lang="ts">
import { watch } from 'vue';
import { $t } from '@/locales';
import { useEcharts } from '@/hooks/common/echarts';

defineOptions({
  name: 'TemperatureChart'
});

const props = withDefaults(
  defineProps<{
    data?: number[];
    timestamps?: string[];
  }>(),
  {
    data: () => [],
    timestamps: () => []
  }
);

const { domRef, updateOptions } = useEcharts(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'cross',
      label: {
        backgroundColor: '#6a7985'
      }
    }
  },
  legend: {
    data: [$t('page.health.chart.temperature')]
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: [] as string[]
  },
  yAxis: {
    type: 'value',
    min: 30, // 设置 Y 轴最小值
    max: 41 // 设置 Y 轴最大值
  },
  series: [
    {
      color: '#ff8c00', // 温度使用的颜色，例如暗橙色，体现出温暖的感觉
      name: $t('page.health.chart.temperature'),
      type: 'line',
      smooth: true,
      stack: 'Total',
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            {
              offset: 0.25,
              color: '#ff8c00' // 温度渐变起始颜色
            },
            {
              offset: 1,
              color: '#fff' // 渐变结束颜色
            }
          ]
        }
      },
      emphasis: {
        focus: 'series'
      },
      data: [] as number[]
    }
  ]
}));
async function init() {
  await new Promise(resolve => {
    setTimeout(resolve, 1000);
  });

  updateOptions(opts => {
    opts.xAxis.data = props.timestamps;
    opts.series[0].data = props.data;

    return opts;
  });
}
watch(
  () => props.data,
  newData => {
    updateOptions(opts => {
      opts.series[0].data = newData;
      return opts;
    });
  },
  { immediate: true }
);

watch(
  () => props.timestamps,
  newTimestamps => {
    updateOptions(opts => {
      opts.xAxis.data = newTimestamps;
      return opts;
    });
  },
  { immediate: true }
);

init();
</script>

<template>
  <NCard :bordered="false" class="chart-container card-wrapper">
    <div ref="domRef" class="h-600px overflow-hidden"></div>
  </NCard>
</template>

<style scoped>
.chart-container {
  height: 600px; /* Set your desired height */
}
</style>
