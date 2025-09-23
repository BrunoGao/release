<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddAlertRules, fetchUpdateAlertRulesInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { useAuthStore } from '@/store/modules/auth';

defineOptions({
  name: 'TAlertRulesOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Health.AlertRules | null;
}

const props = defineProps<Props>();

interface Emits {
  (e: 'submitted'): void;
}

const emit = defineEmits<Emits>();

const visible = defineModel<boolean>('visible', {
  default: false
});

const { dictOptions } = useDict();
const { formRef, validate, restoreValidation } = useNaiveForm();
const authStore = useAuthStore();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: $t('common.add'),
    edit: $t('common.edit')
  };
  return titles[props.operateType];
});

type Model = Api.Health.AlertRules;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    id: '',
    ruleCategory: 'SINGLE',
    ruleType: '',
    physicalSign: '',
    thresholdMin: 0,
    thresholdMax: 0,
    deviationPercentage: 0,
    trendDuration: 1,
    timeWindowSeconds: 300,
    cooldownSeconds: 600,
    priorityLevel: 3,
    parameters: '',
    triggerCondition: '',
    alertMessage: '',
    level: 'MEDIUM',
    severityLevel: '',
    notificationType: '',
    enabledChannels: ['message'],
    isEnabled: true,
    effectiveTimeStart: null,
    effectiveTimeEnd: null,
    effectiveDays: '',
    conditionExpression: null,
    version: 0,
    customerId: authStore.userInfo?.customerId || 0,
    createUser: '',
    createTime: '',
    updateUser: '',
    updateTime: ''
  };
}

function handleInitModel() {
  Object.assign(model, createDefaultModel());

  if (!props.rowData) return;

  if (props.operateType === 'edit' && props.rowData) {
    Object.assign(model, props.rowData);
  }
}

function closeDrawer() {
  visible.value = false;
}

const isAdd = computed(() => props.operateType === 'add');

// 新增状态和选项
const submitLoading = ref(false);

// 规则类型选项
const ruleCategoryOptions = [
  { label: '单体征规则', value: 'SINGLE' },
  { label: '复合规则', value: 'COMPOSITE' },
  { label: '复杂规则', value: 'COMPLEX', disabled: true }
];

// 优先级选项
const priorityOptions = [
  { label: '最高', value: 1 },
  { label: '高', value: 2 },
  { label: '中', value: 3 },
  { label: '低', value: 4 }
];

// 严重级别选项
const severityOptions = [
  { label: '紧急', value: 'CRITICAL' },
  { label: '高', value: 'HIGH' },
  { label: '中', value: 'MEDIUM' },
  { label: '低', value: 'LOW' }
];

// 健康数据类型选项
const healthDataOptions = [
  { label: '心率', value: 'heart_rate' },
  { label: '血氧', value: 'blood_oxygen' },
  { label: '体温', value: 'temperature' },
  { label: '收缩压', value: 'pressure_high' },
  { label: '舒张压', value: 'pressure_low' },
  { label: '步数', value: 'step' },
  { label: '卡路里', value: 'calorie' },
  { label: '距离', value: 'distance' },
  { label: '睡眠', value: 'sleep' },
  { label: '压力', value: 'stress' }
];

// 表单验证规则
const formRules = {
  ruleCategory: [{ required: true, message: '请选择规则类型', trigger: 'change' }],
  physicalSign: [
    {
      required: true,
      message: '请选择监控指标',
      trigger: 'change',
      validator: () => {
        if (model.ruleCategory === 'SINGLE' && !model.physicalSign) {
          return new Error('单体征规则必须选择监控指标');
        }
        return true;
      }
    }
  ],
  priorityLevel: [{ required: true, type: 'number', message: '请选择优先级', trigger: 'change' }],
  level: [{ required: true, message: '请选择严重级别', trigger: 'change' }],
  enabledChannels: [{ required: true, type: 'array', min: 1, message: '请至少选择一个通知渠道', trigger: 'change' }]
};

// 开关样式
const switchRailStyle = ({ focused, checked }: { focused: boolean; checked: boolean }) => {
  const style: Record<string, string> = {};
  if (checked) {
    style.background = '#10b981';
  }
  if (focused) {
    style.boxShadow = '0 0 0 2px rgba(16, 185, 129, 0.3)';
  }
  return style;
};

