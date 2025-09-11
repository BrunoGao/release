<script setup lang="tsx">
import { NButton, NPopconfirm, NTag, NSpace, NAvatar, NProgress } from 'naive-ui';
import { type Ref, onMounted, ref, shallowRef, watch, computed, h } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchGetOrgUnitsTree } from '@/service/api';
import { handleBindUsersByOrgId } from '@/utils/deviceUtils';
import { convertToBeijingTime } from '@/utils/date';
import HealthProfileSearch from './modules/health-search.vue';
import HealthProfileOperateDrawer from './modules/health-profile-operate-drawer.vue';
import ProfileAnalyticsViewer from './modules/profile-analytics-viewer.vue';
import ProfileTemplateManager from './modules/profile-template-manager.vue';

defineOptions({
  name: 'HealthProfilePage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');
const appStore = useAppStore();
const { hasAuth } = useAuth();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

const editingData: Ref<Api.Health.HealthProfile | null> = ref(null);
const analyticsViewerVisible = ref(false);
const templateManagerVisible = ref(false);
const selectedProfile = ref(null);

// 模拟 API 调用函数
const fetchGetHealthProfileList = async (params: any) => {
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  const mockProfiles = [
    {
      id: '1',
      userId: 'U001',
      userName: '张三',
      userDepartment: '技术部',
      userPosition: '软件工程师',
      avatar: 'https://picsum.photos/32/32?random=1',
      overallHealthScore: 78,
      riskLevel: 'medium',
      profileCompleteness: 85,
      lastUpdated: '2024-01-21 15:30:00',
      keyMetrics: {
        cardiovascular: { score: 82, trend: 'up' },
        respiratory: { score: 75, trend: 'stable' },
        mental: { score: 68, trend: 'down' },
        physical: { score: 85, trend: 'up' }
      },
      riskFactors: ['压力偏高', '睡眠不足'],
      strengths: ['运动规律', '心率正常'],
      recommendations: 5,
      alerts: 2,
      dataQuality: 92,
      profileStatus: 'active'
    },
    {
      id: '2',
      userId: 'U002',
      userName: '李四',
      userDepartment: '销售部',
      userPosition: '销售经理',
      avatar: 'https://picsum.photos/32/32?random=2',
      overallHealthScore: 65,
      riskLevel: 'high',
      profileCompleteness: 73,
      lastUpdated: '2024-01-20 09:45:00',
      keyMetrics: {
        cardiovascular: { score: 58, trend: 'down' },
        respiratory: { score: 72, trend: 'stable' },
        mental: { score: 55, trend: 'down' },
        physical: { score: 75, trend: 'stable' }
      },
      riskFactors: ['血压偏高', '心率异常', '体重超标'],
      strengths: ['血氧正常'],
      recommendations: 8,
      alerts: 5,
      dataQuality: 88,
      profileStatus: 'active'
    },
    {
      id: '3',
      userId: 'U003',
      userName: '王五',
      userDepartment: '市场部',
      userPosition: '市场专员',
      avatar: 'https://picsum.photos/32/32?random=3',
      overallHealthScore: 86,
      riskLevel: 'low',
      profileCompleteness: 94,
      lastUpdated: '2024-01-21 11:20:00',
      keyMetrics: {
        cardiovascular: { score: 88, trend: 'up' },
        respiratory: { score: 85, trend: 'up' },
        mental: { score: 82, trend: 'stable' },
        physical: { score: 90, trend: 'up' }
      },
      riskFactors: [],
      strengths: ['整体健康', '运动充足', '睡眠良好', '心理健康'],
      recommendations: 2,
      alerts: 0,
      dataQuality: 96,
      profileStatus: 'active'
    }
  ];

  return {
    error: null,
    data: {
      records: mockProfiles,
      total: mockProfiles.length,
      page: params.page || 1,
      pageSize: params.pageSize || 20
    }
  };
};

const fetchDeleteHealthProfile = async (ids: string[]) => {
  await new Promise(resolve => setTimeout(resolve, 500));
  return { error: null, data: { success: true } };
};

const today = new Date();
const startDate = new Date(today.setHours(0, 0, 0, 0)).getTime();
const endDate = new Date(today.setHours(23, 59, 59, 999)).getTime();

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetHealthProfileList,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId,
    orgId: null,
    userId: null,
    riskLevel: null,
    profileStatus: null,
    startDate,
    endDate
  },
  columns: () => [
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },
    {
      key: 'userInfo',
      title: '用户信息',
      align: 'left',
      minWidth: 180,
      render: row => (
        <div class="flex items-center gap-3">
          <NAvatar src={row.avatar} size="small" />
          <div>
            <div class="font-medium">{row.userName}</div>
            <div class="text-xs text-gray-500">{row.userDepartment} · {row.userPosition}</div>
          </div>
        </div>
      )
    },
    {
      key: 'overallHealthScore',
      title: '健康评分',
      align: 'center',
      width: 120,
      render: row => (
        <div class="flex items-center justify-center">
          <span class={`font-bold text-lg ${
            row.overallHealthScore >= 80 ? 'text-green-600' : 
            row.overallHealthScore >= 60 ? 'text-yellow-600' : 'text-red-600'
          }`}>
            {row.overallHealthScore}
          </span>
        </div>
      )
    },
    {
      key: 'riskLevel',
      title: '风险等级',
      align: 'center',
      width: 100,
      render: row => {
        const riskMap = {
          low: { type: 'success', text: '低风险' },
          medium: { type: 'warning', text: '中风险' },
          high: { type: 'error', text: '高风险' }
        } as const;
        const risk = riskMap[row.riskLevel as keyof typeof riskMap];
        return h(NTag, { type: risk.type, size: 'small' }, () => risk.text);
      }
    },
    {
      key: 'profileCompleteness',
      title: '完整度',
      align: 'center',
      width: 120,
      render: row => (
        <div class="flex items-center justify-center">
          <NProgress 
            type="circle" 
            size="small"
            percentage={row.profileCompleteness}
            status={row.profileCompleteness >= 90 ? 'success' : row.profileCompleteness >= 70 ? 'info' : 'warning'}
            show-indicator={false}
            stroke-width={8}
          />
          <span class="ml-2 text-sm">{row.profileCompleteness}%</span>
        </div>
      )
    },
    {
      key: 'keyMetrics',
      title: '关键指标',
      align: 'center',
      width: 200,
      render: row => (
        <div class="grid grid-cols-2 gap-1 text-xs">
          <div class="flex items-center gap-1">
            <span>心血管:</span>
            <span class={`font-medium ${row.keyMetrics.cardiovascular.score >= 70 ? 'text-green-600' : 'text-red-600'}`}>
              {row.keyMetrics.cardiovascular.score}
            </span>
            <span class={`${row.keyMetrics.cardiovascular.trend === 'up' ? 'text-green-500' : 
              row.keyMetrics.cardiovascular.trend === 'down' ? 'text-red-500' : 'text-gray-500'}`}>
              {row.keyMetrics.cardiovascular.trend === 'up' ? '↗' : 
               row.keyMetrics.cardiovascular.trend === 'down' ? '↘' : '→'}
            </span>
          </div>
          <div class="flex items-center gap-1">
            <span>呼吸:</span>
            <span class={`font-medium ${row.keyMetrics.respiratory.score >= 70 ? 'text-green-600' : 'text-red-600'}`}>
              {row.keyMetrics.respiratory.score}
            </span>
            <span class={`${row.keyMetrics.respiratory.trend === 'up' ? 'text-green-500' : 
              row.keyMetrics.respiratory.trend === 'down' ? 'text-red-500' : 'text-gray-500'}`}>
              {row.keyMetrics.respiratory.trend === 'up' ? '↗' : 
               row.keyMetrics.respiratory.trend === 'down' ? '↘' : '→'}
            </span>
          </div>
          <div class="flex items-center gap-1">
            <span>心理:</span>
            <span class={`font-medium ${row.keyMetrics.mental.score >= 70 ? 'text-green-600' : 'text-red-600'}`}>
              {row.keyMetrics.mental.score}
            </span>
            <span class={`${row.keyMetrics.mental.trend === 'up' ? 'text-green-500' : 
              row.keyMetrics.mental.trend === 'down' ? 'text-red-500' : 'text-gray-500'}`}>
              {row.keyMetrics.mental.trend === 'up' ? '↗' : 
               row.keyMetrics.mental.trend === 'down' ? '↘' : '→'}
            </span>
          </div>
          <div class="flex items-center gap-1">
            <span>体能:</span>
            <span class={`font-medium ${row.keyMetrics.physical.score >= 70 ? 'text-green-600' : 'text-red-600'}`}>
              {row.keyMetrics.physical.score}
            </span>
            <span class={`${row.keyMetrics.physical.trend === 'up' ? 'text-green-500' : 
              row.keyMetrics.physical.trend === 'down' ? 'text-red-500' : 'text-gray-500'}`}>
              {row.keyMetrics.physical.trend === 'up' ? '↗' : 
               row.keyMetrics.physical.trend === 'down' ? '↘' : '→'}
            </span>
          </div>
        </div>
      )
    },
    {
      key: 'alerts',
      title: '预警数',
      align: 'center',
      width: 80,
      render: row => (
        <span class={`font-medium ${row.alerts > 0 ? 'text-red-600' : 'text-green-600'}`}>
          {row.alerts}
        </span>
      )
    },
    {
      key: 'recommendations',
      title: '建议数',
      align: 'center',
      width: 80
    },
    {
      key: 'dataQuality',
      title: '数据质量',
      align: 'center',
      width: 100,
      render: row => (
        <span class={`font-medium ${
          row.dataQuality >= 90 ? 'text-green-600' : 
          row.dataQuality >= 70 ? 'text-yellow-600' : 'text-red-600'
        }`}>
          {row.dataQuality}%
        </span>
      )
    },
    {
      key: 'lastUpdated',
      title: '更新时间',
      align: 'center',
      width: 160,
      render: row => convertToBeijingTime(row.lastUpdated)
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 280,
      minWidth: 280,
      render: row => (
        <NSpace size="small">
          <NButton 
            type="info" 
            quaternary 
            size="small" 
            onClick={() => viewProfile(row)}
          >
            查看详情
          </NButton>
          <NButton 
            type="primary" 
            quaternary 
            size="small" 
            onClick={() => generateProfile(row)}
          >
            重新生成
          </NButton>
          {hasAuth('health:profile:edit') && (
            <NButton 
              type="primary" 
              quaternary 
              size="small" 
              onClick={() => edit(row)}
            >
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('health:profile:delete') && (
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
        </NSpace>
      )
    }
  ]
});

