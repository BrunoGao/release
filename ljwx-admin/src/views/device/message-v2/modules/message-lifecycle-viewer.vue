<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import {
  NAlert,
  NButton,
  NCard,
  NDescriptions,
  NDescriptionsItem,
  NEmpty,
  NGrid,
  NGridItem,
  NIcon,
  NProgress,
  NSpace,
  NSpin,
  NStatistic,
  NTag,
  NTime,
  NTimeline,
  NTimelineItem
} from 'naive-ui';
import {
  CheckmarkCircleOutline,
  CloseCircleOutline,
  HourglassOutline,
  InformationCircleOutline,
  PlayCircleOutline,
  SendOutline,
  StopCircleOutline,
  TimeOutline
} from '@vicons/ionicons5';
import { fetchGetDeviceMessageV2Detail, fetchGetMessageSummary } from '@/service/api/health/device-message-v2';

interface Props {
  messageId: number;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  close: [];
}>();

const loading = ref(true);
const messageDetail = ref<Api.Health.DeviceMessageV2Detail | null>(null);
const messageSummary = ref<Api.Health.MessageSummaryV2 | null>(null);

// 模拟生命周期数据（实际应用中从API获取）
const lifecycleTrace = ref<Api.Health.MessageLifecycleTrace | null>(null);

// 计算生命周期阶段
const lifecycleStages = computed(() => {
  if (!messageDetail.value) return [];

  const stages: Api.Health.MessageLifecycleStage[] = [];
  const message = messageDetail.value;

  // 创建阶段
  stages.push({
    stage: 'CREATED',
    timestamp: message.createTime || new Date().toISOString(),
    details: {
      title: message.title,
      messageType: message.messageType,
      urgency: message.urgency
    }
  });

  // 发送阶段
  if (message.sentTime) {
    const createTime = new Date(message.createTime || '').getTime();
    const sentTime = new Date(message.sentTime).getTime();
    stages.push({
      stage: 'SENT',
      timestamp: message.sentTime,
      duration: sentTime - createTime,
      details: {
        targetCount: message.totalTargets,
        channels: message.details?.map(d => d.channel) || []
      }
    });
  }

  // 送达阶段
  if (message.deliveredCount > 0) {
    const firstDelivered = message.details?.find(d => d.deliveredTime);
    if (firstDelivered?.deliveredTime) {
      const sentTime = new Date(message.sentTime || '').getTime();
      const deliveredTime = new Date(firstDelivered.deliveredTime).getTime();
      stages.push({
        stage: 'DELIVERED',
        timestamp: firstDelivered.deliveredTime,
        duration: deliveredTime - sentTime,
        details: {
          deliveredCount: message.deliveredCount,
          totalTargets: message.totalTargets
        }
      });
    }
  }

  // 确认阶段
  if (message.acknowledgedCount > 0) {
    const firstAcknowledged = message.details?.find(d => d.acknowledgedTime);
    if (firstAcknowledged?.acknowledgedTime) {
      const deliveredTime = new Date(firstAcknowledged.deliveredTime || '').getTime();
      const acknowledgedTime = new Date(firstAcknowledged.acknowledgedTime).getTime();
      stages.push({
        stage: 'ACKNOWLEDGED',
        timestamp: firstAcknowledged.acknowledgedTime,
        duration: acknowledgedTime - deliveredTime,
        details: {
          acknowledgedCount: message.acknowledgedCount,
          totalTargets: message.totalTargets
        }
      });
    }
  }

  // 失败阶段
  if (message.failedCount > 0) {
    stages.push({
      stage: 'FAILED',
      timestamp: new Date().toISOString(), // 实际应该从详情中获取
      details: {
        failedCount: message.failedCount,
        reasons:
          message.details
            ?.filter(d => d.deliveryStatus === 'FAILED')
            .map(d => d.failureReason)
            .filter(Boolean) || []
      }
    });
  }

  return stages;
});

// 当前状态
const currentStage = computed(() => {
  if (!messageDetail.value) return 'CREATED';

  const message = messageDetail.value;
  if (message.failedCount > 0 && message.failedCount === message.totalTargets) return 'FAILED';
  if (message.acknowledgedCount === message.totalTargets) return 'ACKNOWLEDGED';
  if (message.deliveredCount > 0) return 'DELIVERED';
  if (message.sentTime) return 'SENT';
  return 'CREATED';
});

