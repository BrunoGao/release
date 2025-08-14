<script setup lang="tsx">
import { NButton, NIcon, NPopconfirm, NTag, type TagProps } from 'naive-ui';
import type { Ref } from 'vue';
import { onMounted, ref, shallowRef, watch } from 'vue';
import { BatteryChargingOutline, BatteryDeadOutline, BatteryFullOutline } from '@vicons/ionicons5';
import { useAppStore } from '@/store/modules/app';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteDeviceInfo, fetchGetDeviceInfoList, fetchGetInterfaceList, fetchGetOrgUnitsTree } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { convertToBeijingTime } from '@/utils/date';
import { handleBindUsersByOrgId } from '@/utils/deviceUtils';
import TDeviceInfoSearch from './modules/device-info-search.vue';
import TDeviceInfoOperateDrawer from './modules/device-info-operate-drawer.vue';
defineOptions({
  name: 'TDeviceInfoPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();

const authStore = useAuthStore();
const { hasAuth } = useAuth();

const { dictTag } = useDict();

const editingData: Ref<Api.Health.DeviceInfo | null> = ref(null);
const customerId = authStore.userInfo?.customerId;
const deviceInactiveThreshold = ref(60000); // 默认60秒，动态获取

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetDeviceInfoList,
  apiParams: {
    page: 1,
    pageSize: 20,
    imei: null,
    model: null,
    status: null,
    wearableStatus: null,
    chargingStatus: null,
    orgId: customerId,
    userId: null
  },
  columns: () => [
    { type: 'selection', width: 40, align: 'center' },
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },
    {
      key: 'orgName',
      title: $t('page.health.data.info.departmentInfo'),
      align: 'center',
      width: 200
    },
    {
      key: 'userName',
      title: $t('page.health.data.info.username'),
      align: 'center',
      width: 200
    },
    {
      key: 'systemSoftwareVersion',
      title: $t('page.health.device.info.systemSoftwareVersion'),
      align: 'center',
      minWidth: 200
    },
    {
      key: 'serialNumber',
      title: $t('page.health.device.info.serialNumber'),
      align: 'center',
      width: 180
    },
    {
      key: 'model',
      title: $t('page.health.device.info.model'),
      align: 'center',
      minWidth: 50,
      render: row => {
        const systemVersion = row.systemSoftwareVersion || '';
        const match = systemVersion.match(/^([A-Z0-9-]+)CN/);
        const model = match ? match[1] : 'Unknown';
        return model;
      }
    },

    {
      key: 'wearableStatus',
      title: $t('page.health.device.info.wearableStatus'),
      align: 'center',
      minWidth: 100,
      render: row => dictTag('wear_status', row.wearableStatus)
    },
    {
      key: 'batteryLevel',
      title: $t('page.health.device.info.batterylevel'),
      align: 'center',
      render: row => {
        // const batteryLevelStr = row.batteryLevel || '0%';
        // const batteryLevel = Number.parseInt(batteryLevelStr.replace('%', ''), 10); // Extract numeric value
        let type: TagProps['type'] = 'default'; // Default type

        if (row.batteryLevel >= 80) {
          type = 'success';
        } else if (row.batteryLevel < 20) {
          type = 'error';
        }

        return <NTag type={type}>{row.batteryLevel}%</NTag>; // Use NTag for styling
      }
    },
    {
      key: 'chargingStatus',
      title: $t('page.health.device.info.chargingStatus'),
      align: 'center',
      render: row => {
        const statusIcon: Record<string, any> = {
          CHARGING: BatteryChargingOutline,
          'fully charged': BatteryFullOutline,
          NOT_CHARGING: BatteryDeadOutline
        };
        const statusColor: Record<string, TagProps['type']> = {
          CHARGING: 'info',
          'fully charged': 'success',
          NOT_CHARGING: 'error'
        };
        const statusText: Record<string, string> = {
          NOT_CHARGING: '未充电',
          CHARGING: '充电',
          'fully charged': '已充满'
        };
        return (
          <NTag type={statusColor[row.chargingStatus]} style="display: flex; align-items: center;">
            <NIcon component={statusIcon[row.chargingStatus]} style="margin-right: 4px;" />
            {statusText[row.chargingStatus] || row.chargingStatus}
          </NTag>
        );
      }
    },
    {
      key: 'status',
      title: $t('page.health.device.info.status'),
      align: 'center',
      minWidth: 200,
      render: row => {
        const now = Date.now(); // 当前时间戳（毫秒）
        const rowTime = new Date(row.timestamp).getTime(); // 设备上报时间戳
        const diffMs = now - rowTime;
        const status = diffMs > deviceInactiveThreshold.value ? 'INACTIVE' : row.status;
        console.log('deviceInactiveThreshold', deviceInactiveThreshold.value);

        return dictTag('device_status', status);
      }
    },
    {
      key: 'updateTime',
      title: $t('page.health.device.info.updateTime'),
      align: 'center',
      minWidth: 200,
      render: row => convertToBeijingTime(row.updateTime)
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 200,
      minWidth: 200,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('t:device:info:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:device:info:delete') && (
            <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
              {{
                default: () => $t('common.confirmDelete'),
                trigger: () => (
                  <NButton type="error" quaternary size="small">
                    {$t('common.delete')}
                  </NButton>
                )
              }}
            </NPopconfirm>
          )}
        </div>
      )
    }
  ]
});

