<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { $t } from '@/locales';
import { useAuthStore } from '@/store/modules/auth';
import { useEcharts } from '@/hooks/common/echarts';
import { fetchGetUserHealthDataList } from '@/service/api/health';

defineOptions({ name: 'LineChart' });

const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

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
    data: ['心率']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  graphic: {
    elements: [
      {
        type: 'text',
        left: 'center',
        top: 'middle',
        style: {
          text: '',
          fontSize: 18,
          fill: '#999',
          opacity: 0
        },
        z: 100
      }
    ]
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: []
  },
  yAxis: {
    type: 'value',
    name: '心率(次/分)'
  },
  series: [
    {
      name: '心率',
      type: 'line',
      smooth: true,
      itemStyle: {
        color: '#8e9dff'
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
              color: '#8e9dff'
            },
            {
              offset: 1,
              color: '#fff'
            }
          ]
        }
      },
      data: []
    }
  ]
}));

const healthData = ref<{ heartrate: number[]; timestamps: string[] }>({ heartrate: [], timestamps: [] });

async function fetchHeartRateData() {
  try {
    const now = new Date();
    const startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const endDate = startDate + 86399999;

    const { data } = await fetchGetUserHealthDataList({
      departmentInfo: String(customerId),
      deviceSn: null,
      page: 1,
      pageSize: 100,
      startDate,
      endDate
    });

    const records = data?.records || [];
    if (!records.length) {
      updateOptions(opts => {
        opts.graphic.elements[0].style.text = '当天暂无健康数据';
        opts.graphic.elements[0].style.opacity = 1;
        return opts;
      });
      return;
    }

    const filtered = records.filter(r => r.heartRate > 0);
    if (filtered.length === 0) {
      updateOptions(opts => {
        opts.graphic.elements[0].style.text = '当天暂无心率数据';
        opts.graphic.elements[0].style.opacity = 1;
        return opts;
      });
      return;
    }

    healthData.value = {
      heartrate: filtered.map(r => r.heartRate),
      timestamps: filtered.map(r => new Date(r.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
    };

    updateOptions(opts => {
      opts.graphic.elements[0].style.opacity = 0;
      (opts.xAxis as any).data = healthData.value.timestamps;
      (opts.series[0] as any).data = healthData.value.heartrate;
      return opts;
    });
  } catch (error) {
    console.error('Failed to fetch health data:', error);
    updateOptions(opts => {
      opts.graphic.elements[0].style.text = '数据加载失败';
      opts.graphic.elements[0].style.opacity = 1;
      return opts;
    });
  }
}

onMounted(fetchHeartRateData);
</script>

<template>
  <NCard :title="$t('page.home.chart.name')" :bordered="false" class="card-wrapper">
    <template #header-extra>
      <a class="text-primary" href="./health/chart">{{ $t('page.home.chart.moreChart') }}</a>
    </template>
    <div ref="domRef" class="h-360px overflow-hidden"></div>
  </NCard>
</template>

<style scoped></style>
