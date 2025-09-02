<script setup lang="tsx">
import { NButton, NTooltip } from 'naive-ui';
import { type Ref, h, onMounted, ref, shallowRef, watch } from 'vue';
import { utils, writeFile } from 'xlsx';

import * as XLSX from 'xlsx';

import { useAppStore } from '@/store/modules/app';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteUserHealthData, fetchGetHealthDataConfigList, fetchGetOrgUnitsTree, fetchGetUserHealthDataList } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { convertToBeijingTime } from '@/utils/date';

import { handleBindUsersByOrgId } from '@/utils/deviceUtils';

import UserHealthDataSearch from './modules/user-health-data-search.vue';
import UserHealthDataOperateDrawer from './modules/user-health-data-operate-drawer.vue';
defineOptions({
  name: 'TUserHealthDataPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();
const authStore = useAuthStore();

const customerId = authStore.userInfo?.customerId;

const editingData: Ref<Api.Health.UserHealthData | null> = ref(null);

const today = new Date();
const startDate = new Date(today.setHours(0, 0, 0, 0)).getTime();
const endDate = new Date(today.setHours(23, 59, 59, 999)).getTime();

// 列配置
const columns = ref<any[]>([]);
const enabledDataTypes = ref<Set<string>>(new Set());

// 初始化列配置
async function initColumns() {
  try {
    const params: Api.Customer.HealthDataConfigSearchParams = {
      customerId,
      departmentInfo: searchParams.departmentInfo || null,
      page: 1,
      pageSize: 20
    };

    const { error, data } = await fetchGetHealthDataConfigList(params);
    if (!error && data?.records) {
      enabledDataTypes.value = new Set(
        data.records.filter((config: Api.Customer.HealthDataConfig) => config.isEnabled === 1).map(config => config.dataType)
      );

      console.log('enabledDataTypes.value', enabledDataTypes.value);
      // 生成列配置
      columns.value = [
        { type: 'selection', width: 40, align: 'center' },
        // 固定列
        {
          key: 'index',
          title: $t('common.index'),
          width: 64,
          align: 'center'
        },
        {
          key: 'departmentInfo',
          title: $t('page.health.data.info.departmentInfo'),
          align: 'center',
          width: 200
        },
        {
          key: 'userName',
          title: $t('page.health.data.info.username'),
          align: 'center',
          width: 100
        },
        {
          key: 'heartRate',
          title: `${$t('page.health.data.info.heartrate')}`,
          width: 60
        },
        {
          key: 'pressureHigh',
          title: `${$t('page.health.data.info.pressurehigh')}/${$t('page.health.data.info.pressurelow')}(mmHg)`,
          render: row => `${row.pressureHigh}/${row.pressureLow}`,
          width: 80
        },
        {
          key: 'bloodOxygen',
          title: `${$t('page.health.data.info.bloodoxygen')}(%)`,
          width: 60
        },
        {
          key: 'temperature',
          title: `${$t('page.health.data.info.temperature')}(℃)`,
          width: 60
        },
        // 动态生成启用的列
        ...[
          {
            key: 'stress',
            title: `${$t('page.health.data.info.stress')}(级)`,
            show: enabledDataTypes.value.has('stress'),
            width: 60
          },
          {
            key: 'step',
            title: `${$t('page.health.data.info.step')}(步)`,
            align: 'center',
            width: 100,
            show: enabledDataTypes.value.has('step')
          },
          {
            key: 'distance',
            title: `${$t('page.health.data.info.distance')}(米)`,
            align: 'center',
            width: 80,
            show: enabledDataTypes.value.has('distance')
          },
          {
            key: 'calorie',
            title: `${$t('page.health.data.info.calorie')}(卡)`,
            align: 'center',
            width: 80,
            show: enabledDataTypes.value.has('calorie')
          },
          {
            key: 'sleepData',
            title: `${$t('page.health.data.info.sleepdata')}(小时)`,
            align: 'center',
            width: 100,
            show: enabledDataTypes.value.has('sleep'),
            render: row => {
              const sleepData = row.sleepData && Object.keys(row.sleepData).length > 0 ? row.sleepData : { value: '-', tooltip: '-' };
              const valueText = sleepData.value ?? '-';
              const tooltipText = sleepData.tooltip ?? '-';
              const tooltipContent = h('div', null, [
                h('div', { class: 'font-bold mb-2' }, '睡眠详情：'),
                h('ul', { class: 'list-none m-0 p-0' }, [
                  ...tooltipText
                    .split('；')
                    .filter(Boolean)
                    .map(t => h('li', { class: 'py-1' }, t))
                ])
              ]);

              return h(
                NTooltip, // 👈 使用变量，不用 resolveComponent
                {
                  trigger: 'hover',
                  placement: 'top'
                },
                {
                  trigger: () =>
                    h(
                      'span',
                      {
                        style: 'color:#333;cursor:pointer;user-select:none;'
                      },
                      valueText
                    ),
                  default: () => tooltipContent
                }
              );
            }
          },
          {
            key: 'workoutData',
            title: `${$t('page.health.data.info.workoutData')}(分钟)`,
            align: 'center',
            width: 100,
            show: enabledDataTypes.value.has('work_out'),
            render: row => {
              const workoutData = row.workoutData && Object.keys(row.workoutData).length > 0 ? row.workoutData : { value: '-', tooltip: '-' };

              const valueText = workoutData.value ?? '-';
              const tooltipText = workoutData.tooltip ?? '-';
              const tooltipContent = h('div', null, [
                h('div', { class: 'font-bold mb-2' }, '运动详情：'),
                h('ul', { class: 'list-none m-0 p-0' }, [
                  ...tooltipText
                    .split('；')
                    .filter(Boolean)
                    .map(t => h('li', { class: 'py-1' }, t))
                ])
              ]);

              return h(
                NTooltip, // 👈 使用变量，不用 resolveComponent
                {
                  trigger: 'hover',
                  placement: 'top'
                },
                {
                  trigger: () =>
                    h(
                      'span',
                      {
                        style: 'color:#333;cursor:pointer;user-select:none;'
                      },
                      valueText
                    ),
                  default: () => tooltipContent
                }
              );
            }
          },
          {
            key: 'exerciseDailyData',
            title: `${$t('page.health.data.info.exerciseDailyData')}(分钟)`,
            align: 'center',
            width: 100,
            show: enabledDataTypes.value.has('exercise_daily'),
            render: row => {
              const exerciseDailyData =
                row.exerciseDailyData && Object.keys(row.exerciseDailyData).length > 0 ? row.exerciseDailyData : { value: '-', tooltip: '-' };

              const valueText = exerciseDailyData.value ?? '-';
              const tooltipText = exerciseDailyData.tooltip ?? '-';

              const tooltipContent = h('div', null, [
                h('div', { class: 'font-bold mb-2' }, '运动详情：'),
                h('ul', { class: 'list-none m-0 p-0' }, [
                  ...tooltipText
                    .split('；')
                    .filter(Boolean)
                    .map(t => h('li', { class: 'py-1' }, t))
                ])
              ]);

              return h(
                NTooltip, // 👈 使用变量，不用 resolveComponent
                {
                  trigger: 'hover',
                  placement: 'top'
                },
                {
                  trigger: () =>
                    h(
                      'span',
                      {
                        style: 'color:#333;cursor:pointer;user-select:none;'
                      },
                      valueText
                    ),
                  default: () => tooltipContent
                }
              );
            }
          },
          {
            key: 'coordinates',
            title: `${$t('page.health.data.info.coordinates')}(度)`,
            align: 'center',
            minWidth: 300,
            render: row => `(${row.latitude}, ${row.longitude}, ${row.altitude})`,
            show: enabledDataTypes.value.has('location')
          }
        ].filter(col => col.show), // 只保留启用的列
        // 其他固定列

        {
          key: 'timestamp',
          title: $t('page.health.data.info.timestamp'),
          align: 'center',
          width: 200,
          render: row => convertToBeijingTime(row.timestamp)
        }
      ];
    }
  } catch (error) {
    console.error('Error fetching health data config:', error);
  }
}

const {
  columns: tableColumns,
  columnChecks,
  data,
  loading,
  getData,
  getDataByPage,
  mobilePagination,
  searchParams,
  resetSearchParams
} = useTable({
  apiFn: fetchGetUserHealthDataList,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId,
    departmentInfo: null,
    userId: null,
    startDate,
    endDate
  },
  columns: () => columns.value
});

const { drawerVisible, openDrawer, checkedRowKeys, onDeleted, onBatchDeleted } = useTableOperate(data, getData);

function handleAdd() {
  operateType.value = 'add';
  openDrawer();
}

function edit(item: Api.Health.UserHealthData) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteUserHealthData(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteUserHealthData(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}

function exportExcel() {
  // 确保包含部门信息列
  const exportColumns = [
    {
      key: 'departmentInfo',
      title: '直属部门',
      width: 120
    },
    ...columns.value.slice(2)
  ];

  // 预计算列宽
  const colWidths = exportColumns.map(item => ({
    width: item.key === 'coordinates' ? Math.round((Number(item.width || 180) * 1.5) / 6) : Math.round(Number(item.width || 120) / 6),
    wch: item.key === 'coordinates' ? Math.round((Number(item.width || 180) * 1.5) / 6) : Math.round(Number(item.width || 120) / 6)
  }));

  // 预计算表头样式
  const headerStyle = {
    font: { bold: true, color: { rgb: '000000' }, sz: 12 },
    fill: { fgColor: { rgb: 'E0E0E0' } },
    alignment: { horizontal: 'center', vertical: 'center', wrapText: true },
    border: {
      top: { style: 'thin', color: { rgb: '000000' } },
      bottom: { style: 'thin', color: { rgb: '000000' } },
      left: { style: 'thin', color: { rgb: '000000' } },
      right: { style: 'thin', color: { rgb: '000000' } }
    }
  };

  // 预计算数据行样式
  const dataStyle = {
    alignment: { horizontal: 'center', vertical: 'center', wrapText: true },
    font: { color: { rgb: '000000' }, sz: 11 },
    border: {
      top: { style: 'thin', color: { rgb: 'E0E0E0' } },
      bottom: { style: 'thin', color: { rgb: 'E0E0E0' } },
      left: { style: 'thin', color: { rgb: 'E0E0E0' } },
      right: { style: 'thin', color: { rgb: 'E0E0E0' } }
    }
  };

  // 预计算表头
  const titleList = exportColumns.map(col => {
    if (col.key === 'coordinates') return '坐标(纬度,经度,海拔)(度)';
    if (col.key === 'pressureHigh') return '血压(低压/高压)(mmHg)';
    if (col.key === 'heartRate') return '心率(次/分)';
    if (col.key === 'bloodOxygen') return '血氧(%)';
    if (col.key === 'temperature') return '体温(℃)';
    if (col.key === 'stress') return '压力(级)';
    if (col.key === 'step') return '步数(步)';
    if (col.key === 'distance') return '距离(米)';
    if (col.key === 'calorie') return '卡路里(卡)';
    if (col.key === 'sleepData') return '睡眠数据(小时)';
    if (col.key === 'workOutData') return '每日运动数据(分钟)';
    if (col.key === 'timestamp') return '时间';
    if (col.key === 'departmentInfo') return '直属部门';
    return col.title;
  });

  // 批量处理数据
  const excelList = [titleList];
  const batchSize = 1000;
  const totalRows = data.value.length;

  for (let i = 0; i < totalRows; i += batchSize) {
    const batch = data.value.slice(i, i + batchSize);
    const batchRows = batch.map(item => {
      return exportColumns.map(col => {
        if (col.key === 'timestamp') return convertToBeijingTime(item[col.key]);
        if (col.key === 'coordinates') return `(${item.latitude || 0}, ${item.longitude || 0}, ${item.altitude || 0})`;
        if (col.key === 'pressureHigh') return `${item.pressureLow || '-'}/${item.pressureHigh || '-'}`;
        if (col.key === 'sleepData' || col.key === 'workoutData' || col.key === 'exerciseDailyData') {
          const v = item[col.key];
          return typeof v === 'object' && v !== null ? (v.tooltip ?? '') : (v ?? '');
        }
        if (col.key === 'departmentInfo') return item.departmentInfo || '-';
        return item[col.key] ?? '-';
      });
    });
    excelList.push(...batchRows);
  }

  const workBook = utils.book_new();
  const workSheet = utils.aoa_to_sheet(excelList);

  // 设置列宽
  workSheet['!cols'] = colWidths;

  // 设置样式
  const range = XLSX.utils.decode_range(workSheet['!ref'] || 'A1');
  const totalCols = range.e.c - range.s.c + 1;

  // 只设置表头样式
  for (let C = 0; C < totalCols; C++) {
    const cellAddress = XLSX.utils.encode_cell({ r: 0, c: C });
    if (workSheet[cellAddress]) {
      workSheet[cellAddress].s = headerStyle;
    }
  }

  // 添加筛选功能
  workSheet['!autofilter'] = { ref: workSheet['!ref'] || 'A1' };

  // 冻结首行
  workSheet['!freeze'] = { xSplit: '0', ySplit: '1' };

  utils.book_append_sheet(workBook, workSheet, '健康数据列表');

  // 生成文件名
  const now = new Date();
  const timestamp = now
    .toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
    .replace(/[/\s:]/g, '');

  const department = data.value[0]?.departmentInfo || '全部';
  const userName = data.value[0]?.userName || '全部';
  const fileName = `健康数据_${department}_${userName}_${timestamp}.xlsx`;

  writeFile(workBook, fileName);
}

const handleUpload = async ({ file }) => {
  try {
    const reader = new FileReader();
    reader.onload = async e => {
      const excelData = new Uint8Array(e.target.result as ArrayBuffer);
      const workbook = XLSX.read(excelData, { type: 'array' });
      const firstSheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[firstSheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      // Send jsonData to your backend API for database insertion
      await importDataToDatabase(jsonData);

      // Re-fetch the data after import
      getDataByPage();
    };
    reader.readAsArrayBuffer(file);
  } catch (error) {
    console.error('Failed to upload and process Excel file:', error);
  }
};

async function importDataToDatabase(jsonData: any) {
  console.log(jsonData);
}

onMounted(() => {
  handleInitOptions();
  initColumns();
});
type OrgUnitsTree = Api.SystemManage.OrgUnitsTree;

/** org units tree data */
const orgUnitsTree = shallowRef<OrgUnitsTree[]>([]);
const userOptions = ref<{ label: string; value: string }[]>([]);

async function handleInitOptions() {
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
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <UserHealthDataSearch
      v-model:model="searchParams"
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <NSpace align="center" wrap justify="end" class="lt-sm:w-full">
        <TableHeaderOperation
          v-model:columns="columnChecks"
          :disabled-delete="checkedRowKeys.length === 0"
          :loading="loading"
          add-auth="t:user:health:data:add"
          delete-auth="t:user:health:data:delete"
          @add="handleAdd"
          @delete="handleBatchDelete"
          @refresh="getData"
        />
        <NButton size="small" ghost type="primary" @click="exportExcel">
          <template #icon>
            <icon-file-icons:microsoft-excel class="text-icon" />
          </template>
          导出excel
        </NButton>
      </NSpace>
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
      <UserHealthDataOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>
