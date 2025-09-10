<template>
  <div class="alert-rules-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>
          <el-icon><Notification /></el-icon>
          告警规则管理
        </h2>
        <p>管理和配置系统告警规则，支持单体征、复合和复杂规则</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="openWizard">
          <el-icon><Plus /></el-icon>
          新建规则
        </el-button>
        <el-button @click="refreshRules" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon><DataBoard /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.totalRules }}</div>
              <div class="stat-label">总规则数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon active">
              <el-icon><Check /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.activeRules }}</div>
              <div class="stat-label">启用规则</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon alerts">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.todayAlerts }}</div>
              <div class="stat-label">今日告警</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon performance">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.avgResponseTime }}ms</div>
              <div class="stat-label">平均响应</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 搜索和过滤 -->
    <el-card class="filter-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="规则名称">
          <el-input 
            v-model="searchForm.keyword" 
            placeholder="搜索规则名称" 
            clearable
            style="width: 200px;"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="规则类型">
          <el-select v-model="searchForm.ruleCategory" placeholder="规则类型" clearable style="width: 150px;">
            <el-option label="单体征规则" value="SINGLE" />
            <el-option label="复合规则" value="COMPOSITE" />
            <el-option label="复杂规则" value="COMPLEX" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="严重程度">
          <el-select v-model="searchForm.severityLevel" placeholder="严重程度" clearable style="width: 120px;">
            <el-option label="信息" value="info" />
            <el-option label="一般" value="minor" />
            <el-option label="重要" value="major" />
            <el-option label="紧急" value="critical" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="searchForm.isActive" placeholder="状态" clearable style="width: 100px;">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="searchRules" :loading="loading">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetSearch">
            <el-icon><RefreshRight /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
      
      <!-- 批量操作 -->
      <div class="batch-actions" v-if="selectedRules.length > 0">
        <el-alert 
          :title="`已选择 ${selectedRules.length} 个规则`"
          type="info" 
          show-icon 
          :closable="false"
          style="margin-bottom: 15px;"
        />
        <el-button type="success" @click="batchEnable" :loading="batchLoading">
          <el-icon><Check /></el-icon>
          批量启用
        </el-button>
        <el-button type="warning" @click="batchDisable" :loading="batchLoading">
          <el-icon><Close /></el-icon>
          批量禁用
        </el-button>
        <el-button type="danger" @click="batchDelete" :loading="batchLoading">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>
    </el-card>
    
    <!-- 规则列表 -->
    <el-card class="table-card">
      <el-table 
        :data="rulesList" 
        v-loading="loading"
        @selection-change="handleSelectionChange"
        @sort-change="handleSortChange"
        row-key="id"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="ruleName" label="规则名称" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="rule-name-cell">
              <div class="rule-name">
                <el-link @click="viewRule(row)" type="primary">{{ row.ruleName }}</el-link>
              </div>
              <div class="rule-tags" v-if="row.ruleTags && row.ruleTags.length">
                <el-tag 
                  v-for="tag in row.ruleTags.slice(0, 2)" 
                  :key="tag" 
                  size="small"
                  style="margin-right: 4px;"
                >
                  {{ tag }}
                </el-tag>
                <el-tag v-if="row.ruleTags.length > 2" size="small" type="info">
                  +{{ row.ruleTags.length - 2 }}
                </el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="ruleCategory" label="规则类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getRuleTypeTagType(row.ruleCategory)" size="small">
              {{ getRuleTypeText(row.ruleCategory) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="physicalSign" label="监测指标" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.ruleCategory === 'SINGLE'">
              {{ getPhysicalSignText(row.physicalSign) }}
            </span>
            <el-tooltip v-else-if="row.ruleCategory === 'COMPOSITE'" effect="dark" placement="top">
              <template #content>
                {{ getCompositeSignsText(row.conditionExpression) }}
              </template>
              <span>复合指标</span>
            </el-tooltip>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="severityLevel" label="严重程度" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getSeverityTagType(row.severityLevel)" size="small">
              {{ getSeverityText(row.severityLevel) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="priorityLevel" label="优先级" width="80" sortable align="center">
          <template #default="{ row }">
            <el-rate 
              v-model="row.priorityLevel" 
              disabled 
              show-score 
              text-color="#ff9900" 
              :max="5"
              size="small"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="enabledChannels" label="通知渠道" width="120" align="center">
          <template #default="{ row }">
            <div class="channels">
              <el-tooltip content="微信通知" v-if="row.enabledChannels?.includes('wechat')">
                <el-icon class="channel-icon wechat"><ChatDotRound /></el-icon>
              </el-tooltip>
              <el-tooltip content="内部消息" v-if="row.enabledChannels?.includes('message')">
                <el-icon class="channel-icon message"><Message /></el-icon>
              </el-tooltip>
              <el-tooltip content="短信通知" v-if="row.enabledChannels?.includes('sms')">
                <el-icon class="channel-icon sms"><Phone /></el-icon>
              </el-tooltip>
              <el-tooltip content="邮件通知" v-if="row.enabledChannels?.includes('email')">
                <el-icon class="channel-icon email"><Message /></el-icon>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="isActive" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-switch 
              v-model="row.isActive" 
              @change="toggleRuleStatus(row)"
              :loading="row.statusLoading"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="updateTime" label="更新时间" width="160" sortable align="center">
          <template #default="{ row }">
            {{ formatTime(row.updateTime) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" @click="viewRule(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button size="small" type="primary" @click="editRule(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-dropdown @command="handleCommand" trigger="click">
              <el-button size="small">
                更多
                <el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="{ action: 'duplicate', row }">
                    <el-icon><CopyDocument /></el-icon>
                    复制
                  </el-dropdown-item>
                  <el-dropdown-item :command="{ action: 'test', row }" divided>
                    <el-icon><VideoPlay /></el-icon>
                    测试规则
                  </el-dropdown-item>
                  <el-dropdown-item :command="{ action: 'export', row }">
                    <el-icon><Download /></el-icon>
                    导出配置
                  </el-dropdown-item>
                  <el-dropdown-item :command="{ action: 'delete', row }" divided>
                    <el-icon><Delete /></el-icon>
                    <span style="color: #f56c6c;">删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination 
          v-model:current-page="pagination.current" 
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <!-- 规则详情对话框 -->
    <el-dialog 
      v-model="detailDialogVisible" 
      title="规则详情" 
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedRule" class="rule-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="规则名称" :span="2">
            <strong>{{ selectedRule.ruleName }}</strong>
          </el-descriptions-item>
          <el-descriptions-item label="规则类型">
            <el-tag :type="getRuleTypeTagType(selectedRule.ruleCategory)">
              {{ getRuleTypeText(selectedRule.ruleCategory) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="严重程度">
            <el-tag :type="getSeverityTagType(selectedRule.severityLevel)">
              {{ getSeverityText(selectedRule.severityLevel) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="优先级">
            <el-rate 
              v-model="selectedRule.priorityLevel" 
              disabled 
              show-score 
              text-color="#ff9900" 
              :max="5"
            />
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedRule.isActive ? 'success' : 'danger'">
              {{ selectedRule.isActive ? '启用' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="通知渠道" :span="2">
            <el-tag 
              v-for="channel in selectedRule.enabledChannels" 
              :key="channel"
              size="small"
              style="margin-right: 8px;"
            >
              {{ getChannelText(channel) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatTime(selectedRule.createTime) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatTime(selectedRule.updateTime) }}
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 条件详情 -->
        <div class="condition-detail" v-if="selectedRule.ruleCategory === 'SINGLE'">
          <h4>单体征条件</h4>
          <el-card class="condition-card">
            <p><strong>监测指标：</strong>{{ getPhysicalSignText(selectedRule.physicalSign) }}</p>
            <p><strong>正常范围：</strong>{{ selectedRule.thresholdMin }} - {{ selectedRule.thresholdMax }}</p>
            <p><strong>连续次数：</strong>{{ selectedRule.trendDuration }}</p>
            <p><strong>时间窗口：</strong>{{ selectedRule.timeWindowSeconds }}秒</p>
          </el-card>
        </div>
        
        <div class="condition-detail" v-if="selectedRule.ruleCategory === 'COMPOSITE' && selectedRule.conditionExpression">
          <h4>复合条件</h4>
          <el-card class="condition-card">
            <div v-for="(condition, index) in JSON.parse(selectedRule.conditionExpression).conditions" :key="index" class="composite-condition">
              <p>
                <strong>条件 {{ index + 1 }}：</strong>
                {{ getPhysicalSignText(condition.physical_sign) }} 
                {{ condition.operator }} 
                {{ condition.threshold }}
                <span v-if="condition.duration_seconds"> (持续{{ condition.duration_seconds }}秒)</span>
              </p>
            </div>
            <p><strong>逻辑关系：</strong>{{ JSON.parse(selectedRule.conditionExpression).logical_operator === 'AND' ? '并且' : '或者' }}</p>
          </el-card>
        </div>
        
        <div class="alert-message-detail" v-if="selectedRule.alertMessage">
          <h4>告警消息模板</h4>
          <el-card class="message-card">
            {{ selectedRule.alertMessage }}
          </el-card>
        </div>
      </div>
    </el-dialog>
    
    <!-- 规则配置向导 -->
    <el-dialog 
      v-model="wizardVisible" 
      title="告警规则配置"
      width="90%"
      :close-on-click-modal="false"
      :before-close="handleWizardClose"
    >
      <AlertRuleWizard 
        :visible="wizardVisible"
        :edit-rule="editingRule"
        @update:visible="wizardVisible = $event"
        @success="handleWizardSuccess"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Refresh, Search, RefreshRight, Check, Close, Delete, 
  View, Edit, ArrowDown, CopyDocument, VideoPlay, Download,
  Notification, DataBoard, Warning, TrendCharts, Message, 
  ChatDotRound, Phone
} from '@element-plus/icons-vue'
import AlertRuleWizard from './components/AlertRuleWizard.vue'
import { 
  fetchAlertRules, 
  deleteAlertRule, 
  updateRuleStatus, 
  batchUpdateRuleStatus,
  getAlertStatistics
} from '@/service/api/health/alert-rules'

// 响应式数据
const loading = ref(false)
const batchLoading = ref(false)
const rulesList = ref([])
const selectedRules = ref([])
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
    ElMessage.error('加载规则列表失败：' + (error.message || '未知错误'))
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
    await ElMessageBox.confirm('确定复制此规则吗？', '确认操作')
    
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
      ElMessage.error('复制失败：' + error)
    }
  }
}

const testRule = (rule: any) => {
  ElMessage.info('规则测试功能开发中...')
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
    await ElMessageBox.confirm(
      `确定删除规则"${rule.ruleName}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await deleteAlertRule(rule.id)
    ElMessage.success('删除成功')
    loadRulesList()
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + error)
    }
  }
}

const toggleRuleStatus = async (rule: any) => {
  rule.statusLoading = true
  try {
    await updateRuleStatus(rule.id, rule.isActive)
    ElMessage.success(rule.isActive ? '规则已启用' : '规则已禁用')
  } catch (error: any) {
    rule.isActive = !rule.isActive // 回滚状态
    ElMessage.error('状态更新失败：' + (error.message || '未知错误'))
  } finally {
    rule.statusLoading = false
  }
}

const batchEnable = async () => {
  batchLoading.value = true
  try {
    const ruleIds = selectedRules.value.map((rule: any) => rule.id)
    await batchUpdateRuleStatus(ruleIds, true)
    ElMessage.success('批量启用成功')
    loadRulesList()
    selectedRules.value = []
  } catch (error: any) {
    ElMessage.error('批量启用失败：' + (error.message || '未知错误'))
  } finally {
    batchLoading.value = false
  }
}

const batchDisable = async () => {
  batchLoading.value = true
  try {
    const ruleIds = selectedRules.value.map((rule: any) => rule.id)
    await batchUpdateRuleStatus(ruleIds, false)
    ElMessage.success('批量禁用成功')
    loadRulesList()
    selectedRules.value = []
  } catch (error: any) {
    ElMessage.error('批量禁用失败：' + (error.message || '未知错误'))
  } finally {
    batchLoading.value = false
  }
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedRules.value.length} 个规则吗？此操作不可恢复。`,
      '确认批量删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    batchLoading.value = true
    
    const deletePromises = selectedRules.value.map((rule: any) => deleteAlertRule(rule.id))
    await Promise.all(deletePromises)
    
    ElMessage.success('批量删除成功')
    loadRulesList()
    selectedRules.value = []
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败：' + error)
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

const handleSelectionChange = (selection: any[]) => {
  selectedRules.value = selection
}

const handleSortChange = ({ prop, order }: { prop: string, order: string }) => {
  sortConfig.prop = prop
  sortConfig.order = order
  loadRulesList()
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

const handleWizardClose = (done: Function) => {
  ElMessageBox.confirm('确定关闭配置向导吗？未保存的更改将丢失。')
    .then(() => {
      done()
    })
    .catch(() => {
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
    'SINGLE': '',
    'COMPOSITE': 'success',
    'COMPLEX': 'warning'
  }
  return types[category] || ''
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
    'minor': '',
    'major': 'warning',
    'critical': 'danger'
  }
  return types[level] || ''
}

const getPhysicalSignText = (sign: string) => {
  return physicalSignsMap[sign] || sign
}

const getChannelText = (channel: string) => {
  return channelMap[channel] || channel
}

const getCompositeSignsText = (expression: string) => {
  if (!expression) return '-'
  
  try {
    const parsed = JSON.parse(expression)
    if (parsed.conditions) {
      return parsed.conditions.map((c: any) => getPhysicalSignText(c.physical_sign)).join(', ')
    }
  } catch (e) {
    console.error('解析复合条件失败:', e)
  }
  
  return '复合指标'
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
.alert-rules-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 5px 0;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-left p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 10px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 10px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-icon.active {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-icon.alerts {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.stat-icon.performance {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.filter-card {
  margin-bottom: 20px;
}

.batch-actions {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 10px;
}

.table-card {
  margin-bottom: 20px;
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

.channels {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.channel-icon {
  font-size: 16px;
  cursor: pointer;
}

.channel-icon.wechat { color: #1aad19; }
.channel-icon.message { color: #409eff; }
.channel-icon.sms { color: #e6a23c; }
.channel-icon.email { color: #909399; }

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.rule-detail {
  max-height: 600px;
  overflow-y: auto;
}

.condition-detail {
  margin-top: 20px;
}

.condition-detail h4 {
  margin: 20px 0 10px 0;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}

.condition-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafbfc;
}

.composite-condition {
  padding: 8px 0;
  border-bottom: 1px solid #f0f2f5;
}

.composite-condition:last-child {
  border-bottom: none;
}

.alert-message-detail {
  margin-top: 20px;
}

.alert-message-detail h4 {
  margin: 20px 0 10px 0;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}

.message-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #f8f9fa;
  font-family: 'Courier New', monospace;
  color: #495057;
}

@media (max-width: 768px) {
  .alert-rules-management {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  
  .stats-cards .el-col {
    margin-bottom: 10px;
  }
  
  .header-right {
    justify-content: center;
  }
  
  .batch-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  
  .stat-content {
    flex-direction: column;
    text-align: center;
  }
  
  .stat-icon {
    margin-right: 0;
    margin-bottom: 10px;
  }
}
</style>