const { drawerVisible, openDrawer, checkedRowKeys, onDeleted, onBatchDeleted } = useTableOperate(data, getData);

function handleAdd() {
  operateType.value = 'add';
  editingData.value = null;
  openDrawer();
}

function edit(item: Api.Health.HealthProfile) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

function viewProfile(item: Api.Health.HealthProfile) {
  selectedProfile.value = item;
  analyticsViewerVisible.value = true;
}

function openTemplateManager() {
  templateManagerVisible.value = true;
}

async function generateProfile(item: Api.Health.HealthProfile) {
  // 模拟重新生成画像
  window.$message?.info('正在重新生成健康画像...');
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // 更新数据
  const index = data.value.findIndex(d => d.id === item.id);
  if (index > -1) {
    data.value[index].lastUpdated = new Date().toISOString().replace('T', ' ').substring(0, 19);
    data.value[index].profileCompleteness = Math.min(100, data.value[index].profileCompleteness + 5);
  }
  
  window.$message?.success('健康画像生成完成');
}

async function handleDelete(id: string) {
  const { error, data: result } = await fetchDeleteHealthProfile([id]);
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  const { error, data: result } = await fetchDeleteHealthProfile(checkedRowKeys.value);
  if (!error && result) {
    await onBatchDeleted();
  }
}

