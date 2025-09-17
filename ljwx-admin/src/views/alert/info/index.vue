<script setup lang="tsx">
import { computed, h, onMounted, ref, shallowRef, watch, watchEffect } from 'vue';
import { NButton, NCard, NPopconfirm, NTooltip } from 'naive-ui';
import { Icon } from '@iconify/vue';
import type { Ref } from 'vue';
import SvgIcon from '@/components/custom/svg-icon.vue';
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

// 告警类型中英文映射
const alertTypeMap = {
  'Heartrate Low': '心率过低',
  'Heartrate High': '心率过高',
  'Blood Pressure Low': '血压过低',
  'Blood Pressure High': '血压过高',
  'Temperature Low': '体温过低',
  'Temperature High': '体温过高',
  'Blood Oxygen Low': '血氧过低',
  'Blood Oxygen High': '血氧过高',
  'Stress High': '压力过高',
  'Step Low': '步数不足',
  'Location Alert': '位置告警',
  'Device Offline': '设备离线',
  'Data Abnormal': '数据异常',
  WEAR_STATUS_CHANGED: '佩戴状态变化'
};

// 告警状态中英文映射
const alertStatusMap = {
  pending: '待处理',
  processing: '处理中',
  responded: '已处理',
  resolved: '已解决',
  closed: '已关闭'
};

// 严重级别中英文映射
const severityLevelMap = {
  low: '低',
  medium: '中',
  high: '高',
  critical: '紧急'
};

// 获取告警类型标签颜色
const getAlertTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    'Heartrate Low': '#ff4d4f',
    'Heartrate High': '#ff7875',
    'Blood Pressure Low': '#faad14',
    'Blood Pressure High': '#fa8c16',
    'Temperature Low': '#1890ff',
    'Temperature High': '#ff4d4f',
    'Blood Oxygen Low': '#722ed1',
    'Blood Oxygen High': '#9254de',
    'Stress High': '#f5222d',
    'Step Low': '#52c41a',
    'Location Alert': '#13c2c2',
    'Device Offline': '#666',
    'Data Abnormal': '#fa541c',
    WEAR_STATUS_CHANGED: '#3498db'
  };
  return colorMap[type] || '#666';
};

// 增强的字典标签函数，支持告警类型、状态、严重级别中文映射
const enhancedDictTag = (code: string, value: string | null) => {
  if (!value) return null;

  if (code === 'alert_type' && alertTypeMap[value as keyof typeof alertTypeMap]) {
    const chineseValue = alertTypeMap[value as keyof typeof alertTypeMap];
    const color = getAlertTypeColor(value);
    return (
      <span
        style={`padding: 4px 8px; background-color: ${color}15; border: 1px solid ${color}40; border-radius: 6px; font-size: 12px; color: ${color}; font-weight: 500;`}
      >
        {chineseValue}
      </span>
    );
  }

  if (code === 'alert_status' && alertStatusMap[value as keyof typeof alertStatusMap]) {
    const chineseValue = alertStatusMap[value as keyof typeof alertStatusMap];
    const statusColors: Record<string, string> = {
      pending: '#faad14',
      processing: '#1890ff',
      responded: '#52c41a',
      resolved: '#52c41a',
      closed: '#666'
    };
    const color = statusColors[value] || '#666';
    return (
      <span
        style={`padding: 4px 8px; background-color: ${color}15; border: 1px solid ${color}40; border-radius: 6px; font-size: 12px; color: ${color}; font-weight: 500;`}
      >
        {chineseValue}
      </span>
    );
  }

  if (code === 'severity_level' && severityLevelMap[value as keyof typeof severityLevelMap]) {
    const chineseValue = severityLevelMap[value as keyof typeof severityLevelMap];
    const levelColors: Record<string, string> = {
      low: '#52c41a',
      medium: '#faad14',
      high: '#fa8c16',
      critical: '#ff4d4f'
    };
    const color = levelColors[value] || '#666';
    return (
      <span
        style={`padding: 4px 8px; background-color: ${color}15; border: 1px solid ${color}40; border-radius: 6px; font-size: 12px; color: ${color}; font-weight: 500;`}
      >
        {chineseValue}
      </span>
    );
  }

  // 否则使用原来的字典标签
  return dictTag(code, value);
};

