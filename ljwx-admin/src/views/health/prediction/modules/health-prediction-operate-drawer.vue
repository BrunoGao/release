<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { 
  NButton, 
  NDrawer, 
  NDrawerContent, 
  NForm, 
  NFormItem, 
  NInput, 
  NSelect, 
  NTreeSelect, 
  NInputNumber, 
  NCheckboxGroup, 
  NCheckbox, 
  NRadioGroup, 
  NRadio,
  NSpace,
  NCard,
  NAlert,
  NTag,
  useMessage 
} from 'naive-ui';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';

defineOptions({
  name: 'HealthPredictionOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.PredictionTask | null;
  /** organization tree */
  orgUnitsTree: Api.SystemManage.OrgUnitsTree[];
  /** user options */
  userOptions: { label: string; value: string }[];
}

interface Emits {
  (e: 'submitted'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();
const visible = defineModel<boolean>('visible', { default: false });
const message = useMessage();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: '创建预测任务',
    edit: '编辑预测任务'
  };
  return titles[props.operateType];
});

// 预测模型选项
const modelOptions = [
  { label: 'LSTM健康预测模型v2.1', value: 'lstm_v2_1', description: '基于长短期记忆网络的时序预测模型，适用于连续性健康指标预测' },
  { label: 'RandomForest风险评估模型v1.3', value: 'rf_v1_3', description: '基于随机森林算法的风险评估模型，适用于多因素风险分析' },
  { label: 'XGBoost综合预测模型v1.0', value: 'xgb_v1_0', description: '基于梯度提升的综合预测模型，适用于复杂健康状态预测' },
  { label: 'CNN时序分析模型v2.0', value: 'cnn_v2_0', description: '基于卷积神经网络的时序分析模型，适用于模式识别' }
];

// 健康特征选项
const featureOptions = [
  { label: '心率', value: 'heart_rate', description: '心脏每分钟跳动次数' },
  { label: '血氧', value: 'blood_oxygen', description: '血液中氧气饱和度' },
  { label: '体温', value: 'temperature', description: '体表温度' },
  { label: '收缩压', value: 'pressure_high', description: '心脏收缩时动脉血压' },
  { label: '舒张压', value: 'pressure_low', description: '心脏舒张时动脉血压' },
  { label: '压力指数', value: 'stress', description: '身心压力水平' },
  { label: '步数', value: 'step', description: '每日步行数量' },
  { label: '距离', value: 'distance', description: '每日运动距离' },
  { label: '卡路里', value: 'calorie', description: '每日消耗热量' },
  { label: '睡眠', value: 'sleep', description: '睡眠时间和质量' }
];

// 预测时长选项
const horizonOptions = [
  { label: '1天', value: 1 },
  { label: '3天', value: 3 },
  { label: '7天', value: 7 },
  { label: '14天', value: 14 },
  { label: '30天', value: 30 },
  { label: '90天', value: 90 }
];

// 目标用户类型
const targetUserTypes = [
  { label: '全体用户', value: 'all' },
  { label: '指定用户', value: 'selected' },
  { label: '按部门', value: 'department' }
];

// 组织树选项
const orgOptions = computed(() => 
  props.orgUnitsTree.map(item => ({
    key: item.id,
    label: item.name,
    value: item.id,
    children: item.children?.map(child => ({
      key: child.id,
      label: child.name,
      value: child.id
    }))
  }))
);

type FormModel = Pick<Api.Health.PredictionTask, 
  'name' | 'modelId' | 'predictionHorizon' | 'features' | 'description'
> & {
  targetUserType: 'all' | 'selected' | 'department';
  targetUsers: string[];
  targetDepartments: string[];
  priority: 'high' | 'medium' | 'low';
  notifyOnComplete: boolean;
  autoRetry: boolean;
  maxRetries: number;
};

const formModel: FormModel = reactive({
  name: '',
  modelId: '',
  predictionHorizon: 7,
  features: [] as string[],
  description: '',
  targetUserType: 'all',
  targetUsers: [],
  targetDepartments: [],
  priority: 'medium',
  notifyOnComplete: true,
  autoRetry: false,
  maxRetries: 3
});

const { createRequiredRule } = useFormRules();
const { formRef, validate, restoreValidation } = useNaiveForm();

