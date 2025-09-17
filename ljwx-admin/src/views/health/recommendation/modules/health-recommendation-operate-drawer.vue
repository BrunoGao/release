<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import {
  NAlert,
  NButton,
  NCard,
  NCheckbox,
  NCheckboxGroup,
  NDatePicker,
  NDrawer,
  NDrawerContent,
  NForm,
  NFormItem,
  NInput,
  NRadio,
  NRadioGroup,
  NSelect,
  NSpace,
  NSwitch,
  NTag,
  NTreeSelect,
  useMessage
} from 'naive-ui';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';

defineOptions({
  name: 'HealthRecommendationOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.RecommendationTask | null;
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
    add: '创建健康建议',
    edit: '编辑健康建议'
  };
  return titles[props.operateType];
});

// 建议类型选项
const typeOptions = [
  { label: '生活方式建议', value: 'lifestyle', description: '作息、习惯等生活方式改善建议' },
  { label: '运动健身建议', value: 'exercise', description: '运动计划、健身指导等建议' },
  { label: '营养饮食建议', value: 'nutrition', description: '饮食结构、营养搭配等建议' },
  { label: '医疗健康建议', value: 'medical', description: '就医、体检、用药等医疗建议' },
  { label: '心理健康建议', value: 'mental', description: '情绪管理、压力缓解等心理建议' }
];

// 优先级选项
const priorityOptions = [
  { label: '高优先级', value: 'high', description: '紧急需要关注的健康问题' },
  { label: '中优先级', value: 'medium', description: '需要适当关注的健康问题' },
  { label: '低优先级', value: 'low', description: '可以逐步改善的健康问题' }
];

// 目标用户类型
const targetUserTypes = [
  { label: '指定用户', value: 'selected' },
  { label: '按部门', value: 'department' },
  { label: '按条件筛选', value: 'filtered' }
];

// 筛选条件选项
const filterConditions = [
  { label: '健康评分低于60分', value: 'health_score_low' },
  { label: '心率异常', value: 'heart_rate_abnormal' },
  { label: '血压异常', value: 'blood_pressure_abnormal' },
  { label: '睡眠质量差', value: 'sleep_quality_poor' },
  { label: '压力指数高', value: 'stress_high' },
  { label: '运动不足', value: 'exercise_insufficient' }
];

// 发送方式选项
const deliveryMethods = [
  { label: '系统内消息', value: 'system', description: '在系统内发送消息通知' },
  { label: '微信推送', value: 'wechat', description: '通过微信小程序推送' },
  { label: '短信通知', value: 'sms', description: '发送短信提醒' },
  { label: '邮件发送', value: 'email', description: '发送邮件通知' }
];

// 建议模板选项
const templateOptions = [
  { label: '不使用模板', value: null },
  { label: '睡眠改善模板', value: 'T001' },
  { label: '运动计划模板', value: 'T002' },
  { label: '饮食调理模板', value: 'T003' },
  { label: '压力管理模板', value: 'T004' },
  { label: '心血管保健模板', value: 'T005' }
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

type FormModel = Pick<Api.Health.RecommendationTask, 'title' | 'content' | 'recommendationType' | 'priority'> & {
  targetUserType: 'selected' | 'department' | 'filtered';
  targetUsers: string[];
  targetDepartments: string[];
  filterConditions: string[];
  deliveryMethods: string[];
  templateId: string | null;
  scheduledAt: number | null;
  autoSend: boolean;
  enableFeedback: boolean;
  reminderEnabled: boolean;
  reminderDays: number;
};

const formModel: FormModel = reactive({
  title: '',
  content: '',
  recommendationType: 'lifestyle',
  priority: 'medium',
  targetUserType: 'selected',
  targetUsers: [],
  targetDepartments: [],
  filterConditions: [],
  deliveryMethods: ['system'],
  templateId: null,
  scheduledAt: null,
  autoSend: false,
  enableFeedback: true,
  reminderEnabled: false,
  reminderDays: 3
});

const { createRequiredRule } = useFormRules();
const { formRef, validate, restoreValidation } = useNaiveForm();

const rules = {
  title: createRequiredRule('请输入建议标题'),
  content: [
    createRequiredRule('请输入建议内容'),
    {
      min: 10,
      max: 1000,
      message: '建议内容长度在10-1000字符之间',
      trigger: ['input', 'blur']
    }
  ],
  recommendationType: createRequiredRule('请选择建议类型'),
  priority: createRequiredRule('请选择优先级'),
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
  },
  filterConditions: {
    validator: (rule: any, value: string[]) => {
      if (formModel.targetUserType === 'filtered' && (!value || value.length === 0)) {
        return new Error('请选择筛选条件');
      }
      return true;
    },
    trigger: ['blur', 'change']
  },
  deliveryMethods: {
    type: 'array',
    required: true,
    min: 1,
    message: '请至少选择一种发送方式',
    trigger: ['blur', 'change']
  }
};

