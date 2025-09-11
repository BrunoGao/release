<template>
  <div class="alert-rules-management p-4">
    <!-- 页面头部 -->
    <div class="page-header mb-4 flex justify-between items-center">
      <div class="header-left">
        <h2 class="text-xl font-semibold flex items-center gap-2 mb-1">
          <n-icon size="20">
            <icon-ic:baseline-notifications />
          </n-icon>
          告警规则管理
        </h2>
        <p class="text-gray-600 text-sm">管理和配置系统告警规则，支持单体征、复合和复杂规则</p>
      </div>
      <div class="header-right">
        <n-space>
          <n-button type="primary" @click="openWizard">
            <template #icon>
              <n-icon><icon-ic:baseline-add /></n-icon>
            </template>
            新建规则
          </n-button>
          <n-button @click="refreshRules" :loading="loading">
            <template #icon>
              <n-icon><icon-ic:baseline-refresh /></n-icon>
            </template>
            刷新
          </n-button>
        </n-space>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <n-grid :cols="4" :x-gap="20" class="stats-cards mb-4">
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content flex items-center p-4">
            <div class="stat-icon total w-15 h-15 rounded-xl flex items-center justify-center mr-4 text-white text-xl">
              <n-icon size="24"><icon-ic:baseline-dashboard /></n-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value text-2xl font-bold">{{ statistics.totalRules }}</div>
              <div class="stat-label text-gray-500 text-sm">总规则数</div>
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content flex items-center p-4">
            <div class="stat-icon active w-15 h-15 rounded-xl flex items-center justify-center mr-4 text-white text-xl">
              <n-icon size="24"><icon-ic:baseline-check /></n-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value text-2xl font-bold">{{ statistics.activeRules }}</div>
              <div class="stat-label text-gray-500 text-sm">启用规则</div>
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content flex items-center p-4">
            <div class="stat-icon alerts w-15 h-15 rounded-xl flex items-center justify-center mr-4 text-white text-xl">
              <n-icon size="24"><icon-ic:baseline-warning /></n-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value text-2xl font-bold">{{ statistics.todayAlerts }}</div>
              <div class="stat-label text-gray-500 text-sm">今日告警</div>
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item>
        <n-card class="stat-card">
          <div class="stat-content flex items-center p-4">
            <div class="stat-icon performance w-15 h-15 rounded-xl flex items-center justify-center mr-4 text-white text-xl">
              <n-icon size="24"><icon-ic:baseline-trending-up /></n-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value text-2xl font-bold">{{ statistics.avgResponseTime }}ms</div>
              <div class="stat-label text-gray-500 text-sm">平均响应</div>
            </div>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>
    
    <!-- 搜索和过滤 -->
    <n-card class="filter-card mb-4">
      <n-space justify="space-between" align="center">
        <n-space>
          <n-input 
            v-model:value="searchForm.keyword" 
            placeholder="搜索规则名称" 
            clearable
            style="width: 200px;"
          >
            <template #prefix>
              <n-icon><icon-ic:baseline-search /></n-icon>
            </template>
          </n-input>
          
          <n-select 
            v-model:value="searchForm.ruleCategory" 
            placeholder="规则类型" 
            clearable 
            style="width: 150px;"
            :options="[
              { label: '单体征规则', value: 'SINGLE' },
              { label: '复合规则', value: 'COMPOSITE' },
              { label: '复杂规则', value: 'COMPLEX' }
            ]"
          />
          
          <n-select 
            v-model:value="searchForm.severityLevel" 
            placeholder="严重程度" 
            clearable 
            style="width: 120px;"
            :options="[
              { label: '信息', value: 'info' },
              { label: '一般', value: 'minor' },
              { label: '重要', value: 'major' },
              { label: '紧急', value: 'critical' }
            ]"
          />
          
          <n-select 
            v-model:value="searchForm.isActive" 
            placeholder="状态" 
            clearable 
            style="width: 100px;"
            :options="[
              { label: '启用', value: true },
              { label: '禁用', value: false }
            ]"
          />
          
          <n-button type="primary" @click="searchRules" :loading="loading">
            <template #icon>
              <n-icon><icon-ic:baseline-search /></n-icon>
            </template>
            查询
          </n-button>
          <n-button @click="resetSearch">
            <template #icon>
              <n-icon><icon-ic:baseline-refresh /></n-icon>
            </template>
            重置
          </n-button>
        </n-space>
      </n-space>
      
      <!-- 批量操作 -->
      <div v-if="selectedRules.length > 0" class="batch-actions mt-4 pt-4 border-t border-gray-200">
        <n-alert 
          :title="`已选择 ${selectedRules.length} 个规则`"
          type="info"
          class="mb-3"
        />
        <n-space>
          <n-button type="success" @click="batchEnable" :loading="batchLoading">
            <template #icon>
              <n-icon><icon-ic:baseline-check /></n-icon>
            </template>
            批量启用
          </n-button>
          <n-button type="warning" @click="batchDisable" :loading="batchLoading">
            <template #icon>
              <n-icon><icon-ic:baseline-close /></n-icon>
            </template>
            批量禁用
          </n-button>
          <n-button type="error" @click="batchDelete" :loading="batchLoading">
            <template #icon>
              <n-icon><icon-ic:baseline-delete /></n-icon>
            </template>
            批量删除
          </n-button>
        </n-space>
      </div>
    </n-card>
    
    <!-- 规则列表 -->
    <n-card class="table-card">
      <n-data-table 
        :data="rulesList" 
        :loading="loading"
        :columns="tableColumns"
        :row-key="(row) => row.id"
        v-model:checked-row-keys="selectedRuleIds"
        striped
        size="small"
      />
      
      <!-- 分页 -->
      <div class="pagination-wrapper mt-4 flex justify-center">
        <n-pagination 
          v-model:page="pagination.current" 
          v-model:page-size="pagination.pageSize"
          :item-count="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          show-size-picker
          show-quick-jumper
          @update:page="handleCurrentChange"
          @update:page-size="handleSizeChange"
        />
      </div>
    </n-card>
    
    <!-- 规则详情对话框 -->
    <n-modal 
      v-model:show="detailDialogVisible" 
      preset="dialog"
      title="规则详情"
      style="width: 800px;"
    >
      <div v-if="selectedRule" class="rule-detail">
        <n-descriptions :column="2" bordered>
          <n-descriptions-item label="规则名称" :span="2">
            <strong>{{ selectedRule.ruleName }}</strong>
          </n-descriptions-item>
          <n-descriptions-item label="规则类型">
            <n-tag :type="getRuleTypeTagType(selectedRule.ruleCategory)">
              {{ getRuleTypeText(selectedRule.ruleCategory) }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="严重程度">
            <n-tag :type="getSeverityTagType(selectedRule.severityLevel)">
              {{ getSeverityText(selectedRule.severityLevel) }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="优先级">
            <n-rate 
              :value="selectedRule.priorityLevel" 
              readonly 
              :count="5"
            />
          </n-descriptions-item>
          <n-descriptions-item label="状态">
            <n-tag :type="selectedRule.isActive ? 'success' : 'error'">
              {{ selectedRule.isActive ? '启用' : '禁用' }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="通知渠道" :span="2">
            <n-space>
              <n-tag 
                v-for="channel in selectedRule.enabledChannels" 
                :key="channel"
                size="small"
              >
                {{ getChannelText(channel) }}
              </n-tag>
            </n-space>
          </n-descriptions-item>
          <n-descriptions-item label="创建时间">
            {{ formatTime(selectedRule.createTime) }}
          </n-descriptions-item>
          <n-descriptions-item label="更新时间">
            {{ formatTime(selectedRule.updateTime) }}
          </n-descriptions-item>
        </n-descriptions>
        
        <!-- 条件详情 -->
        <div class="condition-detail mt-6" v-if="selectedRule.ruleCategory === 'SINGLE'">
          <h4 class="text-lg font-medium mb-3">单体征条件</h4>
          <n-card>
            <p><strong>监测指标：</strong>{{ getPhysicalSignText(selectedRule.physicalSign) }}</p>
            <p><strong>正常范围：</strong>{{ selectedRule.thresholdMin }} - {{ selectedRule.thresholdMax }}</p>
            <p><strong>连续次数：</strong>{{ selectedRule.trendDuration }}</p>
            <p><strong>时间窗口：</strong>{{ selectedRule.timeWindowSeconds }}秒</p>
          </n-card>
        </div>
        
        <div class="condition-detail mt-6" v-if="selectedRule.ruleCategory === 'COMPOSITE' && selectedRule.conditionExpression">
          <h4 class="text-lg font-medium mb-3">复合条件</h4>
          <n-card>
            <div v-for="(condition, index) in JSON.parse(selectedRule.conditionExpression).conditions" :key="index" class="mb-2">
              <p>
                <strong>条件 {{ index + 1 }}：</strong>
                {{ getPhysicalSignText(condition.physical_sign) }} 
                {{ condition.operator }} 
                {{ condition.threshold }}
                <span v-if="condition.duration_seconds"> (持续{{ condition.duration_seconds }}秒)</span>
              </p>
            </div>
            <p><strong>逻辑关系：</strong>{{ JSON.parse(selectedRule.conditionExpression).logical_operator === 'AND' ? '并且' : '或者' }}</p>
          </n-card>
        </div>
        
        <div class="alert-message-detail mt-6" v-if="selectedRule.alertMessage">
          <h4 class="text-lg font-medium mb-3">告警消息模板</h4>
          <n-card>
            <n-code :code="selectedRule.alertMessage" language="text" />
          </n-card>
        </div>
      </div>
    </n-modal>
    
    <!-- 规则配置向导 -->
    <n-modal 
      v-model:show="wizardVisible" 
      preset="dialog"
      title="告警规则配置"
      style="width: 90%;"
      :mask-closable="false"
      @close="handleWizardClose"
    >
      <AlertRuleWizard 
        :visible="wizardVisible"
        :edit-rule="editingRule"
        @update:visible="wizardVisible = $event"
        @success="handleWizardSuccess"
      />
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, h } from 'vue'
import { useMessage, useDialog, NButton, NIcon, NTag, NRate, NSpace, NDropdown } from 'naive-ui'
import AlertRuleWizard from './components/AlertRuleWizard.vue'
import { 
  fetchGetAlertRulesList as fetchAlertRules, 
  fetchDeleteAlertRules as deleteAlertRule
} from '@/service/api/health/alert-rules'

// Placeholder functions for missing APIs
const updateRuleStatus = async (id: string, isActive: boolean) => {
  console.log('Update rule status:', id, isActive)
  return Promise.resolve()
}

const batchUpdateRuleStatus = async (ids: string[], isActive: boolean) => {
  console.log('Batch update rule status:', ids, isActive)
  return Promise.resolve()
}

const getAlertStatistics = async () => {
  return Promise.resolve({
    data: {
      totalRules: 0,
      activeRules: 0,
      todayAlerts: 0,
      avgResponseTime: 0
    }
  })
}

// 响应式数据
const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const batchLoading = ref(false)
const rulesList = ref([])
const selectedRules = ref([])
const selectedRuleIds = ref([])
const detailDialogVisible = ref(false)
const selectedRule = ref(null)
const wizardVisible = ref(false)
const editingRule = ref(null)

// 搜索表单
const searchForm = reactive({
  keyword: '',
  ruleCategory: '',
  severityLevel: '',
  isActive: null
})

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

// 排序
const sortConfig = reactive({
  prop: '',
  order: ''
})

// 统计数据
const statistics = reactive({
  totalRules: 0,
  activeRules: 0,
  todayAlerts: 0,
  avgResponseTime: 0
})

// 生理指标映射
const physicalSignsMap: Record<string, string> = {
  'heart_rate': '心率',
  'blood_oxygen': '血氧',
  'temperature': '体温',
  'pressure_high': '收缩压',
  'pressure_low': '舒张压',
  'step': '步数',
  'calorie': '卡路里',
  'distance': '距离',
  'stress': '压力指数'
}

// 通知渠道映射
const channelMap: Record<string, string> = {
  'message': '内部消息',
  'wechat': '微信',
  'sms': '短信',
  'email': '邮件'
}

// 表格列定义
const tableColumns = computed(() => [
  {
    type: 'selection',
    key: 'selection'
  },
  {
    title: '规则名称',
    key: 'ruleName',
    minWidth: 200,
    ellipsis: { tooltip: true },
    render: (row: any) => {
      return h('div', { class: 'rule-name-cell' }, [
        h('div', { class: 'rule-name font-medium' }, [
          h(NButton, { 
            text: true, 
            type: 'primary',
            onClick: () => viewRule(row) 
          }, () => row.ruleName)
        ]),
        row.ruleTags && row.ruleTags.length ? h('div', { class: 'rule-tags flex gap-1 mt-1' }, [
          ...row.ruleTags.slice(0, 2).map((tag: string) => 
            h(NTag, { size: 'small' }, () => tag)
          ),
          row.ruleTags.length > 2 ? h(NTag, { size: 'small', type: 'info' }, () => `+${row.ruleTags.length - 2}`) : null
        ].filter(Boolean)) : null
      ])
    }
  },
  {
    title: '规则类型',
    key: 'ruleCategory',
    width: 120,
    align: 'center',
    render: (row: any) => h(NTag, { 
      type: getRuleTypeTagType(row.ruleCategory), 
      size: 'small' 
    }, () => getRuleTypeText(row.ruleCategory))
  },
  {
    title: '监测指标',
    key: 'physicalSign',
    width: 120,
    align: 'center',
    render: (row: any) => {
      if (row.ruleCategory === 'SINGLE') {
        return getPhysicalSignText(row.physicalSign)
      } else if (row.ruleCategory === 'COMPOSITE') {
        return '复合指标'
      } else {
        return '-'
      }
    }
  },
  {
    title: '严重程度',
    key: 'severityLevel',
    width: 100,
    align: 'center',
    render: (row: any) => h(NTag, { 
      type: getSeverityTagType(row.severityLevel), 
      size: 'small' 
    }, () => getSeverityText(row.severityLevel))
  },
  {
    title: '优先级',
    key: 'priorityLevel',
    width: 120,
    align: 'center',
    render: (row: any) => h(NRate, { 
      value: row.priorityLevel, 
      readonly: true,
      count: 5,
      size: 'small'
    })
  },
  {
    title: '通知渠道',
    key: 'enabledChannels',
    width: 120,
    align: 'center',
    render: (row: any) => {
      if (!row.enabledChannels || !row.enabledChannels.length) return '-'
      return h(NSpace, { size: 'small' }, () => 
        row.enabledChannels.slice(0, 3).map((channel: string) => 
          h(NTag, { size: 'small' }, () => getChannelText(channel))
        )
      )
    }
  },
  {
    title: '状态',
    key: 'isActive',
    width: 80,
    align: 'center',
    render: (row: any) => h('n-switch', { 
      value: row.isActive,
      loading: row.statusLoading,
      'onUpdate:value': (value: boolean) => toggleRuleStatus({ ...row, isActive: value })
    })
  },
  {
    title: '更新时间',
    key: 'updateTime',
    width: 160,
    align: 'center',
    render: (row: any) => formatTime(row.updateTime)
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    align: 'center',
    fixed: 'right',
    render: (row: any) => {
      const options = [
        {
          label: '复制',
          key: 'duplicate',
          icon: () => h(NIcon, () => h('icon-ic:baseline-content-copy'))
        },
        {
          label: '测试规则',
          key: 'test',
          icon: () => h(NIcon, () => h('icon-ic:baseline-play-arrow'))
        },
        {
          label: '导出配置',
          key: 'export',
          icon: () => h(NIcon, () => h('icon-ic:baseline-download'))
        },
        {
          type: 'divider',
          key: 'divider'
        },
        {
          label: '删除',
          key: 'delete',
          icon: () => h(NIcon, () => h('icon-ic:baseline-delete')),
          props: {
            style: { color: '#f56c6c' }
          }
        }
      ]

      return h(NSpace, () => [
        h(NButton, { 
          size: 'small',
          onClick: () => viewRule(row)
        }, () => '详情'),
        h(NButton, { 
          size: 'small', 
          type: 'primary',
          onClick: () => editRule(row) 
        }, () => '编辑'),
        h(NDropdown, {
          options,
          onSelect: (key: string) => handleCommand({ action: key, row })
        }, () => h(NButton, { size: 'small' }, () => '更多'))
      ])
    }
  }
])

// 监听选中行变化
const handleSelectionChange = (keys: string[]) => {
  selectedRuleIds.value = keys
  selectedRules.value = rulesList.value.filter((rule: any) => keys.includes(rule.id))
}

// 生命周期
onMounted(() => {
  loadRulesList()
  loadStatistics()
})

// 方法
const loadRulesList = async () => {
  loading.value = true
  try {
    const params = {
      ...searchForm,
      page: pagination.current,
      pageSize: pagination.pageSize,
      sortProp: sortConfig.prop,
      sortOrder: sortConfig.order
    }
    
    const response = await fetchAlertRules(params)
    rulesList.value = response.data.list || []
    pagination.total = response.data.total || 0
    
  } catch (error: any) {
    message.error('加载规则列表失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const loadStatistics = async () => {
  try {
    const response = await getAlertStatistics()
    Object.assign(statistics, response.data)
  } catch (error: any) {
    console.error('加载统计数据失败：', error)
  }
}

const refreshRules = () => {
  loadRulesList()
  loadStatistics()
}

const openWizard = () => {
  editingRule.value = null
  wizardVisible.value = true
}

const editRule = (rule: any) => {
  editingRule.value = { ...rule }
  wizardVisible.value = true
}

const viewRule = (rule: any) => {
  selectedRule.value = rule
  detailDialogVisible.value = true
}

const handleCommand = (command: { action: string, row: any }) => {
  const { action, row } = command
  
  switch (action) {
    case 'duplicate':
      duplicateRule(row)
      break
    case 'test':
      testRule(row)
      break
    case 'export':
      exportRule(row)
      break
    case 'delete':
      deleteRuleConfirm(row)
      break
  }
}

const duplicateRule = async (rule: any) => {
  try {
    await new Promise((resolve, reject) => {
      dialog.warning({
        title: '确认操作',
        content: '确定复制此规则吗？',
        positiveText: '确定',
        negativeText: '取消',
        onPositiveClick: resolve,
        onNegativeClick: reject
      })
    })
    
    const duplicatedRule = {
      ...rule,
      id: undefined,
      ruleName: rule.ruleName + ' (副本)',
      isActive: false
    }
    
    editingRule.value = duplicatedRule
    wizardVisible.value = true
    
  } catch (error) {
    if (error !== 'cancel') {
      message.error('复制失败：' + error)
    }
  }
}

const testRule = (rule: any) => {
  message.info('规则测试功能开发中...')
}

const exportRule = (rule: any) => {
  const data = JSON.stringify(rule, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `alert-rule-${rule.ruleName}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const deleteRuleConfirm = async (rule: any) => {
  try {
    await new Promise((resolve, reject) => {
      dialog.error({
        title: '确认删除',
        content: `确定删除规则"${rule.ruleName}"吗？此操作不可恢复。`,
        positiveText: '确定删除',
        negativeText: '取消',
        onPositiveClick: resolve,
        onNegativeClick: reject
      })
    })
    
    await deleteAlertRule({ ids: [rule.id] })
    message.success('删除成功')
    loadRulesList()
    
  } catch (error) {
    if (error !== 'cancel') {
      message.error('删除失败：' + error)
    }
  }
}

const toggleRuleStatus = async (rule: any) => {
  rule.statusLoading = true
  try {
    await updateRuleStatus(rule.id, rule.isActive)
    message.success(rule.isActive ? '规则已启用' : '规则已禁用')
  } catch (error: any) {
    rule.isActive = !rule.isActive // 回滚状态
    message.error('状态更新失败：' + (error.message || '未知错误'))
  } finally {
    rule.statusLoading = false
  }
}

const batchEnable = async () => {
  batchLoading.value = true
  try {
    const ruleIds = selectedRules.value.map((rule: any) => rule.id)
    await batchUpdateRuleStatus(ruleIds, true)
    message.success('批量启用成功')
    loadRulesList()
    selectedRules.value = []
    selectedRuleIds.value = []
  } catch (error: any) {
    message.error('批量启用失败：' + (error.message || '未知错误'))
  } finally {
    batchLoading.value = false
  }
}

const batchDisable = async () => {
  batchLoading.value = true
  try {
    const ruleIds = selectedRules.value.map((rule: any) => rule.id)
    await batchUpdateRuleStatus(ruleIds, false)
    message.success('批量禁用成功')
    loadRulesList()
    selectedRules.value = []
    selectedRuleIds.value = []
  } catch (error: any) {
    message.error('批量禁用失败：' + (error.message || '未知错误'))
  } finally {
    batchLoading.value = false
  }
}

const batchDelete = async () => {
  try {
    await new Promise((resolve, reject) => {
      dialog.error({
        title: '确认批量删除',
        content: `确定删除选中的 ${selectedRules.value.length} 个规则吗？此操作不可恢复。`,
        positiveText: '确定删除',
        negativeText: '取消',
        onPositiveClick: resolve,
        onNegativeClick: reject
      })
    })
    
    batchLoading.value = true
    
    const deletePromises = selectedRules.value.map((rule: any) => deleteAlertRule({ ids: [rule.id] }))
    await Promise.all(deletePromises)
    
    message.success('批量删除成功')
    loadRulesList()
    selectedRules.value = []
    selectedRuleIds.value = []
    
  } catch (error) {
    if (error !== 'cancel') {
      message.error('批量删除失败：' + error)
    }
  } finally {
    batchLoading.value = false
  }
}

const searchRules = () => {
  pagination.current = 1
  loadRulesList()
}

const resetSearch = () => {
  Object.keys(searchForm).forEach(key => {
    if (key === 'isActive') {
      ;(searchForm as any)[key] = null
    } else {
      ;(searchForm as any)[key] = ''
    }
  })
  searchRules()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.current = 1
  loadRulesList()
}

const handleCurrentChange = (page: number) => {
  pagination.current = page
  loadRulesList()
}

const handleWizardClose = () => {
  new Promise((resolve, reject) => {
    dialog.warning({
      title: '确认关闭',
      content: '确定关闭配置向导吗？未保存的更改将丢失。',
      positiveText: '确定',
      negativeText: '取消',
      onPositiveClick: resolve,
      onNegativeClick: reject
    })
  }).then(() => {
    wizardVisible.value = false
  }).catch(() => {
    // 取消关闭
  })
}

const handleWizardSuccess = () => {
  loadRulesList()
  loadStatistics()
}

// 格式化方法
const getRuleTypeText = (category: string) => {
  const types: Record<string, string> = {
    'SINGLE': '单体征',
    'COMPOSITE': '复合',
    'COMPLEX': '复杂'
  }
  return types[category] || ''
}

const getRuleTypeTagType = (category: string) => {
  const types: Record<string, string> = {
    'SINGLE': 'default',
    'COMPOSITE': 'success',
    'COMPLEX': 'warning'
  }
  return types[category] || 'default'
}

const getSeverityText = (level: string) => {
  const levels: Record<string, string> = {
    'info': '信息',
    'minor': '一般',
    'major': '重要',
    'critical': '紧急'
  }
  return levels[level] || ''
}

const getSeverityTagType = (level: string) => {
  const types: Record<string, string> = {
    'info': 'info',
    'minor': 'default',
    'major': 'warning',
    'critical': 'error'
  }
  return types[level] || 'default'
}

const getPhysicalSignText = (sign: string) => {
  return physicalSignsMap[sign] || sign
}

const getChannelText = (channel: string) => {
  return channelMap[channel] || channel
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.active {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.alerts {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.performance {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.rule-name-cell .rule-name {
  font-weight: 500;
  color: #303133;
  margin-bottom: 5px;
}

.rule-name-cell .rule-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>