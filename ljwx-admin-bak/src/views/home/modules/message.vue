<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { $t } from '@/locales';
import { formatDateTime } from '@/utils/date';

defineOptions({
  name: 'MessageBanner'
});

interface Message {
  id: number;
  message: string;
  received_time: string;
  sentTime?: string;
  messageType?: 'announcement' | 'job' | 'task' | 'notification' | 'warning';
  messageStatus?: string;
  priority?: 'high' | 'medium' | 'low';
  status?: 'unread' | 'read';
}

interface NewsItem {
  id: number;
  content: string;
  time: string;
  type: 'announcement' | 'job' | 'task' | 'notification' | 'warning';
  priority: 'high' | 'medium' | 'low';
  status: 'unread' | 'read';
}

// 消息类型图标映射
const typeIconMap = {
  announcement: 'ant-design:notification-outlined',
  job: 'ant-design:schedule-outlined',
  task: 'ant-design:check-circle-outlined',
  notification: 'ant-design:info-circle-outlined',
  warning: 'ant-design:warning-outlined'
} as const;

// 消息类型标签颜色映射
const typeColorMap = {
  announcement: '#f6b93b',
  job: '#4834d4',
  task: '#6ab04c',
  notification: '#22a6b3',
  warning: '#e74c3c'
} as const;

// 消息类型对应的中文名称
const typeNameMap = {
  announcement: '系统公告',
  job: '作业指引',
  task: '任务管理',
  notification: '通知消息',
  warning: '警告消息'
} as const;

// 优先级对应的中文名称
const priorityNameMap = {
  high: '紧急',
  medium: '普通',
  low: '低优先级'
} as const;

// 优先级标签配置
const priorityConfig = {
  high: { color: 'error', icon: 'ant-design:arrow-up-outlined' },
  medium: { color: 'warning', icon: 'ant-design:minus-outlined' },
  low: { color: 'success', icon: 'ant-design:arrow-down-outlined' }
} as const;

// 消息类型对应的标签类型
const typeTagMap = {
  announcement: 'warning',
  job: 'primary',
  task: 'success',
  notification: 'info',
  warning: 'error'
} as const;

const props = defineProps({
  messageInfo: {
    type: Object as () => {
      messages: Message[];
    },
    required: true
  },
  customerId: {
    type: String,
    required: true
  }
});

const newses = computed<NewsItem[]>(() => {
  const messages = props.messageInfo?.messages || [];
  return messages.map(message => ({
    id: message.id,
    content: message.message,
    time: formatDateTime(message.sentTime || message.received_time),
    type: message.messageType || 'notification',
    priority: message.priority || 'medium',
    status: (message.messageStatus === '1' ? 'unread' : 'read') as 'unread' | 'read'
  }));
});

const hasData = computed(() => newses.value.length > 0);
const router = useRouter();
// 处理更多告警点击
function handleMoreMessage() {
  router.push('/device/message');
}
</script>

<template>
  <NCard :title="$t('page.home.message.name')" :bordered="false" size="small" segmented class="card-wrapper">
    <template #header-extra>
      <NButton text type="primary" @click="handleMoreMessage">
        <template #icon>
          <SvgIcon icon="ant-design:more-outlined" />
        </template>
        {{ $t('page.home.message.moreMessage') }}
      </NButton>
    </template>

    <div class="message-list-wrapper">
      <div v-if="!hasData" class="empty-state">
        <div class="empty-icon">
          <SvgIcon icon="ant-design:inbox-outlined" class="text-40px text-gray-300" />
        </div>
        <div class="empty-text">暂无消息数据</div>
        <div class="empty-desc">当前没有任何消息记录</div>
      </div>
      <NList v-else hoverable clickable>
        <NListItem v-for="item in newses" :key="item.id" class="message-item">
          <template #prefix>
            <div class="message-icon" :style="{ backgroundColor: typeColorMap[item.type] }">
              <SvgIcon :icon="typeIconMap[item.type]" class="text-20px text-white" />
            </div>
          </template>

          <NThing class="message-content">
            <template #header>
              <div class="flex items-center gap-2">
                <span class="message-title" :class="{ 'font-bold': item.status === 'unread' }">{{ item.content }}</span>
                <NTag v-if="item.status === 'unread'" size="small" type="error" round>新</NTag>
              </div>
            </template>

            <template #description>
              <div class="flex items-center gap-2 text-14px text-gray-400">
                <span>{{ item.time }}</span>
                <NDivider vertical />
                <NTag :type="priorityConfig[item.priority].color" size="small" round>
                  <template #icon>
                    <SvgIcon :icon="priorityConfig[item.priority].icon" class="text-12px" />
                  </template>
                  {{ priorityNameMap[item.priority] }}
                </NTag>
                <NTag :type="typeTagMap[item.type]" size="small" round>{{ typeNameMap[item.type] }}</NTag>
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

.message-list-wrapper {
  flex: 1;
  overflow-y: auto;
  min-height: 300px;
  max-height: 400px;
  margin: 0 -16px;
  padding: 0 16px;
}

.message-list-wrapper::-webkit-scrollbar {
  width: 6px;
}

.message-list-wrapper::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.message-list-wrapper::-webkit-scrollbar-track {
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