function updateFormModelByFormType() {
  const handlers: Record<NaiveUI.TableOperateType, () => void> = {
    add: () => {
      const defaultFormModel: FormModel = {
        title: '',
        content: '',
        recommendationType: 'lifestyle',
        priority: 'medium',
        targetUserType: 'selected',
        targetUsers: [],
        targetDepartments: [],
        filterConditions: [],
        deliveryMethods: ['system'],
        templateId: null,
        scheduledAt: null,
        autoSend: false,
        enableFeedback: true,
        reminderEnabled: false,
        reminderDays: 3
      };
      Object.assign(formModel, defaultFormModel);
    },
    edit: () => {
      if (props.rowData) {
        Object.assign(formModel, {
          title: props.rowData.title,
          content: props.rowData.content,
          recommendationType: props.rowData.recommendationType,
          priority: props.rowData.priority,
          targetUserType: 'selected',
          targetUsers: [],
          targetDepartments: [],
          filterConditions: [],
          deliveryMethods: ['system'],
          templateId: props.rowData.templateId || null,
          scheduledAt: null,
          autoSend: false,
          enableFeedback: true,
          reminderEnabled: false,
          reminderDays: 3
        });
      }
    }
  };
  handlers[props.operateType]();
}

// 应用模板
function applyTemplate() {
  if (!formModel.templateId) {
    message.warning('请先选择一个模板');
    return;
  }

  const templates = {
    T001: {
      title: '改善睡眠质量建议',
      content: '建议您调整作息时间，每天保证7-8小时的睡眠，睡前1小时避免使用电子设备，创造安静舒适的睡眠环境。',
      type: 'lifestyle'
    },
    T002: {
      title: '个人运动计划建议',
      content: '建议每周进行3-4次中等强度有氧运动，如快走、游泳或骑行，每次30-45分钟，同时配合力量训练。',
      type: 'exercise'
    },
    T003: {
      title: '健康饮食调理建议',
      content: '建议增加蔬菜水果摄入，减少油腻和高盐食物，保持饮食规律，控制每餐七分饱。',
      type: 'nutrition'
    },
    T004: {
      title: '压力管理建议',
      content: '建议学习放松技巧如深呼吸、冥想，保持工作生活平衡，适当参与社交活动缓解压力。',
      type: 'mental'
    },
    T005: {
      title: '心血管健康保健建议',
      content: '建议定期监测血压心率，保持适量运动，戒烟限酒，如有异常及时就医咨询。',
      type: 'medical'
    }
  };

  const template = templates[formModel.templateId as keyof typeof templates];
  if (template) {
    formModel.title = template.title;
    formModel.content = template.content;
    formModel.recommendationType = template.type;
    message.success('模板应用成功');
  }
}

async function handleSubmit() {
  // 模拟API调用
  await new Promise(resolve => setTimeout(resolve, 1000));

  message.success(props.operateType === 'add' ? '健康建议创建成功' : '健康建议更新成功');

  closeDrawer();
}

function closeDrawer() {
  visible.value = false;
}

const selectedType = computed(() => {
  return typeOptions.find(type => type.value === formModel.recommendationType);
});

const selectedPriority = computed(() => {
  return priorityOptions.find(priority => priority.value === formModel.priority);
});

const targetUserCount = computed(() => {
  switch (formModel.targetUserType) {
    case 'selected':
      return formModel.targetUsers.length;
    case 'department':
      return formModel.targetDepartments.length * 10; // 估算
    case 'filtered':
      return formModel.filterConditions.length * 25; // 估算
    default:
      return 0;
  }
});

