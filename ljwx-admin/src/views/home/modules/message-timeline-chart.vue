<script setup lang="ts">
import { computed, nextTick, onMounted, watch } from 'vue';
import { useEcharts } from '@/hooks/common/echarts';
import { useThemeStore } from '@/store/modules/theme';

defineOptions({ name: 'MessageTimelineChart' });

interface Message {
  id: number;
  messageType: string;
  messageStatus: string;
  sentTime: number;
  receiverName?: string;
  content?: string;
}

const props = withDefaults(defineProps<{ messageInfo?: any }>(), {
  messageInfo: () => ({})
});

const themeStore = useThemeStore();

const messages = computed(() => {
  const messagesArray = props.messageInfo?.messages || [];
  return Array.isArray(messagesArray) ? messagesArray : [];
});

const hasData = computed(() => messages.value.length > 0);

// 中文翻译映射
const translations = {
  messageType: {
    system: '系统消息',
    alert: '告警消息',
    notification: '通知消息',
    reminder: '提醒消息',
    warning: '警告消息',
    info: '信息消息',
    announcement: '公告消息',
    job: '作业指引',
    task: '任务管理',
    作业指引消息: '作业指引',
    任务管理消息: '任务管理',
    公告消息: '公告',
    '1': '一般',
    '2': '重要'
  },
  messageStatus: {
    sent: '已发送',
    delivered: '已送达',
    read: '已读',
    failed: '发送失败',
    pending: '待发送'
  }
};

// 使用系统主题色彩 - 更专业的配色方案
const colors = computed(() => ({
  messageType: {
    system: '#34495e',           // 系统-深灰
    alert: '#e74c3c',           // 告警-红色
    notification: '#f39c12',     // 通知-橙色
    reminder: '#3498db',        // 提醒-蓝色
    warning: '#e67e22',         // 警告-深橙
    info: '#1abc9c',            // 信息-青色
    announcement: '#9b59b6',     // 公告-紫色
    job: '#2c3e50',             // 作业-深蓝灰
    task: '#27ae60',            // 任务-绿色
    作业指引消息: '#2c3e50',
    任务管理消息: '#27ae60',
    公告消息: '#9b59b6',
    '1': '#27ae60',
    '2': '#f39c12'
  },
  messageStatus: {
    sent: '#27ae60',      // 已发送-绿色
    delivered: '#3498db', // 已送达-蓝色
    read: '#95a5a6',      // 已读-灰色
    failed: '#e74c3c',    // 失败-红色
    pending: '#f39c12'    // 待发送-橙色
  }
}));

// 处理消息时序数据 - 修复数量显示问题
function processMessageTimelineData() {
  if (!hasData.value) return { dates: [], series: [] };

  // 生成最近14天的日期序列
  const dates: string[] = [];
  const dailyData = new Map<string, { messageType: Map<string, number>; messageStatus: Map<string, number> }>();

  const today = new Date();
  for (let i = 13; i >= 0; i -= 1) { // 最近14天
    const date = new Date(today.getTime() - i * 24 * 60 * 60 * 1000);
    const dateStr = `${date.getMonth() + 1}/${date.getDate()}`;
    dates.push(dateStr);
    dailyData.set(dateStr, {
      messageType: new Map(),
      messageStatus: new Map()
    });
  }

  // 统计真实数据
  messages.value.forEach((message: Message) => {
    const messageDate = new Date(message.sentTime);
    const dateStr = `${messageDate.getMonth() + 1}/${messageDate.getDate()}`;

    if (dailyData.has(dateStr)) {
      const dayData = dailyData.get(dateStr)!;

      // 统计消息类型
      const messageType = message.messageType || '其他';
      dayData.messageType.set(messageType, (dayData.messageType.get(messageType) || 0) + 1);

      // 统计消息状态
      const messageStatus = message.messageStatus || 'sent';
      dayData.messageStatus.set(messageStatus, (dayData.messageStatus.get(messageStatus) || 0) + 1);
    }
  });

  const series: any[] = [];

  // 消息类型系列（折线图）
  const allMessageTypes = [...new Set(messages.value.map((m: Message) => m.messageType || '其他'))];
  allMessageTypes.forEach(type => {
    const data = dates.map(date => dailyData.get(date)?.messageType.get(type) || 0);
    const total = data.reduce((sum, val) => sum + val, 0);

    if (total > 0) { // 只显示有数据的系列
      series.push({
        name: translations.messageType[type as keyof typeof translations.messageType] || type,
        type: 'line',
        data,
        itemStyle: { color: colors.value.messageType[type as keyof typeof colors.value.messageType] || themeStore.themeColor },
        smooth: true,
        symbol: 'circle',
        symbolSize: 4
      });
    }
  });

  // 消息状态系列（面积图）
  const allMessageStatuses = [...new Set(messages.value.map((m: Message) => m.messageStatus || 'sent'))];
  allMessageStatuses.forEach(status => {
    const data = dates.map(date => dailyData.get(date)?.messageStatus.get(status) || 0);
    const total = data.reduce((sum, val) => sum + val, 0);

    if (total > 0) { // 只显示有数据的系列
      series.push({
        name: translations.messageStatus[status as keyof typeof translations.messageStatus] || status,
        type: 'line',
        stack: 'messageStatus',
        data,
        itemStyle: { color: colors.value.messageStatus[status as keyof typeof colors.value.messageStatus] || '#bdc3c7' },
        areaStyle: {
          opacity: 0.3
        },
        smooth: true,
        symbol: 'circle',
        symbolSize: 3
      });
    }
  });

  return { dates, series };
}

