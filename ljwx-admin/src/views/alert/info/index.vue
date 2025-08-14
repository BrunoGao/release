<script setup lang="tsx">
import { onMounted, ref, shallowRef, watch, watchEffect } from 'vue';
import { NButton, NPopconfirm, NTooltip } from 'naive-ui';
import { Icon } from '@iconify/vue';
import type { Ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteAlertInfo, fetchGetAlertInfoList, fetchGetOrgUnitsTree, fetchGetUserHealthDataById } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { formatDate } from '@/utils/date';
import { handleBindUsersByOrgId } from '@/utils/deviceUtils';
import AlerinfoSearch from './modules/alerinfo-search.vue';
import AlerinfoOperateDrawer from './modules/alerinfo-operate-drawer.vue';
defineOptions({
  name: 'TAlertInfoPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();
const authStore = useAuthStore();
const { hasAuth } = useAuth();

const { dictTag } = useDict();

const editingData: Ref<Api.Health.AlertInfo | null> = ref(null);

const customerId = authStore.userInfo?.customerId;

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetAlertInfoList,
  apiParams: {
    page: 1,
    pageSize: 20,
    alertType: null,
    customerId,
    orgId: null,
    userId: null
  },
  columns: () => [
    { type: 'selection', width: 40, align: 'center' },
    {
      key: 'index' as any as any,
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },
    {
      key: 'departmentInfo' as any as any,
      title: '部门信息',
      align: 'center',
      width: 200
    },
    {
      key: 'userName' as any,
      title: '用户名称',
      align: 'center',
      width: 200,
      render: (row: any) => row.userName || row.userId || '未知用户'
    },
    {
      key: 'alertType' as any as any,
      title: $t('page.health.alert.info.alertType'),
      align: 'center',
      minWidth: 100,
      render: row => dictTag('alert_type', row.alertType)
    },

    {
      key: 'alertStatus' as any as any,
      title: $t('page.health.alert.info.alertStatus'),
      align: 'center',
      minWidth: 100,
      render: row => dictTag('alert_status', row.alertStatus)
    },
    {
      key: 'alertDesc' as any as any,
      title: $t('page.health.alert.info.alertDesc'),
      align: 'center',
      minWidth: 100
    },
        {
      key: 'healthId' as any as any,
      title: $t('page.health.alert.info.healthId'),
      align: 'center',
      minWidth: 100,
      render: (row: any) => {
        const healthInfo = ref<any>(null);
        const fetchLoading = ref(false);
        const fetchError = ref<string | null>(null);

        const loadHealthData = async (id: string) => {
          fetchLoading.value = true;
          fetchError.value = null;
          try {
            const { data: responseData, error } = await fetchGetUserHealthDataById(id); // #修复类型
            if (!error && responseData) {
              healthInfo.value = responseData;
            } else {
              fetchError.value = '数据获取失败';
            }
          } catch (err: any) {
            fetchError.value = err?.message || '网络错误';
          } finally {
            fetchLoading.value = false;
          }
        };

        watchEffect(() => {
          if (row.healthId) {
            loadHealthData(String(row.healthId));
          }
        });

        const formatValue = (value: any, unit = '') => { // #优化格式化函数
          if (value === null || value === undefined) return '无数据';
          if (value === 0) return `0${unit}`; // #0值也要显示
          return `${value}${unit}`;
        };

        const renderHealthInfo = () => {
          if (fetchLoading.value) return <div style="color: #1890ff;">⏳ 数据加载中...</div>;
          if (fetchError.value) return <div style="color: #ff4d4f;">❌ {fetchError.value}</div>;
          if (!healthInfo.value) return <div style="color: #999;">📋 暂无数据</div>;

          const d = healthInfo.value; // #简化变量名
          return (
            <div style="max-width: 350px; padding: 12px; font-size: 13px; line-height: 1.6; background: #fafafa; border-radius: 6px;">
              <div style="margin-bottom: 6px; display: flex; justify-content: space-between;">
                <span><strong>💓 心率:</strong></span>
                <span style="color: #1890ff; font-weight: 500;">{formatValue(d.heartRate, ' bpm')}</span>
              </div>
              <div style="margin-bottom: 6px; display: flex; justify-content: space-between;">
                <span><strong>🩸 血压:</strong></span>
                <span style="color: #52c41a; font-weight: 500;">{formatValue(d.pressureHigh)}/{formatValue(d.pressureLow)} mmHg</span>
              </div>
              <div style="margin-bottom: 6px; display: flex; justify-content: space-between;">
                <span><strong>🌡️ 体温:</strong></span>
                <span style="color: #fa8c16; font-weight: 500;">{formatValue(d.temperature, '°C')}</span>
              </div>
              <div style="margin-bottom: 6px; display: flex; justify-content: space-between;">
                <span><strong>🫁 血氧:</strong></span>
                <span style="color: #722ed1; font-weight: 500;">{formatValue(d.bloodOxygen, '%')}</span>
              </div>
              <div style="margin-bottom: 6px; display: flex; justify-content: space-between;">
                <span><strong>😰 压力:</strong></span>
                <span style="color: #f5222d; font-weight: 500;">{formatValue(d.stress)}</span>
              </div>
              <div style="margin-bottom: 6px; display: flex; justify-content: space-between;">
                <span><strong>👟 步数:</strong></span>
                <span style="color: #13c2c2; font-weight: 500;">{formatValue(d.step)}</span>
              </div>
              <div style="margin-bottom: 8px; border-top: 1px solid #e8e8e8; padding-top: 6px;">
                <div style="font-size: 12px; color: #666; margin-bottom: 4px;"><strong>📍 位置信息:</strong></div>
                <div style="font-size: 11px; color: #999;">
                  {d.latitude && d.longitude ? `${d.latitude.toFixed(6)}°, ${d.longitude.toFixed(6)}°` : '无位置数据'}
                  {d.altitude > 0 ? ` (海拔${d.altitude}m)` : ''}
                </div>
              </div>
              <div style="font-size: 11px; color: #999; text-align: center; padding-top: 4px; border-top: 1px solid #e8e8e8;">
                📅 {d.timestamp ? new Date(d.timestamp).toLocaleString('zh-CN') : '时间未知'}
              </div>
            </div>
          );
        };

        return (
          <NTooltip placement="right" keepAliveOnHover trigger="hover" showArrow={false}>
            {{
              trigger: () => (
                <span style="cursor: pointer; color: #1890ff; text-decoration: underline; font-weight: 500; padding: 2px 4px; border-radius: 3px; background: #f0f8ff;">
                  {String(row.healthId)}
                </span>
              ),
              default: () => renderHealthInfo()
            }}
          </NTooltip>
        );
      }
    },
    {
      key: 'severityLevel' as any as any,
      title: $t('page.health.alert.info.severityLevel'),
      align: 'center',
      minWidth: 100,
      render: row => dictTag('severity_level', row.severityLevel)
    },
    {
      key: 'alertTimestamp' as any as any,
      title: $t('page.health.alert.info.alertTimestamp'),
      align: 'center',
      minWidth: 100,
      render: row => formatDate(row.alertTimestamp, 'YYYY-MM-DD HH:mm:ss')
    },
    {
      key: 'operate' as any as any,
      title: $t('common.operate'),
      align: 'center',
      width: 200,
      minWidth: 200,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('t:alert:info:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          <NButton type="primary" quaternary size="small" onClick={() => handleAlertInfo(row.id)}>
            {$t('page.health.alert.info.dealAlert')}
          </NButton>
          {hasAuth('t:alert:info:delete') && (
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
function handleAlertInfo(id: string) {
  const bigscreenUrl = import.meta.env.VITE_BIGSCREEN_URL || 'http://localhost:5002';
  fetch(`${bigscreenUrl}/dealAlert?alertId=${id}`)
    .then(response => {
      if (response.ok) {
        location.reload();
      } else {
        console.error('Failed to process alert');
      }
    })
    .catch(error => {
      console.error('Error processing alert:', error);
    });
}

const { drawerVisible, openDrawer, checkedRowKeys, onDeleted, onBatchDeleted } = useTableOperate(data, getData);

async function handleBatchProcessAlert() {
  if (checkedRowKeys.value.length < 2) {
    window.$message?.warning('请选择至少两条告警记录进行批量处理');
    return;
  }

  // 检查选中告警的状态
  const selectedAlerts = data.value.filter(item => checkedRowKeys.value.includes(item.id));
  const respondedAlerts = selectedAlerts.filter(item => item.alertStatus === 'responded');
  
  // 如果有已响应的告警，提示用户
  if (respondedAlerts.length > 0) {
    const message = `选中的告警中有 ${respondedAlerts.length} 条已经处理过，是否继续批量处理？`;
    const confirmed = await new Promise(resolve => {
      window.$dialog?.warning({
        title: '确认批量处理',
        content: message,
        positiveText: '继续处理',
        negativeText: '取消',
        onPositiveClick: () => resolve(true),
        onNegativeClick: () => resolve(false)
      });
    });
    
    if (!confirmed) {
      return;
    }
  }

  const bigscreenUrl = import.meta.env.VITE_BIGSCREEN_URL || 'http://localhost:5001';

  try {
    const response = await fetch(`${bigscreenUrl}/batchDealAlert`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        alertIds: checkedRowKeys.value
      })
    });

    if (response.ok) {
      const result = await response.json();
      if (result.success) {
        let message = `批量处理成功：${result.successCount}条`;
        if (result.failedCount > 0) {
          message += `，失败${result.failedCount}条`;
        }
        if (respondedAlerts.length > 0) {
          message += `（其中${respondedAlerts.length}条已处理过）`;
        }
        window.$message?.success(message);
        await getData();
      } else {
        window.$message?.error(result.message || '批量处理失败');
      }
    } else {
      window.$message?.error('批量处理请求失败');
    }
  } catch {
    window.$message?.error('批量处理出现错误');
  }
}

function handleAdd() {
  operateType.value = 'add';
  openDrawer();
}

function edit(item: Api.Health.AlertInfo) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteAlertInfo(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteAlertInfo(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}

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
onMounted(() => {
  handleInitOptions();
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <AlerinfoSearch
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
        add-auth="t:alert:info:add"
        delete-auth="t:alert:info:delete"
        @add="handleAdd"
        @delete="handleBatchDelete"
        @refresh="getData"
      >
        <template #suffix>
          <NButton
            v-if="hasAuth('t:alert:info:update')"
            size="small"
            ghost
            type="success"
            :disabled="checkedRowKeys.length < 2 || loading"
            @click="handleBatchProcessAlert"
          >
            <template #icon>
              <Icon icon="material-symbols:check-circle-outline" />
            </template>
            一键批量处理
          </NButton>
        </template>
      </TableHeaderOperation>
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
        :row-key="(row: any) => row.id"
        :pagination="mobilePagination"
      />
      <AlerinfoOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        :org-units-tree="orgUnitsTree"
        :user-options="userOptions"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
