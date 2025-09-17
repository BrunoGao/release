<script setup lang="tsx">
import { computed, h, ref } from 'vue';
import { NAlert, NButton, NCard, NDataTable, NDivider, NModal, NPopconfirm, NProgress, NSpace, NTabPane, NTabs, NTag, useMessage } from 'naive-ui';

defineOptions({
  name: 'PredictionModelManager'
});

const emit = defineEmits<{
  (e: 'model-updated'): void;
}>();

const visible = defineModel<boolean>('visible', { default: false });
const message = useMessage();

// 模型数据
const models = ref([
  {
    id: 'lstm_v2_1',
    name: 'LSTM健康预测模型',
    version: 'v2.1',
    type: '时序预测',
    algorithm: 'LSTM',
    accuracy: 0.87,
    precision: 0.85,
    recall: 0.89,
    f1Score: 0.87,
    status: 'active',
    trainingDate: '2024-01-15',
    lastUsed: '2024-01-21',
    description: '基于长短期记忆网络的时序预测模型，特别适用于健康指标的连续性预测',
    features: ['heart_rate', 'blood_oxygen', 'temperature', 'pressure_high', 'pressure_low'],
    usageCount: 156,
    avgExecutionTime: 45 // 秒
  },
  {
    id: 'rf_v1_3',
    name: 'RandomForest风险评估模型',
    version: 'v1.3',
    type: '分类预测',
    algorithm: 'Random Forest',
    accuracy: 0.82,
    precision: 0.81,
    recall: 0.84,
    f1Score: 0.82,
    status: 'active',
    trainingDate: '2024-01-10',
    lastUsed: '2024-01-20',
    description: '基于随机森林算法的多因素风险评估模型，可以评估用户的健康风险等级',
    features: ['heart_rate', 'pressure_high', 'pressure_low', 'stress', 'step'],
    usageCount: 89,
    avgExecutionTime: 28
  },
  {
    id: 'xgb_v1_0',
    name: 'XGBoost综合预测模型',
    version: 'v1.0',
    type: '综合预测',
    algorithm: 'XGBoost',
    accuracy: 0.91,
    precision: 0.9,
    recall: 0.92,
    f1Score: 0.91,
    status: 'training',
    trainingDate: '2024-01-22',
    lastUsed: null,
    description: '基于梯度提升的综合预测模型，结合多种健康指标进行综合性健康状态预测',
    features: ['heart_rate', 'blood_oxygen', 'temperature', 'pressure_high', 'pressure_low', 'stress', 'step', 'sleep'],
    usageCount: 0,
    avgExecutionTime: 35
  },
  {
    id: 'cnn_v2_0',
    name: 'CNN时序分析模型',
    version: 'v2.0',
    type: '模式识别',
    algorithm: 'CNN',
    accuracy: 0.79,
    precision: 0.77,
    recall: 0.81,
    f1Score: 0.79,
    status: 'inactive',
    trainingDate: '2024-01-05',
    lastUsed: '2024-01-12',
    description: '基于卷积神经网络的时序模式识别模型，主要用于健康数据中异常模式的识别',
    features: ['heart_rate', 'blood_oxygen', 'temperature'],
    usageCount: 23,
    avgExecutionTime: 52
  }
]);

const selectedModel = ref(null);
const showModelDetails = computed({
  get: () => Boolean(selectedModel.value),
  set: value => {
    if (!value) {
      selectedModel.value = null;
    }
  }
});
const trainingProgress = ref(0);
const isTraining = ref(false);

