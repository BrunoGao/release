# LJWX-Admin 健康数据分析管理系统设计方案

## 项目概述

基于ljwx-boot的完整健康数据分析功能（健康基线、健康评分、健康预测、健康建议、健康画像），在ljwx-admin管理端提供完整的管理界面，实现数据可视化、手动生成、配置管理、生命周期管理等功能。

## 架构分析

### 现有架构概览

ljwx-admin采用Vue3 + TypeScript + Naive UI的现代化前端架构：

- **路由系统**: 使用elegant-router生成式路由，配置在`src/router/elegant/routes.ts`
- **组件架构**: 基于layout.base布局，支持多级菜单结构
- **API层**: 统一的请求封装，支持TypeScript类型定义
- **状态管理**: Pinia状态管理，支持持久化
- **UI框架**: Naive UI组件库，提供丰富的数据展示组件

### 现有健康模块结构

当前健康模块路径：`/health`，包含以下子模块：

```
health/
├── ai/                  # AI分析
├── alert-rules/         # 告警规则
├── analysis/            # 数据分析
├── baseline/            # 健康基线（已存在）
├── chart/               # 图表展示
├── config/              # 配置管理
├── echarts/             # ECharts图表
├── info/                # 健康信息
├── profile/             # 健康档案
└── score/               # 健康评分（已存在）
```

## 功能架构设计

### 1. 核心功能模块

#### 1.1 健康基线管理 (Health Baseline Management)
- **路径**: `/health/baseline`
- **功能**: 
  - 基线数据查看与分析
  - 手动生成基线任务
  - 基线参数配置管理
  - 基线趋势分析图表
- **权限**: 管理员、数据分析师

#### 1.2 健康评分管理 (Health Score Management)  
- **路径**: `/health/score`
- **功能**:
  - 评分算法配置管理
  - 权重配置界面
  - 评分结果展示与分析
  - 手动重新计算评分
- **权限**: 管理员、数据分析师

#### 1.3 健康预测管理 (Health Prediction Management)
- **路径**: `/health/prediction`
- **功能**:
  - 预测模型管理
  - 预测任务配置与执行
  - 预测结果可视化
  - 预测准确率分析
- **权限**: 数据科学家、管理员

#### 1.4 健康建议管理 (Health Recommendation Management)
- **路径**: `/health/recommendation` 
- **功能**:
  - 建议规则配置
  - 建议模板管理
  - 建议生成任务管理
  - 建议效果跟踪
- **权限**: 健康顾问、管理员

#### 1.5 健康画像管理 (Health Profile Management)
- **路径**: `/health/portrait`
- **功能**:
  - 用户画像构建配置
  - 画像标签管理
  - 画像分析结果展示
  - 群体画像对比分析
- **权限**: 数据分析师、管理员

#### 1.6 数据分析控制台 (Analytics Dashboard)
- **路径**: `/health/analytics-dashboard`
- **功能**:
  - 统一的数据分析控制台
  - 跨模块数据对比
  - 综合健康报告生成
  - 系统性能监控
- **权限**: 管理员

### 2. 技术实现架构

#### 2.1 前端技术栈
```typescript
// 核心技术栈
Vue 3.3+ (Composition API)
TypeScript 5.0+
Naive UI 2.34+
ECharts 5.4+
Vue Router 4.0+
Pinia 2.0+

// 图表可视化
ECharts (时间序列、散点图、热力图)
D3.js (复杂数据可视化)
Chart.js (快速图表原型)

// 数据处理
Lodash (数据操作)
Day.js (时间处理) 
NumJS (数值计算)
```

#### 2.2 API接口设计

