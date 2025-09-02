<script setup lang="ts">
import { $t } from '@/locales';

import { useEcharts } from '@/hooks/common/echarts';

defineOptions({
  name: 'PieChart'
});

const props = withDefaults(
  defineProps<{
    data?: { name: string; value: number }[][];
  }>(),
  {
    data: () => [[], []]
  }
);

const { domRef, updateOptions } = useEcharts(() => ({
  tooltip: {
    trigger: 'item'
  },
  legend: {
    bottom: '1%',
    left: 'center',
    itemStyle: {
      borderWidth: 0
    }
  },
  series: [
    {
      color: ['#5da8ff', '#8e9dff', '#fedc69', '#26deca'],
      name: $t('page.health.alert.info.alertType'),
      type: 'pie',
      radius: ['65%', '75%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 1
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: '12'
        }
      },
      labelLine: {
        show: false
      },
      data: props.data[0] as { name: string; value: number }[]
    },
    {
      color: ['#ff7f50', '#87cefa', '#da70d6', '#32cd32'],
      name: $t('page.health.alert.info.alertStatus'),
      type: 'pie',
      radius: ['45%', '55%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 1
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: '12'
        }
      },
      labelLine: {
        show: false
      },
      data: props.data[1] as { name: string; value: number }[]
    },
    {
      color: ['#ff6347', '#4682b4', '#9acd32', '#ff69b4'],
      name: $t('page.health.alert.info.severityLevel'),
      type: 'pie',
      radius: ['25%', '35%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 1
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: '12'
        }
      },
      labelLine: {
        show: false
      },
      data: props.data[2] as { name: string; value: number }[]
    }
  ]
}));

async function init() {
  await new Promise(resolve => {
    setTimeout(resolve, 1000);
  });

  updateOptions(opts => {
    opts.series[0].data = props.data[0];
    opts.series[1].data = props.data[1];
    opts.series[2].data = props.data[2];

    return opts;
  });
}

// init
init();
</script>

<template>
  <NCard :bordered="false" class="card-wrapper">
    <div ref="domRef" class="h-360px overflow-hidden"></div>
  </NCard>
</template>

<style scoped></style>
