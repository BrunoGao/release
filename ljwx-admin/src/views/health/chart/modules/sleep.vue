<script setup lang="ts">
import { onUnmounted, watch } from 'vue';
import { $t } from '@/locales';
import { useEcharts } from '@/hooks/common/echarts';

defineOptions({
  name: 'SleepChart'
});

const props = withDefaults(
  defineProps<{
    data?: number[];
    timestamps?: string[];
    name?: string;
    lengend?: string;
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
    },
    formatter: params => {
      const [point] = params;
      const time = point.axisValue;
      const rate = point.data;
      let status = 'Normal';
      if (rate < 6) {
        status = 'Too Low';
      } else if (rate > 10) {
        status = 'Too High';
      }
      return `
        <div>
          <strong>Time:</strong> ${time}<br/>
          <strong>Sleep</strong> ${rate}<br/>
          <strong>Status:</strong> ${status}
        </div>
      `;
    }
  },
  legend: {
    data: [$t('page.health.chart.sleep')]
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
    min: 1, // 设置 Y 轴最小值
    max: 12 // 设置 Y 轴最大值
  },
  series: [
    {
      name: $t('page.health.chart.sleep'),
      type: 'line',
      smooth: true,
      data: props.data.map(item => item.rate),
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
              color: '#8e9dff'
            },
            {
              offset: 1,
              color: '#fff'
            }
          ]
        }
      },
      markLine: {
        data: [
          { yAxis: 6, name: $t('page.health.chart.lowThreshold'), lineStyle: { color: '#ff7f50' } },
          { yAxis: 10, name: $t('page.health.chart.highThreshold'), lineStyle: { color: '#ff7f50' } }
        ]
      },
      emphasis: {
        focus: 'series'
      },
      itemStyle: {
        color: params => {
          if (params.value > 10 || params.value < 6) {
            return '#ff0000'; // 超出正常范围显示红色
          }
          return '#8e9dff'; // 正常范围显示默认颜色
        }
      }
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