```typescript
// API 类型定义 - src/typings/api/health/
interface HealthAnalyticsAPI {
  // 基线管理
  baseline: {
    getBaselineList: (params: BaselineQueryParams) => Promise<BaselineListResponse>
    generateBaseline: (params: BaselineGenerateParams) => Promise<TaskResponse>
    getBaselineChart: (params: BaselineChartParams) => Promise<ChartDataResponse>
    configBaseline: (config: BaselineConfig) => Promise<ConfigResponse>
  }
  
  // 评分管理  
  score: {
    getScoreList: (params: ScoreQueryParams) => Promise<ScoreListResponse>
    recalculateScore: (params: ScoreCalcParams) => Promise<TaskResponse>
    configWeights: (weights: WeightConfig[]) => Promise<ConfigResponse>
    getScoreTrends: (params: TrendsParams) => Promise<ChartDataResponse>
  }
  
  // 预测管理
  prediction: {
    getPredictionList: (params: PredictionQueryParams) => Promise<PredictionListResponse>
    createPredictionTask: (task: PredictionTask) => Promise<TaskResponse>
    getPredictionResults: (taskId: string) => Promise<PredictionResultResponse>
    managePredictionModel: (model: PredictionModel) => Promise<ModelResponse>
  }
  
  // 建议管理
  recommendation: {
    getRecommendationList: (params: RecommendationQueryParams) => Promise<RecommendationListResponse>
    configRecommendationRules: (rules: RecommendationRule[]) => Promise<ConfigResponse>
    generateRecommendations: (params: RecommendationGenerateParams) => Promise<TaskResponse>
    getRecommendationStats: (params: StatsParams) => Promise<StatsResponse>
  }
  
  // 画像管理
  portrait: {
    getPortraitList: (params: PortraitQueryParams) => Promise<PortraitListResponse>
    configPortraitTags: (tags: PortraitTag[]) => Promise<ConfigResponse>
    generatePortrait: (params: PortraitGenerateParams) => Promise<TaskResponse>
    getPortraitAnalysis: (params: AnalysisParams) => Promise<AnalysisResponse>
  }
}
```

#### 2.3 组件设计模式

```vue
<!-- 统一的页面布局模式 -->
<template>
  <div class="health-analytics-page">
    <!-- 页面头部 -->
    <PageHeader 
      :title="pageTitle"
      :breadcrumb="breadcrumb"
      :actions="headerActions"
    />
    
    <!-- 搜索和筛选区域 -->
    <SearchPanel
      v-model:search-params="searchParams"
      :search-config="searchConfig"
      @search="handleSearch"
      @reset="handleReset"
    />
    
    <!-- 操作工具栏 -->
    <ActionToolbar
      :actions="toolbarActions"
      :selected-rows="selectedRows"
      @action="handleAction"
    />
    
    <!-- 数据表格/图表展示区域 -->
    <DataDisplay
      :display-mode="displayMode"
      :data="data"
      :loading="loading"
      @selection-change="handleSelectionChange"
    >
      <!-- 表格视图 -->
      <template #table>
        <NDataTable
          :data="data"
          :columns="columns"
          :row-key="(row) => row.id"
          :loading="loading"
          v-model:checked-row-keys="selectedRowKeys"
          @update:checked-row-keys="handleSelectionChange"
        />
      </template>
      
      <!-- 图表视图 -->
      <template #chart>
        <div ref="chartRef" class="chart-container h-96"></div>
      </template>
      
      <!-- 统计视图 -->  
      <template #stats>
        <StatsCards :stats="statistics" />
      </template>
    </DataDisplay>
    
    <!-- 分页组件 -->
    <NPagination
      v-model:page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      :show-size-picker="true"
      :page-sizes="[10, 20, 50, 100]"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
    />
    
    <!-- 操作抽屉/弹窗 -->
    <OperateDrawer
      v-model:visible="drawerVisible"
      :operation-type="operationType"
      :record="currentRecord"
      @save="handleSave"
    />
  </div>
</template>
```

### 3. 详细功能设计

#### 3.1 健康基线管理页面

**页面组件**: `src/views/health/baseline/index.vue`

**核心功能**:

1. **基线数据展示**
   - 时间序列图表展示各健康指标基线变化
   - 支持按用户、部门、时间维度筛选
   - 基线数据表格，支持导出Excel/PDF

2. **手动基线生成**
   ```vue
   <NButton 
     type="primary" 
     @click="handleGenerateBaseline"
     :loading="generating"
   >
     <template #icon>
       <NIcon :component="RefreshIcon" />
     </template>
     生成基线
   </NButton>
   ```

3. **基线配置管理**
   - 配置基线计算参数（时间窗口、统计方法等）
   - 异常值检测阈值配置
   - 基线更新频率设置

4. **基线质量监控**
   - 数据覆盖率监控
   - 基线计算状态跟踪
   - 异常基线预警

