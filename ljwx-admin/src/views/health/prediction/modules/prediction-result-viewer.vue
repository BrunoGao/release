<script setup lang="tsx">
import { ref, computed, watch, onMounted } from 'vue';
import { 
  NModal, 
  NCard, 
  NTabs, 
  NTabPane, 
  NDataTable, 
  NTag, 
  NSpace,
  NStatistic,
  NDivider,
  NAlert,
  NButton,
  NDescriptions,
  NDescriptionsItem,
  useMessage
} from 'naive-ui';
import * as echarts from 'echarts';

defineOptions({
  name: 'PredictionResultViewer'
});

interface Props {
  taskData: any;
}

const props = defineProps<Props>();
const visible = defineModel<boolean>('visible', { default: false });
const message = useMessage();

// 图表引用
const predictionChartRef = ref<HTMLElement>();
const riskDistributionChartRef = ref<HTMLElement>();
const accuracyTrendChartRef = ref<HTMLElement>();

// 预测结果数据（模拟）
const predictionResults = ref({
  totalUsers: 1248,
  analysisDate: '2024-01-21',
  modelAccuracy: 0.87,
  avgConfidence: 0.82,
  riskDistribution: {
    low: 756,
    medium: 362,
    high: 130
  },
  topRiskUsers: [
    {
      id: 'U001',
      name: '张三',
      department: '技术部',
      riskScore: 0.91,
      riskLevel: 'high',
      keyFactors: ['心率异常', '血压偏高', '睡眠不足'],
      prediction: '未来7天内有85%概率出现健康风险'
    },
    {
      id: 'U002',
      name: '李四',
      department: '销售部',
      riskScore: 0.87,
      riskLevel: 'high',
      keyFactors: ['压力指数高', '运动不足', '体温波动'],
      prediction: '未来7天内有82%概率出现健康风险'
    },
    {
      id: 'U003',
      name: '王五',
      department: '市场部',
      riskScore: 0.79,
      riskLevel: 'medium',
      keyFactors: ['血氧偏低', '心率不稳'],
      prediction: '未来7天内有76%概率需要关注健康状况'
    }
  ],
  featureImportance: [
    { feature: '心率', importance: 0.28, description: '心率异常是主要风险因素' },
    { feature: '血氧', importance: 0.22, description: '血氧饱和度对整体评估影响较大' },
    { feature: '血压', importance: 0.18, description: '血压变化是重要预警信号' },
    { feature: '压力指数', importance: 0.15, description: '心理压力影响身体健康' },
    { feature: '睡眠质量', importance: 0.12, description: '睡眠质量影响恢复能力' },
    { feature: '运动量', importance: 0.05, description: '运动不足影响相对较小' }
  ],
  predictionTrend: [
    { date: '2024-01-15', lowRisk: 45, mediumRisk: 35, highRisk: 20 },
    { date: '2024-01-16', lowRisk: 44, mediumRisk: 36, highRisk: 20 },
    { date: '2024-01-17', lowRisk: 43, mediumRisk: 37, highRisk: 20 },
    { date: '2024-01-18', lowRisk: 42, mediumRisk: 38, highRisk: 20 },
    { date: '2024-01-19', lowRisk: 41, mediumRisk: 38, highRisk: 21 },
    { date: '2024-01-20', lowRisk: 40, mediumRisk: 39, highRisk: 21 },
    { date: '2024-01-21', lowRisk: 39, mediumRisk: 40, highRisk: 21 }
  ]
});

// 高风险用户表格列
const riskUserColumns = [
  {
    key: 'name',
    title: '姓名',
    width: 100
  },
  {
    key: 'department',
    title: '部门',
    width: 120
  },
  {
    key: 'riskLevel',
    title: '风险等级',
    width: 100,
    render: (row: any) => {
      const riskMap = {
        low: { type: 'success', text: '低风险' },
        medium: { type: 'warning', text: '中风险' },
        high: { type: 'error', text: '高风险' }
      } as const;
      const risk = riskMap[row.riskLevel as keyof typeof riskMap];
      return <NTag type={risk.type} size="small">{risk.text}</NTag>;
    }
  },
  {
    key: 'riskScore',
    title: '风险评分',
    width: 100,
    render: (row: any) => (row.riskScore * 100).toFixed(1) + '%'
  },
  {
    key: 'keyFactors',
    title: '关键因素',
    render: (row: any) => (
      <NSpace size="small">
        {row.keyFactors.slice(0, 2).map((factor: string) => (
          <NTag key={factor} type="info" size="small">{factor}</NTag>
        ))}
        {row.keyFactors.length > 2 && (
          <NTag type="default" size="small">+{row.keyFactors.length - 2}</NTag>
        )}
      </NSpace>
    )
  }
];

