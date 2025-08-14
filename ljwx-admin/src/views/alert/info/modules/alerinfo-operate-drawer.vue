<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddAlertInfo, fetchGetEditUserInfo, fetchUpdateAlertInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'TAlertInfoOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.AlertInfo | null;
  /** the org units tree */
  orgUnitsTree: Array<any>;
  /** the user options */
  userOptions: Array<any>;
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
console.log(dictOptions('alert_type'));
const { formRef, validate, restoreValidation } = useNaiveForm();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: $t('common.add'),
    edit: $t('common.edit')
  };
  return titles[props.operateType];
});

type Model = Api.Health.AlertInfo;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    id: '',
    alertType: '',
    departmentInfo: '',
    userId: '',
    deviceSn: '',
    alertTimestamp: '',
    alertStatus: '',
    severityLevel: '',
    alertDesc: '',
    createUser: '',
    createTime: '',
    updateUser: '',
    updateTime: '',
    healthId: 0,
    customerId: 0,
    ruleId: 102
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
  const { error: userErr, data: userData } = await fetchGetEditUserInfo(model.userId);
  console.log('userData', userData);
  if (userErr || !userData?.deviceSn) {
    window.$message?.error('用户没有绑定手表');
    return;
  }
  model.deviceSn = userData.deviceSn;
  const func = isAdd.value ? fetchAddAlertInfo : fetchUpdateAlertInfo;
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
        <NFormItem span="24 s:8 m:12" :label="$t('page.health.device.message.departmentName')" path="departmentName">
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
        </NFormItem>
        <NFormItem span="24 s:8 m:6" :label="$t('page.health.device.message.userName')" path="userId">
          <NSelect v-model:value="model.userId" size="small" :placeholder="$t('page.health.device.message.form.userName')" :options="userOptions" />
        </NFormItem>
        <NFormItem :label="$t('page.health.alert.info.alertType')" path="alertType">
          <NSelect v-model:value="model.alertType" :options="dictOptions('alert_type')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.alert.info.alertDesc')" path="alertDesc">
          <NInput v-model:value="model.alertDesc" :placeholder="$t('page.health.alert.info.form.alertDesc')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.alert.info.alertStatus')" path="alertStatus">
          <NSelect v-model:value="model.alertStatus" :options="dictOptions('alert_status')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.alert.info.severityLevel')" path="severityLevel">
          <NSelect v-model:value="model.severityLevel" :options="dictOptions('severity_level')" />
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