**图表类型**:
```typescript
const chartConfigs = {
  // 时间序列基线图
  timeSeriesBaseline: {
    type: 'line',
    smooth: true,
    areaStyle: { opacity: 0.3 },
    features: ['心率基线', '血氧基线', '体温基线', '血压基线']
  },
  
  // 基线分布热力图
  baselineHeatmap: {
    type: 'heatmap', 
    dimensions: ['用户', '健康指标', '基线值'],
    colorScale: 'viridis'
  },
  
  // 基线偏差分析
  deviationAnalysis: {
    type: 'scatter',
    regression: true,
    confidence: 0.95
  }
}
```

#### 3.2 健康评分管理页面

**页面组件**: `src/views/health/score/index.vue`

**核心功能**:

1. **评分结果展示**
   - 综合健康评分排行榜
   - 评分分布直方图
   - 评分趋势分析图表

2. **权重配置界面**
   ```vue
   <div class="weight-config-section">
     <NCard title="权重配置">
       <div v-for="metric in healthMetrics" :key="metric.key">
         <div class="flex items-center justify-between mb-2">
           <span>{{ metric.name }}</span>
           <NSlider
             v-model:value="metric.weight"
             :min="0"
             :max="1"
             :step="0.01"
             :format-tooltip="(value) => `${(value * 100).toFixed(1)}%`"
             class="w-48"
           />
         </div>
       </div>
       <div class="mt-4">
         <span class="font-semibold">
           权重总和: {{ totalWeight.toFixed(3) }}
         </span>
         <NAlert
           v-if="Math.abs(totalWeight - 1) > 0.001"
           type="warning"
           class="mt-2"
         >
           权重总和应该等于1.0
         </NAlert>
       </div>
     </NCard>
   </div>
   ```

3. **评分重新计算**
   - 支持按用户/部门/全部重新计算
   - 批量计算进度跟踪
   - 计算结果对比分析

4. **评分规则管理**
   - 评分算法参数配置
   - 评分等级定义管理
   - 评分阈值设置

#### 3.3 健康预测管理页面

**页面组件**: `src/views/health/prediction/index.vue`

**核心功能**:

1. **预测模型管理**
   - 模型列表展示（模型名称、版本、准确率、状态）
   - 模型训练任务创建与监控
   - 模型版本比较和切换

2. **预测任务执行**
   ```typescript
   interface PredictionTask {
     id: string
     name: string
     modelId: string
     targetUsers: string[] | 'all'
     predictionHorizon: number // 预测时间跨度（天）
     features: string[] // 使用的健康特征
     status: 'pending' | 'running' | 'completed' | 'failed'
     createdAt: string
     results?: PredictionResult[]
   }
   ```

3. **预测结果可视化**
   - 预测结果时间序列图
   - 预测置信区间展示
   - 风险预警仪表盘

4. **预测准确率分析**
   - 历史预测vs实际结果对比
   - 模型性能指标监控
   - 预测误差分析

#### 3.4 健康建议管理页面

**页面组件**: `src/views/health/recommendation/index.vue`

**核心功能**:

1. **建议规则配置**
   ```typescript
   interface RecommendationRule {
     id: string
     name: string
     conditions: RuleCondition[] // 触发条件
     template: string // 建议模板
     priority: 'high' | 'medium' | 'low'
     category: '运动' | '饮食' | '作息' | '医疗'
     enabled: boolean
   }
   
   interface RuleCondition {
     metric: string // 健康指标
     operator: '>' | '<' | '>=' | '<=' | '==' | '!='
     value: number
     duration?: number // 持续时间要求
   }
   ```

2. **建议模板管理**
   - 建议内容模板编辑器
   - 模板变量支持（用户名、数值等）
   - 多语言建议模板支持

3. **建议生成与推送**
   - 手动生成建议任务
   - 自动推送配置
   - 推送渠道管理（短信、邮件、APP推送）

4. **建议效果跟踪**
   - 建议接受率统计
   - 用户行为改变跟踪
   - 建议有效性分析

#### 3.5 健康画像管理页面

**页面组件**: `src/views/health/portrait/index.vue`

**核心功能**:

1. **画像标签管理**
   ```typescript
   interface PortraitTag {
     id: string
     name: string
     category: '基础信息' | '健康状态' | '行为特征' | '风险评估'
     dataType: 'numeric' | 'categorical' | 'boolean'
     calculation: string // 计算规则
     description: string
   }
   ```

2. **用户画像构建**
   - 画像维度配置
   - 画像更新策略设置
   - 画像计算任务管理