// 特征重要性表格列
const featureColumns = [
  {
    key: 'feature',
    title: '健康特征',
    width: 100
  },
  {
    key: 'importance',
    title: '重要性',
    width: 120,
    render: (row: any) => (
      <div class="flex items-center gap-2">
        <div class="w-20 bg-gray-200 rounded-full h-2">
          <div 
            class="bg-blue-500 h-2 rounded-full" 
            style={{ width: `${row.importance * 100}%` }}
          ></div>
        </div>
        <span class="text-sm">{(row.importance * 100).toFixed(1)}%</span>
      </div>
    )
  },
  {
    key: 'description',
    title: '说明',
    render: (row: any) => row.description
  }
];

// 初始化预测趋势图表
function initPredictionChart() {
  if (!predictionChartRef.value) return;
  
  const chart = echarts.init(predictionChartRef.value);
  const option = {
    title: {
      text: '风险预测趋势',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['低风险', '中风险', '高风险'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: predictionResults.value.predictionTrend.map(item => item.date.substring(5))
    },
    yAxis: {
      type: 'value',
      name: '百分比 (%)'
    },
    series: [
      {
        name: '低风险',
        type: 'line',
        stack: 'total',
        areaStyle: {},
        emphasis: {
          focus: 'series'
        },
        data: predictionResults.value.predictionTrend.map(item => item.lowRisk),
        itemStyle: {
          color: '#52c41a'
        }
      },
      {
        name: '中风险',
        type: 'line',
        stack: 'total',
        areaStyle: {},
        emphasis: {
          focus: 'series'
        },
        data: predictionResults.value.predictionTrend.map(item => item.mediumRisk),
        itemStyle: {
          color: '#faad14'
        }
      },
      {
        name: '高风险',
        type: 'line',
        stack: 'total',
        areaStyle: {},
        emphasis: {
          focus: 'series'
        },
        data: predictionResults.value.predictionTrend.map(item => item.highRisk),
        itemStyle: {
          color: '#ff4d4f'
        }
      }
    ]
  };
  
  chart.setOption(option);
  
  // 响应式调整
  const resizeObserver = new ResizeObserver(() => {
    chart.resize();
  });
  resizeObserver.observe(predictionChartRef.value);
}

// 初始化风险分布图表
function initRiskDistributionChart() {
  if (!riskDistributionChartRef.value) return;
  
  const chart = echarts.init(riskDistributionChartRef.value);
  const { riskDistribution } = predictionResults.value;
  const total = riskDistribution.low + riskDistribution.medium + riskDistribution.high;
  
  const option = {
    title: {
      text: '风险等级分布',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      bottom: 0
    },
    series: [
      {
        name: '风险分布',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        labelLine: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        data: [
          { 
            value: riskDistribution.low, 
            name: '低风险',
            itemStyle: { color: '#52c41a' }
          },
          { 
            value: riskDistribution.medium, 
            name: '中风险',
            itemStyle: { color: '#faad14' }
          },
          { 
            value: riskDistribution.high, 
            name: '高风险',
            itemStyle: { color: '#ff4d4f' }
          }
        ]
      }
    ]
  };
  
  chart.setOption(option);
  
  const resizeObserver = new ResizeObserver(() => {
    chart.resize();
  });
  resizeObserver.observe(riskDistributionChartRef.value);
}

// 初始化准确率趋势图表
function initAccuracyTrendChart() {
  if (!accuracyTrendChartRef.value) return;
  
  const chart = echarts.init(accuracyTrendChartRef.value);
  
  // 模拟准确率数据
  const accuracyData = [
    { date: '2024-01-15', accuracy: 0.83, confidence: 0.78 },
    { date: '2024-01-16', accuracy: 0.85, confidence: 0.80 },
    { date: '2024-01-17', accuracy: 0.84, confidence: 0.79 },
    { date: '2024-01-18', accuracy: 0.86, confidence: 0.81 },
    { date: '2024-01-19', accuracy: 0.87, confidence: 0.82 },
    { date: '2024-01-20', accuracy: 0.88, confidence: 0.83 },
    { date: '2024-01-21', accuracy: 0.87, confidence: 0.82 }
  ];
  
  const option = {
    title: {
      text: '模型性能趋势',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['准确率', '置信度'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: accuracyData.map(item => item.date.substring(5))
    },
    yAxis: {
      type: 'value',
      name: '百分比',
      min: 0.7,
      max: 1.0,
      axisLabel: {
        formatter: '{value}'
      }
    },
    series: [
      {
        name: '准确率',
        type: 'line',
        data: accuracyData.map(item => item.accuracy),
        itemStyle: {
          color: '#1890ff'
        },
        lineStyle: {
          width: 3
        },
        symbol: 'circle',
        symbolSize: 6
      },
      {
        name: '置信度',
        type: 'line',
        data: accuracyData.map(item => item.confidence),
        itemStyle: {
          color: '#52c41a'
        },
        lineStyle: {
          width: 3,
          type: 'dashed'
        },
        symbol: 'circle',
        symbolSize: 6
      }
    ]
  };
  
  chart.setOption(option);
  
  const resizeObserver = new ResizeObserver(() => {
    chart.resize();
  });
  resizeObserver.observe(accuracyTrendChartRef.value);
}

// 导出报告
function exportReport() {
  message.info('导出功能正在开发中...');
}

// 监听弹窗打开，初始化图表
watch(visible, (newVisible) => {
  if (newVisible) {
    // 延迟初始化图表，确保DOM已渲染
    setTimeout(() => {
      initPredictionChart();
      initRiskDistributionChart();
      initAccuracyTrendChart();
    }, 100);
  }
});

// 计算统计数据
const riskPercentages = computed(() => {
  const { riskDistribution, totalUsers } = predictionResults.value;
  return {
    low: ((riskDistribution.low / totalUsers) * 100).toFixed(1),
    medium: ((riskDistribution.medium / totalUsers) * 100).toFixed(1),
    high: ((riskDistribution.high / totalUsers) * 100).toFixed(1)
  };
});
</script>

<template>
  <NModal v-model:show="visible" preset="card" title="预测结果查看" class="w-full max-w-7xl">
    <template #header-extra>
      <NButton type="primary" @click="exportReport">
        <template #icon>
          <div class="i-mdi:download" />
        </template>
        导出报告
      </NButton>
    </template>

    <div v-if="taskData" class="space-y-6">
      <!-- 任务基本信息 -->
      <NCard title="任务信息" size="small">
        <NDescriptions bordered :column="3" size="small">
          <NDescriptionsItem label="任务名称">{{ taskData.name }}</NDescriptionsItem>
          <NDescriptionsItem label="预测模型">{{ taskData.modelName }}</NDescriptionsItem>
          <NDescriptionsItem label="预测时长">{{ taskData.predictionHorizon }}天</NDescriptionsItem>
          <NDescriptionsItem label="分析用户数">{{ predictionResults.totalUsers.toLocaleString() }}人</NDescriptionsItem>
          <NDescriptionsItem label="模型准确率">{{ (predictionResults.modelAccuracy * 100).toFixed(1) }}%</NDescriptionsItem>
          <NDescriptionsItem label="平均置信度">{{ (predictionResults.avgConfidence * 100).toFixed(1) }}%</NDescriptionsItem>
        </NDescriptions>
      </NCard>

      <!-- 关键统计指标 -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <NCard size="small">
          <NStatistic label="低风险用户" :value="predictionResults.riskDistribution.low">
            <template #suffix>
              <span class="text-sm text-gray-500">（{{ riskPercentages.low }}%）</span>
            </template>
          </NStatistic>
        </NCard>
        
        <NCard size="small">
          <NStatistic label="中风险用户" :value="predictionResults.riskDistribution.medium">
            <template #suffix>
              <span class="text-sm text-gray-500">（{{ riskPercentages.medium }}%）</span>
            </template>
          </NStatistic>
        </NCard>
        
        <NCard size="small">
          <NStatistic label="高风险用户" :value="predictionResults.riskDistribution.high">
            <template #suffix>
              <span class="text-sm text-gray-500">（{{ riskPercentages.high }}%）</span>
            </template>
          </NStatistic>
        </NCard>
      </div>

      <!-- 风险提醒 -->
      <div v-if="predictionResults.riskDistribution.high > 100">
        <NAlert type="warning" show-icon>
          <template #header>高风险用户预警</template>
          检测到 {{ predictionResults.riskDistribution.high }} 名用户处于高风险状态，建议及时关注并采取相应的健康干预措施。
        </NAlert>
      </div>

      <!-- 详细分析 -->
      <NTabs type="line" animated>
        <!-- 可视化分析 -->
        <NTabPane name="charts" tab="可视化分析">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 风险分布图 -->
            <NCard title="风险等级分布" size="small">
              <div ref="riskDistributionChartRef" class="w-full h-80"></div>
            </NCard>
            
            <!-- 预测趋势图 -->
            <NCard title="风险预测趋势" size="small">
              <div ref="predictionChartRef" class="w-full h-80"></div>
            </NCard>
          </div>
          
          <!-- 模型性能 -->
          <NCard title="模型性能分析" size="small" class="mt-6">
            <div ref="accuracyTrendChartRef" class="w-full h-80"></div>
          </NCard>
        </NTabPane>

        <!-- 高风险用户 -->
        <NTabPane name="high-risk" tab="高风险用户">
          <NCard size="small">
            <template #header>
              <div class="flex items-center justify-between">
                <span>高风险用户列表</span>
                <NTag type="error" size="small">{{ predictionResults.topRiskUsers.length }} 人</NTag>
              </div>
            </template>
            
            <NDataTable
              :data="predictionResults.topRiskUsers"
              :columns="riskUserColumns"
              :row-key="(row: any) => row.id"
              size="small"
              striped
            />
          </NCard>

          <!-- 风险用户详情 -->
          <div class="mt-6 space-y-4">
            <div v-for="user in predictionResults.topRiskUsers.slice(0, 3)" :key="user.id">
              <NCard size="small">
                <template #header>
                  <div class="flex items-center justify-between">
                    <span class="font-medium">{{ user.name }} - {{ user.department }}</span>
                    <NTag :type="user.riskLevel === 'high' ? 'error' : 'warning'" size="small">
                      风险评分: {{ (user.riskScore * 100).toFixed(1) }}%
                    </NTag>
                  </div>
                </template>
                
                <div class="space-y-3">
                  <div>
                    <div class="text-sm text-gray-600 mb-2">关键风险因素：</div>
                    <NSpace>
                      <NTag v-for="factor in user.keyFactors" :key="factor" type="warning" size="small">
                        {{ factor }}
                      </NTag>
                    </NSpace>
                  </div>
                  
                  <div>
                    <div class="text-sm text-gray-600 mb-1">健康预测：</div>
                    <div class="text-sm">{{ user.prediction }}</div>
                  </div>
                </div>
              </NCard>
            </div>
          </div>
        </NTabPane>

        <!-- 特征重要性 -->
        <NTabPane name="features" tab="特征重要性">
          <NCard title="健康特征重要性分析" size="small">
            <template #header-extra>
              <span class="text-sm text-gray-500">基于当前预测模型的特征权重分析</span>
            </template>
            
            <NDataTable
              :data="predictionResults.featureImportance"
              :columns="featureColumns"
              :row-key="(row: any) => row.feature"
              size="small"
              striped
            />
          </NCard>

          <!-- 特征重要性说明 -->
          <NCard title="分析说明" size="small" class="mt-6">
            <div class="text-sm text-gray-700 space-y-2">
              <p>• <strong>心率</strong>：作为最重要的生命体征指标，心率异常往往是健康问题的早期信号</p>
              <p>• <strong>血氧</strong>：血氧饱和度反映呼吸系统和循环系统的功能状态</p>
              <p>• <strong>血压</strong>：血压变化是心血管疾病的重要预警指标</p>
              <p>• <strong>压力指数</strong>：心理压力会显著影响身体健康状况</p>
              <p>• <strong>睡眠质量</strong>：良好的睡眠是身体恢复和免疫力维持的关键</p>
              <p>• <strong>运动量</strong>：适量运动有助于维持整体健康水平</p>
            </div>
          </NCard>
        </NTabPane>

        <!-- 建议措施 -->
        <NTabPane name="recommendations" tab="建议措施">
          <div class="space-y-4">
            <!-- 针对高风险用户的建议 -->
            <NCard title="高风险用户干预建议" size="small">
              <div class="space-y-3 text-sm">
                <div class="flex items-start gap-3">
                  <div class="text-red-500 mt-1">🚨</div>
                  <div>
                    <div class="font-medium">立即关注</div>
                    <div class="text-gray-600">建议立即联系高风险用户，了解其当前健康状况，必要时安排医疗检查</div>
                  </div>
                </div>
                
                <div class="flex items-start gap-3">
                  <div class="text-orange-500 mt-1">📋</div>
                  <div>
                    <div class="font-medium">健康计划制定</div>
                    <div class="text-gray-600">根据个人风险因素制定针对性的健康改善计划，包括运动、饮食、作息调整等</div>
                  </div>
                </div>
                
                <div class="flex items-start gap-3">
                  <div class="text-blue-500 mt-1">📊</div>
                  <div>
                    <div class="font-medium">持续监控</div>
                    <div class="text-gray-600">增加健康数据监测频率，定期评估健康状况变化</div>
                  </div>
                </div>
              </div>
            </NCard>

            <!-- 针对中风险用户的建议 -->
            <NCard title="中风险用户关注建议" size="small">
              <div class="space-y-3 text-sm">
                <div class="flex items-start gap-3">
                  <div class="text-yellow-500 mt-1">⚠️</div>
                  <div>
                    <div class="font-medium">定期关注</div>
                    <div class="text-gray-600">建议每周关注一次，了解健康状况变化趋势</div>
                  </div>
                </div>
                
                <div class="flex items-start gap-3">
                  <div class="text-green-500 mt-1">💡</div>
                  <div>
                    <div class="font-medium">预防性干预</div>
                    <div class="text-gray-600">提供健康教育和生活方式指导，预防风险进一步升级</div>
                  </div>
                </div>
              </div>
            </NCard>

            <!-- 系统优化建议 -->
            <NCard title="预测系统优化建议" size="small">
              <div class="space-y-3 text-sm">
                <div class="flex items-start gap-3">
                  <div class="text-purple-500 mt-1">🔧</div>
                  <div>
                    <div class="font-medium">模型调优</div>
                    <div class="text-gray-600">当前模型准确率为 {{ (predictionResults.modelAccuracy * 100).toFixed(1) }}%，建议收集更多训练数据以提高准确性</div>
                  </div>
                </div>
                
                <div class="flex items-start gap-3">
                  <div class="text-indigo-500 mt-1">📈</div>
                  <div>
                    <div class="font-medium">数据质量</div>
                    <div class="text-gray-600">加强数据采集的完整性和准确性，特别关注高重要性特征的数据质量</div>
                  </div>
                </div>
              </div>
            </NCard>
          </div>
        </NTabPane>
      </NTabs>
    </div>

    <template #footer>
      <div class="flex justify-end">
        <NButton @click="visible = false">关闭</NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
:deep(.n-card) {
  margin-bottom: 0;
}

:deep(.n-tabs .n-tab-pane) {
  padding-top: 16px;
}

:deep(.n-statistic .n-statistic-value) {
  font-size: 1.8rem;
  font-weight: bold;
}

:deep(.n-descriptions-table-wrapper) {
  --n-th-padding: 8px 12px;
  --n-td-padding: 8px 12px;
}
</style>