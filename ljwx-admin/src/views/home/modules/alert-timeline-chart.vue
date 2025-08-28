<script setup lang="ts">
import { computed, nextTick, onMounted, watch } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';
import { useThemeStore } from '@/store/modules/theme';

defineOptions({ name: 'AlertTimelineChart' });

interface Alert {
  id: number;
  alertType: string;
  alertStatus: string;
  severityLevel: string;
  alertTimestamp: number;
  userName?: string;
  departmentInfo?: string;
}

const props = withDefaults(defineProps<{ alertInfo?: any }>(), {
  alertInfo: () => ({})
});

const themeStore = useThemeStore();

const alerts = computed(() => {
  const alertsArray = props.alertInfo?.alerts || [];
  return Array.isArray(alertsArray) ? alertsArray : [];
});

const hasData = computed(() => alerts.value.length > 0);

// 中文翻译映射
const translations = {
  alertType: {
    heart_rate: '心率异常',
    blood_pressure: '血压异常',
    temperature: '体温异常',
    blood_oxygen: '血氧异常',
    stress: '压力异常',
    sleep: '睡眠异常',
    fall_down: '跌倒告警',
    one_key_alarm: '一键告警',
    作业指引消息: '作业指引',
    任务管理消息: '任务管理',
    公告消息: '公告',
    '1': '低级',
    '2': '中级'
  },
  alertStatus: {
    pending: '待处理',
    responded: '已响应',
    resolved: '已解决'
  },
  severityLevel: {
    low: '低风险',
    medium: '中风险',
    high: '高风险',
    critical: '危急',
    '1': '低级',
    '2': '中级'
  }
};

// 使用系统主题色彩 - 更专业的配色方案
const colors = computed(() => ({
  alertType: {
    heart_rate: '#e74c3c', // 心率-红色
    blood_pressure: '#9b59b6', // 血压-紫色
    temperature: '#f39c12', // 体温-橙色
    blood_oxygen: '#3498db', // 血氧-蓝色
    stress: '#e67e22', // 压力-深橙
    sleep: '#2c3e50', // 睡眠-深蓝灰
    fall_down: '#c0392b', // 跌倒-深红
    one_key_alarm: '#8e44ad', // 一键告警-深紫
    作业指引消息: themeStore.themeColor,
    任务管理消息: '#27ae60',
    公告消息: '#f1c40f',
    '1': '#27ae60',
    '2': '#f39c12'
  },
  alertStatus: {
    pending: '#f39c12',
    responded: '#3498db',
    resolved: '#27ae60'
  },
  severityLevel: {
    low: '#27ae60', // 低风险-绿色
    medium: '#f39c12', // 中风险-橙色
    high: '#e74c3c', // 高风险-红色
    critical: '#8e44ad', // 危急-紫色
    '1': '#27ae60',
    '2': '#f39c12'
  }
}));

// 处理时序数据 - 更专业的数据处理
function processTimelineData() {
  if (!hasData.value) return { dates: [], series: [] };

  // 生成最近14天的日期序列
  const dates: string[] = [];
  const dailyData = new Map<string, { alertType: Map<string, number>; severityLevel: Map<string, number> }>();

  const today = new Date();
  for (let i = 13; i >= 0; i -= 1) {
    const date = new Date(today.getTime() - i * 24 * 60 * 60 * 1000);
    const dateStr = `${date.getMonth() + 1}/${date.getDate()}`;
    dates.push(dateStr);
    dailyData.set(dateStr, {
      alertType: new Map(),
      severityLevel: new Map()
    });
  }

  // 统计真实数据
  alerts.value.forEach((alert: Alert) => {
    const alertDate = new Date(alert.alertTimestamp);
    const dateStr = `${alertDate.getMonth() + 1}/${alertDate.getDate()}`;

    if (dailyData.has(dateStr)) {
      const dayData = dailyData.get(dateStr)!;

      const alertType = alert.alertType || '其他';
      dayData.alertType.set(alertType, (dayData.alertType.get(alertType) || 0) + 1);

      const severity = alert.severityLevel || '1';
      dayData.severityLevel.set(severity, (dayData.severityLevel.get(severity) || 0) + 1);
    }
  });

  const series: any[] = [];

  // 告警类型系列（折线图）- 按重要性排序
  const allAlertTypes = [...new Set(alerts.value.map((a: Alert) => a.alertType || '其他'))].sort((a, b) => {
    const priority: Record<string, number> = { one_key_alarm: 1, fall_down: 2, heart_rate: 3, blood_pressure: 4, sleep: 5 };
    return (priority[a] || 99) - (priority[b] || 99);
  });

  allAlertTypes.forEach(type => {
    const data = dates.map(date => dailyData.get(date)?.alertType.get(type) || 0);
    const total = data.reduce((sum, val) => sum + val, 0);

    if (total > 0) {
      series.push({
        name: translations.alertType[type as keyof typeof translations.alertType] || type,
        type: 'line',
        data,
        itemStyle: { color: colors.value.alertType[type as keyof typeof colors.value.alertType] || '#95a5a6' },
        lineStyle: { width: 3 },
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        emphasis: {
          focus: 'series',
          lineStyle: { width: 4 },
          symbolSize: 8
        }
      });
    }
  });

  // 严重程度系列（柱状图）- 按严重程度排序
  const severityOrder = ['critical', 'high', 'medium', 'low', '2', '1'];
  const allSeverityLevels = [...new Set(alerts.value.map((a: Alert) => a.severityLevel || '1'))].sort(
    (a, b) => severityOrder.indexOf(a) - severityOrder.indexOf(b)
  );

  allSeverityLevels.forEach(level => {
    const data = dates.map(date => dailyData.get(date)?.severityLevel.get(level) || 0);
    const total = data.reduce((sum, val) => sum + val, 0);

    if (total > 0) {
      series.push({
        name: translations.severityLevel[level as keyof typeof translations.severityLevel] || level,
        type: 'bar',
        data,
        itemStyle: {
          color: colors.value.severityLevel[level as keyof typeof colors.value.severityLevel] || '#95a5a6',
          borderRadius: [2, 2, 0, 0]
        },
        barWidth: '50%',
        emphasis: {
          focus: 'series',
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' }
        }
      });
    }
  });

  return { dates, series };
}