const { domRef, updateOptions } = useEcharts(() => ({
  title: { text: '消息时序统计', left: 'center', textStyle: { fontSize: 16, color: '#333' } },
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'cross' },
    backgroundColor: 'rgba(255,255,255,0.9)',
    borderColor: '#ccc',
    textStyle: { color: '#333' }
  },
  legend: { bottom: 5, type: 'scroll', textStyle: { fontSize: 11 } },
  grid: { left: '8%', right: '8%', bottom: '20%', top: '15%', containLabel: true },
  xAxis: {
    type: 'category',
    data: [],
    axisLabel: { fontSize: 10, color: '#666' },
    axisLine: { lineStyle: { color: '#e0e0e0' } }
  },
  yAxis: {
    type: 'value',
    name: '数量',
    nameTextStyle: { fontSize: 10, color: '#666' },
    axisLabel: { fontSize: 10, color: '#666' },
    axisLine: { lineStyle: { color: '#e0e0e0' } },
    splitLine: { lineStyle: { color: '#f0f0f0' } }
  },
  series: []
}));

function renderChart() {
  if (!hasData.value) {
    updateOptions(() => ({
      title: {
        text: '消息时序统计',
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
              text: '暂无消息数据',
              fontSize: 16,
              fill: '#999',
              textAlign: 'center'
            }
          }
        ]
      },
      xAxis: { type: 'category', data: [] },
      yAxis: { type: 'value', name: '消息数量' },
      series: []
    }));
    return;
  }

  const { dates, series } = processMessageTimelineData();
  const totalMessages = messages.value.length;

  // 计算时间范围
  const startDate = dates[0];
  const endDate = dates[dates.length - 1];
  const timeRange = startDate === endDate ? startDate : `${startDate}-${endDate}`;

  updateOptions(() => ({
    title: {
      text: '消息时序统计',
      left: 'center',
      textStyle: { fontSize: 18, color: '#2c3e50', fontWeight: 'bold' },
      subtext: `共 ${totalMessages} 条消息 | 时间范围: ${timeRange}`,
      subtextStyle: { fontSize: 12, color: '#7f8c8d' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(255,255,255,0.9)',
      borderColor: '#ccc',
      textStyle: { color: '#333' }
    },
    legend: { bottom: 5, type: 'scroll', textStyle: { fontSize: 11 } },
    grid: { left: '8%', right: '8%', bottom: '20%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { fontSize: 10, color: '#666' },
      axisLine: { lineStyle: { color: '#e0e0e0' } }
    },
    yAxis: {
      type: 'value',
      name: '数量',
      nameTextStyle: { fontSize: 10, color: '#666' },
      axisLabel: { fontSize: 10, color: '#666' },
      axisLine: { lineStyle: { color: '#e0e0e0' } },
      splitLine: { lineStyle: { color: '#f0f0f0' } }
    },
    series,
    graphic: undefined
  }));
}

watch(
  () => [props.messageInfo, themeStore.themeColor],
  () => renderChart(),
  { immediate: true, deep: true }
);

onMounted(async () => {
  await nextTick();
  renderChart();
});
</script>

<template>
  <NCard title="消息分析" size="small" :bordered="false" class="h-360px">
    <div ref="domRef" class="h-full w-full"></div>
  </NCard>
</template>

<style scoped></style>
