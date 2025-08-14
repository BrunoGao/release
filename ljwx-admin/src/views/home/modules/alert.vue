<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { $t } from '@/locales';
import { formatDateTime } from '@/utils/date';

defineOptions({
  name: 'AlertBanner'
});

interface Alert {
  id: number;
  userName: string;
  severityLevel: 'critical' | 'high' | 'medium' | 'low';
  alertType: string;
  alertTimestamp: number;
  alertStatus?: 'pending' | 'responded' | 'resolved';
}

interface NewsItem {
  id: number;
  content: string;
  time: string;
  severityLevel: 'critical' | 'high' | 'medium' | 'low';
  status: 'pending' | 'responded' | 'resolved';
}

// 告警级别图标映射
const severityIconMap = {
  critical: 'ant-design:alert-filled',
  high: 'ant-design:warning-filled',
  medium: 'ant-design:exclamation-circle-outlined',
  low: 'ant-design:info-circle-outlined'
} as const;

// 告警级别颜色映射
const severityColorMap = {
  critical: '#e74c3c',
  high: '#e67e22',
  medium: '#f1c40f',
  low: '#3498db'
} as const;

// 告警级别标签类型
const severityTagMap = {
  critical: 'error',
  high: 'warning',
  medium: 'warning',
  low: 'info'
} as const;

// 告警级别中文名称
const severityNameMap = {
  critical: '严重',
  high: '高危',
  medium: '中等',
  low: '低危'
} as const;

const props = defineProps({
  alertInfo: {
    type: Object as () => {
      alerts: Alert[];
    },
    required: true
  },
  customerId: {
    type: String,
    required: true
  }
});

const router = useRouter();

const newses = computed<NewsItem[]>(() => {
  const alerts = props.alertInfo?.alerts || [];
  return alerts.map(alert => ({
    id: alert.id,
    content: `${alert.userName}发生${severityNameMap[alert.severityLevel]}级别的${alert.alertType}告警`,
    time: formatDateTime(alert.alertTimestamp),
    severityLevel: alert.severityLevel,
    status: alert.alertStatus || 'pending'
  }));
});

const hasData = computed(() => newses.value.length > 0);

// 处理更多告警点击
function handleMoreAlert() {
  router.push('/alert/info');
}
</script>

<template>
  <NCard :title="$t('page.home.alert.name')" :bordered="false" size="small" segmented class="card-wrapper">
    <template #header-extra>
      <NButton text type="primary" @click="handleMoreAlert">
        <template #icon>
          <SvgIcon icon="ant-design:more-outlined" />
        </template>
        {{ $t('page.home.alert.moreAlert') }}
      </NButton>
    </template>

    <div class="alert-list-wrapper">
      <div v-if="!hasData" class="empty-state">
        <div class="empty-icon">
          <SvgIcon icon="ant-design:warning-outlined" class="text-40px text-gray-300" />
        </div>
        <div class="empty-text">暂无告警数据</div>
        <div class="empty-desc">当前没有任何告警记录</div>
      </div>
      <NList v-else hoverable clickable>
        <NListItem v-for="item in newses" :key="item.id" class="message-item">
          <template #prefix>
            <div class="message-icon" :style="{ backgroundColor: severityColorMap[item.severityLevel] }">
              <SvgIcon :icon="severityIconMap[item.severityLevel]" class="text-20px text-white" />
            </div>
          </template>

          <NThing class="message-content">
            <template #header>
              <div class="flex items-center gap-2">
                <span class="message-title" :class="{ 'font-bold': item.status === 'pending' }">{{ item.content }}</span>
                <NTag v-if="item.status === 'pending'" size="small" type="error" round>新</NTag>
              </div>
            </template>

            <template #description>
              <div class="flex items-center gap-2 text-14px text-gray-400">
                <span>{{ item.time }}</span>
                <NDivider vertical />
                <NTag :type="severityTagMap[item.severityLevel]" size="small" round>
                  <template #icon>
                    <SvgIcon :icon="severityIconMap[item.severityLevel]" class="text-12px" />
                  </template>
                  {{ severityNameMap[item.severityLevel] }}级
                </NTag>
              </div>
            </template>
          </NThing>
        </NListItem>
      </NList>
    </div>
  </NCard>
</template>

<style scoped>
.card-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.alert-list-wrapper {
  flex: 1;
  overflow-y: auto;
  min-height: 300px;
  max-height: 400px;
  margin: 0 -16px;
  padding: 0 16px;
}

.alert-list-wrapper::-webkit-scrollbar {
  width: 6px;
}

.alert-list-wrapper::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.alert-list-wrapper::-webkit-scrollbar-track {
  background-color: transparent;
}

.message-item {
  padding: 16px;
  transition: all 0.3s ease;
}

.message-item:hover {
  background-color: rgba(0, 0, 0, 0.02);
  transform: translateX(4px);
}

.message-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.message-icon:hover {
  transform: scale(1.1);
}

.message-title {
  font-size: 14px;
  line-height: 1.5;
  transition: color 0.3s ease;
}

.message-content {
  flex: 1;
  margin-left: 12px;
}

:deep(.n-list-item__prefix) {
  width: 40px;
  height: 40px;
  margin-right: 0;
}

:deep(.n-thing-main) {
  flex: 1;
}

:deep(.n-tag) {
  display: inline-flex;
  align-items: center;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
  text-align: center;
  padding: 40px 20px;
}

.empty-icon {
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-text {
  font-size: 16px;
  color: #666;
  margin-bottom: 8px;
  font-weight: 500;
}

.empty-desc {
  font-size: 14px;
  color: #999;
}
</style>
