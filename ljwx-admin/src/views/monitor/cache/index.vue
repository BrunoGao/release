<script setup lang="ts">
import { onActivated, ref, watch, computed } from 'vue';
import { $t } from '@/locales';
import { fetchGetCacheRedisInfo, fetchClearAllCache, fetchClearCacheByPattern } from '@/service/api';
import { useEcharts } from '@/hooks/common/echarts';
import { useAppStore } from '@/store/modules/app';
import { useNaiveForm } from '@/hooks/common/form';
import { useAuthStore } from '@/store/modules/auth';

defineOptions({
  name: 'MonitorCacheRedis'
});

const redisInfo = ref<Api.Monitor.RedisInfo>();

const appStore = useAppStore();
const authStore = useAuthStore();

// 控制清理缓存的模态框
const showClearModal = ref(false);
const clearPattern = ref('');
const { formRef, validate } = useNaiveForm();
const loading = ref(false);

// echarts options
const { domRef, updateOptions } = useEcharts(() => ({
  title: {
    text: $t('page.monitor.cache.redis.echartsTitle'),
    subtext: $t('page.monitor.cache.redis.echartsSubTitle'),
    left: 'center'
  },
  tooltip: {
    trigger: 'item'
  },
  legend: {
    bottom: '1%',
    left: 'center'
  },
  series: [
    {
      name: 'Access From',
      type: 'pie',
      radius: '50%',
      data: [] as { name: string; value: number }[]
    }
  ]
}));

// get cache redis info
async function getCacheRedis() {
  const { error, data } = await fetchGetCacheRedisInfo();
  if (!error) {
    redisInfo.value = data;
    updateOptions(opts => {
      opts.series[0].data = data.commandStats;
      return opts;
    });
  }
}

// changed locale need update text and subText
function updateLocale() {
  updateOptions((opts, factory) => {
    const originOpts = factory();

    opts.title.text = originOpts.title.text;
    opts.title.subtext = originOpts.title.subtext;

    opts.series[0].data = redisInfo.value?.commandStats || [];

    return opts;
  });
}

// 清理全部缓存
async function clearAllCache() {
  const dialog = $dialog.warning({
    title: $t('page.monitor.cache.redis.clearAllCache'),
    content: $t('page.monitor.cache.redis.confirmClearAll'),
    positiveText: $t('common.confirm'),
    negativeText: $t('common.cancel'),
    onPositiveClick: async () => {
      dialog.loading = true;
      try {
        const { error } = await fetchClearAllCache();
        if (!error) {
          $message.success($t('page.monitor.cache.redis.clearSuccess'));
          await getCacheRedis(); // 刷新缓存信息
        } else {
          $message.error($t('page.monitor.cache.redis.clearError'));
        }
      } catch (e) {
        $message.error($t('page.monitor.cache.redis.clearError'));
      } finally {
        dialog.loading = false;
      }
    }
  });
}

// 按模式清理缓存
async function clearCacheByPattern() {
  const valid = await validate();
  if (!valid) return;

  const dialog = $dialog.warning({
    title: $t('page.monitor.cache.redis.clearCacheByPattern'),
    content: $t('page.monitor.cache.redis.confirmClearPattern', { pattern: clearPattern.value }),
    positiveText: $t('common.confirm'),
    negativeText: $t('common.cancel'),
    onPositiveClick: async () => {
      dialog.loading = true;
      try {
        const { error } = await fetchClearCacheByPattern(clearPattern.value);
        if (!error) {
          $message.success($t('page.monitor.cache.redis.clearSuccess'));
          showClearModal.value = false;
          clearPattern.value = '';
          await getCacheRedis(); // 刷新缓存信息
        } else {
          $message.error($t('page.monitor.cache.redis.clearError'));
        }
      } catch (e) {
        $message.error($t('page.monitor.cache.redis.clearError'));
      } finally {
        dialog.loading = false;
      }
    }
  });
}

