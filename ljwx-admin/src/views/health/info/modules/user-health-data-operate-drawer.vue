<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddUserHealthData, fetchUpdateUserHealthDataInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { deviceOptions, handleBindDevice } from '@/utils/deviceUtils';
defineOptions({
  name: 'TUserHealthDataOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.UserHealthData | null;

}

const props = defineProps<Props>();

interface Emits {
  (e: 'submitted'): void;
}

const emit = defineEmits<Emits>();

const visible = defineModel<boolean>('visible', {
  default: false
});

const { formRef, validate, restoreValidation } = useNaiveForm();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: $t('common.add'),
    edit: $t('common.edit')
  };
  return titles[props.operateType];
});

type Model = Api.Health.UserHealthData;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    phoneNumber: '',
    heartRate: 0,
    pressureHigh: 0,
    pressureLow: 0,
    bloodOxygen: 0,
    temperature: 0,
    step: 0,
    timestamp: '',
    userName: '',
    latitude: 0,
    longitude: 0,
    altitude: 0,
    deviceSn: '',
    distance: 0,
    calorie: 0,
    sleepData: '',
    exerciseDailyData: '',
    exerciseDailyWeekData: '',
    scientificSleepData: '',
    startDate: 0,
    endDate: 0
  };
}

function handleInitModel() {
  Object.assign(model, createDefaultModel());

  if (!props.rowData) return;

  if (props.operateType === 'edit' && props.rowData) {
    Object.assign(model, props.rowData);
  }
}

function closeDrawer() {
  visible.value = false;
}

const isAdd = computed(() => props.operateType === 'add');

async function handleSubmit() {
  await validate();
  const func = isAdd.value ? fetchAddUserHealthData : fetchUpdateUserHealthDataInfo;
  const { error, data } = await func(model);
  if (!error && data) {
    window.$message?.success(isAdd.value ? $t('common.addSuccess') : $t('common.updateSuccess'));
    closeDrawer();
    emit('submitted');
  }
}

watch(visible, () => {
  if (visible.value) {
    handleInitModel();
    restoreValidation();
  }
});
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="360">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model">
        <NFormItem :label="$t('page.health.data.info.phonenumber')" path="phoneNumber">
          <NInput v-model:value="model.phoneNumber" :placeholder="$t('page.health.data.info.form.phoneNumber')" :disabled="!isAdd" />
        </NFormItem>
        <NFormItem :label="$t('page.health.data.info.devicesn')" path="deviceSn">
          <NSelect
            v-model:value="model.deviceSn"
            size="small"
            :placeholder="$t('page.health.data.info.form.deviceSn')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.health.data.info.username')" path="userName">
          <NInput v-model:value="model.userName" :placeholder="$t('page.health.data.info.form.userName')" :disabled="!isAdd" />
        </NFormItem>
        <NFormItem :label="$t('page.health.data.info.heartrate')" path="heartRate">
          <NInputNumber v-model:value="model.heartRate" :placeholder="$t('page.health.data.info.form.heartRate')" :disabled="!isAdd" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace>
          <NButton quaternary @click="closeDrawer">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
