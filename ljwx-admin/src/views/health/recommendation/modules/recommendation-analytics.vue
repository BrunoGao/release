<script setup lang="tsx">
import { ref, computed, watch, onMounted } from 'vue';
import { 
  NModal, 
  NCard, 
  NTabs, 
  NTabPane, 
  NDescriptions,
  NDescriptionsItem,
  NTag, 
  NSpace,
  NStatistic,
  NAlert,
  NButton,
  NTimeline,
  NTimelineItem,
  NRate,
  useMessage
} from 'naive-ui';
import * as echarts from 'echarts';

defineOptions({
  name: 'RecommendationAnalytics'
});

interface Props {
  recommendationData: any;
}

const props = defineProps<Props>();
const visible = defineModel<boolean>('visible', { default: false });
const message = useMessage();

// 图表引用
const engagementChartRef = ref<HTMLElement>();
const effectivenessChartRef = ref<HTMLElement>();
const timelineChartRef = ref<HTMLElement>();

// 模拟详细分析数据
const analyticsData = ref({
  engagement: {
    sent: 1,
    delivered: 1,
    opened: 1,
    clicked: 1,
    feedback: 1,
    openRate: 100,
    clickRate: 100,
    feedbackRate: 100
  },
  userProfile: {
    age: 32,
    gender: '男',
    department: '技术部',
    position: '软件工程师',
    healthScore: 72,
    riskLevel: 'medium',
    previousRecommendations: 15,
    followedRecommendations: 12
  },
  healthTrends: [
    { date: '2024-01-15', score: 68, category: '心率异常' },
    { date: '2024-01-16', score: 70, category: '睡眠改善' },
    { date: '2024-01-17', score: 71, category: '运动增加' },
    { date: '2024-01-18', score: 72, category: '压力缓解' },
    { date: '2024-01-19', score: 74, category: '整体提升' },
    { date: '2024-01-20', score: 73, category: '血压稳定' },
    { date: '2024-01-21', score: 75, category: '综合改善' }
  ],
  timeline: [
    {
      time: '2024-01-21 14:30:00',
      type: 'create',
      title: '建议创建',
      content: '系统基于用户健康数据生成个性化建议',
      status: 'success'
    },
    {
      time: '2024-01-21 15:00:00',
      type: 'review',
      title: '人工审核',
      content: '健康专家审核并优化建议内容',
      status: 'success'
    },
    {
      time: '2024-01-22 09:00:00',
      type: 'send',
      title: '发送建议',
      content: '通过系统消息和微信推送发送给用户',
      status: 'success'
    },
    {
      time: '2024-01-22 10:30:00',
      type: 'read',
      title: '用户查看',
      content: '用户查看了建议详情，停留时间2分钟',
      status: 'info'
    },
    {
      time: '2024-01-22 18:45:00',
      type: 'feedback',
      title: '用户反馈',
      content: '用户反馈建议有用，评分4星',
      status: 'info'
    },
    {
      time: '2024-01-23 22:00:00',
      type: 'action',
      title: '行为改变',
      content: '监测到用户睡眠时间提前1小时',
      status: 'success'
    }
  ],
  similarCases: [
    {
      id: 'SC001',
      userName: '王某',
      department: '技术部',
      similarity: 85,
      outcome: '改善显著',
      effectivenessScore: 4.5,
      followUpDays: 7
    },
    {
      id: 'SC002',
      userName: '李某',
      department: '产品部',
      similarity: 78,
      outcome: '部分改善',
      effectivenessScore: 3.8,
      followUpDays: 10
    },
    {
      id: 'SC003',
      userName: '张某',
      department: '技术部',
      similarity: 72,
      outcome: '效果一般',
      effectivenessScore: 3.2,
      followUpDays: 14
    }
  ]
});