const { domRef, updateOptions } = useEcharts(() => ({
  title: {
    text: '告警时序统计',
    left: 'center',
    textStyle: { fontSize: 18, color: '#2c3e50', fontWeight: 'bold' },
    subtextStyle: { fontSize: 12, color: '#7f8c8d' }
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'cross',
      crossStyle: { color: '#999' }
    },
    backgroundColor: 'rgba(255,255,255,0.95)',
    borderColor: '#ddd',
    borderWidth: 1,
    textStyle: { color: '#333', fontSize: 12 },
    padding: [10, 15],
    extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-radius: 6px;'
  },
  legend: {
    bottom: 8,
    type: 'scroll',
    textStyle: { fontSize: 11, color: '#555' },
    itemGap: 15,
    icon: 'roundRect'
  },
  grid: {
    left: '10%',
    right: '10%',
    bottom: '22%',
    top: '18%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: [],
    axisLabel: {
      fontSize: 11,
      color: '#666',
      interval: 0,
      rotate: 45
    },
    axisLine: { lineStyle: { color: '#e0e0e0', width: 1 } },
    axisTick: { show: false }
  },
  yAxis: {
    type: 'value',
    name: '告警数量',
    nameTextStyle: { fontSize: 12, color: '#666', padding: [0, 0, 0, 20] },
    axisLabel: { fontSize: 11, color: '#666' },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: {
      lineStyle: {
        color: '#f5f5f5',
        type: 'dashed'
      }
    }
  },
  series: []
}));

function renderChart() {
  if (!hasData.value) {
    updateOptions(() => ({
      title: {
        text: '告警时序统计',
        left: 'center',
        textStyle: { fontSize: 18, color: '#2c3e50', fontWeight: 'bold' },
        subtext: '暂无数据',
        subtextStyle: { fontSize: 12, color: '#999' }
      },
      graphic: {
        elements: [
          {
            type: 'text',
            left: 'center',
            top: 'middle',
            style: {
              text: '暂无告警数据',
              fontSize: 16,
              fill: '#999',
              textAlign: 'center'
            }
          }
        ]
      },
      xAxis: { type: 'category', data: [] },
      yAxis: { type: 'value', name: '告警数量' },
      series: []
    }));
    return;
  }

  const { dates, series } = processTimelineData();
  const totalAlerts = alerts.value.length;

  // 计算时间范围
  const startDate = dates[0];
  const endDate = dates[dates.length - 1];
  const timeRange = startDate === endDate ? startDate : `${startDate}-${endDate}`;

  updateOptions(() => ({
    title: {
      text: '告警时序统计',
      left: 'center',
      textStyle: { fontSize: 18, color: '#2c3e50', fontWeight: 'bold' },
      subtext: `共 ${totalAlerts} 条告警 | 时间范围: ${timeRange}`,
      subtextStyle: { fontSize: 12, color: '#7f8c8d' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        crossStyle: { color: '#999' }
      },
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#ddd',
      borderWidth: 1,
      textStyle: { color: '#333', fontSize: 12 },
      padding: [10, 15],
      extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-radius: 6px;'
    },
    legend: {
      bottom: 8,
      type: 'scroll',
      textStyle: { fontSize: 11, color: '#555' },
      itemGap: 15,
      icon: 'roundRect'
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '22%',
      top: '18%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        fontSize: 11,
        color: '#666',
        interval: 0,
        rotate: 45
      },
      axisLine: { lineStyle: { color: '#e0e0e0', width: 1 } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      name: '告警数量',
      nameTextStyle: { fontSize: 12, color: '#666', padding: [0, 0, 0, 20] },
      axisLabel: { fontSize: 11, color: '#666' },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: {
        lineStyle: {
          color: '#f5f5f5',
          type: 'dashed'
        }
      }
    },
    series,
    graphic: undefined
  }));
}

watch(
  () => [props.alertInfo, themeStore.themeColor],
  () => renderChart(),
  { immediate: true, deep: true }
);

onMounted(async () => {
  await nextTick();
  renderChart();
});
</script>

<template>
  <NCard title="告警分析" size="small" :bordered="false" class="h-360px">
    <div ref="domRef" class="h-full w-full"></div>
  </NCard>
</template>

<style scoped></style>