// 更新提交处理
async function handleSubmit() {
  submitLoading.value = true;

  try {
    await validate();

    // 处理数据格式
    const submitData = {
      ...model,
      enabledChannels: JSON.stringify(model.enabledChannels),
      effectiveDays: Array.isArray(model.effectiveDays) ? model.effectiveDays.join(',') : model.effectiveDays,
      conditionExpression: model.conditionExpression ? JSON.stringify(model.conditionExpression) : null
    };

    const func = isAdd.value ? fetchAddAlertRules : fetchUpdateAlertRulesInfo;
    const { error, data } = await func(submitData);

    if (!error && data) {
      window.$message?.success(isAdd.value ? '规则创建成功' : '规则更新成功');
      closeDrawer();
      emit('submitted');
    } else if (error) {
      // 处理特定的错误类型
      const errorMsg = error.message || '操作失败';
      if (errorMsg.includes('告警规则配置冲突') || errorMsg.includes('数据重复')) {
        window.$message?.error(errorMsg);
      } else {
        window.$message?.error('操作失败，请稍后重试');
      }
    }
  } catch (error) {
    console.error('提交失败:', error);
  } finally {
    submitLoading.value = false;
  }
}

watch(visible, () => {
  if (visible.value) {
    handleInitModel();
    restoreValidation();
  }
});
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="480" class="enhanced-drawer alert-theme">
    <NDrawerContent :title="title" :native-scrollbar="false" closable class="enhanced-drawer alert-theme">
      <div class="form-container">
        <!-- 提示信息 -->
        <NAlert v-if="isAdd" type="info" :show-icon="false" class="mb-4">
          <template #header>
            <div class="flex items-center gap-2">
              <NIcon size="16" color="#1890ff">
                <i class="i-material-symbols:lightbulb"></i>
              </NIcon>
              <span class="font-medium">使用建议</span>
            </div>
          </template>
          <div class="text-sm">
            <p>
              推荐使用
              <strong>配置向导</strong>
              创建规则，提供分步引导和智能配置建议。
            </p>
            <p>此表单适合快速编辑现有规则。</p>
          </div>
        </NAlert>

        <NForm ref="formRef" :model="model" :rules="formRules" label-width="120">
          <!-- 基础信息 -->
          <NDivider title-placement="left">
            <div class="flex items-center gap-2">
              <NIcon color="#3b82f6">
                <i class="i-material-symbols:info"></i>
              </NIcon>
              <span>基础信息</span>
            </div>
          </NDivider>

          <NFormItem label="规则类型" path="ruleCategory">
            <NSelect v-model:value="model.ruleCategory" :options="ruleCategoryOptions" placeholder="选择规则类型" :disabled="!isAdd" />
          </NFormItem>

          <NFormItem v-if="model.ruleCategory === 'SINGLE'" label="监控指标" path="physicalSign">
            <NSelect v-model:value="model.physicalSign" :options="healthDataOptions" placeholder="选择监控的健康指标" />
          </NFormItem>

          <NFormItem label="优先级" path="priorityLevel">
            <NSelect v-model:value="model.priorityLevel" :options="priorityOptions" placeholder="选择优先级" />
          </NFormItem>

          <NFormItem label="严重级别" path="level">
            <NSelect v-model:value="model.level" :options="severityOptions" placeholder="选择严重级别" />
          </NFormItem>

          <NFormItem label="规则状态" path="isEnabled">
            <NSwitch v-model:value="model.isEnabled" :rail-style="switchRailStyle">
              <template #checked>启用</template>
              <template #unchecked>禁用</template>
            </NSwitch>
          </NFormItem>

          <!-- 阈值配置 (仅单体征规则) -->
          <template v-if="model.ruleCategory === 'SINGLE'">
            <NDivider title-placement="left">
              <div class="flex items-center gap-2">
                <NIcon color="#10b981">
                  <i class="i-material-symbols:tune"></i>
                </NIcon>
                <span>阈值设置</span>
              </div>
            </NDivider>

            <NFormItem label="最小值" path="thresholdMin">
              <NInputNumber v-model:value="model.thresholdMin" placeholder="最小阈值" style="width: 100%" :min="0" />
            </NFormItem>

            <NFormItem label="最大值" path="thresholdMax">
              <NInputNumber v-model:value="model.thresholdMax" placeholder="最大阈值" style="width: 100%" :min="0" />
            </NFormItem>

            <NFormItem label="持续时长" path="trendDuration">
              <NInputNumber v-model:value="model.trendDuration" placeholder="异常持续分钟数" style="width: 100%" :min="1" :max="60" />
              <template #feedback>
                <span class="text-xs text-gray-500">监控指标异常需持续的分钟数</span>
              </template>
            </NFormItem>
          </template>

          <!-- 时间配置 -->
          <NDivider title-placement="left">
            <div class="flex items-center gap-2">
              <NIcon color="#fa8c16">
                <i class="i-material-symbols:schedule"></i>
              </NIcon>
              <span>时间配置</span>
            </div>
          </NDivider>

          <NFormItem label="时间窗口" path="timeWindowSeconds">
            <NInputNumber v-model:value="model.timeWindowSeconds" placeholder="检测时间窗口" style="width: 100%" :min="60" :max="3600" />
            <template #feedback>
              <span class="text-xs text-gray-500">数据检测的时间窗口，单位：秒</span>
            </template>
          </NFormItem>

          <NFormItem label="冷却期" path="cooldownSeconds">
            <NInputNumber v-model:value="model.cooldownSeconds" placeholder="告警冷却期" style="width: 100%" :min="300" :max="86400" />
            <template #feedback>
              <span class="text-xs text-gray-500">告警触发后的静默时间，单位：秒</span>
            </template>
          </NFormItem>

          <NFormItem label="生效时间">
            <NSpace>
              <NTimePicker v-model:value="model.effectiveTimeStart" placeholder="开始时间" format="HH:mm:ss" />
              <span>至</span>
              <NTimePicker v-model:value="model.effectiveTimeEnd" placeholder="结束时间" format="HH:mm:ss" />
            </NSpace>
            <template #feedback>
              <span class="text-xs text-gray-500">留空表示全天生效</span>
            </template>
          </NFormItem>

          <!-- 通知配置 -->
          <NDivider title-placement="left">
            <div class="flex items-center gap-2">
              <NIcon color="#722ed1">
                <i class="i-material-symbols:notifications"></i>
              </NIcon>
              <span>通知配置</span>
            </div>
          </NDivider>

          <NFormItem label="通知渠道" path="enabledChannels">
            <NCheckboxGroup v-model:value="model.enabledChannels">
              <NSpace vertical>
                <NCheckbox value="message" label="内部消息" />
                <NCheckbox value="wechat" label="微信通知" />
                <NCheckbox value="sms" label="短信通知" />
                <NCheckbox value="email" label="邮件通知" />
              </NSpace>
            </NCheckboxGroup>
          </NFormItem>

          <NFormItem label="告警消息" path="alertMessage">
            <NInput
              v-model:value="model.alertMessage"
              type="textarea"
              :rows="3"
              placeholder="请输入告警消息模板，支持变量：{device_sn}, {value}, {timestamp} 等"
              maxlength="200"
              show-count
            />
          </NFormItem>

          <!-- 高级配置 -->
          <NDivider title-placement="left">
            <div class="flex items-center gap-2">
              <NIcon color="#f56565">
                <i class="i-material-symbols:settings"></i>
              </NIcon>
              <span>高级配置</span>
            </div>
          </NDivider>

          <NFormItem v-if="model.ruleCategory === 'COMPOSITE'" label="条件表达式" path="conditionExpression">
            <NInput v-model:value="model.conditionExpression" type="textarea" :rows="4" placeholder="复合规则的条件表达式 (JSON格式)" disabled />
            <template #feedback>
              <span class="text-xs text-gray-500">复合规则需要使用配置向导创建</span>
            </template>
          </NFormItem>

          <NFormItem label="规则标签" path="ruleTags">
            <NInput v-model:value="model.ruleTags" placeholder="规则标签 (可选)" />
          </NFormItem>
        </NForm>

        <!-- 内联操作按钮 -->
        <div class="form-actions">
          <NSpace class="w-full justify-end">
            <NButton quaternary @click="closeDrawer">取消</NButton>
            <NButton type="primary" :loading="submitLoading" @click="handleSubmit">
              {{ isAdd ? '创建' : '更新' }}
            </NButton>
          </NSpace>
        </div>
      </div>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped>