// 完成状态
const isCompleted = computed(() => {
  if (!messageDetail.value) return false;
  const message = messageDetail.value;
  return message.acknowledgedCount === message.totalTargets || message.failedCount === message.totalTargets || message.messageStatus === 'EXPIRED';
});

// 成功状态
const isSuccess = computed(() => {
  if (!messageDetail.value) return false;
  const message = messageDetail.value;
  return message.acknowledgedCount === message.totalTargets;
});

// 总耗时
const totalDuration = computed(() => {
  if (!messageDetail.value || !messageDetail.value.sentTime) return 0;

  const createTime = new Date(messageDetail.value.createTime || '').getTime();
  const lastTime =
    messageDetail.value.acknowledgedCount > 0
      ? new Date(messageDetail.value.details?.find(d => d.acknowledgedTime)?.acknowledgedTime || '').getTime()
      : messageDetail.value.deliveredCount > 0
        ? new Date(messageDetail.value.details?.find(d => d.deliveredTime)?.deliveredTime || '').getTime()
        : new Date(messageDetail.value.sentTime).getTime();

  return lastTime - createTime;
});

// 获取阶段图标和颜色
function getStageIcon(stage: Api.Health.MessageLifecycleStage['stage']) {
  switch (stage) {
    case 'CREATED':
      return { icon: PlayCircleOutline, color: 'default' };
    case 'SENT':
      return { icon: SendOutline, color: 'info' };
    case 'DELIVERED':
      return { icon: CheckmarkCircleOutline, color: 'success' };
    case 'ACKNOWLEDGED':
      return { icon: CheckmarkCircleOutline, color: 'success' };
    case 'FAILED':
      return { icon: CloseCircleOutline, color: 'error' };
    case 'EXPIRED':
      return { icon: StopCircleOutline, color: 'warning' };
    default:
      return { icon: HourglassOutline, color: 'default' };
  }
}

