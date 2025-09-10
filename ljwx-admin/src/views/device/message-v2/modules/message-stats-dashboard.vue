<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { 
  NCard, NStatistic, NGrid, NGridItem, NSpin, NEmpty, NTabs, NTabPane,
  NSpace, NButton, NIcon, NDatePicker, NSelect, NAlert, NProgress,
  NTable, NTag
} from 'naive-ui';
import { 
  StatsChartOutline, TrendingUpOutline, TimeOutline, SpeedometerOutline,
  BarChartOutline, PieChartOutline, CalendarOutline, RefreshOutline
} from '@vicons/ionicons5';
import { 
  fetchGetMessageStatistics, 
  fetchGetChannelStatistics,
  fetchGetResponseTimeStatistics,
  fetchGetMessageTypeDistribution
} from '@/service/api/health/device-message-v2';
import type { DataTableColumns } from 'naive-ui';

interface Props {
  customerId?: number;
  orgId?: number;
  messageStats?: Api.Health.MessageStatisticsV2 | null;
  channelStats?: Record<string, any> | null;
}

const props = defineProps<Props>();

const loading = ref(false);
const activeTab = ref('overview');
const dateRange = ref<[number, number]>([
  Date.now() - 7 * 24 * 60 * 60 * 1000, // 7天前
  Date.now()
]);

// 本地统计数据（可能与props传入的不同时间范围）
const localStats = ref<Api.Health.MessageStatisticsV2 | null>(null);
const localChannelStats = ref<Record<string, any> | null>(null);
const responseTimeStats = ref<Record<string, any> | null>(null);
const typeDistribution = ref<Record<string, number> | null>(null);

// 当前使用的统计数据（优先使用本地数据）
const currentStats = computed(() => localStats.value || props.messageStats);
const currentChannelStats = computed(() => localChannelStats.value || props.channelStats);

// 概览统计
const overviewStats = computed(() => {
  if (!currentStats.value) return null;
  
  const stats = currentStats.value;
  return {
    total: stats.totalMessages,
    sent: stats.sentMessages,
    received: stats.receivedMessages,
    acknowledged: stats.acknowledgedMessages,
    failed: stats.failedMessages,
    expired: stats.expiredMessages,
    pending: stats.pendingMessages,
    sendSuccessRate: stats.sendSuccessRate,
    receiveSuccessRate: stats.receiveSuccessRate,
    acknowledgeSuccessRate: stats.acknowledgeSuccessRate,
    averageResponseTime: stats.averageResponseTime
  };
});

// 消息类型统计
const messageTypeStats = computed(() => {
  if (!currentStats.value?.messageTypeStats) return [];
  
  return Object.entries(currentStats.value.messageTypeStats).map(([type, count]) => ({
    type,
    count,
    percentage: currentStats.value!.totalMessages > 0 
      ? (count / currentStats.value!.totalMessages * 100).toFixed(1)
      : '0'
  }));
});

// 紧急程度统计
const urgencyStats = computed(() => {
  if (!currentStats.value?.urgencyStats) return [];
  
  const urgencyOrder = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
  return urgencyOrder.map(urgency => ({
    urgency,
    count: currentStats.value!.urgencyStats[urgency] || 0,
    percentage: currentStats.value!.totalMessages > 0 
      ? ((currentStats.value!.urgencyStats[urgency] || 0) / currentStats.value!.totalMessages * 100).toFixed(1)
      : '0'
  })).filter(item => item.count > 0);
});

// 渠道统计表格列
const channelColumns: DataTableColumns<any> = [
  {
    title: '渠道',
    key: 'channel',
    render(row) {
      const channelColors = {
        'DEVICE': 'info',
        'SMS': 'success',
        'EMAIL': 'warning', 
        'PUSH': 'error',
        'WECHAT': 'success'
      } as const;
      return h(NTag, { 
        type: channelColors[row.channel as keyof typeof channelColors] || 'default',
        size: 'small' 
      }, () => row.channel);
    }
  },
  {
    title: '总消息数',
    key: 'total',
    sorter: (a, b) => a.total - b.total
  },
  {
    title: '已送达',
    key: 'delivered',
    render(row) {
      return h('div', { class: 'flex items-center gap-4px' }, [
        h('span', row.delivered),
        h(NProgress, {
          type: 'line',
          percentage: row.total > 0 ? (row.delivered / row.total) * 100 : 0,
          color: '#52c41a',
          height: 6,
          showIndicator: false,
          style: { width: '60px' }
        })
      ]);
    }
  },
  {
    title: '成功率',
    key: 'successRate',
    render(row) {
      const rate = row.total > 0 ? (row.delivered / row.total * 100).toFixed(1) : '0';
      return h('span', { 
        class: `font-medium ${Number(rate) >= 90 ? 'text-green-600' : Number(rate) >= 70 ? 'text-yellow-600' : 'text-red-600'}`
      }, `${rate}%`);
    },
    sorter: (a, b) => {
      const rateA = a.total > 0 ? a.delivered / a.total : 0;
      const rateB = b.total > 0 ? b.delivered / b.total : 0;
      return rateA - rateB;
    }
  },
  {
    title: '平均响应时间',
    key: 'avgResponseTime',
    render(row) {
      return formatDuration(row.avgResponseTime || 0);
    }
  }
];