const columns = [
  {
    key: 'name',
    title: '模型名称',
    width: 200,
    render: (row: any) => (
      <div>
        <div class="font-medium">{row.name}</div>
        <div class="text-xs text-gray-500">
          {row.version} • {row.algorithm}
        </div>
      </div>
    )
  },
  {
    key: 'type',
    title: '类型',
    width: 100,
    render: (row: any) => (
      <NTag size="small" type="info">
        {row.type}
      </NTag>
    )
  },
  {
    key: 'status',
    title: '状态',
    width: 100,
    render: (row: any) => {
      const statusMap = {
        active: { type: 'success', text: '活跃' },
        inactive: { type: 'warning', text: '未激活' },
        training: { type: 'info', text: '训练中' },
        error: { type: 'error', text: '错误' }
      } as const;
      const status = statusMap[row.status as keyof typeof statusMap];
      return h(NTag, { type: status.type, size: 'small' }, () => status.text);
    }
  },
  {
    key: 'accuracy',
    title: '准确率',
    width: 100,
    render: (row: any) => {
      if (row.status === 'training') {
        return h(NProgress, {
          percentage: trainingProgress.value,
          status: 'info',
          showIndicator: false
        });
      }
      return `${(row.accuracy * 100).toFixed(1)}%`;
    }
  },
  {
    key: 'usageCount',
    title: '使用次数',
    width: 100
  },
  {
    key: 'avgExecutionTime',
    title: '平均执行时间',
    width: 120,
    render: (row: any) => `${row.avgExecutionTime}秒`
  },
  {
    key: 'lastUsed',
    title: '最后使用',
    width: 120,
    render: (row: any) => row.lastUsed || '未使用'
  },
  {
    key: 'operate',
    title: '操作',
    width: 200,
    render: (row: any) => (
      <NSpace size="small">
        <NButton size="small" type="info" quaternary onClick={() => viewModelDetails(row)}>
          详情
        </NButton>
        {row.status === 'active' && (
          <NButton size="small" type="warning" quaternary onClick={() => deactivateModel(row.id)}>
            停用
          </NButton>
        )}
        {row.status === 'inactive' && (
          <NButton size="small" type="success" quaternary onClick={() => activateModel(row.id)}>
            激活
          </NButton>
        )}
        {row.status !== 'training' && (
          <NButton size="small" type="primary" quaternary onClick={() => retrainModel(row.id)}>
            重训练
          </NButton>
        )}
        <NPopconfirm onPositiveClick={() => deleteModel(row.id)}>
          {{
            default: () => '确认删除此模型？',
            trigger: () => (
              <NButton size="small" type="error" quaternary>
                删除
              </NButton>
            )
          }}
        </NPopconfirm>
      </NSpace>
    )
  }
];

const modelStats = computed(() => {
  return {
    total: models.value.length,
    active: models.value.filter(m => m.status === 'active').length,
    training: models.value.filter(m => m.status === 'training').length,
    avgAccuracy: models.value.reduce((acc, m) => acc + m.accuracy, 0) / models.value.length
  };
});

function viewModelDetails(model: any) {
  selectedModel.value = model;
}

function activateModel(id: string) {
  const model = models.value.find(m => m.id === id);
  if (model) {
    model.status = 'active';
    message.success('模型已激活');
    emit('model-updated');
  }
}

function deactivateModel(id: string) {
  const model = models.value.find(m => m.id === id);
  if (model) {
    model.status = 'inactive';
    message.success('模型已停用');
    emit('model-updated');
  }
}

function retrainModel(id: string) {
  const model = models.value.find(m => m.id === id);
  if (model) {
    model.status = 'training';
    trainingProgress.value = 0;
    isTraining.value = true;

    // 模拟训练进度
    const interval = setInterval(() => {
      trainingProgress.value += Math.random() * 10;
      if (trainingProgress.value >= 100) {
        clearInterval(interval);
        trainingProgress.value = 100;
        setTimeout(() => {
          model.status = 'active';
          model.accuracy = Math.min(0.95, model.accuracy + Math.random() * 0.05);
          model.trainingDate = new Date().toISOString().split('T')[0];
          isTraining.value = false;
          message.success('模型训练完成');
          emit('model-updated');
        }, 1000);
      }
    }, 200);

    message.info('模型开始重新训练...');
  }
}

function deleteModel(id: string) {
  const index = models.value.findIndex(m => m.id === id);
  if (index > -1) {
    models.value.splice(index, 1);
    message.success('模型已删除');
    emit('model-updated');
  }
}

function createNewModel() {
  message.info('创建新模型功能正在开发中...');
}
</script>

