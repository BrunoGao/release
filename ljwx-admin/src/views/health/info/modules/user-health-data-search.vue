<script setup lang="ts">
import { $t } from '@/locales';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'TUserHealthDataSearch'
});
const props = defineProps<{
  orgUnitsTree: Array<any>; // Adjust the type according to your data structure
  userOptions: Array<any>;
}>();

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const model = defineModel<Api.Health.UserHealthDataSearchParams>('model', { required: true });

const { dictOptions } = useDict();

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
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
