<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { $t } from '@/locales';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { useDict } from '@/hooks/business/dict';
import { handleBindUsersByOrgId } from '@/utils/deviceUtils';
defineOptions({
  name: 'HealthChartSearch'
});

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

interface Props {
  orgUnitsTree: Array<any>;
}

const props = defineProps<Props>();

const emit = defineEmits<Emits>();

const { dictOptions } = useDict();

const { formRef, restoreValidation } = useNaiveForm();

const model = defineModel<Api.Health.HealthChartSearchParams>('model', { required: true });

const userOptions = ref<Array<any>>([]);
watch(
  () => model.value.departmentInfo,
  async (newValue, oldValue) => {
    // console.log('search props.orgUnitsTree', props.orgUnitsTree);
    console.log('model.departmentName changed from', oldValue, 'to', newValue);
    if (newValue) {
      const result = await handleBindUsersByOrgId(newValue);
      console.log('handleBindUsers.result', result);
      if (Array.isArray(result)) {
        userOptions.value = result;
      } else {
        console.error('Failed to fetch user options');
      }
    }
  }
);
async function reset() {
  await restoreValidation();
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :title="$t('common.search')" :bordered="false" size="small" class="card-wrapper">
    <NForm ref="formRef" :model="model" :rules="rules" label-placement="left" :label-width="80">
      <NGrid responsive="screen" item-responsive>
        <NFormItemGi span="24 s:8 m:12" :label="$t('page.health.device.message.departmentName')" path="departmentName">
          <NTreeSelect
            v-model:value="model.departmentInfo"
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
          <NSelect v-model:value="model.userName" size="small" :placeholder="$t('page.health.device.message.form.userName')" :options="userOptions" />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.health.chart.dataType')" path="dataType" class="pr-24px">
          <NSelect v-model:value="model.dataType" :placeholder="$t('page.health.chart.dataType')" :options="dictOptions('health_data_type')" />
        </NFormItemGi>

        <NFormItemGi span="24 s:12 m:6" :label="$t('page.health.chart.startDate')" path="startDate" class="pr-24px">
          <NDatePicker v-model:value="model.startDate" :placeholder="$t('page.health.chart.startDate')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.health.chart.endDate')" path="endDate" class="pr-24px">
          <NDatePicker v-model:value="model.endDate" :placeholder="$t('page.health.chart.endDate')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.health.chart.timeType')" path="timeType" class="pr-24px">
          <NSelect v-model:value="model.timeType" :placeholder="$t('page.health.chart.timeType')" :options="dictOptions('time_type')" />
        </NFormItemGi>
        <NFormItemGi span="24 m:12" class="pr-24px">
          <NSpace class="w-full" justify="end">
            <NButton @click="reset">
              <template #icon>
                <icon-ic-round-refresh class="text-icon" />
              </template>
              {{ $t('common.reset') }}
            </NButton>
            <NButton type="primary" ghost @click="search">
              <template #icon>
                <icon-ic-round-search class="text-icon" />
              </template>
              {{ $t('common.search') }}
            </NButton>
          </NSpace>
        </NFormItemGi>
      </NGrid>
    </NForm>
  </NCard>
</template>

<style scoped></style>