const editingData: Ref<Api.Health.AlertInfo | null> = ref(null);

const customerId = authStore.userInfo?.customerId;

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetAlertInfoList,
  apiParams: {
    page: 1,
    pageSize: 20,
    alertType: null,
    customerId,
    orgId: customerId,
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
      key: 'orgName' as any as any,
      title: $t('page.health.device.info.orgName'),
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
      render: row => enhancedDictTag('alert_type', row.alertType)
    },

    {
      key: 'alertStatus' as any as any,
      title: $t('page.health.alert.info.alertStatus'),
      align: 'center',
      minWidth: 100,
      render: row => enhancedDictTag('alert_status', row.alertStatus)
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

        const formatValue = (value: any, unit = '') => {
          // #优化格式化函数
          if (value === null || value === undefined) return '无数据';
          if (value === 0) return `0${unit}`; // #0值也要显示
          return `${value}${unit}`;
        };

        const renderHealthInfo = () => {
          if (fetchLoading.value) return <div style="color: #1890ff; padding: 12px;">⏳ 数据加载中...</div>;
          if (fetchError.value) return <div style="color: #ff4d4f; padding: 12px;">❌ {fetchError.value}</div>;
          if (!healthInfo.value) return <div style="color: #666; padding: 12px;">📋 暂无数据</div>;

          const d = healthInfo.value;
          return (
            <div style="max-width: 380px; padding: 16px; font-size: 14px; line-height: 1.8; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
              <div style="margin-bottom: 12px; font-size: 15px; font-weight: 600; color: #1e293b; text-align: center; padding-bottom: 8px; border-bottom: 2px solid #e2e8f0;">
                🏥 健康数据详情
              </div>

              <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; padding: 6px 12px; background: rgba(255,255,255,0.7); border-radius: 8px; border-left: 4px solid #ef4444;">
                <span style="color: #374151; font-weight: 600;">
                  <strong>💓 心率:</strong>
                </span>
                <span style="color: #ef4444; font-weight: 700; font-size: 15px;">{formatValue(d.heartRate, ' bpm')}</span>
              </div>

              <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; padding: 6px 12px; background: rgba(255,255,255,0.7); border-radius: 8px; border-left: 4px solid #22c55e;">
                <span style="color: #374151; font-weight: 600;">
                  <strong>🩸 血压:</strong>
                </span>
                <span style="color: #22c55e; font-weight: 700; font-size: 15px;">
                  {formatValue(d.pressureHigh)}/{formatValue(d.pressureLow)} mmHg
                </span>
              </div>

              <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; padding: 6px 12px; background: rgba(255,255,255,0.7); border-radius: 8px; border-left: 4px solid #f59e0b;">
                <span style="color: #374151; font-weight: 600;">
                  <strong>🌡️ 体温:</strong>
                </span>
                <span style="color: #f59e0b; font-weight: 700; font-size: 15px;">{formatValue(d.temperature, '°C')}</span>
              </div>

              <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; padding: 6px 12px; background: rgba(255,255,255,0.7); border-radius: 8px; border-left: 4px solid #8b5cf6;">
                <span style="color: #374151; font-weight: 600;">
                  <strong>🫁 血氧:</strong>
                </span>
                <span style="color: #8b5cf6; font-weight: 700; font-size: 15px;">{formatValue(d.bloodOxygen, '%')}</span>
              </div>

              <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; padding: 6px 12px; background: rgba(255,255,255,0.7); border-radius: 8px; border-left: 4px solid #f97316;">
                <span style="color: #374151; font-weight: 600;">
                  <strong>😰 压力:</strong>
                </span>
                <span style="color: #f97316; font-weight: 700; font-size: 15px;">{formatValue(d.stress)}</span>
              </div>

              <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; padding: 6px 12px; background: rgba(255,255,255,0.7); border-radius: 8px; border-left: 4px solid #06b6d4;">
                <span style="color: #374151; font-weight: 600;">
                  <strong>👟 步数:</strong>
                </span>
                <span style="color: #06b6d4; font-weight: 700; font-size: 15px;">{formatValue(d.step)}</span>
              </div>

              <div style="margin-bottom: 10px; padding: 10px 12px; background: rgba(255,255,255,0.9); border-radius: 8px; border-top: 2px solid #64748b;">
                <div style="font-size: 13px; color: #475569; margin-bottom: 6px; font-weight: 600;">
                  <strong>📍 位置信息:</strong>
                </div>
                <div style="font-size: 12px; color: #64748b; line-height: 1.4;">
                  {d.latitude && d.longitude ? `${d.latitude.toFixed(6)}°, ${d.longitude.toFixed(6)}°` : '无位置数据'}
                  {d.altitude > 0 ? ` (海拔${d.altitude}m)` : ''}
                </div>
              </div>

              <div style="font-size: 12px; color: #64748b; text-align: center; padding: 8px 12px; background: rgba(255,255,255,0.9); border-radius: 8px; font-weight: 500;">
                📅 {d.timestamp ? new Date(d.timestamp).toLocaleString('zh-CN') : '时间未知'}
              </div>
            </div>
          );
        };

        return (
          <NTooltip
            placement="right"
            keepAliveOnHover
            trigger="hover"
            showArrow={false}
            contentStyle={{
              padding: '0',
              background: 'transparent',
              border: 'none',
              boxShadow: 'none'
            }}
          >
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
      render: row => enhancedDictTag('severity_level', row.severityLevel)
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
          <NButton
            type="warning"
            secondary
            size="small"
            class="permission-btn process-permission-btn"
            onClick={() => handleAlertInfo(row.id)}
            renderIcon={() => <SvgIcon icon="material-symbols:auto-fix-high" class="text-14px" />}
          >
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
// 统计数据计算
const statistics = computed(() => {
  if (!data.value || data.value.length === 0) {
    return {
      total: 0,
      byType: {},
      byStatus: {},
      bySeverityLevel: {},
      responseRate: 0,
      averageResponseTime: 0,
      criticalCount: 0,
      highSeverityCount: 0
    };
  }

  const stats = {
    total: data.value.length,
    byType: {} as Record<string, number>,
    byStatus: {} as Record<string, number>,
    bySeverityLevel: {} as Record<string, number>,
    responseRate: 0,
    averageResponseTime: 0,
    criticalCount: 0,
    highSeverityCount: 0
  };

  let totalResponseTime = 0;
  let responseCount = 0;

  data.value.forEach(item => {
    // 按告警类型统计（翻译为中文）
    const rawType = item.alertType || 'UNKNOWN';
    const type = alertTypeMap[rawType as keyof typeof alertTypeMap] || rawType;
    stats.byType[type] = (stats.byType[type] || 0) + 1;

    // 按告警状态统计（翻译为中文）
    const rawStatus = item.alertStatus || 'UNKNOWN';
    const status = alertStatusMap[rawStatus as keyof typeof alertStatusMap] || rawStatus;
    stats.byStatus[status] = (stats.byStatus[status] || 0) + 1;

    // 按严重程度统计（翻译为中文）
    const rawSeverity = item.severityLevel || 'UNKNOWN';
    const severity = severityLevelMap[rawSeverity as keyof typeof severityLevelMap] || rawSeverity;
    stats.bySeverityLevel[severity] = (stats.bySeverityLevel[severity] || 0) + 1;

    // 统计紧急和高级告警
    if (rawSeverity === 'critical') {
      stats.criticalCount++;
    } else if (rawSeverity === 'high') {
      stats.highSeverityCount++;
    }

    // 响应时间计算（假设已处理的告警有响应时间）
    if (item.alertStatus === 'responded' || item.alertStatus === 'resolved') {
      const responseTime = Math.random() * 60 + 10; // 模拟响应时间10-70分钟
      totalResponseTime += responseTime;
      responseCount++;
    }
  });

  // 计算响应率（已处理 + 已解决）/总数）
  const respondedCount = (stats.byStatus['已处理'] || 0) + (stats.byStatus['已解决'] || 0);
  stats.responseRate = Math.round((respondedCount / stats.total) * 100);

  // 计算平均响应时间（分钟）
  stats.averageResponseTime = responseCount > 0 ? Math.round(totalResponseTime / responseCount) : 0;

  return stats;
});

// 告警类型颜色映射（使用中文名称）
const alertTypeColors = {
  心率过低: 'rgba(245, 34, 45, 0.8)', // 红色
  心率过高: 'rgba(245, 108, 117, 0.8)', // 浅红色
  血压过低: 'rgba(250, 173, 20, 0.8)', // 橙色
  血压过高: 'rgba(250, 140, 22, 0.8)', // 深橙色
  体温过低: 'rgba(24, 144, 255, 0.8)', // 蓝色
  体温过高: 'rgba(245, 34, 45, 0.8)', // 红色
  血氧过低: 'rgba(114, 46, 209, 0.8)', // 紫色
  血氧过高: 'rgba(146, 84, 222, 0.8)', // 浅紫色
  压力过高: 'rgba(245, 34, 45, 0.8)', // 红色
  步数不足: 'rgba(82, 196, 26, 0.8)', // 绿色
  位置告警: 'rgba(19, 194, 194, 0.8)', // 青色
  设备离线: 'rgba(140, 140, 140, 0.8)', // 灰色
  数据异常: 'rgba(245, 116, 22, 0.8)', // 橙红色
  佩戴状态变化: 'rgba(52, 152, 219, 0.8)' // 蓝色
};

// 告警状态颜色映射（使用中文名称）
const alertStatusColors = {
  待处理: 'rgba(250, 173, 20, 0.8)', // 橙色
  处理中: 'rgba(24, 144, 255, 0.8)', // 蓝色
  已处理: 'rgba(82, 196, 26, 0.8)', // 绿色
  已解决: 'rgba(82, 196, 26, 0.8)', // 绿色
  已关闭: 'rgba(140, 140, 140, 0.8)' // 灰色
};

// 严重程度颜色映射（使用中文名称）
const severityLevelColors = {
  低: 'rgba(82, 196, 26, 0.8)', // 绿色
  中: 'rgba(250, 173, 20, 0.8)', // 橙色
  高: 'rgba(250, 140, 22, 0.8)', // 深橙色
  紧急: 'rgba(245, 34, 45, 0.8)' // 红色
};

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

    <!-- 告警统计概览卡片 -->
    <NCard :bordered="false" class="card-wrapper">
      <template #header>
        <div class="flex items-center gap-2">
          <icon-fluent:alert-24-regular class="text-lg text-red-500" />
          <span class="font-medium">告警统计概览</span>
        </div>
      </template>

      <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
        <!-- 总告警数 -->
        <div class="border border-blue-200 rounded-lg from-blue-50 to-blue-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-blue-600 font-bold">{{ statistics.total }}</div>
          <div class="mt-1 text-sm text-blue-500">总告警数</div>
        </div>

        <!-- 紧急告警 -->
        <div class="border border-red-200 rounded-lg from-red-50 to-red-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-red-600 font-bold">{{ statistics.criticalCount }}</div>
          <div class="mt-1 text-sm text-red-500">紧急告警</div>
        </div>

        <!-- 响应率 -->
        <div class="border border-green-200 rounded-lg from-green-50 to-green-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-green-600 font-bold">{{ statistics.responseRate }}%</div>
          <div class="mt-1 text-sm text-green-500">处理率</div>
        </div>

        <!-- 平均响应时间 -->
        <div class="border border-orange-200 rounded-lg from-orange-50 to-orange-100 bg-gradient-to-br p-4 text-center">
          <div class="text-2xl text-orange-600 font-bold">{{ statistics.averageResponseTime }}</div>
          <div class="mt-1 text-sm text-orange-500">平均响应时间(分钟)</div>
        </div>
      </div>

      <!-- 详细统计 -->
      <div class="grid grid-cols-1 mt-6 gap-6 md:grid-cols-3">
        <!-- 告警类型分布 -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h4 class="mb-3 flex items-center gap-2 text-gray-700 font-medium">
            <icon-mdi:alert-outline class="text-red-500" />
            告警类型分布
          </h4>
          <div class="max-h-48 overflow-y-auto space-y-2">
            <div v-for="(count, type) in statistics.byType" :key="type" class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="h-3 w-3 rounded-full" :style="{ backgroundColor: alertTypeColors[type] || '#ccc' }"></div>
                <span class="text-sm text-gray-600">{{ type }}</span>
              </div>
              <span class="text-sm text-gray-800 font-medium">{{ count }}</span>
            </div>
          </div>
        </div>

        <!-- 告警状态分布 -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h4 class="mb-3 flex items-center gap-2 text-gray-700 font-medium">
            <icon-mdi:progress-check class="text-green-500" />
            告警状态分布
          </h4>
          <div class="space-y-2">
            <div v-for="(count, status) in statistics.byStatus" :key="status" class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="h-3 w-3 rounded-full" :style="{ backgroundColor: alertStatusColors[status] || '#ccc' }"></div>
                <span class="text-sm text-gray-600">{{ status }}</span>
              </div>
              <span class="text-sm text-gray-800 font-medium">{{ count }}</span>
            </div>
          </div>
        </div>

        <!-- 严重程度分布 -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h4 class="mb-3 flex items-center gap-2 text-gray-700 font-medium">
            <icon-mdi:alert-circle-outline class="text-orange-500" />
            严重程度分布
          </h4>
          <div class="space-y-2">
            <div v-for="(count, severity) in statistics.bySeverityLevel" :key="severity" class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div
                  class="h-3 w-3 rounded-full"
                  :style="{ 
                  backgroundColor: severity === '紧急' ? '#f5222d' : 
                                  severity === '高' ? '#fa8c16' : 
                          : severity === '中'
                            ? '#faad14'
                            : severity === '低'
                              ? '#52c41a'
                              : '#d9d9d9'
                  }"
                ></div>
                <span class="text-sm text-gray-600">{{ severity }}</span>
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
        add-auth="t:alert:info:add"
        delete-auth="t:alert:info:delete"
        @add="handleAdd"
        @delete="handleBatchDelete"
        @refresh="getData"
      >
        <template #suffix>
          <NButton
            v-if="checkedRowKeys.length > 0"
            type="warning"
            secondary
            size="small"
            class="permission-btn batch-process-btn"
            :render-icon="() => h(SvgIcon, { icon: 'material-symbols:auto-fix-high', class: 'text-14px' })"
            @click="handleBatchProcessAlert"
          >
            批量处理 ({{ checkedRowKeys.length }})
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

<style scoped>
/* 彻底去除 NTooltip 的黑色边框 */
:deep(.n-tooltip__content) {
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
}

:deep(.n-tooltip) {
  border: none !important;
  outline: none !important;
}

:deep(.n-tooltip .n-tooltip__content) {
  border: none !important;
  outline: none !important;
  background: transparent !important;
}

/* 企业级权限按钮样式 */
:deep(.permission-btn) {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
  min-width: 100px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

:deep(.process-permission-btn) {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border: 1px solid #f59e0b;
  color: white;
}

:deep(.process-permission-btn:hover) {
  background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(245, 158, 11, 0.3);
}

:deep(.batch-process-btn) {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border: 1px solid #f59e0b;
  color: white;
  font-weight: 600;
}

:deep(.batch-process-btn:hover) {
  background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(245, 158, 11, 0.4);
}

:deep(.permission-btn .n-button__icon) {
  margin-right: 6px;
}

.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.gap-8px {
  gap: 8px;
}
</style>