// 组织架构和用户选项
type OrgUnitsTree = Api.SystemManage.OrgUnitsTree;
const orgUnitsTree = shallowRef<OrgUnitsTree[]>([]);
const userOptions = ref<{ label: string; value: string }[]>([]);

async function handleInitOptions() {
  fetchGetOrgUnitsTree(customerId).then(({ error, data: treeData }) => {
    if (!error && treeData) {
      orgUnitsTree.value = treeData;
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

// 统计信息
const profileStats = computed(() => {
  const stats = {
    total: data.value.length,
    highRisk: 0,
    lowCompleteness: 0,
    needUpdate: 0,
    avgHealthScore: 0
  };
  
  let totalHealthScore = 0;
  const now = new Date();
  
  data.value.forEach(profile => {
    if (profile.riskLevel === 'high') {
      stats.highRisk++;
    }
    if (profile.profileCompleteness < 80) {
      stats.lowCompleteness++;
    }
    
    // 检查是否需要更新（超过7天）
    const lastUpdate = new Date(profile.lastUpdated);
    const daysSinceUpdate = (now.getTime() - lastUpdate.getTime()) / (1000 * 60 * 60 * 24);
    if (daysSinceUpdate > 7) {
      stats.needUpdate++;
    }
    
    totalHealthScore += profile.overallHealthScore;
  });
  
  stats.avgHealthScore = data.value.length > 0 ? totalHealthScore / data.value.length : 0;
  return stats;
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
      <NCard size="small">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-600">总画像数</div>
            <div class="text-2xl font-bold text-primary">{{ profileStats.total }}</div>
          </div>
          <div class="text-3xl text-primary opacity-20">👤</div>
        </div>
      </NCard>
      
      <NCard size="small">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-600">高风险用户</div>
            <div class="text-2xl font-bold text-error">{{ profileStats.highRisk }}</div>
          </div>
          <div class="text-3xl text-error opacity-20">⚠️</div>
        </div>
      </NCard>
      
      <NCard size="small">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-600">待完善画像</div>
            <div class="text-2xl font-bold text-warning">{{ profileStats.lowCompleteness }}</div>
          </div>
          <div class="text-3xl text-warning opacity-20">📊</div>
        </div>
      </NCard>
      
      <NCard size="small">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-600">平均健康分</div>
            <div class="text-2xl font-bold text-success">{{ profileStats.avgHealthScore.toFixed(0) }}</div>
          </div>
          <div class="text-3xl text-success opacity-20">💚</div>
        </div>
      </NCard>
    </div>

    <!-- 搜索组件 -->
    <HealthProfileSearch
      v-model:model="searchParams"
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      :customer-id="customerId"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    
    <!-- 主要内容区域 -->
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg font-semibold">健康画像管理</span>
          <NSpace>
            <NButton type="info" @click="openTemplateManager">
              <template #icon>
                <div class="i-mdi:file-document-edit" />
              </template>
              画像模板
            </NButton>
          </NSpace>
        </div>
      </template>
      
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="health:profile:add"
        delete-auth="health:profile:delete"
        @add="handleAdd"
        @delete="handleBatchDelete"
        @refresh="getData"
      >
        <template #default>
          <NButton type="primary" @click="handleAdd">
            <template #icon>
              <div class="i-mdi:plus" />
            </template>
            创建健康画像
          </NButton>
        </template>
      </TableHeaderOperation>
      
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        striped
        size="small"
        class="sm:h-full"
        :data="data"
        :scroll-x="1400"
        :columns="columns"
        :flex-height="!appStore.isMobile"
        :loading="loading"
        :single-line="false"
        :row-key="row => row.id"
        :pagination="mobilePagination"
      />
    </NCard>

    <!-- 操作抽屉 -->
    <HealthProfileOperateDrawer 
      v-model:visible="drawerVisible" 
      :operate-type="operateType" 
      :row-data="editingData" 
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      @submitted="getDataByPage" 
    />

    <!-- 画像详情查看器 -->
    <ProfileAnalyticsViewer 
      v-model:visible="analyticsViewerVisible"
      :profile-data="selectedProfile"
    />

    <!-- 模板管理器弹窗 -->
    <ProfileTemplateManager 
      v-model:visible="templateManagerVisible"
      @template-updated="getData"
    />
  </div>
</template>

<style scoped>
.card-wrapper :deep(.n-card__content) {
  @apply flex-1-hidden;
}

.text-primary {
  color: var(--primary-color);
}

.text-success {
  color: var(--success-color);
}

.text-info {
  color: var(--info-color);
}

.text-warning {
  color: var(--warning-color);
}

.text-error {
  color: var(--error-color);
}
</style>
