<script setup lang="ts">
import { watch } from 'vue';
import { $t } from '@/locales';
import { useDict } from '@/hooks/business/dict';
defineOptions({
  name: 'TDeviceInfoSearch'
});

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Health.DeviceInfoSearchParams>('model', { required: true });

const { dictOptions } = useDict();

// Define the customerId prop
const props = defineProps<{
  orgUnitsTree: Array<any>;
  userOptions: Array<any>;
}>();

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}

// 监听选择字段变化，处理'all'选项
watch(
  () => [model.value.model, model.value.status, model.value.wearableStatus, model.value.chargingStatus],
  ([model_val, status_val, wearable_val, charging_val]) => {
    if (model_val === 'all') model.value.model = null;
    if (status_val === 'all') model.value.status = null;
    if (wearable_val === 'all') model.value.wearableStatus = null;
    if (charging_val === 'all') model.value.chargingStatus = null;
  }
);
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper rounded p-4 shadow-sm">
    <NForm :model="model" label-placement="left" :show-feedback="false" :label-width="90" class="gap-8px">
      <NGrid responsive="screen" item-responsive :x-gap="12" :y-gap="8" cols="1 s:1 m:5 l:5 xl:5 2xl:5">
        <NGridItem span="4">
          <NGrid responsive="screen" item-responsive :x-gap="12">
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
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.message.userName')" path="userName">
              <NSelect
                v-model:value="model.userId"
                size="small"
                :placeholder="$t('page.health.device.message.form.userName')"
                :options="userOptions"
              />
            </NFormItemGi>
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.info.model')" path="model">
              <NSelect v-model:value="model.model" :options="[{ label: '全部', value: 'all' }, ...dictOptions('device_model')]" size="small" />
            </NFormItemGi>
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.info.status')" path="status">
              <NSelect v-model:value="model.status" :options="[{ label: '全部', value: 'all' }, ...dictOptions('device_status')]" size="small" />
            </NFormItemGi>
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.info.wearableStatus')" path="wearableStatus">
              <NSelect
                v-model:value="model.wearableStatus"
                :options="[{ label: '全部', value: 'all' }, ...dictOptions('wear_status')]"
                size="small"
              />
            </NFormItemGi>
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.info.chargingStatus')" path="chargingStatus">
              <NSelect
                v-model:value="model.chargingStatus"
                :options="[{ label: '全部', value: 'all' }, ...dictOptions('charging_status')]"
                size="small"
              />
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