const rules = {
  name: createRequiredRule('请输入任务名称'),
  modelId: createRequiredRule('请选择预测模型'),
  predictionHorizon: createRequiredRule('请选择预测时长'),
  features: {
    type: 'array',
    required: true,
    min: 1,
    message: '请至少选择一个健康特征',
    trigger: ['blur', 'change']
  },
  targetUsers: {
    validator: (rule: any, value: string[]) => {
      if (formModel.targetUserType === 'selected' && (!value || value.length === 0)) {
        return new Error('请选择目标用户');
      }
      return true;
    },
    trigger: ['blur', 'change']
  },
  targetDepartments: {
    validator: (rule: any, value: string[]) => {
      if (formModel.targetUserType === 'department' && (!value || value.length === 0)) {
        return new Error('请选择目标部门');
      }
      return true;
    },
    trigger: ['blur', 'change']
  }
};

function updateFormModelByFormType() {
  const handlers: Record<NaiveUI.TableOperateType, () => void> = {
    add: () => {
      const defaultFormModel: FormModel = {
        name: '',
        modelId: '',
        predictionHorizon: 7,
        features: [],
        description: '',
        targetUserType: 'all',
        targetUsers: [],
        targetDepartments: [],
        priority: 'medium',
        notifyOnComplete: true,
        autoRetry: false,
        maxRetries: 3
      };
      Object.assign(formModel, defaultFormModel);
    },
    edit: () => {
      if (props.rowData) {
        Object.assign(formModel, {
          name: props.rowData.name,
          modelId: props.rowData.modelId || '',
          predictionHorizon: props.rowData.predictionHorizon,
          features: props.rowData.features || [],
          description: props.rowData.description || '',
          targetUserType: Array.isArray(props.rowData.targetUsers) ? 'selected' : 'all',
          targetUsers: Array.isArray(props.rowData.targetUsers) ? props.rowData.targetUsers : [],
          targetDepartments: [],
          priority: 'medium',
          notifyOnComplete: true,
          autoRetry: false,
          maxRetries: 3
        });
      }
    }
  };
  handlers[props.operateType]();
}

async function handleSubmit() {
  // 模拟API调用
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  message.success(
    props.operateType === 'add' 
      ? '预测任务创建成功，正在后台执行...' 
      : '预测任务更新成功'
  );
  
  closeDrawer();
}

function closeDrawer() {
  visible.value = false;
}

const selectedModel = computed(() => {
  return modelOptions.find(model => model.value === formModel.modelId);
});

const estimatedDuration = computed(() => {
  const baseTime = 30; // 基础执行时间（分钟）
  const userMultiplier = formModel.targetUserType === 'all' ? 2 : 1;
  const featureMultiplier = formModel.features.length * 0.5;
  const horizonMultiplier = formModel.predictionHorizon / 7;
  
  return Math.ceil(baseTime * userMultiplier * (1 + featureMultiplier) * horizonMultiplier);
});

