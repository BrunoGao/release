<template>
  <div class="overflow-hidden">
    <NCard title="AI模型管理" :bordered="false" size="small" class="sm:flex-1 sm:h-full">
      <template #header-extra>
        <NSpace>
          <NButton type="primary" @click="refreshModels">
            <template #icon>
              <icon-ic-round-refresh class="text-icon" />
            </template>
            刷新
          </NButton>
          <NButton type="success" @click="checkHealth">
            <template #icon>
              <icon-ic-round-health-and-safety class="text-icon" />
            </template>
            健康检查
          </NButton>
        </NSpace>
      </template>

      <!-- 服务状态卡片 -->
      <div class="mb-4">
        <NCard title="服务状态" size="small">
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <NBadge :type="healthStatus.healthy ? 'success' : 'error'" dot>
                <span class="text-sm">服务状态</span>
              </NBadge>
              <span class="font-medium">
                {{ healthStatus.healthy ? '正常' : '异常' }}
              </span>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-gray-500">检查时间:</span>
              <span class="text-sm">{{ formatTime(healthStatus.checkTime) }}</span>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-gray-500">可用模型:</span>
              <span class="text-sm font-medium">{{ healthStatus.availableModels?.length || 0 }}</span>
            </div>
          </div>
        </NCard>
      </div>

      <!-- 模型列表 -->
      <div class="mb-4">
        <NCard title="可用模型" size="small">
          <NDataTable
            :columns="modelColumns"
            :data="modelData"
            :loading="loading"
            :pagination="false"
            size="small"
          />
        </NCard>
      </div>

      <!-- 预测测试区域 -->
      <div class="mb-4">
        <NCard title="模型测试" size="small">
          <NForm :model="testForm" label-placement="left" label-width="80px">
            <NFormItem label="用户ID">
              <NInputNumber v-model:value="testForm.userId" placeholder="输入用户ID" class="w-full" />
            </NFormItem>
            <NFormItem label="预测天数">
              <NInputNumber v-model:value="testForm.days" :min="1" :max="30" placeholder="1-30天" class="w-full" />
            </NFormItem>
            <NFormItem label="健康问题">
              <NDynamicTags v-model:value="testForm.healthIssues" placeholder="添加健康问题" />
            </NFormItem>
          </NForm>
          
          <NSpace class="mt-4">
            <NButton 
              type="primary" 
              @click="testPredict" 
              :loading="testLoading.predict"
              :disabled="!testForm.userId"
            >
              测试预测
            </NButton>
            <NButton 
              type="info" 
              @click="testAdvice" 
              :loading="testLoading.advice"
              :disabled="!testForm.userId"
            >
              测试建议
            </NButton>
          </NSpace>
        </NCard>
      </div>

      <!-- 测试结果显示 -->
      <div v-if="testResult">
        <NCard title="测试结果" size="small">
          <NTabs type="line" animated>
            <NTabPane name="prediction" tab="预测结果" v-if="testResult.prediction">
              <div class="space-y-4">
                <div>
                  <h4 class="font-medium mb-2">健康趋势</h4>
                  <NAlert type="info" show-icon>
                    {{ testResult.prediction.healthTrend }}
                  </NAlert>
                </div>
                
                <div v-if="testResult.prediction.riskFactors?.length">
                  <h4 class="font-medium mb-2">风险因子</h4>
                  <NSpace>
                    <NTag v-for="risk in testResult.prediction.riskFactors" :key="risk" type="warning">
                      {{ risk }}
                    </NTag>
                  </NSpace>
                </div>
                
                <div v-if="testResult.prediction.keyIndicators?.length">
                  <h4 class="font-medium mb-2">关注指标</h4>
                  <NSpace>
                    <NTag v-for="indicator in testResult.prediction.keyIndicators" :key="indicator" type="primary">
                      {{ indicator }}
                    </NTag>
                  </NSpace>
                </div>
                
                <div v-if="testResult.prediction.recommendations?.length">
                  <h4 class="font-medium mb-2">建议</h4>
                  <NList>
                    <NListItem v-for="(rec, index) in testResult.prediction.recommendations" :key="index">
                      {{ rec }}
                    </NListItem>
                  </NList>
                </div>
                
                <div>
                  <h4 class="font-medium mb-2">置信度</h4>
                  <NProgress 
                    :percentage="(testResult.prediction.confidence || 0) * 100" 
                    :indicator-text-color="'white'"
                    :color="getConfidenceColor(testResult.prediction.confidence || 0)"
                  />
                </div>
              </div>
            </NTabPane>
            
            <NTabPane name="advice" tab="建议结果" v-if="testResult.advice">
              <div class="space-y-4">
                <div v-if="testResult.advice.lifestyleAdvice">
                  <h4 class="font-medium mb-2">生活方式建议</h4>
                  <NTabs type="card" size="small">
                    <NTabPane name="diet" tab="饮食" v-if="testResult.advice.lifestyleAdvice.diet?.length">
                      <NList>
                        <NListItem v-for="(item, index) in testResult.advice.lifestyleAdvice.diet" :key="index">
                          {{ item }}
                        </NListItem>
                      </NList>
                    </NTabPane>
                    <NTabPane name="exercise" tab="运动" v-if="testResult.advice.lifestyleAdvice.exercise?.length">
                      <NList>
                        <NListItem v-for="(item, index) in testResult.advice.lifestyleAdvice.exercise" :key="index">
                          {{ item }}
                        </NListItem>
                      </NList>
                    </NTabPane>
                    <NTabPane name="sleep" tab="睡眠" v-if="testResult.advice.lifestyleAdvice.sleep?.length">
                      <NList>
                        <NListItem v-for="(item, index) in testResult.advice.lifestyleAdvice.sleep" :key="index">
                          {{ item }}
                        </NListItem>
                      </NList>
                    </NTabPane>
                  </NTabs>
                </div>
                
                <div v-if="testResult.advice.shortTermPlan">
                  <h4 class="font-medium mb-2">短期计划 ({{ testResult.advice.shortTermPlan.duration }})</h4>
                  <div class="space-y-2">
                    <div v-if="testResult.advice.shortTermPlan.goals?.length">
                      <span class="text-sm font-medium">目标:</span>
                      <NList>
                        <NListItem v-for="(goal, index) in testResult.advice.shortTermPlan.goals" :key="index">
                          {{ goal }}
                        </NListItem>
                      </NList>
                    </div>
                    <div v-if="testResult.advice.shortTermPlan.actions?.length">
                      <span class="text-sm font-medium">行动:</span>
                      <NList>
                        <NListItem v-for="(action, index) in testResult.advice.shortTermPlan.actions" :key="index">
                          {{ action }}
                        </NListItem>
                      </NList>
                    </div>
                  </div>
                </div>
                
                <div v-if="testResult.advice.longTermGoals?.length">
                  <h4 class="font-medium mb-2">长期目标</h4>
                  <NList>
                    <NListItem v-for="(goal, index) in testResult.advice.longTermGoals" :key="index">
                      {{ goal }}
                    </NListItem>
                  </NList>
                </div>
              </div>
            </NTabPane>
            
            <NTabPane name="raw" tab="原始响应">
              <NCode 
                :code="JSON.stringify(testResult, null, 2)" 
                language="json" 
                show-line-numbers
                style="max-height: 400px; overflow-y: auto;"
              />
            </NTabPane>
          </NTabs>
        </NCard>
      </div>
    </NCard>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, h } from 'vue';
