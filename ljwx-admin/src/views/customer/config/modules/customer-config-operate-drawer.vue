<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddCustomerConfig, fetchUpdateCustomerConfigInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'TCustomerConfigOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Customer.CustomerConfig | null;
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

interface EditModel {
  customerName: string;
  description: string;
  uploadMethod: string;
  licenseKey: number;
  supportLicense: string;
  enableResume: string;
  uploadRetryCount: number;
  cacheMaxCount: number;
}

const model: EditModel = reactive(createDefaultModel());

function createDefaultModel(): EditModel {
  return {
    customerName: '',
    description: '',
    uploadMethod: '',
    licenseKey: 0,
    supportLicense: 'false',
    enableResume: 'false',
    uploadRetryCount: 0,
    cacheMaxCount: 0
  };
}

function handleInitModel() {
  Object.assign(model, createDefaultModel());

  if (!props.rowData) return;

  if (props.operateType === 'edit' && props.rowData) {
    Object.assign(model, {
      ...props.rowData,
      supportLicense: String(props.rowData.supportLicense),
      enableResume: String(props.rowData.enableResume)
    });
  }
}

function closeDrawer() {
  visible.value = false;
}

const isAdd = computed(() => props.operateType === 'add');

async function handleSubmit() {
  await validate();

  const submitData = {
    ...model,
    supportLicense: model.supportLicense === 'true',
    enableResume: model.enableResume === 'true'
  };

  const func = isAdd.value ? fetchAddCustomerConfig : fetchUpdateCustomerConfigInfo;
  const { error, data } = await func(submitData as any);
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

const yesNoOptions = [
  { label: '是', value: 'true' },
  { label: '否', value: 'false' }
];
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="360">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model">
        <NFormItem :label="$t('page.customer.config.customerName')" path="customerName">
          <NInput v-model:value="model.customerName" :placeholder="$t('page.customer.config.form.customerName')" :disabled="!isAdd" />
        </NFormItem>
        <NFormItem :label="$t('page.customer.config.description')" path="description">
          <NInput v-model:value="model.description" :placeholder="$t('page.customer.config.form.description')" />
        </NFormItem>
        <NFormItem :label="$t('page.customer.config.uploadMethod')" path="uploadMethod">
          <NSelect
            v-model:value="model.uploadMethod"
            size="small"
            :placeholder="$t('page.customer.config.form.uploadMethod')"
            :options="dictOptions('upload_method')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.customer.config.licenseKey')" path="licenseKey">
          <NInputNumber v-model:value="model.licenseKey" :placeholder="$t('page.customer.config.form.licenseKey')" />
        </NFormItem>
        <NFormItem :label="$t('page.customer.config.supportLicense')" path="supportLicense">
          <NSelect
            v-model:value="model.supportLicense"
            size="small"
            :placeholder="$t('page.customer.config.form.supportLicense')"
            :options="yesNoOptions"
          />
        </NFormItem>
        <NFormItem :label="$t('page.customer.config.enableResume')" path="enableResume">
          <NSelect
            v-model:value="model.enableResume"
            size="small"
            :placeholder="$t('page.customer.config.form.enableResume')"
            :options="yesNoOptions"
          />
        </NFormItem>
        <NFormItem :label="$t('page.customer.config.uploadRetryCount')" path="uploadRetryCount">
          <NInputNumber v-model:value="model.uploadRetryCount" :placeholder="$t('page.customer.config.form.uploadRetryCount')" />
        </NFormItem>
        <NFormItem :label="$t('page.customer.config.cacheMaxCount')" path="cacheMaxCount">
          <NInputNumber v-model:value="model.cacheMaxCount" :placeholder="$t('page.customer.config.form.cacheMaxCount')" />
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