watch(visible, () => {
  if (visible.value) {
    updateFormModelByFormType();
  }
});
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" width="720">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="formModel" :rules="rules" label-placement="top" label-width="auto">
        <div class="grid grid-cols-1 gap-4">
          <!-- 基本信息 -->
          <NCard title="基本信息" size="small">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <NFormItem label="任务名称" path="name">
                <NInput 
                  v-model:value="formModel.name" 
                  placeholder="请输入任务名称"
                  maxlength="100"
                  show-count
                />
              </NFormItem>

              <NFormItem label="预测时长" path="predictionHorizon">
                <NSelect 
                  v-model:value="formModel.predictionHorizon" 
                  :options="horizonOptions" 
                  placeholder="请选择预测时长" 
                />
              </NFormItem>
            </div>

            <NFormItem label="任务描述" path="description">
              <NInput 
                v-model:value="formModel.description" 
                type="textarea"
                placeholder="请输入任务描述（可选）"
                :autosize="{ minRows: 2, maxRows: 4 }"
                maxlength="500"
                show-count
              />
            </NFormItem>
          </NCard>

          <!-- 预测模型 -->
          <NCard title="预测模型" size="small">
            <NFormItem label="选择模型" path="modelId">
              <NSelect 
                v-model:value="formModel.modelId" 
                :options="modelOptions" 
                placeholder="请选择预测模型"
              />
            </NFormItem>

            <div v-if="selectedModel" class="mt-3">
              <NAlert type="info" :show-icon="false">
                <div class="text-sm">
                  <div class="font-medium mb-1">{{ selectedModel.label }}</div>
                  <div class="text-gray-600">{{ selectedModel.description }}</div>
                </div>
              </NAlert>
            </div>
          </NCard>

          <!-- 健康特征 -->
          <NCard title="健康特征" size="small">
            <NFormItem label="选择特征" path="features">
              <NCheckboxGroup v-model:value="formModel.features">
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  <NCheckbox 
                    v-for="feature in featureOptions" 
                    :key="feature.value" 
                    :value="feature.value"
                    :label="feature.label"
                  />
                </div>
              </NCheckboxGroup>
            </NFormItem>

            <div v-if="formModel.features.length > 0" class="mt-3">
              <div class="text-sm text-gray-600 mb-2">已选择的特征：</div>
              <NSpace>
                <NTag 
                  v-for="feature in formModel.features" 
                  :key="feature"
                  type="info"
                  size="small"
                >
                  {{ featureOptions.find(f => f.value === feature)?.label }}
                </NTag>
              </NSpace>
            </div>
          </NCard>

          <!-- 目标用户 -->
          <NCard title="目标用户" size="small">
            <NFormItem label="用户范围" path="targetUserType">
              <NRadioGroup v-model:value="formModel.targetUserType">
                <div class="flex flex-col gap-2">
                  <NRadio 
                    v-for="type in targetUserTypes" 
                    :key="type.value" 
                    :value="type.value"
                  >
                    {{ type.label }}
                  </NRadio>
                </div>
              </NRadioGroup>
            </NFormItem>

            <NFormItem 
              v-if="formModel.targetUserType === 'selected'" 
              label="选择用户" 
              path="targetUsers"
            >
              <NSelect
                v-model:value="formModel.targetUsers"
                :options="userOptions"
                multiple
                filterable
                placeholder="请选择目标用户"
                max-tag-count="responsive"
              />
            </NFormItem>

            <NFormItem 
              v-if="formModel.targetUserType === 'department'" 
              label="选择部门" 
              path="targetDepartments"
            >
              <NTreeSelect
                v-model:value="formModel.targetDepartments"
                :options="orgOptions"
                multiple
                checkable
                placeholder="请选择目标部门"
                key-field="value"
                label-field="label"
                children-field="children"
              />
            </NFormItem>
          </NCard>

          <!-- 高级设置 -->
          <NCard title="高级设置" size="small">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <NFormItem label="任务优先级" path="priority">
                <NSelect
                  v-model:value="formModel.priority"
                  :options="[
                    { label: '高优先级', value: 'high' },
                    { label: '普通优先级', value: 'medium' },
                    { label: '低优先级', value: 'low' }
                  ]"
                />
              </NFormItem>

              <NFormItem label="最大重试次数" path="maxRetries" v-if="formModel.autoRetry">
                <NInputNumber 
                  v-model:value="formModel.maxRetries"
                  :min="1"
                  :max="10"
                  placeholder="重试次数"
                />
              </NFormItem>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <NFormItem>
                <NCheckbox v-model:checked="formModel.notifyOnComplete">
                  完成后发送通知
                </NCheckbox>
              </NFormItem>

              <NFormItem>
                <NCheckbox v-model:checked="formModel.autoRetry">
                  失败时自动重试
                </NCheckbox>
              </NFormItem>
            </div>
          </NCard>

          <!-- 预估信息 -->
          <NAlert type="info" class="mb-4">
            <div class="text-sm">
              <div class="font-medium mb-2">任务预估信息</div>
              <div class="space-y-1 text-gray-600">
                <div>• 预计执行时间：约 {{ estimatedDuration }} 分钟</div>
                <div>• 选择特征数量：{{ formModel.features.length }} 个</div>
                <div v-if="formModel.targetUserType === 'all'">• 目标范围：全体用户</div>
                <div v-else-if="formModel.targetUserType === 'selected'">
                  • 目标范围：{{ formModel.targetUsers.length }} 个用户
                </div>
                <div v-else>• 目标范围：{{ formModel.targetDepartments.length }} 个部门</div>
              </div>
            </div>
          </NAlert>
        </div>
      </NForm>

      <template #footer>
        <div class="flex justify-end gap-12px">
          <NButton @click="closeDrawer">取消</NButton>
          <NButton type="primary" @click="handleSubmit">
            {{ props.operateType === 'add' ? '创建任务' : '更新任务' }}
          </NButton>
        </div>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped>
:deep(.n-card) {
  margin-bottom: 0;
}

:deep(.n-card .n-card__header) {
  padding: 12px 16px 8px;
}

:deep(.n-card .n-card__content) {
  padding: 8px 16px 12px;
}

:deep(.n-alert) {
  border-radius: 6px;
}
</style>