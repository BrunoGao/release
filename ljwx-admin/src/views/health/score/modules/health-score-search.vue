<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { $t } from '@/locales';
import { useDict } from '@/hooks/business/dict';

import { fetchBaseFeatures } from '@/service/api/health';

defineOptions({
  name: 'THealthScoreSearch'
});
const props = defineProps<{
  orgUnitsTree: Array<any>; // Adjust the type according to your data structure
  userOptions: Array<any>;
  customerId: number;
}>();

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Health.HealthScoreSearchParams>('model', { required: true });
// 特征选项
const featureOptions = ref<Array<{ label: string; value: string }>>([]);

// 获取基础特征
async function loadFeatureOptions() {
  console.log('🔄 加载特征选项 - customerId:', props.customerId);

  try {
    const response = await fetchBaseFeatures(props.customerId);
    if (response && response.data) {
      featureOptions.value = [{ label: '全部', value: 'all' }, ...response.data];
      console.log('✅ 加载特征选项成功:', featureOptions.value);
    }
  } catch (error) {
    console.error('❌ 加载特征选项失败:', error);
    // 使用默认选项作为后备
    featureOptions.value = [
      { label: '全部', value: 'all' },
      { label: '心率', value: 'heart_rate' },
      { label: '血氧', value: 'blood_oxygen' },
      { label: '体温', value: 'temperature' },
      { label: '压力', value: 'stress' },
      { label: '睡眠', value: 'sleep' },
      { label: '步数', value: 'step' },
      { label: '距离', value: 'distance' },
      { label: '卡路里', value: 'calorie' }
    ];
  }
}
const { dictOptions } = useDict();

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
// 监听dataType变化，如果选择全部则设置为null
watch(
  () => model.value.dataType,
  dataType_val => {
    if (dataType_val === 'all') model.value.dataType = null;
  }
);
// 组件挂载时加载特征选项
onMounted(() => {
  loadFeatureOptions();
});
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NForm :model="model" label-placement="left" :show-feedback="false" :label-width="80">
      <NGrid responsive="screen" item-responsive :x-gap="8" :y-gap="8" cols="1 s:1 m:5 l:5 xl:5 2xl:5">
        <NGridItem span="4">
          <NGrid responsive="screen" item-responsive :x-gap="8">
            <NFormItemGi span="24 s:8 m:12" :label="$t('page.health.device.message.departmentName')" path="orgId">
              <NTreeSelect
                v-model:value="model.orgId"
                size="small"
                checkable
                filterable
                key-field="id"
                label-field="name"
                default-expand-all
                :max-tag-count="7"
                :placeholder="$t('page.health.device.message.form.departmentName')"
                :options="props.orgUnitsTree"
              />
            </NFormItemGi>
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.message.userName')" path="userId">
              <NSelect
                v-model:value="model.userId"
                size="small"
                :placeholder="$t('page.health.device.message.form.userName')"
                :options="userOptions"
              />
            </NFormItemGi>
            <NFormItemGi span="24 s:12 m:6" :label="$t('page.health.chart.dataType')" path="dataType" class="pr-24px">
              <NSelect
                v-model:value="model.dataType"
                :placeholder="$t('page.health.chart.dataType')"
                :options="featureOptions"
                :loading="featureOptions.length === 0"
              />
            </NFormItemGi>
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.data.info.startDate')" path="startDate">
              <NDatePicker v-model:value="model.startDate" size="small" :placeholder="$t('page.health.data.info.form.startDate')" />
            </NFormItemGi>
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.data.info.endDate')" path="endDate">
              <NDatePicker v-model:value="model.endDate" size="small" :placeholder="$t('page.health.data.info.form.endDate')" />
            </NFormItemGi>
          </NGrid>
        </NGridItem>
        <NGridItem>
          <NFormItemGi span="24 s:8 m:6">
            <NSpace class="w-full" justify="end">
              <NButton type="primary" ghost @click="search">
                <template #icon>
                  <icon-ic-round-search class="text-icon" />
                </template>
                {{ $t('common.search') }}
              </NButton>
              <NButton quaternary @click="reset">
                <template #icon>
                  <icon-ic-round-refresh class="text-icon" />
                </template>
                {{ $t('common.reset') }}
              </NButton>
            </NSpace>
          </NFormItemGi>
        </NGridItem>
      </NGrid>
    </NForm>
  </NCard>
</template>

<style scoped></style>