<template>
  <NModal v-model:show="visible" preset="card" title="预测模型管理" class="max-w-7xl w-full">
    <template #header-extra>
      <NButton type="primary" @click="createNewModel">
        <template #icon>
          <div class="i-mdi:plus" />
        </template>
        创建新模型
      </NButton>
    </template>

    <div class="space-y-4">
      <!-- 统计卡片 -->
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <NCard size="small">
          <div class="text-center">
            <div class="text-2xl text-primary font-bold">{{ modelStats.total }}</div>
            <div class="text-sm text-gray-600">总模型数</div>
          </div>
        </NCard>

        <NCard size="small">
          <div class="text-center">
            <div class="text-2xl text-success font-bold">{{ modelStats.active }}</div>
            <div class="text-sm text-gray-600">活跃模型</div>
          </div>
        </NCard>

        <NCard size="small">
          <div class="text-center">
            <div class="text-2xl text-info font-bold">{{ modelStats.training }}</div>
            <div class="text-sm text-gray-600">训练中</div>
          </div>
        </NCard>

        <NCard size="small">
          <div class="text-center">
            <div class="text-2xl text-warning font-bold">{{ (modelStats.avgAccuracy * 100).toFixed(1) }}%</div>
            <div class="text-sm text-gray-600">平均准确率</div>
          </div>
        </NCard>
      </div>

      <!-- 训练进度提醒 -->
      <div v-if="isTraining">
        <NAlert type="info" show-icon>
          <div class="flex items-center justify-between">
            <span>正在训练模型，请稍候...</span>
            <NProgress :percentage="trainingProgress" status="info" class="w-32" />
          </div>
        </NAlert>
      </div>

      <!-- 模型列表 -->
      <NCard>
        <template #header>
          <span class="text-lg font-semibold">模型列表</span>
        </template>

        <NDataTable :data="models" :columns="columns" :row-key="(row: any) => row.id" size="small" striped />
      </NCard>

      <!-- 模型详情 -->
      <NModal v-model:show="showModelDetails" preset="card" title="模型详情" class="max-w-4xl w-full">
        <div v-if="selectedModel" class="space-y-4">
          <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <!-- 基本信息 -->
            <NCard title="基本信息" size="small">
              <div class="space-y-3">
                <div class="flex justify-between">
                  <span class="text-gray-600">模型名称:</span>
                  <span class="font-medium">{{ selectedModel.name }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">版本:</span>
                  <span>{{ selectedModel.version }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">算法:</span>
                  <span>{{ selectedModel.algorithm }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">类型:</span>
                  <NTag type="info" size="small">{{ selectedModel.type }}</NTag>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">状态:</span>
                  <NTag :type="selectedModel.status === 'active' ? 'success' : 'warning'" size="small">
                    {{ selectedModel.status === 'active' ? '活跃' : '未激活' }}
                  </NTag>
                </div>
              </div>
            </NCard>

            <!-- 性能指标 -->
            <NCard title="性能指标" size="small">
              <div class="space-y-3">
                <div class="flex justify-between">
                  <span class="text-gray-600">准确率:</span>
                  <span class="font-medium">{{ (selectedModel.accuracy * 100).toFixed(1) }}%</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">精确率:</span>
                  <span>{{ (selectedModel.precision * 100).toFixed(1) }}%</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">召回率:</span>
                  <span>{{ (selectedModel.recall * 100).toFixed(1) }}%</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">F1分数:</span>
                  <span>{{ (selectedModel.f1Score * 100).toFixed(1) }}%</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">平均执行时间:</span>
                  <span>{{ selectedModel.avgExecutionTime }}秒</span>
                </div>
              </div>
            </NCard>
          </div>

          <!-- 使用统计 -->
          <NCard title="使用统计" size="small">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div class="text-center">
                <div class="text-2xl text-primary font-bold">{{ selectedModel.usageCount }}</div>
                <div class="text-sm text-gray-600">使用次数</div>
              </div>
              <div class="text-center">
                <div class="text-lg text-gray-600">{{ selectedModel.trainingDate }}</div>
                <div class="text-sm text-gray-600">训练日期</div>
              </div>
              <div class="text-center">
                <div class="text-lg text-gray-600">{{ selectedModel.lastUsed || '未使用' }}</div>
                <div class="text-sm text-gray-600">最后使用</div>
              </div>
            </div>
          </NCard>

          <!-- 支持的特征 -->
          <NCard title="支持的健康特征" size="small">
            <div class="flex flex-wrap gap-2">
              <NTag v-for="feature in selectedModel.features" :key="feature" type="info" size="small">
                {{ feature }}
              </NTag>
            </div>
          </NCard>

          <!-- 模型描述 -->
          <NCard title="模型描述" size="small">
            <p class="text-gray-700 leading-relaxed">{{ selectedModel.description }}</p>
          </NCard>
        </div>

        <template #footer>
          <div class="flex justify-end">
            <NButton @click="selectedModel = null">关闭</NButton>
          </div>
        </template>
      </NModal>
    </div>
  </NModal>
</template>

<style scoped>
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
</style>
