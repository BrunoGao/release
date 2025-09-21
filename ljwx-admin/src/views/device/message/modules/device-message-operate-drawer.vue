<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

import { fetchAddDeviceMessage, fetchUpdateDeviceMessageInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { handleBindUsersByOrgId } from '@/utils/deviceUtils';

defineOptions({
  name: 'TDeviceMessageOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.DeviceMessage | null;

  /** the org units tree */
  orgUnitsTree: Array<any>;
  /** the user options */
  userOptions: Array<any>;
}

const props = defineProps<Props>();

interface Emits {
  (e: 'submitted'): void;
  (e: 'updateUserOptions', options: Array<any>): void;
}

const emit = defineEmits<Emits>();

const visible = defineModel<boolean>('visible', {
  default: false
});

const { dictOptions } = useDict();
const { formRef, validate } = useNaiveForm();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: $t('common.add'),
    edit: $t('common.edit')
  };
  return titles[props.operateType];
});

type Model = Api.Health.DeviceMessage;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    messageId: 0,
    orgId: '',
    respondedDetail: { totalUsersWithDevices: 0, nonRespondedUsers: [] },
    userId: '',
    message: '',
    messageType: '',
    senderType: '',
    receiverType: '',
    messageStatus: '1',
    sentTime: '',
    receivedTime: '',
    respondedNumber: 0,
    id: '',
    createUser: '',
    createTime: '',
    updateUser: '',
    updateTime: ''
  };
}

async function handleInitModel() {
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

handleInitModel();

async function handleSubmit() {
  await validate();
  const func = isAdd.value ? fetchAddDeviceMessage : fetchUpdateDeviceMessageInfo;
  const submitData = { ...model };
  if (submitData.userId === 'all' || submitData.userId === '') submitData.userId = undefined as any;
  const { error, data } = await func(submitData);
  if (!error && data) {
    window.$message?.success(isAdd.value ? $t('common.addSuccess') : $t('common.updateSuccess'));
    closeDrawer();
    emit('submitted');
  }
}

watch(
  () => model.orgId,
  async newValue => {
    console.log('orgId changed:', newValue, 'type:', typeof newValue);

    if (newValue) {
      console.log('deptId', newValue);
      const result = await handleBindUsersByOrgId(String(newValue));
      if (Array.isArray(result)) {
        console.log('result', result);
        emit('updateUserOptions', result);
      }
      model.userId = '';
    }
  }
);

watch(
  () => visible.value,
  isVisible => {
    if (isVisible) {
      console.log('drawer opened, current orgId:', model.orgId);
      handleInitModel();
    }
  }
);
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="360" class="enhanced-drawer device-theme">
    <NDrawerContent :title="title" :native-scrollbar="false" closable class="enhanced-drawer device-theme">
      <NForm ref="formRef" :model="model">
        <NFormItem :label="$t('page.health.device.message.departmentName')" path="orgId">
          <NTreeSelect
            v-model:value="model.orgId"
            size="small"
            filterable
            key-field="id"
            label-field="name"
            default-expand-all
            :placeholder="$t('page.health.device.message.form.departmentName')"
            :options="props.orgUnitsTree"
          />
        </NFormItem>
        <NFormItem :label="$t('page.health.device.message.userName')" path="userId">
          <NSelect
            v-model:value="model.userId"
            size="small"
            :placeholder="$t('page.health.device.message.form.userName')"
            :options="props.userOptions"
          />
        </NFormItem>
        <NFormItem :label="$t('page.health.device.message.messageType')" path="messageType">
          <NSelect
            v-model:value="model.messageType"
            :placeholder="$t('page.health.device.message.form.messageType')"
            :options="dictOptions('message_type')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.health.device.message.message')" path="message">
          <NInput v-model:value="model.message" :placeholder="$t('page.health.device.message.form.message')" />
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
