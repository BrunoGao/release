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
  rowData?: Api.Health.HealthDataConfig | null;
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

type Model = Api.Health.HealthDataConfig;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    configId: 0,
    customerId: 1,
    dataType: '',
    frequencyInterval: 0,
    isRealtime: 0,
    isEnabled: 0,
    isDefault: 0,
    createTime: '',
    id: '',
    createUser: '',
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
  <NDrawer v-model:show="visible" display-directive="show" :width="360" class="enhanced-drawer health-theme">
    <NDrawerContent :title="title" :native-scrollbar="false" closable class="enhanced-drawer health-theme">
      <NForm ref="formRef" :model="model">
        <NFormItem :label="$t('page.health.data.config.configId')" path="configId">
          <NInputNumber v-model:value="model.configId" :placeholder="$t('page.health.data.config.form.configId')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.data.config.dataType')" path="dataType">
          <NInput v-model:value="model.dataType" :placeholder="$t('page.health.data.config.form.dataType')" :disabled="!isAdd" />
        </NFormItem>
        <NFormItem :label="$t('page.health.data.config.frequencyInterval')" path="frequencyInterval">
          <NRadioGroup v-model:value="model.frequencyInterval">
            <NRadio v-for="item in dictOptions('gender')" :key="item.value" :value="item.value" :label="item.label" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.health.data.config.isRealtime')" path="isRealtime">
          <NInputNumber v-model:value="model.isRealtime" :placeholder="$t('page.health.data.config.form.isRealtime')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.data.config.isEnabled')" path="isEnabled">
          <NRadioGroup v-model:value="model.isEnabled">
            <NRadio v-for="item in dictOptions('status')" :key="item.value" :value="item.value" :label="item.label" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.health.data.config.isDefault')" path="isDefault">
          <NRadioGroup v-model:value="model.isDefault">
            <NRadio v-for="item in dictOptions('status')" :key="item.value" :value="item.value" :label="item.label" />
          </NRadioGroup>
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace :size="16">
          <NButton quaternary @click="closeDrawer">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