watch(visible, () => {
  if (visible.value) {
    updateFormModelByFormType();
  }
});
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" width="800">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="formModel" :rules="rules" label-placement="top" label-width="auto">
        <div class="grid grid-cols-1 gap-4">
          <!-- 基本信息 -->
          <NCard title="基本信息" size="small">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <NFormItem label="建议标题" path="title">
                <NInput v-model:value="formModel.title" placeholder="请输入建议标题" maxlength="100" show-count />
              </NFormItem>

              <NFormItem label="建议类型" path="recommendationType">
                <NSelect v-model:value="formModel.recommendationType" :options="typeOptions" placeholder="请选择建议类型" />
              </NFormItem>
            </div>

            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <NFormItem label="优先级" path="priority">
                <NSelect v-model:value="formModel.priority" :options="priorityOptions" placeholder="请选择优先级" />
              </NFormItem>

              <NFormItem label="建议模板" path="templateId">
                <div class="flex gap-2">
                  <NSelect v-model:value="formModel.templateId" :options="templateOptions" placeholder="请选择模板（可选）" class="flex-1" />
                  <NButton type="primary" @click="applyTemplate">应用</NButton>
                </div>
              </NFormItem>
            </div>

            <NFormItem label="建议内容" path="content">
              <NInput
                v-model:value="formModel.content"
                type="textarea"
                placeholder="请输入详细的健康建议内容"
                :rows="4"
                maxlength="1000"
                show-count
              />
            </NFormItem>

            <div v-if="selectedType" class="mb-4">
              <NAlert type="info" :show-icon="false">
                <div class="text-sm">
                  <div class="mb-1 font-medium">{{ selectedType.label }}</div>
                  <div class="text-gray-600">{{ selectedType.description }}</div>
                </div>
              </NAlert>
            </div>
          </NCard>

          <!-- 目标用户 -->
          <NCard title="目标用户" size="small">
            <NFormItem label="用户范围" path="targetUserType">
              <NRadioGroup v-model:value="formModel.targetUserType">
                <div class="flex flex-col gap-2">
                  <NRadio v-for="type in targetUserTypes" :key="type.value" :value="type.value">
                    {{ type.label }}
                  </NRadio>
                </div>
              </NRadioGroup>
            </NFormItem>

            <NFormItem v-if="formModel.targetUserType === 'selected'" label="选择用户" path="targetUsers">
              <NSelect
                v-model:value="formModel.targetUsers"
                :options="userOptions"
                multiple
                filterable
                placeholder="请选择目标用户"
                max-tag-count="responsive"
              />
            </NFormItem>

            <NFormItem v-if="formModel.targetUserType === 'department'" label="选择部门" path="targetDepartments">
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

            <NFormItem v-if="formModel.targetUserType === 'filtered'" label="筛选条件" path="filterConditions">
              <NCheckboxGroup v-model:value="formModel.filterConditions">
                <div class="grid grid-cols-2 gap-2">
                  <NCheckbox v-for="condition in filterConditions" :key="condition.value" :value="condition.value" :label="condition.label" />
                </div>
              </NCheckboxGroup>
            </NFormItem>

            <div v-if="targetUserCount > 0" class="mt-3">
              <NAlert type="info" :show-icon="false">
                <div class="text-sm">
                  <span class="font-medium">预计目标用户：</span>
                  <span>约 {{ targetUserCount }} 人</span>
                </div>
              </NAlert>
            </div>
          </NCard>

          <!-- 发送设置 -->
          <NCard title="发送设置" size="small">
            <NFormItem label="发送方式" path="deliveryMethods">
              <NCheckboxGroup v-model:value="formModel.deliveryMethods">
                <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
                  <NCheckbox v-for="method in deliveryMethods" :key="method.value" :value="method.value">
                    <div>
                      <div class="font-medium">{{ method.label }}</div>
                      <div class="text-xs text-gray-500">{{ method.description }}</div>
                    </div>
                  </NCheckbox>
                </div>
              </NCheckboxGroup>
            </NFormItem>

            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <NFormItem label="定时发送">
                <NDatePicker
                  v-model:value="formModel.scheduledAt"
                  type="datetime"
                  clearable
                  placeholder="请选择发送时间（可选）"
                  format="yyyy-MM-dd HH:mm"
                  class="w-full"
                />
              </NFormItem>

              <NFormItem label="高级选项">
                <div class="space-y-3">
                  <div class="flex items-center justify-between">
                    <span class="text-sm">启用用户反馈</span>
                    <NSwitch v-model:value="formModel.enableFeedback" />
                  </div>

                  <div class="flex items-center justify-between">
                    <span class="text-sm">启用提醒</span>
                    <NSwitch v-model:value="formModel.reminderEnabled" />
                  </div>
                </div>
              </NFormItem>
            </div>
          </NCard>

          <!-- 预览信息 -->
          <NAlert type="info" class="mb-4">
            <div class="text-sm">
              <div class="mb-2 font-medium">建议预览信息</div>
              <div class="text-gray-600 space-y-1">
                <div>• 建议类型：{{ selectedType?.label || '未选择' }}</div>
                <div>• 优先级：{{ selectedPriority?.label || '未选择' }}</div>
                <div>• 目标用户：约 {{ targetUserCount }} 人</div>
                <div>• 发送方式：{{ formModel.deliveryMethods.join(', ') }}</div>
                <div v-if="formModel.scheduledAt">• 定时发送：{{ new Date(formModel.scheduledAt).toLocaleString() }}</div>
                <div v-else>• 发送方式：立即发送</div>
              </div>
            </div>
          </NAlert>
        </div>
      </NForm>

      <template #footer>
        <div class="flex justify-end gap-12px">
          <NButton @click="closeDrawer">取消</NButton>
          <NButton type="primary" @click="handleSubmit">
            {{ props.operateType === 'add' ? '创建建议' : '更新建议' }}
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