// 渠道统计数据
const channelTableData = computed(() => {
  if (!currentChannelStats.value) return [];
  
  return Object.entries(currentChannelStats.value).map(([channel, stats]: [string, any]) => ({
    channel,
    total: stats.totalMessages || 0,
    delivered: stats.deliveredMessages || 0,
    acknowledged: stats.acknowledgedMessages || 0,
    failed: stats.failedMessages || 0,
    avgResponseTime: stats.averageDeliveryTime || 0,
    successRate: stats.successRate || 0
  }));
});

// 时间格式化
function formatDuration(ms: number) {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${(ms / 60000).toFixed(1)}min`;
  return `${(ms / 3600000).toFixed(1)}h`;
}

// 获取紧急程度颜色
function getUrgencyColor(urgency: string) {
  switch (urgency) {
    case 'CRITICAL': return '#ff4d4f';
    case 'HIGH': return '#faad14';
    case 'MEDIUM': return '#1890ff';
    case 'LOW': return '#52c41a';
    default: return '#d9d9d9';
  }
}

// 获取消息类型颜色
function getMessageTypeColor(type: string) {
  switch (type) {
    case 'EMERGENCY': return '#ff4d4f';
    case 'ALERT': return '#faad14';
    case 'WARNING': return '#faad14';
    case 'NOTIFICATION': return '#1890ff';
    case 'INFO': return '#52c41a';
    default: return '#d9d9d9';
  }
}

// 加载统计数据
async function loadStats() {
  if (!props.customerId) return;
  
  loading.value = true;
  const [startTime, endTime] = dateRange.value;
  
  try {
    // 加载基础统计
    const { error: statsError, data: stats } = await fetchGetMessageStatistics({
      customerId: props.customerId,
      orgId: props.orgId,
      startTime: new Date(startTime).toISOString(),
      endTime: new Date(endTime).toISOString()
    });
    
    if (!statsError && stats) {
      localStats.value = stats;
    }
    
    // 加载渠道统计
    const { error: channelError, data: channelData } = await fetchGetChannelStatistics({
      customerId: props.customerId,
      startTime: new Date(startTime).toISOString(),
      endTime: new Date(endTime).toISOString()
    });
    
    if (!channelError && channelData) {
      localChannelStats.value = channelData;
    }
    
    // 加载响应时间统计
    const { error: responseError, data: responseData } = await fetchGetResponseTimeStatistics({
      customerId: props.customerId,
      startTime: new Date(startTime).toISOString(),
      endTime: new Date(endTime).toISOString()
    });
    
    if (!responseError && responseData) {
      responseTimeStats.value = responseData;
    }
    
    // 加载消息类型分布
    const { error: typeError, data: typeData } = await fetchGetMessageTypeDistribution({
      customerId: props.customerId,
      startTime: new Date(startTime).toISOString(),
      endTime: new Date(endTime).toISOString()
    });
    
    if (!typeError && typeData) {
      typeDistribution.value = typeData;
    }
    
  } catch (error) {
    console.error('加载统计数据失败:', error);
  } finally {
    loading.value = false;
  }
}

// 监听时间范围变化
watch(dateRange, () => {
  loadStats();
});

onMounted(() => {
  if (props.customerId) {
    loadStats();
  }
});
</script>

<template>
  <div class="space-y-16px">
    <!-- 时间范围选择 -->
    <NSpace align="center" justify="space-between">
      <div class="flex items-center gap-8px">
        <NIcon :component="CalendarOutline" />
        <span class="text-sm font-medium">时间范围:</span>
        <NDatePicker
          v-model:value="dateRange"
          type="datetimerange"
          clearable
          size="small"
          :shortcuts="{
            '最近1小时': [Date.now() - 60 * 60 * 1000, Date.now()],
            '最近24小时': [Date.now() - 24 * 60 * 60 * 1000, Date.now()],
            '最近7天': [Date.now() - 7 * 24 * 60 * 60 * 1000, Date.now()],
            '最近30天': [Date.now() - 30 * 24 * 60 * 60 * 1000, Date.now()]
          }"
        />
      </div>
      
      <NButton 
        type="primary" 
        quaternary 
        size="small"
        :loading="loading"
        @click="loadStats"
      >
        <template #icon>
          <NIcon :component="RefreshOutline" />
        </template>
        刷新数据
      </NButton>
    </NSpace>

    <NSpin :show="loading">
      <NTabs v-model:value="activeTab" type="line">
        <!-- 概览统计 -->
        <NTabPane name="overview" tab="概览统计">
          <div class="space-y-16px">
            <div v-if="overviewStats">
              <!-- 核心指标 -->
              <NGrid :cols="4" :x-gap="16" :y-gap="16" class="mb-24px">
                <NGridItem>
                  <NStatistic 
                    label="总消息数" 
                    :value="overviewStats.total"
                    :value-style="{ color: '#1890ff' }"
                  >
                    <template #prefix>
                      <NIcon :component="StatsChartOutline" />
                    </template>
                  </NStatistic>
                </NGridItem>
                <NGridItem>
                  <NStatistic 
                    label="发送成功率" 
                    :value="overviewStats.sendSuccessRate"
                    suffix="%"
                    :precision="1"
                    :value-style="{ 
                      color: overviewStats.sendSuccessRate >= 90 ? '#52c41a' : 
                             overviewStats.sendSuccessRate >= 70 ? '#faad14' : '#ff4d4f' 
                    }"
                  >
                    <template #prefix>
                      <NIcon :component="TrendingUpOutline" />
                    </template>
                  </NStatistic>
                </NGridItem>
                <NGridItem>
                  <NStatistic 
                    label="确认率" 
                    :value="overviewStats.acknowledgeSuccessRate"
                    suffix="%"
                    :precision="1"
                    :value-style="{ 
                      color: overviewStats.acknowledgeSuccessRate >= 80 ? '#52c41a' : 
                             overviewStats.acknowledgeSuccessRate >= 60 ? '#faad14' : '#ff4d4f' 
                    }"
                  >
                    <template #prefix>
                      <NIcon :component="BarChartOutline" />
                    </template>
                  </NStatistic>
                </NGridItem>
                <NGridItem>
                  <NStatistic 
                    label="平均响应时间" 
                    :value="formatDuration(overviewStats.averageResponseTime)"
                    :value-style="{ color: '#722ed1' }"
                  >
                    <template #prefix>
                      <NIcon :component="SpeedometerOutline" />
                    </template>
                  </NStatistic>
                </NGridItem>
              </NGrid>

              <!-- 状态分布 -->
              <NCard title="消息状态分布" size="small">
                <NGrid :cols="3" :x-gap="16" :y-gap="16">
                  <NGridItem>
                    <div class="text-center">
                      <div class="text-2xl font-bold text-green-500 mb-4px">{{ overviewStats.acknowledged }}</div>
                      <div class="text-sm text-gray-500">已确认</div>
                      <NProgress 
                        type="circle" 
                        :percentage="overviewStats.total > 0 ? (overviewStats.acknowledged / overviewStats.total * 100) : 0"
                        :stroke-width="8"
                        color="#52c41a"
                        class="mt-8px"
                        :show-indicator="false"
                        :size="60"
                      />
                    </div>
                  </NGridItem>
                  <NGridItem>
                    <div class="text-center">
                      <div class="text-2xl font-bold text-red-500 mb-4px">{{ overviewStats.failed }}</div>
                      <div class="text-sm text-gray-500">失败</div>
                      <NProgress 
                        type="circle" 
                        :percentage="overviewStats.total > 0 ? (overviewStats.failed / overviewStats.total * 100) : 0"
                        :stroke-width="8"
                        color="#ff4d4f"
                        class="mt-8px"
                        :show-indicator="false"
                        :size="60"
                      />
                    </div>
                  </NGridItem>
                  <NGridItem>
                    <div class="text-center">
                      <div class="text-2xl font-bold text-yellow-500 mb-4px">{{ overviewStats.pending }}</div>
                      <div class="text-sm text-gray-500">待处理</div>
                      <NProgress 
                        type="circle" 
                        :percentage="overviewStats.total > 0 ? (overviewStats.pending / overviewStats.total * 100) : 0"
                        :stroke-width="8"
                        color="#faad14"
                        class="mt-8px"
                        :show-indicator="false"
                        :size="60"
                      />
                    </div>
                  </NGridItem>
                </NGrid>
              </NCard>
            </div>
            
            <NEmpty v-else description="暂无统计数据" />
          </div>
        </NTabPane>

        <!-- 消息分类 -->
        <NTabPane name="categories" tab="消息分类">
          <div class="space-y-16px">
            <!-- 消息类型统计 -->
            <NCard title="消息类型分布" size="small">
              <div v-if="messageTypeStats.length > 0" class="space-y-8px">
                <div 
                  v-for="item in messageTypeStats" 
                  :key="item.type"
                  class="flex items-center justify-between p-12px border border-gray-200 rounded-lg"
                >
                  <div class="flex items-center gap-12px">
                    <div 
                      class="w-12px h-12px rounded-full"
                      :style="{ backgroundColor: getMessageTypeColor(item.type) }"
                    ></div>
                    <span class="font-medium">{{ item.type }}</span>
                  </div>
                  <div class="flex items-center gap-16px">
                    <span class="text-sm text-gray-500">{{ item.percentage }}%</span>
                    <span class="font-bold">{{ item.count }}</span>
                  </div>
                </div>
              </div>
              <NEmpty v-else description="暂无数据" size="small" />
            </NCard>

            <!-- 紧急程度统计 -->
            <NCard title="紧急程度分布" size="small">
              <div v-if="urgencyStats.length > 0" class="space-y-8px">
                <div 
                  v-for="item in urgencyStats" 
                  :key="item.urgency"
                  class="flex items-center justify-between p-12px border border-gray-200 rounded-lg"
                >
                  <div class="flex items-center gap-12px">
                    <div 
                      class="w-12px h-12px rounded-full"
                      :style="{ backgroundColor: getUrgencyColor(item.urgency) }"
                    ></div>
                    <span class="font-medium">{{ item.urgency }}</span>
                  </div>
                  <div class="flex items-center gap-16px">
                    <span class="text-sm text-gray-500">{{ item.percentage }}%</span>
                    <span class="font-bold">{{ item.count }}</span>
                  </div>
                </div>
              </div>
              <NEmpty v-else description="暂无数据" size="small" />
            </NCard>
          </div>
        </NTabPane>

        <!-- 渠道统计 -->
        <NTabPane name="channels" tab="渠道统计">
          <NCard title="渠道分发统计" size="small">
            <NTable 
              v-if="channelTableData.length > 0"
              :columns="channelColumns"
              :data="channelTableData"
              :pagination="false"
              size="small"
            />
            <NEmpty v-else description="暂无渠道统计数据" />
          </NCard>
        </NTabPane>

        <!-- 性能分析 -->
        <NTabPane name="performance" tab="性能分析">
          <div class="space-y-16px">
            <NAlert type="info" show-icon>
              <template #icon>
                <NIcon :component="TimeOutline" />
              </template>
              性能指标基于选定时间范围内的消息传递数据计算
            </NAlert>
            
            <NCard title="响应时间分析" size="small">
              <div v-if="responseTimeStats">
                <NGrid :cols="2" :x-gap="16" :y-gap="16">
                  <NGridItem>
                    <NStatistic 
                      label="平均送达时间" 
                      :value="formatDuration(responseTimeStats.overall?.averageDeliveryTime || 0)"
                      :value-style="{ color: '#1890ff' }"
                    />
                  </NGridItem>
                  <NGridItem>
                    <NStatistic 
                      label="平均确认时间" 
                      :value="formatDuration(responseTimeStats.overall?.averageAcknowledgmentTime || 0)"
                      :value-style="{ color: '#52c41a' }"
                    />
                  </NGridItem>
                  <NGridItem>
                    <NStatistic 
                      label="P90送达时间" 
                      :value="formatDuration(responseTimeStats.overall?.p90DeliveryTime || 0)"
                      :value-style="{ color: '#faad14' }"
                    />
                  </NGridItem>
                  <NGridItem>
                    <NStatistic 
                      label="P99送达时间" 
                      :value="formatDuration(responseTimeStats.overall?.p99DeliveryTime || 0)"
                      :value-style="{ color: '#ff4d4f' }"
                    />
                  </NGridItem>
                </NGrid>
              </div>
              <NEmpty v-else description="暂无性能数据" />
            </NCard>
          </div>
        </NTabPane>
      </NTabs>
    </NSpin>
  </div>
</template>

<style scoped>
:deep(.n-statistic .n-statistic-value) {
  font-weight: 600;
}

:deep(.n-progress-text) {
  font-size: 10px;
}

:deep(.n-card .n-card__content) {
  padding-top: 16px;
}
</style>