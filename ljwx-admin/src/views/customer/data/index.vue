<script setup lang="tsx">
import { NButton, NPopconfirm, NCard, NCollapse, NCollapseItem, NList, NListItem, NIcon, NSpace, NAlert } from 'naive-ui';
import type { Ref } from 'vue';
import { ref, shallowRef } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteHealthDataConfig, fetchGetHealthDataConfigList, fetchGetOrgUnitsTree } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import HealthDataConfigSearch from './modules/health-data-config-search.vue';
import HealthDataConfigOperateDrawer from './modules/health-data-config-operate-drawer.vue';

defineOptions({
  name: 'THealthDataConfigPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;
const { hasAuth } = useAuth();

const { dictTag } = useDict();

const editingData: Ref<Api.Customer.HealthDataConfig | null> = ref(null);

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetHealthDataConfigList,
  apiParams: {
    page: 1,
    pageSize: 20,
    customerId: customerId ?? 0
  },
  columns: () => [
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },

    {
      key: 'dataType',
      title: $t('page.customer.healthDataConfig.dataType'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'frequencyInterval',
      title: `${$t('page.customer.healthDataConfig.frequencyInterval')}(秒)`,
      align: 'center',
      minWidth: 100
    },
    {
      key: 'isEnabled',
      title: $t('page.customer.healthDataConfig.enabled'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'warningHigh',
      title: $t('page.customer.healthDataConfig.warningHigh'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'warningLow',
      title: $t('page.customer.healthDataConfig.warningLow'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'warningCnt',
      title: $t('page.customer.healthDataConfig.warningCnt'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'weight',
      title: $t('page.customer.healthDataConfig.weight'),
      align: 'center',
      minWidth: 100
    },

    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 200,
      minWidth: 200,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('t:health:data:config:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:health:data:config:delete') && (
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

function handleAdd() {}

function edit(item: Api.Customer.HealthDataConfig) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteHealthDataConfig(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteHealthDataConfig(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}

const manualExpanded = ref<string[]>([]);
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <!-- 健康数据配置操作手册 -->
    <NCard :bordered="false" size="small" class="operation-manual">
      <NCollapse v-model:expanded-names="manualExpanded">
        <NCollapseItem name="manual" title="💊 健康数据配置操作手册">
          <div class="space-y-4 text-sm max-h-400px overflow-y-auto">
            <!-- 数据类型说明 -->
            <NCard title="📊 健康数据类型说明" size="small">
              <NList>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#e74c3c">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M4.8 2h14.4C20.26 2 21 2.74 21 3.8v16.4c0 1.06-.74 1.8-1.8 1.8H4.8C3.74 22 3 21.26 3 20.2V3.8C3 2.74 3.74 2 4.8 2z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">心率数据 (heartRate)</div>
                      <div class="text-gray-600">心脏每分钟跳动次数，正常范围60-100次/分钟</div>
                    </div>
                  </NSpace>
                </NListItem>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#3498db">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">血氧饱和度 (spo2)</div>
                      <div class="text-gray-600">血液中氧气饱和度，正常范围95%-100%</div>
                    </div>
                  </NSpace>
                </NListItem>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#9b59b6">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">血压数据 (bloodPressure)</div>
                      <div class="text-gray-600">收缩压和舒张压，正常范围90-140/60-90 mmHg</div>
                    </div>
                  </NSpace>
                </NListItem>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#f39c12">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">体温数据 (temperature)</div>
                      <div class="text-gray-600">人体体温，正常范围36.1℃-37.2℃</div>
                    </div>
                  </NSpace>
                </NListItem>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#e67e22">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">压力指数 (stress)</div>
                      <div class="text-gray-600">心理压力水平，范围0-100，数值越高压力越大</div>
                    </div>
                  </NSpace>
                </NListItem>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#27ae60">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M13.5 5.5c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zM9.8 8.5L6 13.5l1.5 1.5c.5.5 1.1.5 1.6 0L12 12l2.9 3c.5.5 1.1.5 1.6 0l1.5-1.5L14.2 8.5c-.4-.8-1.3-1.3-2.2-1.3H12c-.9 0-1.8.5-2.2 1.3z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">步数统计 (step)</div>
                      <div class="text-gray-600">每日行走步数，建议目标8000-10000步/天</div>
                    </div>
                  </NSpace>
                </NListItem>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#2ecc71">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">运动距离 (distance)</div>
                      <div class="text-gray-600">行走或跑步距离，单位公里，建议每日3-5公里</div>
                    </div>
                  </NSpace>
                </NListItem>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#e74c3c">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M15.5 11c1.38 0 2.5-1.12 2.5-2.5S16.88 6 15.5 6 13 7.12 13 8.5s1.12 2.5 2.5 2.5zM8.5 11c1.38 0 2.5-1.12 2.5-2.5S9.88 6 8.5 6 6 7.12 6 8.5 7.12 11 8.5 11zM15.5 13c-1.83 0-5.5.73-5.5 2.5V18h11v-2.5c0-1.77-3.67-2.5-5.5-2.5zM8.5 13c-.25 0-.54.03-.87.08.48.58.87 1.34.87 2.42V18H2v-2.5c0-1.77 3.67-2.5 5.5-2.5z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">卡路里消耗 (calorie)</div>
                      <div class="text-gray-600">每日能量消耗，单位kcal，成人建议1800-2500kcal/天</div>
                    </div>
                  </NSpace>
                </NListItem>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#8e44ad">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2c-4.97 0-9 4.03-9 9 0 4.17 2.84 7.67 6.69 8.69L12 22l2.31-2.31C18.16 18.67 21 15.17 21 11c0-4.97-4.03-9-9-9zm0 2c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">睡眠质量 (sleep)</div>
                      <div class="text-gray-600">睡眠时长和质量评分，建议7-9小时优质睡眠</div>
                    </div>
                  </NSpace>
                </NListItem>
              </NList>
            </NCard>

            <!-- 配置参数说明 -->
            <NCard title="⚙️ 配置参数说明" size="small">
              <NList>
                <NListItem>
                  <div>
                    <div class="font-medium text-blue-600">📊 采集频率间隔</div>
                    <div class="text-gray-600 mt-1">• 影响：健康数据采集的时间间隔</div>
                    <div class="text-gray-600">• 建议：心率、血氧30-60秒；血压、体温300-600秒</div>
                    <div class="text-gray-600">• 风险：频率过高耗电快，过低可能错过异常</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium text-orange-600">⚠️ 预警阈值设置</div>
                    <div class="text-gray-600 mt-1">• 影响：告警触发的临界值</div>
                    <div class="text-gray-600">• 建议：根据年龄、性别、职业特点个性化设置</div>
                    <div class="text-gray-600">• 风险：阈值过严会误报，过松会漏报</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium text-green-600">🎯 预警次数限制</div>
                    <div class="text-gray-600 mt-1">• 影响：连续超阈值多少次后才触发告警</div>
                    <div class="text-gray-600">• 建议：一般设置2-5次，避免偶发异常误报</div>
                    <div class="text-gray-600">• 风险：次数过多会延迟告警，过少会频繁告警</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium text-purple-600">⚖️ 数据权重</div>
                    <div class="text-gray-600 mt-1">• 影响：该指标在健康评分中的重要程度</div>
                    <div class="text-gray-600">• 建议：心率0.2，血氧0.25，血压0.2，压力0.1，步数0.08，距离0.07，卡路里0.05，睡眠0.05</div>
                    <div class="text-gray-600">• 风险：权重分配不当会影响健康评估准确性</div>
                  </div>
                </NListItem>
              </NList>
            </NCard>

            <!-- 操作指南 -->
            <NCard title="📖 操作指南" size="small">
              <NList>
                <NListItem>
                  <div>
                    <div class="font-medium">1. 配置健康指标</div>
                    <div class="text-gray-600 mt-1">选择数据类型 → 设置采集频率 → 配置预警阈值 → 设置权重比例 → 启用监测</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium">2. 调整预警参数</div>
                    <div class="text-gray-600 mt-1">点击"编辑"按钮 → 修改高低阈值 → 调整预警次数 → 验证设置合理性 → 保存</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium">3. 优化采集策略</div>
                    <div class="text-gray-600 mt-1">根据设备电量和数据重要性，平衡采集频率和电池续航</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium">4. 个性化配置</div>
                    <div class="text-gray-600 mt-1">考虑用户年龄、职业、病史等因素，制定个性化监测方案</div>
                  </div>
                </NListItem>
              </NList>
            </NCard>

            <!-- 最佳实践 -->
            <NCard title="🎯 最佳实践" size="small">
              <NList>
                <NListItem>
                  <div>
                    <div class="font-medium">阈值设置原则</div>
                    <div class="text-gray-600 mt-1">• 参考医学标准范围，结合个体差异</div>
                    <div class="text-gray-600">• 高危人群适当收紧阈值</div>
                    <div class="text-gray-600">• 定期根据历史数据调整基线</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium">频率优化策略</div>
                    <div class="text-gray-600 mt-1">• 白天采集频率可以提高</div>
                    <div class="text-gray-600">• 夜间适当降低频率节省电量</div>
                    <div class="text-gray-600">• 异常状态下自动提高采集频率</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium">权重分配建议</div>
                    <div class="text-gray-600 mt-1">• 总权重保持1.0平衡</div>
                    <div class="text-gray-600">• 生理指标(心率+血氧+血压)权重0.65，运动指标(步数+距离+卡路里)权重0.2，心理睡眠指标权重0.15</div>
                    <div class="text-gray-600">• 根据职业风险调整重点指标：高危作业提升心率血氧权重，久坐办公提升运动指标权重</div>
                    <div class="text-gray-600">• 季节性调整某些指标权重</div>
                  </div>
                </NListItem>
              </NList>
            </NCard>

            <!-- 注意事项 -->
            <NAlert type="warning" title="⚠️ 重要提醒" show-icon class="mt-4">
              <div class="space-y-2">
                <div>• 修改采集频率会影响设备电池续航，请权衡设置</div>
                <div>• 预警阈值变更建议先在小范围测试</div>
                <div>• 权重调整会影响健康评分算法，需要重新计算历史数据</div>
                <div>• 禁用某项监测前请确认没有相关告警规则依赖</div>
              </div>
            </NAlert>
          </div>
        </NCollapseItem>
      </NCollapse>
    </NCard>

    <HealthDataConfigSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="t:health:data:config:add"
        delete-auth="t:health:data:config:delete"
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
      <HealthDataConfigOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>
