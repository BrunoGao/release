<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddHealthDataConfig, fetchUpdateHealthDataConfigInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'THealthDataConfigOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Customer.HealthDataConfig | null;
}

const props = defineProps<Props>();

interface Emits {
  (e: 'submitted'): void;
}

const emit = defineEmits<Emits>();

const visible = defineModel<boolean>('visible', {
  default: false
});

const { dictOptions } = useDict();
const { formRef, validate, restoreValidation } = useNaiveForm();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: $t('common.add'),
    edit: $t('common.edit')
  };
  return titles[props.operateType];
});

type Model = Api.Customer.HealthDataConfig;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    id: '',
    customerId: 0,
    dataType: '',
    frequencyInterval: 0,
    isRealtime: 0,
    isEnabled: 0,
    isDefault: 0,
    createUser: '',
    createTime: '',
    updateUser: '',
    updateTime: ''
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
  const func = isAdd.value ? fetchAddHealthDataConfig : fetchUpdateHealthDataConfigInfo;
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
        <NFormItem :label="$t('page.health.data.config.dataType')" path="dataType">
          <NInput v-model:value="model.dataType" :placeholder="$t('page.health.data.config.form.dataType')" :disabled="!isAdd" />
        </NFormItem>
        <NFormItem :label="$t('page.health.data.config.frequencyInterval')" path="frequencyInterval">
          <NInputNumber v-model:value="model.frequencyInterval" :placeholder="$t('page.health.data.config.form.frequencyInterval')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.data.config.isRealtime')" path="isRealtime">
          <NRadioGroup v-model:value="model.isRealtime">
            <NInputNumber v-model:value="model.isRealtime" :placeholder="$t('page.health.data.config.form.isRealtime')" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.health.data.config.isEnabled')" path="isEnabled">
          <NRadioGroup v-model:value="model.isEnabled">
            <NInputNumber v-model:value="model.isEnabled" :placeholder="$t('page.health.data.config.form.isEnabled')" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.customer.healthDataConfig.warningHigh')" path="warningHigh">
          <NRadioGroup v-model:value="model.warningHigh">
            <NInputNumber v-model:value="model.warningHigh" :placeholder="$t('page.customer.healthDataConfig.form.warningHigh')" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.customer.healthDataConfig.warningLow')" path="warningLow">
          <NRadioGroup v-model:value="model.warningLow">
            <NInputNumber v-model:value="model.warningLow" :placeholder="$t('page.customer.healthDataConfig.form.warningLow')" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.customer.healthDataConfig.warningCnt')" path="warningCnt">
          <NInputNumber v-model:value="model.warningCnt" :placeholder="$t('page.customer.healthDataConfig.form.warningCnt')" />
        </NFormItem>
        <NFormItem :label="$t('page.customer.healthDataConfig.weight')" path="weight">
          <NInputNumber v-model:value="model.weight" :placeholder="$t('page.customer.healthDataConfig.form.weight')" />
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