// 初始化用户互动图表
function initEngagementChart() {
  if (!engagementChartRef.value) return;
  
  const chart = echarts.init(engagementChartRef.value);
  const { engagement } = analyticsData.value;
  
  const option = {
    title: {
      text: '用户互动分析',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}次 ({d}%)'
    },
    series: [
      {
        type: 'funnel',
        left: '10%',
        top: 60,
        bottom: 60,
        width: '80%',
        sort: 'descending',
        gap: 2,
        label: {
          show: true,
          position: 'inside'
        },
        labelLine: {
          length: 10,
          lineStyle: {
            width: 1,
            type: 'solid'
          }
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 1
        },
        emphasis: {
          label: {
            fontSize: 20
          }
        },
        data: [
          { value: engagement.sent, name: '发送' },
          { value: engagement.delivered, name: '送达' },
          { value: engagement.opened, name: '打开' },
          { value: engagement.clicked, name: '点击' },
          { value: engagement.feedback, name: '反馈' }
        ]
      }
    ]
  };
  
  chart.setOption(option);
  
  const resizeObserver = new ResizeObserver(() => {
    chart.resize();
  });
  resizeObserver.observe(engagementChartRef.value);
}

// 初始化有效性趋势图表
function initEffectivenessChart() {
  if (!effectivenessChartRef.value) return;
  
  const chart = echarts.init(effectivenessChartRef.value);
  
  const option = {
    title: {
      text: '健康改善趋势',
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
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: analyticsData.value.healthTrends.map(item => item.date.substring(5))
    },
    yAxis: {
      type: 'value',
      name: '健康评分',
      min: 60,
      max: 80
    },
    series: [
      {
        name: '健康评分',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 3
        },
        areaStyle: {
          opacity: 0.3
        },
        data: analyticsData.value.healthTrends.map(item => item.score),
        itemStyle: {
          color: '#1890ff'
        }
      }
    ]
  };
  
  chart.setOption(option);
  
  const resizeObserver = new ResizeObserver(() => {
    chart.resize();
  });
  resizeObserver.observe(effectivenessChartRef.value);
}

// 初始化时间轴图表
function initTimelineChart() {
  if (!timelineChartRef.value) return;
  
  const chart = echarts.init(timelineChartRef.value);
  const timeline = analyticsData.value.timeline;
  
  const option = {
    title: {
      text: '建议执行时间轴',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'line'
      },
      formatter: function(params: any) {
        const data = params[0];
        const item = timeline[data.dataIndex];
        return `
          <div>
            <strong>${item.title}</strong><br/>
            时间: ${item.time}<br/>
            内容: ${item.content}
          </div>
        `;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: timeline.map((item, index) => `步骤${index + 1}`),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      show: false
    },
    series: [
      {
        name: '执行状态',
        type: 'line',
        step: 'end',
        data: timeline.map((item, index) => ({
          value: index + 1,
          itemStyle: {
            color: item.status === 'success' ? '#52c41a' : '#1890ff'
          }
        })),
        lineStyle: {
          width: 3
        },
        symbol: 'circle',
        symbolSize: 8
      }
    ]
  };
  
  chart.setOption(option);
  
  const resizeObserver = new ResizeObserver(() => {
    chart.resize();
  });
  resizeObserver.observe(timelineChartRef.value);
}

// 监听弹窗打开，初始化图表
watch(visible, (newVisible) => {
  if (newVisible) {
    setTimeout(() => {
      initEngagementChart();
      initEffectivenessChart();
      initTimelineChart();
    }, 100);
  }
});

// 计算统计数据
const engagementStats = computed(() => {
  const { engagement } = analyticsData.value;
  return {
    openRate: ((engagement.opened / engagement.sent) * 100).toFixed(1),
    clickRate: ((engagement.clicked / engagement.sent) * 100).toFixed(1),
    feedbackRate: ((engagement.feedback / engagement.sent) * 100).toFixed(1)
  };
});

function exportAnalytics() {
  message.info('分析报告导出功能正在开发中...');
}

function createFollowUp() {
  message.info('创建跟进建议功能正在开发中...');
}
</script>

