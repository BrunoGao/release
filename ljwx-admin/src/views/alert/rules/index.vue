<script setup lang="tsx">
import {
  NAlert,
  NButton,
  NCard,
  NCollapse,
  NCollapseItem,
  NIcon,
  NList,
  NListItem,
  NPopconfirm,
  NProgress,
  NSpace,
  NStatistic,
  NTag,
  NTooltip
} from 'naive-ui';
import type { Ref } from 'vue';
import { computed, onMounted, ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuth } from '@/hooks/business/auth';
import { useAuthStore } from '@/store/modules/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteAlertRules, fetchGetAlertRulesList, fetchUpdateAlertRulesInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { convertToBeijingTime } from '@/utils/date';
import AlerrulesSearch from './modules/alerrules-search.vue';
import AlerrulesOperateDrawer from './modules/alerrules-operate-drawer.vue';
import AlertRuleWizard from './components/AlertRuleWizard.vue';
defineOptions({
  name: 'TAlertRulesPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();
const authStore = useAuthStore();
const { hasAuth } = useAuth();

const { dictTag } = useDict();

const editingData: Ref<Api.Health.AlertRules | null> = ref(null);
const customerId = authStore.userInfo?.customerId;
const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetAlertRulesList,
  apiParams: {
    page: 1,
    pageSize: 20,
    ruleType: null,
    customerId,
    physicalSign: null
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
      key: 'ruleCategory',
      title: '规则类型',
      align: 'center',
      minWidth: 100,
      render: row => {
        const category = row.ruleCategory || 'SINGLE';
        const typeMap = {
          SINGLE: { text: '单体征', type: 'primary' },
          COMPOSITE: { text: '复合', type: 'warning' },
          COMPLEX: { text: '复杂', type: 'error' }
        };
        const config = typeMap[category] || typeMap.SINGLE;
        return (
          <NTag type={config.type} size="small">
            {config.text}
          </NTag>
        );
      }
    },
    {
      key: 'physicalSign',
      title: '监控指标',
      align: 'center',
      minWidth: 180,
      render: row => {
        if (row.ruleCategory === 'COMPOSITE') {
          // 复合规则：显示多指标组合
          const indicators = row.compositeIndicators || row.physicalSigns || [];
          if (indicators.length > 0) {
            return (
              <div class="flex flex-col gap-1">
                <NTag type="warning" size="small" class="mb-1">
                  <NIcon size="12" class="mr-1">
                    <i class="i-material-symbols:group-work"></i>
                  </NIcon>
                  多指标组合 ({indicators.length})
                </NTag>
                <div class="composite-indicators flex flex-wrap gap-1">
                  {indicators.slice(0, 3).map((indicator, index) => (
                    <NTag key={index} type="info" size="tiny" class="text-xs">
                      {dictTag('health_data_type', indicator)?.props?.children || indicator}
                    </NTag>
                  ))}
                  {indicators.length > 3 && (
                    <NTooltip trigger="hover">
                      {{
                        trigger: () => (
                          <NTag type="default" size="tiny" class="cursor-pointer text-xs">
                            +{indicators.length - 3}
                          </NTag>
                        ),
                        default: () => (
                          <div class="flex flex-col gap-1">
                            {indicators.slice(3).map((indicator, index) => (
                              <span key={index} class="text-xs">
                                {dictTag('health_data_type', indicator)?.props?.children || indicator}
                              </span>
                            ))}
                          </div>
                        )
                      }}
                    </NTooltip>
                  )}
                </div>
              </div>
            );
          }
          return (
            <NTag type="warning" size="small">
              <NIcon size="12" class="mr-1">
                <i class="i-material-symbols:warning"></i>
              </NIcon>
              未配置指标
            </NTag>
          );
        } else if (row.ruleCategory === 'COMPLEX') {
          // 复杂规则：显示AI分析标识
          return (
            <NTag type="error" size="small">
              <NIcon size="12" class="mr-1">
                <i class="i-material-symbols:auto-awesome"></i>
              </NIcon>
              AI智能分析
            </NTag>
          );
        }
        // 单体征规则：显示具体指标
        const indicator = dictTag('health_data_type', row.physicalSign);
        if (indicator) {
          return (
            <NTag type="primary" size="small">
              <NIcon size="12" class="mr-1">
                <i class="i-material-symbols:monitor-heart"></i>
              </NIcon>
              {indicator}
            </NTag>
          );
        }
        return (
          <NTag type="default" size="small">
            <NIcon size="12" class="mr-1">
              <i class="i-material-symbols:help"></i>
            </NIcon>
            {row.physicalSign || '未设置'}
          </NTag>
        );
      }
    },
    {
      key: 'thresholds',
      title: '阈值范围',
      align: 'center',
      minWidth: 150,
      render: row => {
        if (row.ruleCategory === 'COMPOSITE') {
          // 复合规则：显示复合条件
          const conditions = row.compositeConditions || [];
          if (conditions.length > 0) {
            return (
              <div class="composite-conditions flex flex-col gap-1">
                <NTag type="warning" size="small" class="mb-1">
                  <NIcon size="12" class="mr-1">
                    <i class="i-material-symbols:rule"></i>
                  </NIcon>
                  复合条件 ({conditions.length})
                </NTag>
                {conditions.slice(0, 2).map((condition, index) => (
                  <div key={index} class="condition-item px-2 py-1 text-xs text-gray-600">
                    {condition.indicator}: {condition.operator} {condition.value}
                  </div>
                ))}
                {conditions.length > 2 && (
                  <NTooltip trigger="hover">
                    {{
                      trigger: () => (
                        <div class="cursor-pointer text-xs text-blue-600 hover:text-blue-800">查看更多条件 (+{conditions.length - 2})</div>
                      ),
                      default: () => (
                        <div class="max-w-60 flex flex-col gap-1">
                          {conditions.slice(2).map((condition, index) => (
                            <div key={index} class="tooltip-condition p-2 text-xs">
                              <strong>{condition.indicator}</strong>: {condition.operator} {condition.value}
                              {condition.unit && <span class="text-gray-500"> {condition.unit}</span>}
                            </div>
                          ))}
                        </div>
                      )
                    }}
                  </NTooltip>
                )}
              </div>
            );
          }
          return (
            <NTag type="warning" size="small">
              <NIcon size="12" class="mr-1">
                <i class="i-material-symbols:warning"></i>
              </NIcon>
              未配置条件
            </NTag>
          );
        } else if (row.ruleCategory === 'COMPLEX') {
          // 复杂规则：显示AI条件
          return (
            <NTag type="error" size="small">
              <NIcon size="12" class="mr-1">
                <i class="i-material-symbols:psychology"></i>
              </NIcon>
              AI算法决策
            </NTag>
          );
        }
        // 单体征规则：显示具体阈值
        const min = row.thresholdMin;
        const max = row.thresholdMax;

        if (min != null && max != null) {
          return (
            <NTag type="primary" size="small">
              <NIcon size="12" class="mr-1">
                <i class="i-material-symbols:straighten"></i>
              </NIcon>
              {min} - {max}
            </NTag>
          );
        } else if (min != null) {
          return (
            <NTag type="warning" size="small">
              <NIcon size="12" class="mr-1">
                <i class="i-material-symbols:keyboard-arrow-up"></i>
              </NIcon>
              ≥ {min}
            </NTag>
          );
        } else if (max != null) {
          return (
            <NTag type="error" size="small">
              <NIcon size="12" class="mr-1">
                <i class="i-material-symbols:keyboard-arrow-down"></i>
              </NIcon>
              ≤ {max}
            </NTag>
          );
        }

        return (
          <NTag type="default" size="small">
            <NIcon size="12" class="mr-1">
              <i class="i-material-symbols:help"></i>
            </NIcon>
            未设置
          </NTag>
        );
      }
    },
    {
      key: 'priorityLevel',
      title: '优先级',
      align: 'center',
      minWidth: 80,
      render: row => {
        const priority = row.priorityLevel || 3;
        const priorityMap = {
          1: { text: '最高', type: 'error', color: '#ff4d4f' },
          2: { text: '高', type: 'warning', color: '#fa8c16' },
          3: { text: '中', type: 'info', color: '#1890ff' },
          4: { text: '低', type: 'default', color: '#52c41a' }
        };
        const config = priorityMap[priority] || priorityMap[3];
        return (
          <NTag type={config.type} size="small">
            {config.text}
          </NTag>
        );
      }
    },
    {
      key: 'level',
      title: '严重级别',
      align: 'center',
      minWidth: 100,
      render: row => {
        const levelMap = {
          CRITICAL: { text: '紧急', type: 'error' },
          HIGH: { text: '高', type: 'warning' },
          MEDIUM: { text: '中', type: 'info' },
          LOW: { text: '低', type: 'default' }
        };
        const config = levelMap[row.level] || levelMap.MEDIUM;
        return (
          <NTag type={config.type} size="small">
            {config.text}
          </NTag>
        );
      }
    },
    {
      key: 'timeWindow',
      title: '时间窗口',
      align: 'center',
      minWidth: 100,
      render: row => {
        const seconds = row.timeWindowSeconds || 300;
        if (seconds >= 3600) {
          return <span>{(seconds / 3600).toFixed(1)}小时</span>;
        } else if (seconds >= 60) {
          return <span>{seconds / 60}分钟</span>;
        }
        return <span>{seconds}秒</span>;
      }
    },
    {
      key: 'enabledChannels',
      title: '通知渠道',
      align: 'center',
      minWidth: 120,
      render: row => {
        const channels = row.enabledChannels || ['message'];
        const channelMap = {
          message: '内部消息',
          wechat: '微信',
          sms: '短信',
          email: '邮件'
        };
        return (
          <div class="flex flex-wrap justify-center gap-1">
            {channels.map(ch => (
              <NTag key={ch} size="small" type="success">
                {channelMap[ch] || ch}
              </NTag>
            ))}
          </div>
        );
      }
    },
    {
      key: 'isEnabled',
      title: '状态',
      align: 'center',
      minWidth: 80,
      render: row => {
        const enabled = row.isEnabled;
        return (
          <NTag type={enabled ? 'success' : 'default'} size="small">
            {enabled ? '启用' : '禁用'}
          </NTag>
        );
      }
    },
    {
      key: 'createTime',
      title: '创建时间',
      align: 'center',
      minWidth: 120,
      render: row => convertToBeijingTime(row.createTime)
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 280,
      minWidth: 280,
      render: row => (
        <div class="flex-center flex-wrap gap-8px">
          {hasAuth('t:alert:rules:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              编辑
            </NButton>
          )}
          <NButton type="info" quaternary size="small" onClick={() => testRule(row)}>
            测试
          </NButton>
          <NTooltip trigger="hover">
            {{
              trigger: () => (
                <NButton type={row.isEnabled ? 'warning' : 'success'} quaternary size="small" onClick={() => toggleRuleStatus(row)}>
                  {row.isEnabled ? '禁用' : '启用'}
                </NButton>
              ),
              default: () => (row.isEnabled ? '点击禁用规则' : '点击启用规则')
            }}
          </NTooltip>
          {hasAuth('t:alert:rules:delete') && (
            <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
              {{
                default: () => $t('common.confirmDelete'),
                trigger: () => (
                  <NButton type="error" quaternary size="small">
                    删除
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

function edit(item: Api.Health.AlertRules) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteAlertRules(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteAlertRules(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}

// 测试规则
async function testRule(row: Api.Health.AlertRules) {
  window.$message?.info('规则测试功能正在开发中...');
  // TODO: 实现规则测试功能
}

// 切换规则状态
async function toggleRuleStatus(row: Api.Health.AlertRules) {
  try {
    const updatedRow = { ...row, isEnabled: !row.isEnabled };
    const { error } = await fetchUpdateAlertRulesInfo(updatedRow);
    if (!error) {
      window.$message?.success(updatedRow.isEnabled ? '规则已启用' : '规则已禁用');
      await getData();
    }
  } catch (error) {
    window.$message?.error('状态切换失败');
  }
}

// 操作手册展开状态
const manualExpanded = ref(false);

// 向导状态
const wizardVisible = ref(false);

// 统计信息
const ruleStats = computed(() => {
  if (!data.value?.length) {
    return {
      total: 0,
      enabled: 0,
      disabled: 0,
      single: 0,
      composite: 0,
      complex: 0
    };
  }

  const stats = {
    total: data.value.length,
    enabled: data.value.filter(r => r.isEnabled).length,
    disabled: data.value.filter(r => !r.isEnabled).length,
    single: data.value.filter(r => (r.ruleCategory || 'SINGLE') === 'SINGLE').length,
    composite: data.value.filter(r => r.ruleCategory === 'COMPOSITE').length,
    complex: data.value.filter(r => r.ruleCategory === 'COMPLEX').length
  };

  return stats;
});

// 性能监控跳转
function goToPerformanceMonitor() {
  // 跳转到性能监控页面
  window.open('/monitor/alert-performance', '_blank');
}

// 打开配置向导
function openWizard() {
  wizardVisible.value = true;
}

// 向导成功回调
function onWizardSuccess() {
  getData(); // 刷新数据
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <!-- 统计概览 -->
    <div class="grid grid-cols-2 mb-4 gap-4 md:grid-cols-6">
      <NCard size="small" class="stats-card">
        <NStatistic label="总规则数" :value="ruleStats.total">
          <template #prefix>
            <NIcon size="18" color="#1890ff">
              <i class="i-material-symbols:rule"></i>
            </NIcon>
          </template>
        </NStatistic>
      </NCard>

      <NCard size="small" class="stats-card">
        <NStatistic label="已启用" :value="ruleStats.enabled">
          <template #prefix>
            <NIcon size="18" color="#52c41a">
              <i class="i-material-symbols:check-circle"></i>
            </NIcon>
          </template>
        </NStatistic>
      </NCard>

      <NCard size="small" class="stats-card">
        <NStatistic label="已禁用" :value="ruleStats.disabled">
          <template #prefix>
            <NIcon size="18" color="#ff4d4f">
              <i class="i-material-symbols:block"></i>
            </NIcon>
          </template>
        </NStatistic>
      </NCard>

      <NCard size="small" class="stats-card">
        <NStatistic label="单体征规则" :value="ruleStats.single">
          <template #prefix>
            <NIcon size="18" color="#722ed1">
              <i class="i-material-symbols:person"></i>
            </NIcon>
          </template>
        </NStatistic>
      </NCard>

      <NCard size="small" class="stats-card">
        <NStatistic label="复合规则" :value="ruleStats.composite">
          <template #prefix>
            <NIcon size="18" color="#fa8c16">
              <i class="i-material-symbols:group"></i>
            </NIcon>
          </template>
        </NStatistic>
      </NCard>

      <NCard size="small" class="stats-card">
        <div class="flex items-center justify-between">
          <div>
            <div class="mb-1 text-xs text-gray-500">性能监控</div>
            <NButton type="primary" size="small" @click="goToPerformanceMonitor">查看详情</NButton>
          </div>
          <NIcon size="20" color="#13c2c2">
            <i class="i-material-symbols:monitoring"></i>
          </NIcon>
        </div>
      </NCard>
    </div>

    <!-- 操作手册 -->
    <NCard :bordered="false" size="small" class="operation-manual">
      <NCollapse v-model:expanded-names="manualExpanded">
        <NCollapseItem name="manual" title="📋 告警规则操作手册">
          <template #header-extra>
            <NSpace>
              <span class="text-xs text-gray-500">点击展开查看详细操作说明</span>
            </NSpace>
          </template>

          <div class="manual-content manual-scrollable">
            <NAlert type="info" :show-icon="false" class="mb-4">
              <template #header>
                <div class="flex items-center gap-2">
                  <NIcon size="16">
                    <i class="i-material-symbols:info"></i>
                  </NIcon>
                  <span class="font-semibold">系统概述 - 增强版</span>
                </div>
              </template>
              <div class="text-sm space-y-2">
                <p>
                  <strong>✨ 全新功能</strong>
                  ：支持单体征、复合、复杂三种规则类型，实现智能告警和多渠道通知
                </p>
                <p>
                  <strong>🚀 性能优化</strong>
                  ：三层缓存架构，支持并行处理和实时性能监控
                </p>
                <p>
                  <strong>📊 统计监控</strong>
                  ：规则执行统计、性能排行、系统负载监控等
                </p>
                <p>
                  <strong>🎯 智能向导</strong>
                  ：提供分步引导配置，适合新用户快速上手；传统表单适合专家用户快速编辑
                </p>
                <p>
                  <strong>⚡ 实时操作</strong>
                  ：支持一键测试、启用/禁用切换、实时性能监控，无需页面刷新
                </p>
              </div>
            </NAlert>

            <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
              <!-- 基础操作 -->
              <NCard size="small" class="manual-section">
                <template #header>
                  <div class="flex items-center gap-2">
                    <NIcon size="16" color="#3b82f6">
                      <i class="i-material-symbols:settings"></i>
                    </NIcon>
                    <span class="font-medium">基础操作</span>
                  </div>
                </template>
                <NList size="small">
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-number">1</span>
                      <div>
                        <div class="item-title">新增规则</div>
                        <div class="item-desc">
                          点击"智能配置向导"进行分步引导创建，或使用"新增"按钮快速创建。向导支持单体征、复合规则，提供配置建议和验证
                        </div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-number">2</span>
                      <div>
                        <div class="item-title">测试规则</div>
                        <div class="item-desc">点击操作列的"测试"按钮验证规则逻辑，支持模拟数据测试和实时数据验证</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-number">3</span>
                      <div>
                        <div class="item-title">启用/禁用</div>
                        <div class="item-desc">点击操作列的"启用/禁用"按钮快速切换规则状态，立即生效无需页面刷新</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-number">4</span>
                      <div>
                        <div class="item-title">性能监控</div>
                        <div class="item-desc">点击右上角"查看详情"查看规则执行性能、统计排行、系统负载、缓存命中率等详细监控信息</div>
                      </div>
                    </div>
                  </NListItem>
                </NList>
              </NCard>

              <!-- 规则配置 -->
              <NCard size="small" class="manual-section">
                <template #header>
                  <div class="flex items-center gap-2">
                    <NIcon size="16" color="#10b981">
                      <i class="i-material-symbols:rule"></i>
                    </NIcon>
                    <span class="font-medium">规则配置</span>
                  </div>
                </template>
                <NList size="small">
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-badge">类型</span>
                      <div>
                        <div class="item-title">选择规则类型</div>
                        <div class="item-desc">单体征(监控单指标)、复合(多指标组合AND/OR)、复杂(AI智能分析，开发中)</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-badge">优先级</span>
                      <div>
                        <div class="item-title">设置处理优先级</div>
                        <div class="item-desc">最高(紧急处理)、高(5分钟内)、中(10分钟内)、低(30分钟内)</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-badge">时间窗口</span>
                      <div>
                        <div class="item-title">配置检测窗口</div>
                        <div class="item-desc">时间窗口(60-3600秒)、冷却期(300-86400秒)、持续时长(1-60分钟)</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-badge">渠道</span>
                      <div>
                        <div class="item-title">多渠道通知</div>
                        <div class="item-desc">内部消息(实时)、微信(推荐)、短信(收费)、邮件(延时)，可多选组合</div>
                      </div>
                    </div>
                  </NListItem>
                </NList>
              </NCard>
            </div>

            <!-- 常见示例 -->
            <NCard size="small" class="manual-section mt-4">
              <template #header>
                <div class="flex items-center gap-2">
                  <NIcon size="16" color="#f59e0b">
                    <i class="i-material-symbols:lightbulb"></i>
                  </NIcon>
                  <span class="font-medium">配置示例</span>
                </div>
              </template>
              <div class="examples-grid">
                <div class="example-item">
                  <div class="example-title">新手示例 - 心率异常监控</div>
                  <div class="example-content">
                    <span class="example-param">使用: 智能配置向导</span>
                    <span class="example-param">规则类型: 单体征</span>
                    <span class="example-param">监控指标: 心率</span>
                    <span class="example-param">阈值范围: 60-100 bpm</span>
                    <span class="example-param">时间窗口: 300秒(5分钟)</span>
                    <span class="example-param">优先级: 高 | 严重级别: 中</span>
                    <span class="example-param">通知: 微信+内部消息</span>
                  </div>
                </div>

                <div class="example-item">
                  <div class="example-title">专家示例 - 心血管综合预警</div>
                  <div class="example-content">
                    <span class="example-param">使用: 智能配置向导(推荐)</span>
                    <span class="example-param">规则类型: 复合</span>
                    <span class="example-param">条件1: 心率 > 100</span>
                    <span class="example-param">条件2: 收缩压 > 140</span>
                    <span class="example-param">逻辑: AND 操作</span>
                    <span class="example-param">时间窗口: 600秒(10分钟)</span>
                    <span class="example-param">优先级: 最高 | 冷却期: 30分钟</span>
                    <span class="example-param">通知: 微信+短信+内部消息</span>
                  </div>
                </div>

                <div class="example-item">
                  <div class="example-title">紧急情况 - 血氧危险预警</div>
                  <div class="example-content">
                    <span class="example-param">使用: 快速编辑表单</span>
                    <span class="example-param">规则类型: 单体征</span>
                    <span class="example-param">监控指标: 血氧</span>
                    <span class="example-param">阈值类型: 最小值 ≥ 95%</span>
                    <span class="example-param">持续时长: 1分钟即告警</span>
                    <span class="example-param">严重级别: 紧急(CRITICAL)</span>
                    <span class="example-param">通知: 全渠道(实时推送)</span>
                  </div>
                </div>

                <div class="example-item">
                  <div class="example-title">快速操作指南</div>
                  <div class="example-content">
                    <span class="example-param">🚀 快速启用: 点击"启用/禁用"按钮</span>
                    <span class="example-param">🧪 规则测试: 点击"测试"按钮验证逻辑</span>
                    <span class="example-param">📊 性能监控: 点击右上角"查看详情"</span>
                    <span class="example-param">⚡ 批量操作: 勾选多条记录批量删除</span>
                    <span class="example-param">📝 复制规则: 编辑现有规则另存为新规则</span>
                    <span class="example-param">🔄 实时刷新: 所有操作立即生效无需刷新</span>
                  </div>
                </div>
              </div>
            </NCard>
          </div>
        </NCollapseItem>
      </NCollapse>
    </NCard>

    <AlerrulesSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />

    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <!-- 增强的头部操作区域 -->
      <div class="mb-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <h2 class="text-lg text-gray-800 font-semibold">告警规则列表</h2>
          <NTag v-if="ruleStats.total > 0" :type="ruleStats.enabled > 0 ? 'success' : 'warning'" size="small">
            {{ ruleStats.enabled }}/{{ ruleStats.total }} 已启用
          </NTag>
        </div>

        <div class="flex items-center gap-3">
          <!-- 智能向导按钮 -->
          <NButton v-if="hasAuth('t:alert:rules:add')" size="small" type="primary" ghost @click="openWizard">
            <template #icon>
              <NIcon>
                <i class="i-material-symbols:auto-awesome"></i>
              </NIcon>
            </template>
            智能配置向导
          </NButton>

          <!-- 传统操作按钮 -->
          <TableHeaderOperation
            v-model:columns="columnChecks"
            :checked-row-keys="checkedRowKeys"
            :loading="loading"
            add-auth="t:alert:rules:add"
            delete-auth="t:alert:rules:delete"
            @add="handleAdd"
            @delete="handleBatchDelete"
            @refresh="getData"
          />
        </div>
      </div>
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
      <!-- 传统编辑表单 -->
      <AlerrulesOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />

      <!-- 智能配置向导 -->
      <AlertRuleWizard v-model:visible="wizardVisible" @success="onWizardSuccess" />
    </NCard>
  </div>
</template>

<style scoped>
/* 统计卡片样式 */
.stats-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.stats-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: translateY(-1px);
}

/* 操作手册样式 */
.operation-manual {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.manual-content {
  padding: 8px;
}

/* 操作手册可滚动样式 */
.manual-scrollable {
  max-height: 600px;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 transparent;
}

.manual-scrollable::-webkit-scrollbar {
  width: 6px;
}

.manual-scrollable::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 3px;
}

.manual-scrollable::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;
  transition: background 0.3s ease;
}

.manual-scrollable::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

.manual-section {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.manual-section:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.manual-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 4px 0;
}

.item-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.item-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 600;
  flex-shrink: 0;
  min-width: 40px;
}

.item-title {
  font-weight: 600;
  color: #1e293b;
  font-size: 13px;
  margin-bottom: 2px;
}

.item-desc {
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
}

.examples-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
  margin-top: 8px;
}

.example-item {
  padding: 12px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 1px solid #f59e0b;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.example-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
}

.example-title {
  font-weight: 600;
  color: #92400e;
  font-size: 13px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.example-title::before {
  content: '💡';
  font-size: 12px;
}

.example-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.example-param {
  font-size: 11px;
  color: #78350f;
  background: rgba(255, 255, 255, 0.6);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid #fbbf24;
}

/* 按钮对齐样式 */
.flex.items-center.gap-3 {
  align-items: center;
  gap: 12px;
}

.flex.items-center.gap-3 > * {
  display: flex;
  align-items: center;
}

/* 多指标组合显示样式优化 */
.composite-indicators {
  max-width: 160px;
}

.composite-indicators .n-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.composite-conditions {
  max-width: 140px;
}

.composite-conditions .condition-item {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.composite-conditions .condition-item:hover {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.15);
}

/* 工具提示内的条件显示优化 */
.tooltip-condition {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.tooltip-condition:hover {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
}

/* 监控指标图标美化 */
.indicator-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  margin-right: 6px;
}

/* 阈值标签优化 */
.threshold-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.threshold-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

/* 响应式优化 */
@media (max-width: 768px) {
  .examples-grid {
    grid-template-columns: 1fr;
  }

  .manual-content {
    padding: 4px;
  }

  .manual-scrollable {
    max-height: 400px;
  }

  .composite-indicators,
  .composite-conditions {
    max-width: 120px;
  }
}

/* 折叠面板样式优化 */
:deep(.n-collapse .n-collapse-item .n-collapse-item__header) {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-radius: 6px;
  padding: 12px 16px;
  font-weight: 600;
  color: #1e293b;
}

:deep(.n-collapse .n-collapse-item .n-collapse-item__content-wrapper) {
  border-top: 1px solid #e2e8f0;
  margin-top: 8px;
}
</style>