3. **画像分析结果**
   - 用户画像详情展示
   - 画像相似度分析
   - 用户群体聚类分析

4. **群体画像对比**
   - 不同群体画像对比图表
   - 画像差异化分析
   - 群体特征洞察报告

### 4. 图表可视化设计

#### 4.1 ECharts配置模板

```typescript
// src/utils/chart-configs.ts
export const healthChartConfigs = {
  // 基线趋势图
  baselineTrend: {
    title: { text: '健康基线趋势' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['心率', '血氧', '体温'] },
    xAxis: { type: 'time' },
    yAxis: { type: 'value' },
    series: [
      {
        name: '心率',
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.3, color: '#ff6b6b' }
      }
    ]
  },
  
  // 评分分布图
  scoreDistribution: {
    title: { text: '健康评分分布' },
    tooltip: {},
    xAxis: { type: 'category', data: ['0-20', '21-40', '41-60', '61-80', '81-100'] },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      itemStyle: { color: '#4ecdc4' }
    }]
  },
  
  // 预测结果图
  predictionResult: {
    title: { text: '健康预测结果' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'time' },
    yAxis: { type: 'value' },
    series: [
      {
        name: '历史数据',
        type: 'line',
        data: []
      },
      {
        name: '预测数据', 
        type: 'line',
        lineStyle: { type: 'dashed' },
        data: []
      },
      {
        name: '置信区间',
        type: 'line',
        areaStyle: { opacity: 0.2 },
        data: []
      }
    ]
  }
}
```

#### 4.2 响应式图表组件

```vue
<!-- src/components/charts/HealthChart.vue -->
<template>
  <div class="health-chart-container">
    <div 
      ref="chartRef" 
      :style="{ width: '100%', height: chartHeight }"
      class="chart-instance"
    />
    <div v-if="loading" class="chart-loading">
      <NSpin size="large" />
    </div>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { ref, onMounted, watch, onUnmounted } from 'vue'

interface Props {
  chartType: keyof typeof healthChartConfigs
  data: any[]
  loading?: boolean
  height?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  height: '400px'
})

const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  
  chartInstance = echarts.init(chartRef.value)
  const config = healthChartConfigs[props.chartType]
  
  chartInstance.setOption({
    ...config,
    series: config.series.map(s => ({
      ...s,
      data: props.data
    }))
  })
}

// 响应式更新
watch(() => props.data, () => {
  if (chartInstance) {
    chartInstance.setOption({
      series: [{
        data: props.data
      }]
    })
  }
})

onMounted(() => {
  nextTick(initChart)
  
  // 响应式调整
  window.addEventListener('resize', () => {
    chartInstance?.resize()
  })
})

onUnmounted(() => {
  chartInstance?.dispose()
})
</script>
```

### 5. 数据流管理

#### 5.1 Pinia状态管理

```typescript
// src/store/modules/health-analytics/index.ts
export const useHealthAnalyticsStore = defineStore('health-analytics', {
  state: (): HealthAnalyticsState => ({
    // 基线数据
    baselineList: [],
    baselineLoading: false,
    baselineConfig: null,
    
    // 评分数据
    scoreList: [],
    scoreLoading: false,
    weightConfig: [],
    
    // 预测数据
    predictionTasks: [],
    predictionModels: [],
    predictionLoading: false,
    
    // 建议数据
    recommendationList: [],
    recommendationRules: [],
    recommendationLoading: false,
    
    // 画像数据
    portraitList: [],
    portraitTags: [],
    portraitLoading: false,
    
    // 共享数据
    currentUser: null,
    selectedOrgId: null,
    dateRange: [null, null]
  }),
  
  getters: {
    // 获取当前有效基线数据
    activeBaselines: (state) => {
      return state.baselineList.filter(baseline => baseline.isActive)
    },
    
    // 获取评分统计信息
    scoreStatistics: (state) => {
      const scores = state.scoreList.map(item => item.score)
      return {
        average: scores.reduce((a, b) => a + b, 0) / scores.length,
        min: Math.min(...scores),
        max: Math.max(...scores),
        distribution: calculateDistribution(scores)
      }
    }
  },
  
  actions: {
    // 获取基线列表
    async fetchBaselineList(params: BaselineQueryParams) {
      this.baselineLoading = true
      try {
        const response = await healthAnalyticsAPI.baseline.getBaselineList(params)
        this.baselineList = response.data.records
      } finally {
        this.baselineLoading = false
      }
    },
    
    // 生成基线任务
    async generateBaseline(params: BaselineGenerateParams) {
      const response = await healthAnalyticsAPI.baseline.generateBaseline(params)
      // 创建任务后轮询状态
      this.pollTaskStatus(response.taskId)
      return response
    },
    
    // 任务状态轮询
    async pollTaskStatus(taskId: string) {
      const poll = async () => {
        const status = await healthAnalyticsAPI.getTaskStatus(taskId)
        if (status.isCompleted) {
          // 任务完成，刷新数据
          await this.fetchBaselineList()
          return
        }
        setTimeout(poll, 2000) // 2秒后继续轮询
      }
      poll()
    }
  }
})
```

