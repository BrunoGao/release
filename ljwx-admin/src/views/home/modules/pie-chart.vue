<script setup lang="ts">
import { computed, watch } from 'vue';
import { $t } from '@/locales';
import { useEcharts } from '@/hooks/common/echarts';

defineOptions({ name: 'PieChart' });

const props = withDefaults(defineProps<{ data?: { name: string; value: number }[][] }>(), {
  data: () => [[], []]
});

const chartData = computed(() => props.data[0] || []);
const hasData = computed(() => chartData.value.length > 0);

const { domRef, updateOptions } = useEcharts(() => ({
  tooltip: { trigger: 'item', formatter: '{a}<br/>{b}: {c} ({d}%)' },
  title: { text: $t('page.home.alert.chartTitle'), left: 'center', top: 20, textStyle: { fontSize: 16 } },
  legend: { bottom: 10, left: 'center', itemGap: 10 },
  series: [
    {
      name: $t('page.health.alert.info.alertType'),
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      labelLine: { show: false },
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      data: []
    }
  ]
}));

function init() {
  updateOptions(opts => {
    (opts.series[0] as any).data = chartData.value;
    return opts;
  });
}

watch(
  () => props.data,
  () => {
    if (hasData.value) {
      init();
    }
  },
  { immediate: true, deep: true }
);
</script>

<template>
  <NCard :title="$t('page.home.analysis.name')" :bordered="false" class="card-wrapper">
    <template #header-extra>
      <a class="text-primary" href="./health/analysis">{{ $t('page.home.analysis.moreAnalysis') }}</a>
    </template>
    <div v-if="hasData" ref="domRef" class="h-360px overflow-hidden"></div>
    <div v-else class="h-360px flex items-center justify-center text-gray-400">
      {{ $t('common.noData') }}
    </div>
  </NCard>
</template>

<style scoped></style>
