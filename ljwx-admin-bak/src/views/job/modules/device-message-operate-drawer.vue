<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

import { fetchAddDeviceMessage, fetchUpdateDeviceMessageInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { handleBindUsers } from '@/utils/deviceUtils';
defineOptions({
  name: 'TDeviceMessageOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.DeviceMessage | null;
  /** the device options */
  deviceOptions: Array<any>;
  /** the customer id */
  customerId: number;

  /** the org units tree */
  orgUnitsTree: Array<any>;
}

const props = defineProps<Props>();
const userOptions = ref<Array<any>>([]);
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

type Model = Api.Health.DeviceMessage;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    messageId: 0,
    orgId: '',
    userName: '',
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
const selectedDepartments = ref<{ id: string; name: string } | null>(null);
// 处理部门选择变化
function handleDepartmentChange(key: string) {
  model.orgId = key; // 现在是一个字符串值
  // 从 options 中找到对应的完整信息
  const dept = findDepartment(props.orgUnitsTree, key);
  selectedDepartments.value = dept
    ? {
        id: key,
        name: dept.name
      }
    : null;
  console.log('Selected department:', selectedDepartments.value);
}

// 递归查找部门信息
function findDepartment(tree: any[], id: string): any {
  for (const node of tree) {
    if (node.id === id) return node;
    if (node.children) {
      const found = findDepartment(node.children, id);
      if (found) return found;
    }
  }
  return null;
}

watch(
  () => model.orgId,
  async (newValue, oldValue) => {
    console.log('operate-drawer model.orgId changed from', oldValue, 'to', newValue);
    if (newValue) {
      const result = await handleBindUsers(Number(newValue));
      console.log('handleBindUsers.result', result);
      if (Array.isArray(result)) {
        userOptions.value = result;
      } else {
        console.error('Failed to fetch user options');
      }
    }
  }
);

handleInitModel();

async function handleSubmit() {
  await validate();
  const submitData = {
    ...model,
    orgId: selectedDepartments.value ? selectedDepartments.value.id : ''
  };

  const func = isAdd.value ? fetchAddDeviceMessage : fetchUpdateDeviceMessageInfo;
  const { error, data } = await func(model);
  if (!error && data) {
    window.$message?.success(isAdd.value ? $t('common.addSuccess') : $t('common.updateSuccess'));
    closeDrawer();
    emit('submitted');
  }
}
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="360">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model">
        <NFormItem :label="$t('page.health.device.message.departmentName')" path="departmentName">
          <NTreeSelect
            v-model:value="model.orgId"
            size="small"
            checkable
            filterable
            key-field="id"
            label-field="name"
            default-expand-all
            :max-tag-count="7"
            :placeholder="$t('page.health.device.message.form.departmentName')"
            :options="props.orgUnitsTree"
            @update:value="handleDepartmentChange"
          />
        </NFormItem>
        <NFormItem span="24 s:8 m:6" :label="$t('page.health.device.message.userName')" path="userName">
          <NSelect v-model:value="model.userName" size="small" :placeholder="$t('page.health.device.message.form.userName')" :options="userOptions" />
        </NFormItem>

        <NFormItem :label="$t('page.job.message')" path="message">
          <NInput v-model:value="model.message" :placeholder="$t('page.job.form.message')" />
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
