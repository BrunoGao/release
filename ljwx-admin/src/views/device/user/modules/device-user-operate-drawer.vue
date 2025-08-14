<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddDeviceUser, fetchUpdateDeviceUserInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'TDeviceUserOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.DeviceUser | null;
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

type Model = Api.Health.DeviceUser;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    deviceId: 0,
    userId: 0,
    bindTime: '',
    unbindTime: '',
    status: '1',
    createUser: '',
    createTime: '',
    id: '',
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
  const func = isAdd.value ? fetchAddDeviceUser : fetchUpdateDeviceUserInfo;
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
        <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.user.deviceId')" path="deviceId">
          <NInput v-model:value="model.deviceId" size="small" :placeholder="$t('page.health.device.user.form.deviceId')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.user.userId')" path="userId">
          <NInput v-model:value="model.userId" size="small" :placeholder="$t('page.health.device.user.form.userId')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.user.status')" path="status">
          <NInput v-model:value="model.status" size="small" :placeholder="$t('page.health.device.user.form.status')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.user.createUser')" path="createUser">
          <NInput v-model:value="model.createUser" size="small" :placeholder="$t('page.health.device.user.form.createUser')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.user.createTime')" path="createTime">
          <NInput v-model:value="model.createTime" size="small" :placeholder="$t('page.health.device.user.form.createTime')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.user.bindTime')" path="bindTime">
          <NInput v-model:value="model.bindTime" size="small" :placeholder="$t('page.health.device.user.form.bindTime')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:8 m:6" :label="$t('page.health.device.user.unbindTime')" path="unbindTime">
          <NInput v-model:value="model.unbindTime" size="small" :placeholder="$t('page.health.device.user.form.unbindTime')" />
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