const { drawerVisible, openDrawer, checkedRowKeys, onDeleted, onBatchDeleted } = useTableOperate(data, getData);

function handleAdd() {
  operateType.value = 'add';
  openDrawer();
}

function edit(item: Api.Health.DeviceInfo) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteDeviceInfo(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteDeviceInfo(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}
type OrgUnitsTree = Api.SystemManage.OrgUnitsTree;

/** org units tree data */
const orgUnitsTree = shallowRef<OrgUnitsTree[]>([]);
const userOptions = ref<{ label: string; value: string }[]>([]);

// 获取设备接口配置
async function fetchDeviceInactiveThreshold() {
  const { error, data: interfaceData } = await fetchGetInterfaceList({
    customerId,
    page: 1,
    pageSize: 100,
  });

  if (!error && interfaceData?.records?.length > 0) {
    const uploadDeviceInterface = interfaceData.records.find((item) =>
      item.url?.includes('upload_device_info')
    );

    if (uploadDeviceInterface) {
      deviceInactiveThreshold.value =
        (uploadDeviceInterface.callInterval || 60) * 1000; // 转换为毫秒
    }
  }
}

async function handleInitOptions() {
  await fetchDeviceInactiveThreshold();
  fetchGetOrgUnitsTree(customerId).then(({ error, data: treeData }) => {
    if (!error && treeData) {
      orgUnitsTree.value = treeData;
      // 初始化时获取第一个部门的员工列表
      if (treeData.length > 0) {
        handleBindUsersByOrgId(treeData[0].id).then(result => {
          if (Array.isArray(result)) {
            userOptions.value = result;
          }
        });
      }
    }
  });
}

// 监听部门变化，更新员工列表
watch(
  () => searchParams.departmentInfo,
  async newValue => {
    if (newValue) {
      const result = await handleBindUsersByOrgId(String(newValue));
      if (Array.isArray(result)) {
        userOptions.value = result;
      }
    }
  }
);
onMounted(() => {
  handleInitOptions();
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <TDeviceInfoSearch
      v-model:model="searchParams"
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="t:device:info:add"
        delete-auth="t:device:info:delete"
        @add="handleAdd"
        @delete="handleBatchDelete"
        @refresh="getData"
      />
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        remote
        striped
        size="small"
        class="sm:h-full"
        :data="data"
        :scroll-x="962"
        :columns="columns"
        :flex-height="!appStore.isMobile"
        :loading="loading"
        :single-line="false"
        :row-key="row => row.id"
        :pagination="mobilePagination"
      />
      <TDeviceInfoOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>