<template>
  <NModal v-model:show="visible" preset="card" title="建议分析详情" class="w-full max-w-6xl">
    <template #header-extra>
      <NSpace>
        <NButton type="primary" @click="createFollowUp">
          <template #icon>
            <div class="i-mdi:plus" />
          </template>
          创建跟进建议
        </NButton>
        <NButton @click="exportAnalytics">
          <template #icon>
            <div class="i-mdi:download" />
          </template>
          导出报告
        </NButton>
      </NSpace>
    </template>

    <div v-if="recommendationData" class="space-y-6">
      <!-- 建议基本信息 -->
      <NCard title="建议信息" size="small">
        <NDescriptions bordered :column="3" size="small">
          <NDescriptionsItem label="建议标题">{{ recommendationData.title }}</NDescriptionsItem>
          <NDescriptionsItem label="目标用户">{{ recommendationData.userName }}</NDescriptionsItem>
          <NDescriptionsItem label="用户部门">{{ recommendationData.userDepartment }}</NDescriptionsItem>
          <NDescriptionsItem label="建议类型">
            <NTag type="info" size="small">{{ recommendationData.recommendationType }}</NTag>
          </NDescriptionsItem>
          <NDescriptionsItem label="优先级">
            <NTag :type="recommendationData.priority === 'high' ? 'error' : 'warning'" size="small">
              {{ recommendationData.priority }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem label="当前状态">
            <NTag type="success" size="small">{{ recommendationData.status }}</NTag>
          </NDescriptionsItem>
          <NDescriptionsItem label="健康评分">{{ recommendationData.healthScore }}</NDescriptionsItem>
          <NDescriptionsItem label="有效性评分">
            <div class="flex items-center gap-2">
              <NRate :value="recommendationData.effectivenesScore" readonly size="small" />
              <span class="text-sm">{{ recommendationData.effectivenesScore }}/5</span>
            </div>
          </NDescriptionsItem>
          <NDescriptionsItem label="生成方式">
            <NTag :type="recommendationData.aiGenerated ? 'info' : 'default'" size="small">
              {{ recommendationData.aiGenerated ? 'AI生成' : '手动创建' }}
            </NTag>
          </NDescriptionsItem>
        </NDescriptions>

        <div class="mt-4">
          <h4 class="text-sm font-medium mb-2">建议内容：</h4>
          <div class="bg-gray-50 p-3 rounded text-sm leading-relaxed">
            {{ recommendationData.content }}
          </div>
        </div>

        <div v-if="recommendationData.riskFactors?.length" class="mt-4">
          <h4 class="text-sm font-medium mb-2">关键风险因素：</h4>
          <NSpace>
            <NTag v-for="factor in recommendationData.riskFactors" :key="factor" type="warning" size="small">
              {{ factor }}
            </NTag>
          </NSpace>
        </div>
      </NCard>

      <!-- 关键指标统计 -->
      <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <NCard size="small">
          <NStatistic label="打开率" :value="engagementStats.openRate" suffix="%" />
        </NCard>
        
        <NCard size="small">
          <NStatistic label="点击率" :value="engagementStats.clickRate" suffix="%" />
        </NCard>
        
        <NCard size="small">
          <NStatistic label="反馈率" :value="engagementStats.feedbackRate" suffix="%" />
        </NCard>
        
        <NCard size="small">
          <NStatistic label="健康改善" value="+3" suffix="分" />
        </NCard>
      </div>

      <!-- 详细分析标签页 -->
      <NTabs type="line" animated>
        <!-- 用户画像 -->
        <NTabPane name="profile" tab="用户画像">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 基本信息 -->
            <NCard title="基本信息" size="small">
              <NDescriptions bordered :column="1" size="small">
                <NDescriptionsItem label="年龄">{{ analyticsData.userProfile.age }}岁</NDescriptionsItem>
                <NDescriptionsItem label="性别">{{ analyticsData.userProfile.gender }}</NDescriptionsItem>
                <NDescriptionsItem label="部门">{{ analyticsData.userProfile.department }}</NDescriptionsItem>
                <NDescriptionsItem label="职位">{{ analyticsData.userProfile.position }}</NDescriptionsItem>
                <NDescriptionsItem label="健康评分">{{ analyticsData.userProfile.healthScore }}分</NDescriptionsItem>
                <NDescriptionsItem label="风险等级">
                  <NTag type="warning" size="small">{{ analyticsData.userProfile.riskLevel }}</NTag>
                </NDescriptionsItem>
              </NDescriptions>
            </NCard>

            <!-- 历史记录 -->
            <NCard title="历史记录" size="small">
              <div class="space-y-3">
                <div class="flex justify-between">
                  <span class="text-gray-600">历史建议数量：</span>
                  <span class="font-medium">{{ analyticsData.userProfile.previousRecommendations }}条</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">已执行建议：</span>
                  <span class="font-medium">{{ analyticsData.userProfile.followedRecommendations }}条</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">执行率：</span>
                  <span class="font-medium text-green-600">
                    {{ ((analyticsData.userProfile.followedRecommendations / analyticsData.userProfile.previousRecommendations) * 100).toFixed(1) }}%
                  </span>
                </div>
              </div>
            </NCard>
          </div>
        </NTabPane>

        <!-- 互动分析 -->
        <NTabPane name="engagement" tab="互动分析">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 互动漏斗图 -->
            <NCard title="用户互动漏斗" size="small">
              <div ref="engagementChartRef" class="w-full h-80"></div>
            </NCard>
            
            <!-- 健康趋势图 -->
            <NCard title="健康改善趋势" size="small">
              <div ref="effectivenessChartRef" class="w-full h-80"></div>
            </NCard>
          </div>
        </NTabPane>

        <!-- 执行时间轴 -->
        <NTabPane name="timeline" tab="执行时间轴">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 时间轴图表 -->
            <NCard title="执行进度图" size="small">
              <div ref="timelineChartRef" class="w-full h-80"></div>
            </NCard>

            <!-- 详细时间轴 -->
            <NCard title="详细记录" size="small">
              <NTimeline>
                <NTimelineItem
                  v-for="(item, index) in analyticsData.timeline"
                  :key="index"
                  :type="item.status as any"
                  :title="item.title"
                  :content="item.content"
                  :time="item.time"
                />
              </NTimeline>
            </NCard>
          </div>
        </NTabPane>

        <!-- 相似案例 -->
        <NTabPane name="similar" tab="相似案例">
          <NCard title="相似用户案例对比" size="small">
            <div class="space-y-4">
              <div v-for="case_item in analyticsData.similarCases" :key="case_item.id" class="border rounded-lg p-4">
                <div class="flex items-center justify-between mb-2">
                  <div class="font-medium">{{ case_item.userName }} - {{ case_item.department }}</div>
                  <div class="flex items-center gap-2">
                    <span class="text-sm text-gray-600">相似度:</span>
                    <NTag type="info" size="small">{{ case_item.similarity }}%</NTag>
                  </div>
                </div>
                
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span class="text-gray-600">改善效果:</span>
                    <span class="ml-2 font-medium">{{ case_item.outcome }}</span>
                  </div>
                  <div>
                    <span class="text-gray-600">有效性评分:</span>
                    <span class="ml-2 font-medium">{{ case_item.effectivenessScore }}/5</span>
                  </div>
                  <div>
                    <span class="text-gray-600">跟进天数:</span>
                    <span class="ml-2 font-medium">{{ case_item.followUpDays }}天</span>
                  </div>
                </div>
              </div>
            </div>
          </NCard>

          <!-- 对比建议 -->
          <NCard title="基于相似案例的建议" size="small" class="mt-4">
            <NAlert type="info" show-icon>
              <template #header>智能分析建议</template>
              <div class="text-sm space-y-2">
                <p>• 基于相似用户案例，建议关注点击率和执行率的提升</p>
                <p>• 建议在7天后进行首次跟进，14天后进行效果评估</p>
                <p>• 可以参考相似用户的成功经验，调整建议内容的表达方式</p>
                <p>• 建议结合用户的工作特点，提供更具体的实施方案</p>
              </div>
            </NAlert>
          </NCard>
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

:deep(.n-descriptions-table-wrapper) {
  --n-th-padding: 8px 12px;
  --n-td-padding: 8px 12px;
}

:deep(.n-timeline .n-timeline-item-content) {
  min-height: auto;
}
</style>