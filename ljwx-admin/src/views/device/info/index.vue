<script setup lang="tsx">
import { computed, h, onMounted, ref, shallowRef, watch } from 'vue';
import { NButton, NCard, NIcon, NPopconfirm, NTag, type TagProps } from 'naive-ui';
import type { Ref } from 'vue';
import { BatteryChargingOutline, BatteryDeadOutline, BatteryFullOutline } from '@vicons/ionicons5';
import { Icon } from '@iconify/vue';
import SvgIcon from '@/components/custom/svg-icon.vue';
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

// 设备状态中英文映射
const deviceStatusMap = {
  ACTIVE: '在线',
  INACTIVE: '离线',
  CHARGING: '充电中',
  LOW_BATTERY: '低电量',
  MAINTENANCE: '维护中'
};

// 佩戴状态中英文映射
const wearStatusMap = {
  WEARING: '佩戴',
  NOT_WEARING: '未佩戴',
  UNKNOWN: '未知'
};

// 充电状态中英文映射
const chargingStatusMap = {
  CHARGING: '充电中',
  'fully charged': '已充满',
  NOT_CHARGING: '未充电'
};

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
      title: $t('page.health.device.info.orgName'),
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
    pageSize: 100
  });

  if (!error && interfaceData?.records?.length > 0) {
    const uploadDeviceInterface = interfaceData.records.find(item => item.url?.includes('upload_device_info'));

    if (uploadDeviceInterface) {
      deviceInactiveThreshold.value = (uploadDeviceInterface.callInterval || 60) * 1000; // 转换为毫秒
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
  () => searchParams.orgId,
  async newValue => {
    if (newValue) {
      const result = await handleBindUsersByOrgId(String(newValue));
      if (Array.isArray(result)) {
        userOptions.value = result;
      }
    }
  }
);

// 设备统计数据计算
const deviceStatistics = computed(() => {
  if (!data.value || data.value.length === 0) {
    return {
      total: 0,
      byStatus: {},
      byWearStatus: {},
      byChargingStatus: {},
      byModel: {},
      batteryStats: {
        high: 0, // >= 80%
        medium: 0, // 20% - 79%
        low: 0, // < 20%
        average: 0
      },
      onlineRate: 0,
      wearingRate: 0,
      chargingRate: 0,
      lowBatteryCount: 0
    };
  }

  const stats = {
    total: data.value.length,
    byStatus: {} as Record<string, number>,
    byWearStatus: {} as Record<string, number>,
    byChargingStatus: {} as Record<string, number>,
    byModel: {} as Record<string, number>,
    batteryStats: {
      high: 0,
      medium: 0,
      low: 0,
      average: 0
    },
    onlineRate: 0,
    wearingRate: 0,
    chargingRate: 0,
    lowBatteryCount: 0
  };

  let totalBattery = 0;
  let onlineCount = 0;
  let wearingCount = 0;
  let chargingCount = 0;

  data.value.forEach(device => {
    // 计算实时设备状态
    const now = Date.now();
    const deviceTime = new Date(device.timestamp || device.updateTime).getTime();
    const diffMs = now - deviceTime;
    const actualStatus = diffMs > deviceInactiveThreshold.value ? 'INACTIVE' : device.status;
    
    // 按状态统计（翻译为中文）
    const statusKey = deviceStatusMap[actualStatus as keyof typeof deviceStatusMap] || actualStatus || '未知';
    stats.byStatus[statusKey] = (stats.byStatus[statusKey] || 0) + 1;

    // 按佩戴状态统计（翻译为中文）
    const wearStatusKey = wearStatusMap[device.wearableStatus as keyof typeof wearStatusMap] || device.wearableStatus || '未知';
    stats.byWearStatus[wearStatusKey] = (stats.byWearStatus[wearStatusKey] || 0) + 1;

    // 按充电状态统计（翻译为中文）
    const chargingStatusKey = chargingStatusMap[device.chargingStatus as keyof typeof chargingStatusMap] || device.chargingStatus || '未知';
    stats.byChargingStatus[chargingStatusKey] = (stats.byChargingStatus[chargingStatusKey] || 0) + 1;

    // 按设备型号统计
    const systemVersion = device.systemSoftwareVersion || '';
    const match = systemVersion.match(/^([A-Z0-9-]+)CN/);
    const model = match ? match[1] : 'Unknown';
    stats.byModel[model] = (stats.byModel[model] || 0) + 1;

    // 电池统计
    const batteryLevel = device.batteryLevel || 0;
    totalBattery += batteryLevel;
    
    if (batteryLevel >= 80) {
      stats.batteryStats.high++;
    } else if (batteryLevel >= 20) {
      stats.batteryStats.medium++;
    } else {
      stats.batteryStats.low++;
      stats.lowBatteryCount++;
    }

    // 在线、佩戴、充电设备计数
    if (actualStatus === 'ACTIVE') onlineCount++;
    if (device.wearableStatus === 'WEARING') wearingCount++;
    if (device.chargingStatus === 'CHARGING') chargingCount++;
  });

  // 计算比率
  stats.onlineRate = Math.round((onlineCount / stats.total) * 100);
  stats.wearingRate = Math.round((wearingCount / stats.total) * 100);
  stats.chargingRate = Math.round((chargingCount / stats.total) * 100);
  stats.batteryStats.average = Math.round(totalBattery / stats.total);

  return stats;
});

// 设备状态颜色映射
const deviceStatusColors = {
  在线: 'rgba(82, 196, 26, 0.8)', // 绿色
  离线: 'rgba(140, 140, 140, 0.8)', // 灰色
  充电中: 'rgba(24, 144, 255, 0.8)', // 蓝色
  低电量: 'rgba(245, 34, 45, 0.8)', // 红色
  维护中: 'rgba(250, 173, 20, 0.8)' // 橙色
};

// 佩戴状态颜色映射
const wearStatusColors = {
  佩戴: 'rgba(82, 196, 26, 0.8)', // 绿色
  未佩戴: 'rgba(245, 34, 45, 0.8)', // 红色
  未知: 'rgba(140, 140, 140, 0.8)' // 灰色
};

// 充电状态颜色映射
const chargingStatusColors = {
  充电中: 'rgba(24, 144, 255, 0.8)', // 蓝色
  已充满: 'rgba(82, 196, 26, 0.8)', // 绿色
  未充电: 'rgba(250, 173, 20, 0.8)' // 橙色
};

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

    <!-- 设备统计概览卡片 -->
    <NCard :bordered="false" class="card-wrapper">
      <template #header>
        <div class="flex items-center gap-2">
          <icon-mdi:devices class="text-lg text-blue-500" />
          <span class="font-medium">设备统计概览</span>
        </div>
      </template>

      <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
        <!-- 总设备数 -->
        <div class="border border-blue-200 rounded-lg from-blue-50 to-blue-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-blue-600 font-bold">{{ deviceStatistics.total }}</div>
          <div class="mt-1 text-sm text-blue-500">总设备数</div>
        </div>

        <!-- 在线设备 -->
        <div class="border border-green-200 rounded-lg from-green-50 to-green-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-green-600 font-bold">{{ deviceStatistics.onlineRate }}%</div>
          <div class="mt-1 text-sm text-green-500">在线率</div>
        </div>

        <!-- 佩戴设备 -->
        <div class="border border-purple-200 rounded-lg from-purple-50 to-purple-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-purple-600 font-bold">{{ deviceStatistics.wearingRate }}%</div>
          <div class="mt-1 text-sm text-purple-500">佩戴率</div>
        </div>

        <!-- 低电量设备 -->
        <div class="border border-red-200 rounded-lg from-red-50 to-red-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-red-600 font-bold">{{ deviceStatistics.lowBatteryCount }}</div>
          <div class="mt-1 text-sm text-red-500">低电量设备</div>
        </div>
      </div>

      <!-- 电池统计 -->
      <div class="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <!-- 平均电量 -->
        <div class="border border-yellow-200 rounded-lg from-yellow-50 to-yellow-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-yellow-600 font-bold">{{ deviceStatistics.batteryStats.average }}%</div>
          <div class="mt-1 text-sm text-yellow-500">平均电量</div>
        </div>

        <!-- 高电量设备 -->
        <div class="border border-emerald-200 rounded-lg from-emerald-50 to-emerald-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-emerald-600 font-bold">{{ deviceStatistics.batteryStats.high }}</div>
          <div class="mt-1 text-sm text-emerald-500">高电量设备(≥80%)</div>
        </div>

        <!-- 中等电量设备 -->
        <div class="border border-amber-200 rounded-lg from-amber-50 to-amber-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-amber-600 font-bold">{{ deviceStatistics.batteryStats.medium }}</div>
          <div class="mt-1 text-sm text-amber-500">中等电量设备(20%-79%)</div>
        </div>

        <!-- 充电中设备 -->
        <div class="border border-cyan-200 rounded-lg from-cyan-50 to-cyan-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-cyan-600 font-bold">{{ deviceStatistics.chargingRate }}%</div>
          <div class="mt-1 text-sm text-cyan-500">充电率</div>
        </div>
      </div>

      <!-- 详细统计分布 -->
      <div class="grid grid-cols-1 mt-6 gap-6 lg:grid-cols-4">
        <!-- 设备状态分布 -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h4 class="mb-3 flex items-center gap-2 text-gray-700 font-medium">
            <icon-mdi:power class="text-green-500" />
            设备状态分布
          </h4>
          <div class="max-h-48 overflow-y-auto space-y-2">
            <div v-for="(count, status) in deviceStatistics.byStatus" :key="status" class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="h-3 w-3 rounded-full" :style="{ backgroundColor: deviceStatusColors[status] || '#ccc' }"></div>
                <span class="text-sm text-gray-600">{{ status }}</span>
              </div>
              <span class="text-sm text-gray-800 font-medium">{{ count }}</span>
            </div>
          </div>
        </div>

        <!-- 佩戴状态分布 -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h4 class="mb-3 flex items-center gap-2 text-gray-700 font-medium">
            <icon-mdi:watch class="text-purple-500" />
            佩戴状态分布
          </h4>
          <div class="space-y-2">
            <div v-for="(count, wearStatus) in deviceStatistics.byWearStatus" :key="wearStatus" class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="h-3 w-3 rounded-full" :style="{ backgroundColor: wearStatusColors[wearStatus] || '#ccc' }"></div>
                <span class="text-sm text-gray-600">{{ wearStatus }}</span>
              </div>
              <span class="text-sm text-gray-800 font-medium">{{ count }}</span>
            </div>
          </div>
        </div>

        <!-- 充电状态分布 -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h4 class="mb-3 flex items-center gap-2 text-gray-700 font-medium">
            <icon-mdi:battery-charging class="text-blue-500" />
            充电状态分布
          </h4>
          <div class="space-y-2">
            <div v-for="(count, chargingStatus) in deviceStatistics.byChargingStatus" :key="chargingStatus" class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="h-3 w-3 rounded-full" :style="{ backgroundColor: chargingStatusColors[chargingStatus] || '#ccc' }"></div>
                <span class="text-sm text-gray-600">{{ chargingStatus }}</span>
              </div>
              <span class="text-sm text-gray-800 font-medium">{{ count }}</span>
            </div>
          </div>
        </div>

        <!-- 设备型号分布 -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h4 class="mb-3 flex items-center gap-2 text-gray-700 font-medium">
            <icon-mdi:cellphone class="text-indigo-500" />
            设备型号分布
          </h4>
          <div class="max-h-48 overflow-y-auto space-y-2">
            <div v-for="(count, model) in deviceStatistics.byModel" :key="model" class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div 
                  class="h-3 w-3 rounded-full"
                  :style="{ backgroundColor: `hsl(${(Object.keys(deviceStatistics.byModel).indexOf(model) * 137.5) % 360}, 70%, 60%)` }"
                ></div>
                <span class="text-sm text-gray-600">{{ model }}</span>
              </div>
              <span class="text-sm text-gray-800 font-medium">{{ count }}</span>
            </div>
          </div>
        </div>
      </div>
    </NCard>

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

<style scoped>
.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.gap-8px {
  gap: 8px;
}

/* 统计卡片样式优化 */
.card-wrapper {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
}

/* 统计数字动画 */
.text-2xl {
  transition: transform 0.3s ease;
}

.text-2xl:hover {
  transform: scale(1.05);
}

/* 分布卡片样式 */
.border.border-gray-200 {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  transition: all 0.3s ease;
}

.border.border-gray-200:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

/* 彩色点样式 */
.h-3.w-3.rounded-full {
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.8);
  transition: transform 0.2s ease;
}

.h-3.w-3.rounded-full:hover {
  transform: scale(1.2);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .grid-cols-2 {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
  
  .md\:grid-cols-4 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  
  .lg\:grid-cols-4 {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
}
</style>