### 6. 生命周期管理

#### 6.1 任务管理系统

```vue
<!-- 统一的任务管理组件 -->
<template>
  <div class="task-management">
    <NCard title="任务管理">
      <template #header-extra>
        <NSpace>
          <NButton @click="refreshTasks">
            <template #icon>
              <NIcon :component="RefreshIcon" />
            </template>
            刷新
          </NButton>
          <NButton type="primary" @click="createNewTask">
            创建任务
          </NButton>
        </NSpace>
      </template>
      
      <NDataTable
        :data="tasks"
        :columns="taskColumns"
        :row-key="(row) => row.id"
        :loading="loading"
      />
    </NCard>
    
    <!-- 任务详情抽屉 -->
    <NDrawer v-model:show="taskDetailVisible" :width="600">
      <NDrawerContent title="任务详情">
        <TaskDetails :task="selectedTask" />
      </NDrawerContent>
    </NDrawer>
  </div>
</template>

<script setup lang="ts">
const taskColumns = [
  { key: 'name', title: '任务名称' },
  { key: 'type', title: '任务类型' },
  {
    key: 'status',
    title: '状态',
    render: (row: Task) => {
      const statusMap = {
        pending: { type: 'warning', text: '等待中' },
        running: { type: 'info', text: '执行中' },
        completed: { type: 'success', text: '已完成' },
        failed: { type: 'error', text: '失败' }
      }
      const status = statusMap[row.status]
      return h(NTag, { type: status.type }, () => status.text)
    }
  },
  {
    key: 'progress',
    title: '进度',
    render: (row: Task) => {
      return h(NProgress, { 
        percentage: row.progress,
        status: row.status === 'failed' ? 'error' : 'default'
      })
    }
  },
  { key: 'createdAt', title: '创建时间' },
  {
    key: 'actions',
    title: '操作',
    render: (row: Task) => {
      return h(NSpace, null, [
        h(NButton, { 
          size: 'small',
          onClick: () => viewTaskDetails(row)
        }, () => '查看'),
        h(NButton, {
          size: 'small',
          type: 'error',
          disabled: row.status === 'running',
          onClick: () => cancelTask(row.id)
        }, () => '取消')
      ])
    }
  }
]
</script>
```

#### 6.2 定时任务配置

```vue
<!-- 定时任务配置组件 -->
<template>
  <NCard title="定时任务配置">
    <NForm ref="formRef" :model="scheduleForm" :rules="scheduleRules">
      <NFormItem label="任务名称" path="name">
        <NInput v-model:value="scheduleForm.name" />
      </NFormItem>
      
      <NFormItem label="任务类型" path="type">
        <NSelect 
          v-model:value="scheduleForm.type"
          :options="taskTypeOptions"
        />
      </NFormItem>
      
      <NFormItem label="执行频率" path="schedule">
        <NSpace vertical>
          <NRadioGroup v-model:value="scheduleForm.scheduleType">
            <NRadio value="cron">Cron表达式</NRadio>
            <NRadio value="interval">间隔时间</NRadio>
          </NRadioGroup>
          
          <NInput 
            v-if="scheduleForm.scheduleType === 'cron'"
            v-model:value="scheduleForm.cronExpression"
            placeholder="0 0 2 * * ?"
          />
          
          <NInputNumber 
            v-else
            v-model:value="scheduleForm.intervalHours"
            :min="1"
            :max="168"
            suffix="小时"
          />
        </NSpace>
      </NFormItem>
      
      <NFormItem label="目标范围" path="scope">
        <NSpace vertical>
          <NCheckbox v-model:checked="scheduleForm.includeAllUsers">
            包含所有用户
          </NCheckbox>
          
          <div v-if="!scheduleForm.includeAllUsers">
            <NTreeSelect
              v-model:value="scheduleForm.selectedOrgs"
              :options="orgTreeOptions"
              multiple
              checkable
              placeholder="选择组织范围"
            />
          </div>
        </NSpace>
      </NFormItem>
      
      <NFormItem label="任务参数" path="parameters">
        <NCard>
          <div v-for="(param, key) in scheduleForm.parameters" :key="key">
            <NSpace>
              <span class="w-24">{{ param.label }}:</span>
              <NInputNumber 
                v-if="param.type === 'number'"
                v-model:value="param.value"
                :min="param.min"
                :max="param.max"
              />
              <NInput 
                v-else
                v-model:value="param.value"
              />
            </NSpace>
          </div>
        </NCard>
      </NFormItem>
    </NForm>
    
    <template #action>
      <NSpace>
        <NButton @click="resetForm">重置</NButton>
        <NButton type="primary" @click="saveSchedule">保存配置</NButton>
        <NButton type="success" @click="testRun">测试运行</NButton>
      </NSpace>
    </template>
  </NCard>
</template>
```