// 检查权限：只有超级管理员(customerId=0)和租户管理员可以清理缓存
const canClearCache = computed(() => {
  const userInfo = authStore.userInfo;
  return userInfo.customerId === 0 || (userInfo.customerId > 0 && userInfo.userRoleName?.includes('管理员'));
});

function init() {
  getCacheRedis();
}

watch(
  () => appStore.locale,
  () => {
    updateLocale();
  }
);

onActivated(() => {
  init();
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-2">
    <NCard :title="$t('page.monitor.cache.redis.title')" size="small">
      <template #header-extra>
        <NSpace v-if="canClearCache">
          <NButton type="warning" size="small" @click="showClearModal = true">
            {{ $t('page.monitor.cache.redis.clearCacheByPattern') }}
          </NButton>
          <NButton type="error" size="small" @click="clearAllCache">
            {{ $t('page.monitor.cache.redis.clearAllCache') }}
          </NButton>
        </NSpace>
      </template>
      
      <NDescriptions label-placement="left" bordered :column="2">
        <NDescriptionsItem :label="$t('page.monitor.cache.redis.version')">
          {{ redisInfo?.version }}
        </NDescriptionsItem>
        <NDescriptionsItem :label="$t('page.monitor.cache.redis.uptime')">{{ redisInfo?.uptime }}</NDescriptionsItem>
        <NDescriptionsItem :label="$t('page.monitor.cache.redis.connectedClients')">
          {{ redisInfo?.connectedClients }}
        </NDescriptionsItem>
        <NDescriptionsItem :label="$t('page.monitor.cache.redis.totalCommandsProcessed')">
          {{ redisInfo?.totalCommandsProcessed }}
        </NDescriptionsItem>
        <NDescriptionsItem :label="$t('page.monitor.cache.redis.usedMemory')" label-style="color:red;" content-style="color:red;">
          {{ redisInfo?.usedMemory }}
        </NDescriptionsItem>
        <NDescriptionsItem :label="$t('page.monitor.cache.redis.maxMemory')">{{ redisInfo?.maxMemory }}</NDescriptionsItem>
        <NDescriptionsItem :label="$t('page.monitor.cache.redis.memFragmentationRatio')" label-style="color:red;" content-style="color:red;">
          {{ $t('page.monitor.percentage', { value: redisInfo?.memFragmentationRatio }) }}
        </NDescriptionsItem>
        <NDescriptionsItem :label="$t('page.monitor.cache.redis.memoryUsageRate')" label-style="color:red;" content-style="color:red;">
          {{ $t('page.monitor.percentage', { value: redisInfo?.memoryUsageRate }) }}
        </NDescriptionsItem>
      </NDescriptions>
    </NCard>
    
    <NCard class="h-full">
      <div ref="domRef" class="h-full overflow-hidden" />
    </NCard>

    <!-- 按模式清理缓存的模态框 -->
    <NModal v-model:show="showClearModal" :mask-closable="false">
      <NCard style="width: 500px;" :title="$t('page.monitor.cache.redis.clearCacheByPattern')" size="huge" role="dialog" aria-modal="true">
        <NForm ref="formRef" :model="{pattern: clearPattern}" label-placement="top">
          <NFormItem :label="$t('page.monitor.cache.redis.clearCacheByPattern')" path="pattern" :rule="{ required: true, message: $t('page.monitor.cache.redis.patternRequired') }">
            <NInput 
              v-model:value="clearPattern" 
              :placeholder="$t('page.monitor.cache.redis.patternPlaceholder')"
              clearable
            />
          </NFormItem>
        </NForm>
        
        <template #footer>
          <NSpace justify="end">
            <NButton @click="showClearModal = false">{{ $t('common.cancel') }}</NButton>
            <NButton type="warning" @click="clearCacheByPattern" :loading="loading">
              {{ $t('common.confirm') }}
            </NButton>
          </NSpace>
        </template>
      </NCard>
    </NModal>
  </div>
</template>
