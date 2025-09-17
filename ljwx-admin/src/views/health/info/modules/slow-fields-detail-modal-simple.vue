<script setup lang="ts">
import { computed } from 'vue';
import { NButton, NCard, NEmpty, NModal, NSpace, NTag } from 'naive-ui';
import { convertToBeijingTime } from '@/utils/date';

interface Props {
  visible: boolean;
  rowData: any;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  rowData: null
});

const emit = defineEmits<{
  'update:visible': [visible: boolean];
}>();

const modalVisible = computed({
  get: () => props.visible,
  set: (visible: boolean) => emit('update:visible', visible)
});

const hasAnyData = computed(() => {
  if (!props.rowData) return false;

  return Boolean(
    (props.rowData.sleepData && Object.keys(props.rowData.sleepData).length > 0) ||
      (props.rowData.workoutData && Object.keys(props.rowData.workoutData).length > 0) ||
      (props.rowData.exerciseDailyData && Object.keys(props.rowData.exerciseDailyData).length > 0) ||
      (props.rowData.exerciseWeekData && Object.keys(props.rowData.exerciseWeekData).length > 0)
  );
});

// 导出数据
function exportData() {
  const exportData = {
    userInfo: {
      userId: props.rowData.userId,
      userName: props.rowData.userName,
      orgName: props.rowData.orgName,
      timestamp: props.rowData.timestamp
    },
    sleepData: props.rowData.sleepData,
    workoutData: props.rowData.workoutData,
    exerciseDailyData: props.rowData.exerciseDailyData,
    exerciseWeekData: props.rowData.exerciseWeekData
  };

  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `健康数据详情_${props.rowData.userName}_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <NModal v-model:show="modalVisible" :mask-closable="false" preset="card" class="max-w-4xl w-90%">
    <template #header>
      <div class="flex items-center space-x-2">
        <span class="text-lg font-semibold">健康数据详情</span>
        <NTag v-if="props.rowData" type="info" size="small">{{ props.rowData.userName }} - {{ props.rowData.orgName }}</NTag>
      </div>
    </template>

    <div v-if="props.rowData" class="space-y-6">
      <!-- 基本信息 -->
      <NCard size="small" :bordered="false" class="bg-gray-50">
        <template #header>基本信息</template>
        <div class="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
          <div>
            <span class="text-gray-600">用户：</span>
            <span class="font-medium">{{ props.rowData.userName }}</span>
          </div>
          <div>
            <span class="text-gray-600">部门：</span>
            <span class="font-medium">{{ props.rowData.orgName }}</span>
          </div>
          <div>
            <span class="text-gray-600">记录时间：</span>
            <span class="font-medium">{{ convertToBeijingTime(props.rowData.timestamp) }}</span>
          </div>
          <div>
            <span class="text-gray-600">用户ID：</span>
            <span class="font-medium">{{ props.rowData.userId }}</span>
          </div>
        </div>
      </NCard>

      <!-- 睡眠数据 -->
      <div v-if="props.rowData.sleepData && Object.keys(props.rowData.sleepData).length > 0">
        <NCard size="small" :bordered="false">
          <template #header>
            <div class="flex items-center space-x-2">
              <span>睡眠数据</span>
              <NTag type="warning" size="small">Sleep Data</NTag>
            </div>
          </template>

          <div class="space-y-4">
            <div class="rounded bg-purple-50 p-4">
              <h4 class="mb-2 text-purple-800 font-semibold">睡眠详情</h4>
              <pre class="whitespace-pre-wrap text-sm text-purple-700">{{ JSON.stringify(props.rowData.sleepData, null, 2) }}</pre>
            </div>
          </div>
        </NCard>
      </div>

      <!-- 运动数据 -->
      <div v-if="props.rowData.workoutData && Object.keys(props.rowData.workoutData).length > 0">
        <NCard size="small" :bordered="false">
          <template #header>
            <div class="flex items-center space-x-2">
              <span>运动数据</span>
              <NTag type="success" size="small">Workout Data</NTag>
            </div>
          </template>

          <div class="space-y-4">
            <div class="rounded bg-orange-50 p-4">
              <h4 class="mb-2 text-orange-800 font-semibold">运动详情</h4>
              <pre class="whitespace-pre-wrap text-sm text-orange-700">{{ JSON.stringify(props.rowData.workoutData, null, 2) }}</pre>
            </div>
          </div>
        </NCard>
      </div>

      <!-- 每日运动数据 -->
      <div v-if="props.rowData.exerciseDailyData && Object.keys(props.rowData.exerciseDailyData).length > 0">
        <NCard size="small" :bordered="false">
          <template #header>
            <div class="flex items-center space-x-2">
              <span>每日运动数据</span>
              <NTag type="info" size="small">Daily Exercise</NTag>
            </div>
          </template>

          <div class="space-y-4">
            <div class="rounded bg-cyan-50 p-4">
              <h4 class="mb-2 text-cyan-800 font-semibold">每日运动详情</h4>
              <pre class="whitespace-pre-wrap text-sm text-cyan-700">{{ JSON.stringify(props.rowData.exerciseDailyData, null, 2) }}</pre>
            </div>
          </div>
        </NCard>
      </div>

      <!-- 每周运动数据 -->
      <div v-if="props.rowData.exerciseWeekData && Object.keys(props.rowData.exerciseWeekData).length > 0">
        <NCard size="small" :bordered="false">
          <template #header>
            <div class="flex items-center space-x-2">
              <span>每周运动数据</span>
              <NTag type="error" size="small">Weekly Exercise</NTag>
            </div>
          </template>

          <div class="space-y-4">
            <div class="rounded bg-pink-50 p-4">
              <h4 class="mb-2 text-pink-800 font-semibold">每周运动详情</h4>
              <pre class="whitespace-pre-wrap text-sm text-pink-700">{{ JSON.stringify(props.rowData.exerciseWeekData, null, 2) }}</pre>
            </div>
          </div>
        </NCard>
      </div>

      <!-- 空数据提示 -->
      <NEmpty v-if="!hasAnyData" description="暂无详细数据" class="py-12" />
    </div>

    <template #action>
      <NSpace justify="end">
        <NButton @click="modalVisible = false">关闭</NButton>
        <NButton type="primary" @click="exportData">导出数据</NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped>
.space-y-6 > * + * {
  margin-top: 1.5rem;
}

.space-y-4 > * + * {
  margin-top: 1rem;
}

.space-x-2 > * + * {
  margin-left: 0.5rem;
}

.grid {
  display: grid;
}

.grid-cols-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (min-width: 768px) {
  .md\:grid-cols-4 {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.gap-4 {
  gap: 1rem;
}

.py-12 {
  padding-top: 3rem;
  padding-bottom: 3rem;
}

.w-90\% {
  width: 90%;
}

.max-w-4xl {
  max-width: 56rem;
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.font-semibold {
  font-weight: 600;
}

.text-lg {
  font-size: 1.125rem;
  line-height: 1.75rem;
}

.text-sm {
  font-size: 0.875rem;
  line-height: 1.25rem;
}

.text-gray-600 {
  --un-text-opacity: 1;
  color: rgb(75 85 99 / var(--un-text-opacity));
}

.font-medium {
  font-weight: 500;
}

.bg-gray-50 {
  --un-bg-opacity: 1;
  background-color: rgb(249 250 251 / var(--un-bg-opacity));
}

.bg-purple-50 {
  --un-bg-opacity: 1;
  background-color: rgb(250 245 255 / var(--un-bg-opacity));
}

.bg-orange-50 {
  --un-bg-opacity: 1;
  background-color: rgb(255 247 237 / var(--un-bg-opacity));
}

.bg-cyan-50 {
  --un-bg-opacity: 1;
  background-color: rgb(236 254 255 / var(--un-bg-opacity));
}

.bg-pink-50 {
  --un-bg-opacity: 1;
  background-color: rgb(253 242 248 / var(--un-bg-opacity));
}

.p-4 {
  padding: 1rem;
}

.rounded {
  border-radius: 0.25rem;
}

.text-purple-800 {
  --un-text-opacity: 1;
  color: rgb(91 33 182 / var(--un-text-opacity));
}

.text-orange-800 {
  --un-text-opacity: 1;
  color: rgb(154 52 18 / var(--un-text-opacity));
}

.text-cyan-800 {
  --un-text-opacity: 1;
  color: rgb(21 94 117 / var(--un-text-opacity));
}

.text-pink-800 {
  --un-text-opacity: 1;
  color: rgb(157 23 77 / var(--un-text-opacity));
}

.text-purple-700 {
  --un-text-opacity: 1;
  color: rgb(109 40 217 / var(--un-text-opacity));
}

.text-orange-700 {
  --un-text-opacity: 1;
  color: rgb(194 65 12 / var(--un-text-opacity));
}

.text-cyan-700 {
  --un-text-opacity: 1;
  color: rgb(14 116 144 / var(--un-text-opacity));
}

.text-pink-700 {
  --un-text-opacity: 1;
  color: rgb(190 24 93 / var(--un-text-opacity));
}

.mb-2 {
  margin-bottom: 0.5rem;
}

.whitespace-pre-wrap {
  white-space: pre-wrap;
}
</style>
