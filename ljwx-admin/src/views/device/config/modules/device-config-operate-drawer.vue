<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddDeviceConfig, fetchUpdateDeviceConfigInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'TDeviceConfigOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.DeviceConfig | null;
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

type Model = Api.Health.DeviceConfig;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    stressmonitoringenabled: 0,
    stepsmonitoringenabled: 0,
    distancemonitoringenabled: 0,
    caloriemonitoringenabled: 0,
    sleepmonitoringenabled: 0,
    ecgmonitoringenabled: 0,
    locationmonitoringenabled: 0,
    soseventlistenerenabled: 0,
    doubleclickeventlistenerenabled: 0,
    temperatureabnormallistenerenabled: 0,
    heartrateabnormallistenerenabled: 0,
    stressabnormallistenerenabled: 0,
    falleventlistenerenabled: 0,
    spo2abnormallistenerenabled: 0,
    oneclickalarmlistenerenabled: 0,
    wearingstatuslistenerenabled: 0,
    createUser: '',
    createTime: ''
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
  const func = isAdd.value ? fetchAddDeviceConfig : fetchUpdateDeviceConfigInfo;
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
  <NDrawer v-model:show="visible" display-directive="show" :width="360" class="enhanced-drawer device-theme">
    <NDrawerContent :title="title" :native-scrollbar="false" closable class="enhanced-drawer device-theme">
      <NForm ref="formRef" :model="model">
        <NFormItem :label="$t('page.customer.interface.name')" path="name">
          <NInput v-model:value="model.name" :placeholder="$t('page.customer.interface.form.name')" :disabled="!isAdd" />
        </NFormItem>
        <NFormItem :label="$t('page.customer.interface.url')" path="url">
          <NInput v-model:value="model.url" :placeholder="$t('page.customer.interface.form.url')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.data.config.isRealtime')" path="isRealtime">
          <NRadioGroup v-model:value="model.callInterval">
            <NInputNumber v-model:value="model.callInterval" :placeholder="$t('page.customer.interface.form.callInterval')" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.customer.interface.enabled')" path="enabled">
          <NRadioGroup v-model:value="model.method">
            <NInput v-model:value="model.method" :placeholder="$t('page.customer.interface.form.method')" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.customer.interface.description')" path="description">
          <NRadioGroup v-model:value="model.description">
            <NInput v-model:value="model.description" :placeholder="$t('page.customer.interface.form.description')" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.customer.interface.enabled')" path="enabled">
          <NRadioGroup v-model:value="model.enabled">
            <NInputNumber v-model:value="model.enabled" :placeholder="$t('page.customer.interface.form.enabled')" />
          </NRadioGroup>
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