### 7. 权限控制

#### 7.1 权限配置

```typescript
// src/constants/health-permissions.ts
export const HEALTH_PERMISSIONS = {
  // 基线管理权限
  BASELINE: {
    VIEW: 'health:baseline:view',
    GENERATE: 'health:baseline:generate', 
    CONFIG: 'health:baseline:config',
    DELETE: 'health:baseline:delete'
  },
  
  // 评分管理权限
  SCORE: {
    VIEW: 'health:score:view',
    CALCULATE: 'health:score:calculate',
    CONFIG_WEIGHT: 'health:score:config-weight',
    EXPORT: 'health:score:export'
  },
  
  // 预测管理权限
  PREDICTION: {
    VIEW: 'health:prediction:view',
    CREATE_TASK: 'health:prediction:create-task',
    MANAGE_MODEL: 'health:prediction:manage-model',
    DELETE: 'health:prediction:delete'
  },
  
  // 建议管理权限
  RECOMMENDATION: {
    VIEW: 'health:recommendation:view',
    CONFIG_RULE: 'health:recommendation:config-rule',
    GENERATE: 'health:recommendation:generate',
    MANAGE_TEMPLATE: 'health:recommendation:manage-template'
  },
  
  // 画像管理权限
  PORTRAIT: {
    VIEW: 'health:portrait:view',
    CONFIG_TAG: 'health:portrait:config-tag',
    GENERATE: 'health:portrait:generate',
    ANALYSIS: 'health:portrait:analysis'
  }
} as const
```

#### 7.2 权限守卫

```typescript
// src/hooks/business/health-permissions.ts
export function useHealthPermissions() {
  const { hasPermission } = usePermission()
  
  const healthPermissions = computed(() => ({
    // 基线权限检查
    baseline: {
      canView: hasPermission(HEALTH_PERMISSIONS.BASELINE.VIEW),
      canGenerate: hasPermission(HEALTH_PERMISSIONS.BASELINE.GENERATE),
      canConfig: hasPermission(HEALTH_PERMISSIONS.BASELINE.CONFIG),
      canDelete: hasPermission(HEALTH_PERMISSIONS.BASELINE.DELETE)
    },
    
    // 评分权限检查
    score: {
      canView: hasPermission(HEALTH_PERMISSIONS.SCORE.VIEW),
      canCalculate: hasPermission(HEALTH_PERMISSIONS.SCORE.CALCULATE),
      canConfigWeight: hasPermission(HEALTH_PERMISSIONS.SCORE.CONFIG_WEIGHT),
      canExport: hasPermission(HEALTH_PERMISSIONS.SCORE.EXPORT)
    }
    
    // ... 其他权限检查
  }))
  
  return {
    permissions: healthPermissions,
    hasAnyHealthPermission: computed(() => {
      return Object.values(healthPermissions.value).some(module => 
        Object.values(module).some(Boolean)
      )
    })
  }
}
```

### 8. 部署配置

#### 8.1 路由配置扩展

需要在 `src/router/elegant/routes.ts` 中添加新的路由配置：