// 格式化持续时间
function formatDuration(ms: number) {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${(ms / 60000).toFixed(1)}min`;
  return `${(ms / 3600000).toFixed(1)}h`;
}

// 获取阶段描述
function getStageDescription(stage: Api.Health.MessageLifecycleStage) {
  switch (stage.stage) {
    case 'CREATED':
      return `消息已创建：${stage.details?.title || ''}`;
    case 'SENT':
      return `已发送到 ${stage.details?.targetCount || 0} 个目标`;
    case 'DELIVERED':
      return `${stage.details?.deliveredCount || 0}/${stage.details?.totalTargets || 0} 已送达`;
    case 'ACKNOWLEDGED':
      return `${stage.details?.acknowledgedCount || 0}/${stage.details?.totalTargets || 0} 已确认`;
    case 'FAILED':
      return `${stage.details?.failedCount || 0} 个目标发送失败`;
    case 'EXPIRED':
      return '消息已过期';
    default:
      return stage.stage;
  }
}

// 获取分发详情统计
const distributionStats = computed(() => {
  if (!messageSummary.value) return null;

  const summary = messageSummary.value;
  const total = summary.totalTargets;

  return {
    total,
    pending: summary.distributionDetails.pending,
    sent: summary.distributionDetails.sent,
    delivered: summary.distributionDetails.delivered,
    acknowledged: summary.distributionDetails.acknowledged,
    failed: summary.distributionDetails.failed,
    expired: summary.distributionDetails.expired,
    completionRate: summary.completionRate,
    successRate: summary.successRate,
    avgDeliveryTime: summary.averageDeliveryTime,
    avgAckTime: summary.averageAcknowledgmentTime
  };
});

// 加载数据
async function loadData() {
  loading.value = true;

  try {
    // 加载消息详情
    const { error: detailError, data: detail } = await fetchGetDeviceMessageV2Detail(props.messageId);
    if (!detailError && detail) {
      messageDetail.value = detail;
    }

    // 加载消息汇总
    const { error: summaryError, data: summary } = await fetchGetMessageSummary(props.messageId);
    if (!summaryError && summary) {
      messageSummary.value = summary;
    }

    // 构建生命周期追踪数据
    if (messageDetail.value) {
      lifecycleTrace.value = {
        messageId: props.messageId,
        totalDuration: totalDuration.value,
        stages: lifecycleStages.value,
        currentStage: currentStage.value,
        isCompleted: isCompleted.value,
        success: isSuccess.value
      };
    }
  } catch (error) {
    console.error('加载消息生命周期数据失败:', error);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="space-y-24px">
    <NSpin :show="loading">
      <div v-if="messageDetail && lifecycleTrace" class="space-y-24px">
        <!-- 基本信息 -->
        <NCard title="消息基本信息" size="small">
          <NDescriptions :columns="3" label-placement="left">
            <NDescriptionsItem label="消息ID">
              <code class="rounded bg-gray-100 px-2 py-1 text-sm">{{ messageDetail.messageId }}</code>
            </NDescriptionsItem>
            <NDescriptionsItem label="消息标题">{{ messageDetail.title }}</NDescriptionsItem>
            <NDescriptionsItem label="消息类型">
              <NTag :type="messageDetail.messageType === 'EMERGENCY' ? 'error' : 'info'" size="small">
                {{ messageDetail.messageType }}
              </NTag>
            </NDescriptionsItem>
            <NDescriptionsItem label="紧急程度">
              <NTag :type="messageDetail.urgency === 'CRITICAL' ? 'error' : messageDetail.urgency === 'HIGH' ? 'warning' : 'default'" size="small">
                {{ messageDetail.urgency }}
              </NTag>
            </NDescriptionsItem>
            <NDescriptionsItem label="当前状态">
              <NTag :type="isSuccess ? 'success' : isCompleted ? 'warning' : 'info'" size="small">
                {{ currentStage }}
              </NTag>
            </NDescriptionsItem>
            <NDescriptionsItem label="总耗时">
              {{ totalDuration ? formatDuration(totalDuration) : '进行中' }}
            </NDescriptionsItem>
          </NDescriptions>
        </NCard>

        <!-- 分发统计 -->
        <NCard v-if="distributionStats" title="分发统计" size="small">
          <NGrid :cols="4" :x-gap="16" :y-gap="16" class="mb-16px">
            <NGridItem>
              <NStatistic label="总目标数" :value="distributionStats.total" :value-style="{ color: '#1890ff' }" />
            </NGridItem>
            <NGridItem>
              <NStatistic label="已送达" :value="distributionStats.delivered" :value-style="{ color: '#52c41a' }" />
            </NGridItem>
            <NGridItem>
              <NStatistic label="已确认" :value="distributionStats.acknowledged" :value-style="{ color: '#52c41a' }" />
            </NGridItem>
            <NGridItem>
              <NStatistic
                label="成功率"
                :value="distributionStats.successRate"
                suffix="%"
                :precision="1"
                :value-style="{
                  color: distributionStats.successRate >= 90 ? '#52c41a' : distributionStats.successRate >= 70 ? '#faad14' : '#ff4d4f'
                }"
              />
            </NGridItem>
          </NGrid>

          <NProgress
            type="multiple"
            :percentage="[
              { percentage: (distributionStats.delivered / distributionStats.total) * 100, color: '#52c41a' },
              { percentage: (distributionStats.failed / distributionStats.total) * 100, color: '#ff4d4f' },
              { percentage: (distributionStats.pending / distributionStats.total) * 100, color: '#faad14' }
            ]"
            :show-indicator="true"
          />

          <div class="mt-16px flex justify-center gap-24px text-sm">
            <span>
              <span class="mr-4px inline-block h-8px w-8px rounded-full bg-green-500"></span>
              成功: {{ distributionStats.delivered }}
            </span>
            <span>
              <span class="mr-4px inline-block h-8px w-8px rounded-full bg-red-500"></span>
              失败: {{ distributionStats.failed }}
            </span>
            <span>
              <span class="mr-4px inline-block h-8px w-8px rounded-full bg-yellow-500"></span>
              待处理: {{ distributionStats.pending }}
            </span>
          </div>
        </NCard>

        <!-- 生命周期时间线 -->
        <NCard title="生命周期跟踪" size="small">
          <NAlert v-if="!isCompleted" type="info" class="mb-16px">
            <template #icon>
              <NIcon :component="HourglassOutline" />
            </template>
            消息仍在处理中，状态会实时更新
          </NAlert>

          <NTimeline>
            <NTimelineItem v-for="(stage, index) in lifecycleStages" :key="index" :type="getStageIcon(stage.stage).color" :time="stage.timestamp">
              <template #icon>
                <NIcon :component="getStageIcon(stage.stage).icon" />
              </template>

              <template #header>
                <div class="flex items-center gap-8px">
                  <span class="font-medium">{{ stage.stage }}</span>
                  <NTag v-if="stage.duration" size="tiny" type="info">
                    {{ formatDuration(stage.duration) }}
                  </NTag>
                </div>
              </template>

              <div class="space-y-8px">
                <div>{{ getStageDescription(stage) }}</div>
                <NTime :time="new Date(stage.timestamp)" />

                <!-- 详细信息 -->
                <div v-if="stage.details" class="text-sm text-gray-500 space-y-4px">
                  <div v-if="stage.details.channels" class="flex gap-4px">
                    渠道:
                    <NTag v-for="channel in stage.details.channels" :key="channel" size="tiny">
                      {{ channel }}
                    </NTag>
                  </div>
                  <div v-if="stage.details.reasons?.length" class="space-y-2px">
                    失败原因:
                    <div v-for="reason in stage.details.reasons" :key="reason" class="text-xs text-red-500">• {{ reason }}</div>
                  </div>
                </div>
              </div>
            </NTimelineItem>
          </NTimeline>

          <!-- 如果消息已完成，显示总结 -->
          <div v-if="isCompleted" class="mt-16px rounded-lg bg-gray-50 p-16px">
            <div class="mb-8px flex items-center gap-8px">
              <NIcon size="20" :component="isSuccess ? CheckmarkCircleOutline : CloseCircleOutline" :color="isSuccess ? '#52c41a' : '#ff4d4f'" />
              <span class="font-medium">
                {{ isSuccess ? '消息处理完成' : '消息处理结束' }}
              </span>
            </div>
            <div class="text-sm text-gray-600 space-y-4px">
              <div>总耗时: {{ formatDuration(totalDuration) }}</div>
              <div>最终状态: {{ currentStage }}</div>
              <div>成功率: {{ messageDetail ? ((messageDetail.acknowledgedCount / messageDetail.totalTargets) * 100).toFixed(1) : 0 }}%</div>
            </div>
          </div>
        </NCard>

        <!-- 目标详情 -->
        <NCard v-if="messageDetail.details?.length" title="分发目标详情" size="small">
          <div class="space-y-8px">
            <div
              v-for="detail in messageDetail.details"
              :key="`${detail.targetId}-${detail.channel}`"
              class="flex items-center justify-between border border-gray-200 rounded-lg p-12px transition-colors hover:bg-gray-50"
            >
              <div class="flex items-center gap-12px">
                <NTag :type="detail.targetType === 'DEVICE' ? 'info' : 'warning'" size="small">
                  {{ detail.targetType }}
                </NTag>
                <code class="text-sm">{{ detail.targetId }}</code>
                <NTag size="tiny" type="default">{{ detail.channel }}</NTag>
              </div>

              <div class="flex items-center gap-8px">
                <NTag
                  :type="
                    detail.deliveryStatus === 'ACKNOWLEDGED'
                      ? 'success'
                      : detail.deliveryStatus === 'DELIVERED'
                        ? 'info'
                        : detail.deliveryStatus === 'FAILED'
                          ? 'error'
                          : 'warning'
                  "
                  size="small"
                >
                  {{ detail.deliveryStatus }}
                </NTag>

                <div v-if="detail.deliveredTime" class="text-xs text-gray-500">
                  <NTime :time="new Date(detail.deliveredTime)" format="MM-dd HH:mm:ss" />
                </div>
              </div>
            </div>
          </div>
        </NCard>
      </div>

      <NEmpty v-else-if="!loading" description="无法加载消息详情" />
    </NSpin>

    <!-- 操作按钮 -->
    <div class="flex justify-end gap-8px">
      <NButton @click="loadData">刷新数据</NButton>
      <NButton type="primary" @click="emit('close')">关闭</NButton>
    </div>
  </div>
</template>

<style scoped>
:deep(.n-timeline-item-timeline) {
  padding-left: 24px;
}

:deep(.n-descriptions-item-label) {
  font-weight: 500;
}

:deep(.n-progress-text) {
  font-size: 12px;
}

.hover\:bg-gray-50:hover {
  background-color: #f9fafb;
}
</style>
