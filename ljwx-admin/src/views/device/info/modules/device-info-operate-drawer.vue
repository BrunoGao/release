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
    Object.assign(model, {
      ...props.rowData,
      networkAccessMode: Number(props.rowData.networkAccessMode) || 0,
      batteryLevel: Number(props.rowData.batteryLevel) || 0
    });
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
  <NDrawer v-model:show="visible" display-directive="show" :width="420" class="enhanced-drawer device-theme">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <!-- 操作横幅 -->
      <div class="operation-banner">
        <div class="banner-icon">
          <i class="i-material-symbols:devices" v-if="isAdd"></i>
          <i class="i-material-symbols:settings" v-else></i>
        </div>
        <div class="banner-content">
          <h3 class="banner-title">{{ isAdd ? '新增设备' : '编辑设备' }}</h3>
          <p class="banner-desc">{{ isAdd ? '配置新设备的基本信息和参数' : '修改设备配置信息，确保数据准确性' }}</p>
        </div>
      </div>

      <NForm ref="formRef" :model="model">
        <!-- 基本信息 -->
        <div class="form-section">
          <div class="section-title">
            <i class="i-material-symbols:info"></i>
            基本信息
          </div>
          
          <NFormItem :label="$t('page.health.device.info.systemSoftwareVersion')" path="systemSoftwareVersion">
            <NInput
              v-model:value="model.systemSoftwareVersion"
              :placeholder="$t('page.health.device.info.form.systemSoftwareVersion')"
              :disabled="!isAdd"
            >
              <template #prefix>
                <i class="i-material-symbols:system-update"></i>
              </template>
            </NInput>
            <div class="help-text" v-if="!isAdd">系统版本不可修改</div>
          </NFormItem>
          
          <NFormItem :label="$t('page.health.device.info.serialNumber')" path="serialNumber">
            <NInput v-model:value="model.serialNumber" :placeholder="$t('page.health.device.info.form.serialNumber')">
              <template #prefix>
                <i class="i-material-symbols:tag"></i>
              </template>
            </NInput>
          </NFormItem>
          
          <NFormItem :label="$t('page.health.device.info.model')" path="model">
            <NSelect v-model:value="model.model" :options="dictOptions('device_model')">
              <template #arrow>
                <i class="i-material-symbols:smartphone"></i>
              </template>
            </NSelect>
          </NFormItem>
        </div>

        <!-- 网络配置 -->
        <div class="form-section">
          <div class="section-title">
            <i class="i-material-symbols:network-wifi"></i>
            网络配置
          </div>
          
          <NFormItem :label="$t('page.health.device.info.networkAccessMode')" path="networkAccessMode">
            <NInputNumber v-model:value="model.networkAccessMode" :placeholder="$t('page.health.device.info.form.networkAccessMode')">
              <template #prefix>
                <i class="i-material-symbols:router"></i>
              </template>
            </NInputNumber>
            <div class="help-text">网络访问模式配置</div>
          </NFormItem>
        </div>

        <!-- 设备状态 -->
        <div class="form-section">
          <div class="section-title">
            <i class="i-material-symbols:health-and-safety"></i>
            设备状态
          </div>
          
          <NFormItem :label="$t('page.health.device.info.wearableStatus')" path="wearableStatus">
            <NSelect v-model:value="model.wearableStatus" :options="dictOptions('wear_status')">
              <template #arrow>
                <i class="i-material-symbols:watch"></i>
              </template>
            </NSelect>
          </NFormItem>
          
          <NFormItem :label="$t('page.health.device.info.batterylevel')" path="batteryLevel">
            <NInputNumber v-model:value="model.batteryLevel" :placeholder="$t('page.health.device.info.form.batterylevel')">
              <template #prefix>
                <i class="i-material-symbols:battery-full"></i>
              </template>
            </NInputNumber>
            <div class="help-text">电池电量 (0-100%)</div>
          </NFormItem>
          
          <NFormItem :label="$t('page.health.device.info.chargingStatus')" path="chargingStatus">
            <NSelect v-model:value="model.chargingStatus" :options="dictOptions('charging_status')">
              <template #arrow>
                <i class="i-material-symbols:charging-station"></i>
              </template>
            </NSelect>
          </NFormItem>
          
          <NFormItem :label="$t('page.health.device.info.status')" path="status">
            <NSelect v-model:value="model.status" :options="dictOptions('device_status')">
              <template #arrow>
                <i class="i-material-symbols:power"></i>
              </template>
            </NSelect>
          </NFormItem>
        </div>
      </NForm>
      
      <template #footer>
        <div class="drawer-footer">
          <NButton @click="closeDrawer" class="cancel-btn">
            <template #icon>
              <i class="i-material-symbols:close"></i>
            </template>
            {{ $t('common.cancel') }}
          </NButton>
          <NButton type="primary" @click="handleSubmit" class="submit-btn">
            <template #icon>
              <i class="i-material-symbols:check"></i>
            </template>
            {{ isAdd ? $t('common.add') : $t('common.update') }}
          </NButton>
        </div>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