import type { DataTableColumns } from 'naive-ui';
import { useMessage } from 'naive-ui';
import { aiPredictionApi, type AiPrediction } from '@/service/api';
import { $t } from '@/locales';

defineOptions({
  name: 'AiModelsManagement'
});

const message = useMessage();

// 响应式数据
const loading = ref(false);
const healthStatus = ref<AiPrediction.AiHealthStatus>({
  healthy: false,
  availableModels: [],
  checkTime: ''
});

// 模型数据
const modelData = computed(() => {
  return healthStatus.value.availableModels.map((model, index) => ({
    id: index + 1,
    name: model,
    status: healthStatus.value.healthy ? '正常' : '异常',
    type: model.includes('health') ? '健康模型' : '通用模型'
  }));
});

// 模型表格列
const modelColumns: DataTableColumns = [
  {
    title: 'ID',
    key: 'id',
    width: 60
  },
  {
    title: '模型名称',
    key: 'name',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '模型类型',
    key: 'type'
  },
  {
    title: '状态',
    key: 'status',
    render: (row: any) => {
      const isNormal = row.status === '正常';
      return h('div', {
        class: [
          'px-2 py-1 rounded text-xs font-medium',
          isNormal ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        ]
      }, row.status);
    }
  }
];

// 测试表单
const testForm = ref({
  userId: null as number | null,
  days: 7,
  healthIssues: [] as string[]
});

const testLoading = ref({
  predict: false,
  advice: false
});

const testResult = ref<{
  prediction?: AiPrediction.HealthPredictionResult;
  advice?: AiPrediction.HealthAdviceResult;
} | null>(null);

// 方法
const refreshModels = async () => {
  await checkHealth();
};

const checkHealth = async () => {
  loading.value = true;
  try {
    const { data } = await aiPredictionApi.checkHealth();
    healthStatus.value = data;
    message.success('健康检查完成');
  } catch (error) {
    console.error('健康检查失败:', error);
    message.error('健康检查失败');
  } finally {
    loading.value = false;
  }
};

const testPredict = async () => {
  if (!testForm.value.userId) {
    message.warning('请输入用户ID');
    return;
  }
  
  testLoading.value.predict = true;
  try {
    const { data } = await aiPredictionApi.predict(testForm.value.userId, testForm.value.days);
    testResult.value = {
      ...testResult.value,
      prediction: data
    };
    message.success('预测测试完成');
  } catch (error) {
    console.error('预测测试失败:', error);
    message.error('预测测试失败');
  } finally {
    testLoading.value.predict = false;
  }
};

const testAdvice = async () => {
  if (!testForm.value.userId) {
    message.warning('请输入用户ID');
    return;
  }
  
  testLoading.value.advice = true;
  try {
    const { data } = await aiPredictionApi.advice(testForm.value.userId, testForm.value.healthIssues);
    testResult.value = {
      ...testResult.value,
      advice: data
    };
    message.success('建议测试完成');
  } catch (error) {
    console.error('建议测试失败:', error);
    message.error('建议测试失败');
  } finally {
    testLoading.value.advice = false;
  }
};

const formatTime = (time: string) => {
  if (!time) return '-';
  return new Date(time).toLocaleString('zh-CN');
};

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return '#52c41a';
  if (confidence >= 0.6) return '#faad14';
  return '#ff4d4f';
};

// 生命周期
onMounted(() => {
  checkHealth();
});
</script>

<style scoped>
.text-icon {
  font-size: 16px;
}
</style>
