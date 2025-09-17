<script setup lang="ts">
import { watch } from 'vue';
import { $t } from '@/locales';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'Tdevice.messageSearch'
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

const model = defineModel<Api.Health.DeviceMessageSearchParams>('model', { required: true });

const { dictOptions } = useDict();

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}

// 监听选择字段变化，处理'all'选项
watch(
  () => [model.value.messageType, model.value.messageStatus],
  ([type_val, status_val]) => {
    if (type_val === 'all') model.value.messageType = null;
    if (status_val === 'all') model.value.messageStatus = null;
  }
);
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NForm :model="model" label-placement="left" :show-feedback="false" :label-width="80">
      <NGrid responsive="screen" item-responsive :x-gap="8" :y-gap="8" cols="1 s:1 m:5 l:5 xl:5 2xl:5">
        <NGridItem span="4">
          <NGrid responsive="screen" item-responsive :x-gap="8">
            <NFormItemGi span="24 s:8 m:12" :label="$t('page.health.device.message.departmentName')" path="orgName">
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
                :options="props.userOptions"
              />
            </NFormItemGi>

            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.message.messageType')" path="messageType">
              <NSelect
                v-model:value="model.messageType"
                size="small"
                :placeholder="$t('page.health.device.message.form.messageType')"
                :options="[{ label: '全部', value: 'all' }, ...dictOptions('message_type')]"
              />
            </NFormItemGi>

            <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.message.messageStatus')" path="messageStatus">
              <NSelect
                v-model:value="model.messageStatus"
                size="small"
                :placeholder="$t('page.health.device.message.form.messageStatus')"
                :options="[{ label: '全部', value: 'all' }, ...dictOptions('message_status')]"
              />
            </NFormItemGi>

            <NFormItemGi span="24 s:8 m:6" label="开始日期" path="startDate">
              <NDatePicker
                v-model:value="model.startDate"
                size="small"
                type="date"
                placeholder="选择开始日期"
                :is-date-disabled="(date: number) => date > Date.now()"
              />
            </NFormItemGi>

            <NFormItemGi span="24 s:8 m:6" label="结束日期" path="endDate">
              <NDatePicker
                v-model:value="model.endDate"
                size="small"
                type="date"
                placeholder="选择结束日期"
                :is-date-disabled="(date: number) => date > Date.now()"
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