.form-container {
  padding: 16px 0;
  min-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.form-actions {
  margin-top: 32px;
  padding: 20px 0 24px;
  border-top: 1px solid #e5e7eb;
  background: #fff;
  position: sticky;
  bottom: 0;
  z-index: 10;
}

/* 确保抽屉内容区域正确布局 */
:deep(.n-drawer-content) {
  height: 100vh;
  overflow: hidden;
}

:deep(.n-drawer-body-content-wrapper) {
  height: calc(100vh - 60px);
  overflow-y: auto;
  padding: 0 24px;
}

:deep(.n-divider .n-divider__title) {
  font-weight: 600;
  color: #1f2937;
}

:deep(.n-form-item-feedback__wrapper) {
  margin-top: 4px;
}

:deep(.n-checkbox .n-checkbox__label) {
  font-size: 14px;
  color: #374151;
}

:deep(.n-alert) {
  border-radius: 8px;
  border: 1px solid #bfdbfe;
}

:deep(.n-input__border),
:deep(.n-input__state-border) {
  border-radius: 6px;
}

:deep(.n-select .n-base-selection .n-base-selection-label) {
  border-radius: 6px;
}

:deep(.n-input-number .n-input .n-input-wrapper .n-input__input) {
  border-radius: 6px;
}

:deep(.n-time-picker .n-input .n-input-wrapper) {
  border-radius: 6px;
}
</style>
