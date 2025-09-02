<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddDeviceInfo, fetchUpdateDeviceInfoInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';

defineOptions({
  name: 'TDeviceInfoOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.DeviceInfo | null;
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

type Model = Api.Health.DeviceInfo;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    id: '',
    createUser: '',
    createTime: '',
    updateUser: '',
    updateTime: '',
    systemSoftwareVersion: '',
    wifiAddress: '',
    bluetoothAddress: '',
    ipAddress: '',
    networkAccessMode: 0,
    serialNumber: '',
    deviceName: '',
    imei: '',
    createdAt: '',
    batteryLevel: '',
    model: '',
    status: '',
    wearableStatus: 0,
    chargingStatus: 0,
    customerId: 0
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
  const func = isAdd.value ? fetchAddDeviceInfo : fetchUpdateDeviceInfoInfo;
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
        <NFormItem :label="$t('page.health.device.info.systemSoftwareVersion')" path="systemSoftwareVersion">
          <NInput
            v-model:value="model.systemSoftwareVersion"
            :placeholder="$t('page.health.device.info.form.systemSoftwareVersion')"
            :disabled="!isAdd"
          />
        </NFormItem>
        <NFormItem :label="$t('page.health.device.info.serialNumber')" path="serialNumber">
          <NInput v-model:value="model.serialNumber" :placeholder="$t('page.health.device.info.form.serialNumber')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.device.info.model')" path="model">
          <NSelect v-model:value="model.model" :options="dictOptions('device_model')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.device.info.networkAccessMode')" path="networkAccessMode">
          <NRadioGroup v-model:value="model.networkAccessMode">
            <NInputNumber v-model:value="model.networkAccessMode" :placeholder="$t('page.health.device.info.form.networkAccessMode')" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.health.device.info.wearableStatus')" path="wearableStatus">
          <NSelect v-model:value="model.wearableStatus" :options="dictOptions('wear_status')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.device.info.batterylevel')" path="batteryLevel">
          <NInputNumber v-model:value="model.batteryLevel" :placeholder="$t('page.health.device.info.form.batterylevel')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.device.info.chargingStatus')" path="chargingStatus">
          <NSelect v-model:value="model.chargingStatus" :options="dictOptions('charging_status')" />
        </NFormItem>
        <NFormItem :label="$t('page.health.device.info.status')" path="status">
          <NSelect v-model:value="model.status" :options="dictOptions('device_status')" />
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