```typescript
// 在 health 路由组下添加新的子路由
{
  name: 'health',
  path: '/health',
  component: 'layout.base',
  meta: {
    title: 'health',
    i18nKey: 'route.health',
    icon: 'mdi:heart-pulse',
    order: 3
  },
  children: [
    // ... 现有路由
    
    // 新增的健康分析路由
    {
      name: 'health_prediction',
      path: '/health/prediction',
      component: 'view.health_prediction',
      meta: {
        title: 'health_prediction',
        i18nKey: 'route.health_prediction',
        roles: ['R_ADMIN', 'R_HEALTH_ANALYST']
      }
    },
    {
      name: 'health_recommendation',
      path: '/health/recommendation',
      component: 'view.health_recommendation',
      meta: {
        title: 'health_recommendation', 
        i18nKey: 'route.health_recommendation',
        roles: ['R_ADMIN', 'R_HEALTH_ADVISOR']
      }
    },
    {
      name: 'health_portrait',
      path: '/health/portrait',
      component: 'view.health_portrait',
      meta: {
        title: 'health_portrait',
        i18nKey: 'route.health_portrait',
        roles: ['R_ADMIN', 'R_HEALTH_ANALYST']
      }
    },
    {
      name: 'health_analytics-dashboard',
      path: '/health/analytics-dashboard',
      component: 'view.health_analytics-dashboard',
      meta: {
        title: 'health_analytics-dashboard',
        i18nKey: 'route.health_analytics_dashboard',
        roles: ['R_ADMIN']
      }
    }
  ]
}
```

#### 8.2 国际化配置

```typescript
// src/locales/langs/zh-cn.ts - 添加中文翻译
export default {
  route: {
    // ... 现有翻译
    health_prediction: '健康预测',
    health_recommendation: '健康建议',
    health_portrait: '健康画像',
    health_analytics_dashboard: '分析控制台'
  },
  page: {
    health: {
      prediction: {
        title: '健康预测管理',
        createTask: '创建预测任务',
        modelManagement: '模型管理',
        accuracyAnalysis: '准确率分析'
      },
      recommendation: {
        title: '健康建议管理',
        ruleConfig: '规则配置',
        templateManage: '模板管理',
        effectTracking: '效果跟踪'
      },
      portrait: {
        title: '健康画像管理',
        tagManage: '标签管理',
        profileBuild: '画像构建',
        groupAnalysis: '群体分析'
      }
    }
  }
}
```

### 9. 开发计划

#### Phase 1: 基础架构搭建 (2周)
- [ ] API接口类型定义
- [ ] 状态管理架构搭建
- [ ] 共享组件开发
- [ ] 路由和权限配置

#### Phase 2: 核心页面开发 (4周)
- [ ] 健康基线管理页面
- [ ] 健康评分管理页面
- [ ] 基础图表组件开发
- [ ] 任务管理系统

#### Phase 3: 高级功能开发 (4周)
- [ ] 健康预测管理页面
- [ ] 健康建议管理页面
- [ ] 健康画像管理页面
- [ ] 分析控制台

#### Phase 4: 系统集成与测试 (2周)
- [ ] 系统集成测试
- [ ] 性能优化
- [ ] 用户体验优化
- [ ] 文档完善

### 10. 技术亮点

#### 10.1 创新特性
1. **智能图表自适应**: 根据数据类型和业务场景自动选择最适合的图表类型
2. **实时数据流**: WebSocket连接实现实时数据更新和任务状态同步
3. **高性能虚拟化**: 大数据表格虚拟化渲染，支持万级数据展示
4. **AI辅助分析**: 集成机器学习算法进行数据洞察和异常检测

#### 10.2 用户体验优化
1. **响应式设计**: 完美适配PC端、平板和移动端
2. **无障碍支持**: 符合WCAG 2.1标准的无障碍设计
3. **主题定制**: 支持明暗主题切换和企业定制主题
4. **快捷操作**: 键盘快捷键支持和批量操作功能

## 总结

本方案提供了完整的ljwx-admin健康数据分析管理系统设计，涵盖了从基础架构到具体功能实现的全面规划。通过模块化设计、统一的技术栈和完善的权限控制，能够为用户提供专业、易用、高效的健康数据管理体验。

系统设计遵循现有ljwx-admin的架构风格，确保了良好的代码一致性和可维护性。同时通过创新的图表可视化和智能化分析功能，提升了系统的专业性和竞争力。