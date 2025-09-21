<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddInterface, fetchUpdateInterfaceInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'TInterfaceOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Customer.Interface | null;
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

type Model = Api.Customer.Interface;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    name: '',
    url: '',
    callInterval: 0,
    method: '',
    description: '',
    enabled: 0,
    customerId: 0
  };
}

function handleInitModel() {
  if (props.operateType === 'edit' && props.rowData) {
    console.log(props.rowData);
    Object.assign(model, props.rowData);
  } else {
    Object.assign(model, createDefaultModel());
  }
}

function closeDrawer() {
  visible.value = false;
}

const isAdd = computed(() => props.operateType === 'add');

async function handleSubmit() {
  await validate();
  const func = isAdd.value ? fetchAddInterface : fetchUpdateInterfaceInfo;
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
  <NDrawer v-model:show="visible" display-directive="show" :width="360" class="enhanced-drawer">
    <NDrawerContent :title="title" :native-scrollbar="false" closable class="enhanced-drawer">
      <NForm ref="formRef" :model="model">
        <NFormItem :label="$t('page.customer.interface.name')" path="name">
          <NInput v-model:value="model.name" :placeholder="$t('page.customer.interface.form.name')" :disabled="!isAdd" filterable />
        </NFormItem>
        <NFormItem :label="$t('page.customer.interface.url')" path="url">
          <NInput v-model:value="model.url" :placeholder="$t('page.customer.interface.form.url')" filterable />
        </NFormItem>
        <NFormItem :label="$t('page.health.data.config.isRealtime')" path="isRealtime">
          <NRadioGroup v-model:value="model.callInterval">
            <NInputNumber v-model:value="model.callInterval" :placeholder="$t('page.customer.interface.form.callInterval')" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.customer.interface.description')" path="description">
          <NRadioGroup v-model:value="model.description">
            <NInput v-model:value="model.description" :placeholder="$t('page.customer.interface.form.description')" filterable />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.customer.interface.method')" path="method">
          <NRadioGroup v-model:value="model.method">
            <NInput v-model:value="model.method" :placeholder="$t('page.customer.interface.form.method')" filterable />
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
