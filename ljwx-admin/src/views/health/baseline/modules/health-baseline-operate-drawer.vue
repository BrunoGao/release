<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddHealthBaseline, fetchUpdateHealthBaselineInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'THealthBaselineOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.HealthBaseline | null;
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

type Model = Api.Health.HealthBaseline;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    deviceSn: '',
    userId: 0,
    orgId: '',
    customerId: 0,
    featureName: '',
    baselineDate: '',
    meanValue: 0,
    stdValue: 0,
    minValue: 0,
    maxValue: 0,
    sampleCount: 0,
    current: 0,
    baselineTime: '',
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
  const func = isAdd.value ? fetchAddHealthBaseline : fetchUpdateHealthBaselineInfo;
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
  <NDrawer v-model:show="visible" display-directive="show" :width="360" class="enhanced-drawer health-theme">
    <NDrawerContent :title="title" :native-scrollbar="false" closable class="enhanced-drawer health-theme">
      <NForm ref="formRef" :model="model"></NForm>
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
