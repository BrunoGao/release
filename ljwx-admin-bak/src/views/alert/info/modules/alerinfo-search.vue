<script setup lang="ts">
import { ref, watch } from 'vue';
import { $t } from '@/locales';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'TAlertInfoSearch'
});

interface Props {
  orgUnitsTree: Array<any>;
  userOptions: Array<any>;
}

const props = defineProps<Props>();

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Health.AlertInfoSearchParams>('model', { required: true });

const { dictOptions } = useDict();

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}

watch(
  () => [model.value.alertType, model.value.alertStatus],
  ([alertType_val, alertStatus_val]) => {
    if (alertType_val === 'all') model.value.alertType = null;
    if (alertStatus_val === 'all') model.value.alertStatus = null;
  }
);
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
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.message.userName')" path="userName">
              <NSelect
                v-model:value="model.userId"
                size="small"
                :placeholder="$t('page.health.device.message.form.userName')"
                :options="[{ label: '全部', value: 'all' }, ...props.userOptions]"
              />
            </NFormItemGi>
            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.alert.info.alertType')" path="alertType">
              <NSelect v-model:value="model.alertType" :options="[{ label: '全部', value: 'all' }, ...dictOptions('alert_type')]" size="small" />
            </NFormItemGi>

            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.alert.info.alertStatus')" path="alertStatus">
              <NSelect v-model:value="model.alertStatus" :options="[{ label: '全部', value: 'all' }, ...dictOptions('alert_status')]" size="small" />
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
