<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddAlertRules, fetchUpdateAlertRulesInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'TAlertRulesOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.AlertRules | null;
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

type Model = Api.Health.AlertRules;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    id: '',
    ruleType: '',
    physicalSign: '',
    thresholdMin: 0,
    thresholdMax: 0,
    deviationPercentage: 0,
    trendDuration: 0,
    parameters: '',
    triggerCondition: '',
    alertMessage: '',
    severityLevel: '',
    notificationType: '',
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
  const func = isAdd.value ? fetchAddAlertRules : fetchUpdateAlertRulesInfo;
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
        <NFormItem :label="$t('page.health.alert.rules.ruleType')" path="ruleType">
          <NSelect
            v-model:value="model.ruleType"
            size="small"
            :placeholder="$t('page.health.alert.rules.form.ruleType')"
            :options="dictOptions('alert_type')"
            clearable
          />
        </NFormItem>
        <NFormItem :label="$t('page.health.alert.rules.physicalSign')" path="physicalSign">
          <NSelect
            v-model:value="model.physicalSign"
            size="small"
            :placeholder="$t('page.health.alert.rules.form.physicalSign')"
            :options="dictOptions('health_data_type')"
            clearable
          />
        </NFormItem>
        <NFormItem :label="$t('page.health.alert.rules.thresholdMin')" path="thresholdMin">
          <NInputNumber v-model:value="model.thresholdMin" :placeholder="$t('page.health.alert.rules.form.thresholdMin')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.alert.rules.thresholdMax')" path="thresholdMax">
          <NInputNumber v-model:value="model.thresholdMax" :placeholder="$t('page.health.alert.rules.form.thresholdMax')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.alert.rules.trendDuration')" path="trendDuration">
          <NInputNumber v-model:value="model.trendDuration" :placeholder="$t('page.health.alert.rules.form.trendDuration')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.alert.rules.severityLevel')" path="severityLevel">
          <NSelect
            v-model:value="model.severityLevel"
            size="small"
            :placeholder="$t('page.health.alert.rules.form.severityLevel')"
            :options="dictOptions('severity_level')"
            clearable
          />
        </NFormItem>
        <NFormItem :label="$t('page.health.alert.rules.alertMessage')" path="alertMessage">
          <NInput v-model:value="model.alertMessage" :placeholder="$t('page.health.alert.rules.form.alertMessage')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.alert.rules.notificationType')" path="notificationType">
          <NSelect
            v-model:value="model.notificationType"
            size="small"
            :placeholder="$t('page.health.alert.rules.form.notificationType')"
            :options="dictOptions('notification_type')"
            clearable
          />
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
