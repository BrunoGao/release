<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddAleractionLog, fetchUpdateAleractionLogInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'TAlertActionLogOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.AleractionLog | null;
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

type Model = Api.Health.AleractionLog;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    logId: 0,
    alertId: 0,
    action: '',
    actionTimestamp: '',
    actionUser: '',
    actionUserId: 0,
    details: ''
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
  const func = isAdd.value ? fetchAddAleractionLog : fetchUpdateAleractionLogInfo;
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
        <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.alert.log.logId')" path="logId">
          <NInput v-model:value="model.logId" size="small" :placeholder="$t('page.health.alert.log.form.logId')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.alert.log.actionUser')" path="actionUser">
          <NInput v-model:value="model.actionUser" size="small" :placeholder="$t('page.health.alert.log.form.actionUser')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.alert.log.result')" path="result">
          <NSelect
            v-model:value="model.result"
            size="small"
            :placeholder="$t('page.health.alert.log.form.result')"
            :options="dictOptions('alert_result')"
          />
        </NFormItemGi>
        <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.alert.log.details')" path="details">
          <NInput v-model:value="model.details" size="small" :placeholder="$t('page.health.alert.log.form.details')" />
        </NFormItemGi>
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
