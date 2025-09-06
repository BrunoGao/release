<script setup lang="ts">
import { watch } from 'vue';
import { $t } from '@/locales';

import { useEcharts } from '@/hooks/common/echarts';

defineOptions({
  name: 'PressureHighChart'
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
    data: [$t('page.health.chart.pressureHigh')]
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
    data: props.timestamps
  },
  yAxis: {
    type: 'value',
    min: 80, // 设置 Y 轴最小值
    max: 160 // 设置 Y 轴最大值
  },
  series: [
    {
      color: '#ff4500', // 温度使用的颜色，例如暗橙色，体现出温暖的感觉
      name: $t('page.health.chart.pressureHigh'),
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
              color: '#ff4500' // 温度渐变起始颜色
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
      data: props.data
    }
  ]
}));

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

init();
</script>

<template>
  <NCard :bordered="false" class="card-wrapper">
    <div ref="domRef" class="h-600px overflow-hidden"></div>
  </NCard>
</template>

<style scoped></style>
