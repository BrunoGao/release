<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { useMessage } from 'naive-ui';
import { useDict } from '@/hooks/business/dict';
import { fetchAddAlertRules } from '@/service/api';
import { useAuthStore } from '@/store/modules/auth';

interface Props {
  visible: boolean;
}

interface Emits {
  (e: 'update:visible', value: boolean): void;
  (e: 'success'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const message = useMessage();
const { dictOptions } = useDict();
const authStore = useAuthStore();

const visible = computed({
  get: () => props.visible,
  set: value => emit('update:visible', value)
});

// 表单引用
const basicFormRef = ref();
const conditionFormRef = ref();
const notificationFormRef = ref();

// 当前步骤
const currentStep = ref(1);
const currentStepStatus = ref<'process' | 'finish' | 'error'>('process');
const validating = ref(false);
const creating = ref(false);

// 规则类型配置
const ruleTypes = [
  {
    value: 'SINGLE',
    label: '单体征规则',
    description: '监控单一健康指标，当指标超出设定阈值时触发告警',
    features: ['简单易配置', '响应速度快', '适合基础监控'],
    useCase: '心率异常、血压异常、体温监控等单项指标监控',
    icon: 'i-material-symbols:person',
    color: '#3b82f6',
    tagType: 'primary',
    badge: '推荐'
  },
  {
    value: 'COMPOSITE',
    label: '复合规则',
    description: '监控多个健康指标的组合条件，支持AND/OR逻辑运算',
    features: ['多条件组合', '逻辑运算', '精准判断'],
    useCase: '心血管异常、综合健康评估、多指标联合预警',
    icon: 'i-material-symbols:group',
    color: '#fa8c16',
    tagType: 'warning',
    badge: '高级'
  },
  {
    value: 'COMPLEX',
    label: '复杂规则',
    description: '基于机器学习和复杂算法的智能告警规则',
    features: ['智能算法', '自适应学习', '预测性告警'],
    useCase: '健康趋势预测、异常模式识别、智能诊断',
    icon: 'i-material-symbols:psychology',
    color: '#722ed1',
    tagType: 'error',
    badge: '实验性'
  }
];

// 表单数据
const form = reactive({
  ruleCategory: 'SINGLE',
  ruleName: '',
  priorityLevel: 3,
  level: 'MEDIUM',
  timeWindowSeconds: 300,
  cooldownSeconds: 600,
  effectiveTimeStart: null,
  effectiveTimeEnd: null,
  effectiveDays: [],
  physicalSign: '',
  thresholdType: 'range',
  thresholdMin: null,
  thresholdMax: null,
  trendDuration: 1,
  conditions: [],
  logicalOperator: 'AND',
  enabledChannels: ['message'],
  alertMessage: '',
  customerId: authStore.userInfo?.customerId || 0
});

// 选项配置
const priorityOptions = [
  { label: '最高', value: 1 },
  { label: '高', value: 2 },
  { label: '中', value: 3 },
  { label: '低', value: 4 }
];

const severityOptions = [
  { label: '紧急', value: 'CRITICAL' },
  { label: '高', value: 'HIGH' },
  { label: '中', value: 'MEDIUM' },
  { label: '低', value: 'LOW' }
];

const healthDataOptions = [
  { label: '心率', value: 'heart_rate' },
  { label: '血氧', value: 'blood_oxygen' },
  { label: '体温', value: 'temperature' },
  { label: '收缩压', value: 'pressure_high' },
  { label: '舒张压', value: 'pressure_low' },
  { label: '步数', value: 'step' },
  { label: '睡眠', value: 'sleep' }
];

const operatorOptions = [
  { label: '大于 (>)', value: '>' },
  { label: '小于 (<)', value: '<' },
  { label: '大于等于 (>=)', value: '>=' },
  { label: '小于等于 (<=)', value: '<=' },
  { label: '等于 (=)', value: '=' },
  { label: '不等于 (!=)', value: '!=' }
];

// 表单验证规则
const basicRules = {
  ruleName: [
    { required: true, message: '请输入规则名称', trigger: 'blur' },
    { min: 2, max: 50, message: '规则名称长度为2-50个字符', trigger: 'blur' }
  ],
  priorityLevel: [{ required: true, type: 'number', message: '请选择优先级', trigger: 'change' }],
  level: [{ required: true, message: '请选择严重级别', trigger: 'change' }]
};

const conditionRules = {
  physicalSign: [{ required: true, message: '请选择监控指标', trigger: 'change' }]
};

const notificationRules = {
  enabledChannels: [{ required: true, type: 'array', min: 1, message: '请至少选择一个通知渠道', trigger: 'change' }]
};

// 方法定义
function selectRuleType(type: string) {
  form.ruleCategory = type;

  // 重置相关字段
  if (type === 'SINGLE') {
    form.conditions = [];
  } else if (type === 'COMPOSITE') {
    form.physicalSign = '';
    form.thresholdMin = null;
    form.thresholdMax = null;
    // 初始化一个条件
    if (form.conditions.length === 0) {
      addCondition();
    }
  }
}

function addCondition() {
  form.conditions.push({
    physicalSign: '',
    operator: '>',
    threshold: null,
    durationSeconds: 300
  });
}

function removeCondition(index: number) {
  form.conditions.splice(index, 1);
}

async function nextStep() {
  // 验证当前步骤
  let valid = true;

  validating.value = true;

  try {
    switch (currentStep.value) {
      case 1:
        if (!form.ruleCategory) {
          message.error('请选择规则类型');
          valid = false;
        }
        break;

      case 2:
        if (basicFormRef.value) {
          await basicFormRef.value.validate();
        }
        break;

      case 3:
        if (conditionFormRef.value) {
          await conditionFormRef.value.validate();
        }
        // 额外验证
        if (form.ruleCategory === 'SINGLE') {
          if (!form.physicalSign) {
            message.error('请选择监控指标');
            valid = false;
          }
          if (form.thresholdType === 'range' && (!form.thresholdMin || !form.thresholdMax)) {
            message.error('请设置阈值范围');
            valid = false;
          }
        } else if (form.ruleCategory === 'COMPOSITE') {
          if (form.conditions.length === 0) {
            message.error('请至少添加一个条件');
            valid = false;
          }
        }
        break;

      case 4:
        if (notificationFormRef.value) {
          await notificationFormRef.value.validate();
        }
        break;
    }

    if (valid) {
      currentStep.value++;
    }
  } catch (error) {
    // 验证失败
  } finally {
    validating.value = false;
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--;
  }
}

async function createRule() {
  creating.value = true;

  try {
    // 构建提交数据
    const submitData = {
      ...form,
      // 处理复合规则的条件表达式
      conditionExpression:
        form.ruleCategory === 'COMPOSITE'
          ? JSON.stringify({
              conditions: form.conditions,
              logical_operator: form.logicalOperator
            })
          : null,
      // 处理生效时间
      effectiveTimeStart: form.effectiveTimeStart ? new Date(form.effectiveTimeStart) : null,
      effectiveTimeEnd: form.effectiveTimeEnd ? new Date(form.effectiveTimeEnd) : null,
      effectiveDays: form.effectiveDays.join(','),
      // 处理通知渠道
      enabledChannels: JSON.stringify(form.enabledChannels),
      isEnabled: true
    };

    const { error } = await fetchAddAlertRules(submitData);

    if (!error) {
      message.success('告警规则创建成功！');
      emit('success');
      closeWizard();
    }
  } catch (error) {
    message.error('创建规则失败，请重试');
  } finally {
    creating.value = false;
  }
}

function closeWizard() {
  visible.value = false;
  // 重置表单
  resetForm();
}

function resetForm() {
  currentStep.value = 1;
  Object.assign(form, {
    ruleCategory: 'SINGLE',
    ruleName: '',
    priorityLevel: 3,
    level: 'MEDIUM',
    timeWindowSeconds: 300,
    cooldownSeconds: 600,
    effectiveTimeStart: null,
    effectiveTimeEnd: null,
    effectiveDays: [],
    physicalSign: '',
    thresholdType: 'range',
    thresholdMin: null,
    thresholdMax: null,
    trendDuration: 1,
    conditions: [],
    logicalOperator: 'AND',
    enabledChannels: ['message'],
    alertMessage: ''
  });
}

// 辅助方法
function generateMessagePreview() {
  const template = form.alertMessage || '健康指标异常告警：{device_sn} 的 {physical_sign} 数值为 {value}，触发时间：{timestamp}';
  return template
    .replace('{device_sn}', 'TEST001')
    .replace('{physical_sign}', getHealthDataLabel(form.physicalSign) || '心率')
    .replace('{value}', '120')
    .replace('{timestamp}', new Date().toLocaleString());
}

function getRuleTypeLabel(category: string) {
  return ruleTypes.find(t => t.value === category)?.label || category;
}

function getPriorityLabel(priority: number) {
  return priorityOptions.find(p => p.value === priority)?.label || String(priority);
}

function getSeverityLabel(level: string) {
  return severityOptions.find(s => s.value === level)?.label || level;
}

function getHealthDataLabel(sign: string) {
  return healthDataOptions.find(h => h.value === sign)?.label || sign;
}

function getThresholdLabel() {
  if (form.thresholdType === 'range' && form.thresholdMin && form.thresholdMax) {
    return `${form.thresholdMin} - ${form.thresholdMax}`;
  } else if (form.thresholdType === 'min' && form.thresholdMin) {
    return `≥ ${form.thresholdMin}`;
  } else if (form.thresholdType === 'max' && form.thresholdMax) {
    return `≤ ${form.thresholdMax}`;
  }
  return '未设置';
}

function getChannelsLabel() {
  const channelMap = {
    message: '内部消息',
    wechat: '微信',
    sms: '短信',
    email: '邮件'
  };
  return form.enabledChannels.map(ch => channelMap[ch] || ch).join('、');
}

// 监听步骤变化
watch(currentStep, newStep => {
  if (newStep === 5) {
    currentStepStatus.value = 'finish';
  } else {
    currentStepStatus.value = 'process';
  }
});
</script>

<template>
  <NModal v-model:show="visible" preset="dialog" class="alert-rule-wizard">
    <template #header>
      <div class="flex items-center gap-3">
        <NIcon size="24" color="#3b82f6">
          <i class="i-material-symbols:auto-awesome"></i>
        </NIcon>
        <span class="text-xl font-bold">告警规则配置向导</span>
      </div>
    </template>

    <div class="wizard-content">
      <!-- 步骤指示器 -->
      <NSteps :current="currentStep" :status="currentStepStatus" size="small" class="mb-6">
        <NStep title="规则类型">
          <template #icon>
            <NIcon><i class="i-material-symbols:category"></i></NIcon>
          </template>
        </NStep>
        <NStep title="基础配置">
          <template #icon>
            <NIcon><i class="i-material-symbols:settings"></i></NIcon>
          </template>
        </NStep>
        <NStep title="条件设置">
          <template #icon>
            <NIcon><i class="i-material-symbols:rule"></i></NIcon>
          </template>
        </NStep>
        <NStep title="通知配置">
          <template #icon>
            <NIcon><i class="i-material-symbols:notifications"></i></NIcon>
          </template>
        </NStep>
        <NStep title="确认创建">
          <template #icon>
            <NIcon><i class="i-material-symbols:check-circle"></i></NIcon>
          </template>
        </NStep>
      </NSteps>

      <!-- 步骤内容 -->
      <div class="step-content">
        <!-- 步骤1: 选择规则类型 -->
        <div v-show="currentStep === 1" class="step-panel">
          <div class="step-title">
            <h3>选择告警规则类型</h3>
            <p class="text-sm text-gray-500">不同类型的规则适用于不同的监控场景</p>
          </div>

          <div class="rule-type-cards">
            <div
              v-for="type in ruleTypes"
              :key="type.value"
              class="rule-type-card"
              :class="{ active: form.ruleCategory === type.value }"
              @click="selectRuleType(type.value)"
            >
              <div class="card-header">
                <NIcon :size="28" :color="type.color">
                  <i :class="type.icon"></i>
                </NIcon>
                <h4>{{ type.label }}</h4>
                <NTag :type="type.tagType" size="small">{{ type.badge }}</NTag>
              </div>
              <div class="card-content">
                <p class="description">{{ type.description }}</p>
                <div class="features">
                  <div v-for="feature in type.features" :key="feature" class="feature-item">
                    <NIcon size="14" color="#10b981">
                      <i class="i-material-symbols:check"></i>
                    </NIcon>
                    <span>{{ feature }}</span>
                  </div>
                </div>
                <div class="use-cases">
                  <strong>适用场景：</strong>
                  <span class="text-sm text-gray-600">{{ type.useCase }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 步骤2: 基础配置 -->
        <div v-show="currentStep === 2" class="step-panel">
          <div class="step-title">
            <h3>基础信息配置</h3>
            <p class="text-sm text-gray-500">设置规则的基本属性和参数</p>
          </div>

          <NForm ref="basicFormRef" :model="form" :rules="basicRules" class="basic-config-form">
            <div class="form-grid">
              <NFormItem label="规则名称" path="ruleName" class="form-item">
                <NInput v-model:value="form.ruleName" placeholder="请输入规则名称" maxlength="50" show-count />
              </NFormItem>

              <NFormItem label="优先级" path="priorityLevel" class="form-item">
                <NSelect v-model:value="form.priorityLevel" :options="priorityOptions" placeholder="选择优先级" />
              </NFormItem>

              <NFormItem label="严重级别" path="level" class="form-item">
                <NSelect v-model:value="form.level" :options="severityOptions" placeholder="选择严重级别" />
              </NFormItem>

              <NFormItem label="时间窗口" path="timeWindowSeconds" class="form-item">
                <NInputNumber v-model:value="form.timeWindowSeconds" :min="60" :max="3600" placeholder="检测时间窗口(秒)" style="width: 100%" />
              </NFormItem>

              <NFormItem label="冷却期" path="cooldownSeconds" class="form-item">
                <NInputNumber v-model:value="form.cooldownSeconds" :min="300" :max="86400" placeholder="告警冷却期(秒)" style="width: 100%" />
              </NFormItem>

              <NFormItem label="生效时间" path="effectiveTime" class="form-item-full">
                <NSpace>
                  <NTimePicker v-model:value="form.effectiveTimeStart" placeholder="开始时间" format="HH:mm:ss" />
                  <span>至</span>
                  <NTimePicker v-model:value="form.effectiveTimeEnd" placeholder="结束时间" format="HH:mm:ss" />
                </NSpace>
              </NFormItem>

              <NFormItem label="生效星期" path="effectiveDays" class="form-item-full">
                <NCheckboxGroup v-model:value="form.effectiveDays">
                  <NSpace>
                    <NCheckbox value="1" label="周一" />
                    <NCheckbox value="2" label="周二" />
                    <NCheckbox value="3" label="周三" />
                    <NCheckbox value="4" label="周四" />
                    <NCheckbox value="5" label="周五" />
                    <NCheckbox value="6" label="周六" />
                    <NCheckbox value="7" label="周日" />
                  </NSpace>
                </NCheckboxGroup>
              </NFormItem>
            </div>
          </NForm>
        </div>

        <!-- 步骤3: 条件设置 -->
        <div v-show="currentStep === 3" class="step-panel">
          <div class="step-title">
            <h3>告警条件设置</h3>
            <p class="text-sm text-gray-500">根据规则类型配置触发条件</p>
          </div>

          <!-- 单体征规则配置 -->
          <div v-if="form.ruleCategory === 'SINGLE'" class="condition-config">
            <NForm ref="conditionFormRef" :model="form" :rules="conditionRules">
              <div class="form-grid">
                <NFormItem label="监控指标" path="physicalSign" class="form-item">
                  <NSelect v-model:value="form.physicalSign" :options="healthDataOptions" placeholder="选择监控的健康指标" />
                </NFormItem>

                <NFormItem label="阈值类型" path="thresholdType" class="form-item">
                  <NRadioGroup v-model:value="form.thresholdType">
                    <NSpace>
                      <NRadio value="range" label="范围检测" />
                      <NRadio value="min" label="最小值" />
                      <NRadio value="max" label="最大值" />
                    </NSpace>
                  </NRadioGroup>
                </NFormItem>

                <NFormItem v-if="form.thresholdType === 'range' || form.thresholdType === 'min'" label="最小值" path="thresholdMin" class="form-item">
                  <NInputNumber v-model:value="form.thresholdMin" placeholder="最小阈值" style="width: 100%" />
                </NFormItem>

                <NFormItem v-if="form.thresholdType === 'range' || form.thresholdType === 'max'" label="最大值" path="thresholdMax" class="form-item">
                  <NInputNumber v-model:value="form.thresholdMax" placeholder="最大阈值" style="width: 100%" />
                </NFormItem>

                <NFormItem label="持续时长" path="trendDuration" class="form-item">
                  <NInputNumber v-model:value="form.trendDuration" :min="1" :max="60" placeholder="异常持续分钟数" style="width: 100%" />
                </NFormItem>
              </div>
            </NForm>
          </div>

          <!-- 复合规则配置 -->
          <div v-if="form.ruleCategory === 'COMPOSITE'" class="condition-config">
            <div class="composite-conditions">
              <div class="conditions-header">
                <h4>复合条件设置</h4>
                <NButton type="primary" size="small" @click="addCondition">
                  <template #icon>
                    <NIcon><i class="i-material-symbols:add"></i></NIcon>
                  </template>
                  添加条件
                </NButton>
              </div>

              <div v-for="(condition, index) in form.conditions" :key="index" class="condition-item">
                <NCard size="small" class="condition-card">
                  <template #header>
                    <div class="flex items-center justify-between">
                      <span>条件 {{ index + 1 }}</span>
                      <NButton v-if="form.conditions.length > 1" type="error" text size="small" @click="removeCondition(index)">
                        <template #icon>
                          <NIcon><i class="i-material-symbols:delete"></i></NIcon>
                        </template>
                      </NButton>
                    </div>
                  </template>

                  <div class="condition-form">
                    <NFormItem label="监控指标">
                      <NSelect v-model:value="condition.physicalSign" :options="healthDataOptions" placeholder="选择监控指标" />
                    </NFormItem>

                    <NFormItem label="操作符">
                      <NSelect v-model:value="condition.operator" :options="operatorOptions" placeholder="选择比较操作符" />
                    </NFormItem>

                    <NFormItem label="阈值">
                      <NInputNumber v-model:value="condition.threshold" placeholder="设置阈值" style="width: 100%" />
                    </NFormItem>

                    <NFormItem label="持续时长">
                      <NInputNumber v-model:value="condition.durationSeconds" :min="60" :max="3600" placeholder="持续时长(秒)" style="width: 100%" />
                    </NFormItem>
                  </div>
                </NCard>

                <!-- 逻辑连接符 -->
                <div v-if="index < form.conditions.length - 1" class="logical-operator">
                  <NRadioGroup v-model:value="form.logicalOperator">
                    <NSpace>
                      <NRadio value="AND" label="并且(AND)" />
                      <NRadio value="OR" label="或者(OR)" />
                    </NSpace>
                  </NRadioGroup>
                </div>
              </div>
            </div>
          </div>

          <!-- 复杂规则配置 -->
          <div v-if="form.ruleCategory === 'COMPLEX'" class="condition-config">
            <NAlert type="info" class="mb-4">
              <template #icon>
                <NIcon><i class="i-material-symbols:info"></i></NIcon>
              </template>
              复杂规则功能正在开发中，敬请期待！
            </NAlert>
          </div>
        </div>

        <!-- 步骤4: 通知配置 -->
        <div v-show="currentStep === 4" class="step-panel">
          <div class="step-title">
            <h3>通知渠道配置</h3>
            <p class="text-sm text-gray-500">设置告警的通知方式和消息内容</p>
          </div>

          <NForm ref="notificationFormRef" :model="form" :rules="notificationRules">
            <div class="notification-config">
              <NFormItem label="通知渠道" path="enabledChannels">
                <NCheckboxGroup v-model:value="form.enabledChannels">
                  <NSpace vertical>
                    <NCheckbox value="message" label="内部消息">
                      <template #default>
                        <div class="channel-item">
                          <NIcon size="18" color="#1890ff">
                            <i class="i-material-symbols:message"></i>
                          </NIcon>
                          <span>内部消息</span>
                          <NTag size="small" type="info">实时</NTag>
                        </div>
                      </template>
                    </NCheckbox>

                    <NCheckbox value="wechat" label="微信通知">
                      <template #default>
                        <div class="channel-item">
                          <NIcon size="18" color="#10b981">
                            <i class="i-material-symbols:chat"></i>
                          </NIcon>
                          <span>微信通知</span>
                          <NTag size="small" type="success">推荐</NTag>
                        </div>
                      </template>
                    </NCheckbox>

                    <NCheckbox value="sms" label="短信通知">
                      <template #default>
                        <div class="channel-item">
                          <NIcon size="18" color="#fa8c16">
                            <i class="i-material-symbols:sms"></i>
                          </NIcon>
                          <span>短信通知</span>
                          <NTag size="small" type="warning">收费</NTag>
                        </div>
                      </template>
                    </NCheckbox>

                    <NCheckbox value="email" label="邮件通知">
                      <template #default>
                        <div class="channel-item">
                          <NIcon size="18" color="#722ed1">
                            <i class="i-material-symbols:email"></i>
                          </NIcon>
                          <span>邮件通知</span>
                          <NTag size="small" type="default">延时</NTag>
                        </div>
                      </template>
                    </NCheckbox>
                  </NSpace>
                </NCheckboxGroup>
              </NFormItem>

              <NFormItem label="告警消息模板" path="alertMessage">
                <NInput
                  v-model:value="form.alertMessage"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入告警消息模板，支持变量：{device_sn}, {value}, {timestamp} 等"
                  maxlength="200"
                  show-count
                />
              </NFormItem>

              <NFormItem label="消息预览">
                <div class="message-preview">
                  <h5>预览效果：</h5>
                  <div class="preview-content">
                    {{ generateMessagePreview() }}
                  </div>
                </div>
              </NFormItem>
            </div>
          </NForm>
        </div>

        <!-- 步骤5: 确认创建 -->
        <div v-show="currentStep === 5" class="step-panel">
          <div class="step-title">
            <h3>确认配置信息</h3>
            <p class="text-sm text-gray-500">请确认以下配置信息无误后创建规则</p>
          </div>

          <div class="confirmation-content">
            <NCard class="config-summary">
              <template #header>
                <div class="flex items-center gap-2">
                  <NIcon color="#3b82f6"><i class="i-material-symbols:summarize"></i></NIcon>
                  <span>配置摘要</span>
                </div>
              </template>

              <div class="summary-sections">
                <!-- 基础信息 -->
                <div class="summary-section">
                  <h4>基础信息</h4>
                  <div class="summary-items">
                    <div class="summary-item">
                      <span class="label">规则类型：</span>
                      <span class="value">{{ getRuleTypeLabel(form.ruleCategory) }}</span>
                    </div>
                    <div class="summary-item">
                      <span class="label">规则名称：</span>
                      <span class="value">{{ form.ruleName || '未设置' }}</span>
                    </div>
                    <div class="summary-item">
                      <span class="label">优先级：</span>
                      <span class="value">{{ getPriorityLabel(form.priorityLevel) }}</span>
                    </div>
                    <div class="summary-item">
                      <span class="label">严重级别：</span>
                      <span class="value">{{ getSeverityLabel(form.level) }}</span>
                    </div>
                  </div>
                </div>

                <!-- 条件设置 -->
                <div class="summary-section">
                  <h4>条件设置</h4>
                  <div class="summary-items">
                    <div v-if="form.ruleCategory === 'SINGLE'" class="summary-item">
                      <span class="label">监控指标：</span>
                      <span class="value">{{ getHealthDataLabel(form.physicalSign) }}</span>
                    </div>
                    <div v-if="form.ruleCategory === 'SINGLE'" class="summary-item">
                      <span class="label">阈值范围：</span>
                      <span class="value">{{ getThresholdLabel() }}</span>
                    </div>
                    <div v-if="form.ruleCategory === 'COMPOSITE'" class="summary-item">
                      <span class="label">复合条件：</span>
                      <span class="value">{{ form.conditions.length }} 个条件，{{ form.logicalOperator }} 逻辑</span>
                    </div>
                  </div>
                </div>

                <!-- 通知配置 -->
                <div class="summary-section">
                  <h4>通知配置</h4>
                  <div class="summary-items">
                    <div class="summary-item">
                      <span class="label">通知渠道：</span>
                      <span class="value">{{ getChannelsLabel() }}</span>
                    </div>
                    <div class="summary-item">
                      <span class="label">消息模板：</span>
                      <span class="value">{{ form.alertMessage || '使用默认模板' }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </NCard>
          </div>
        </div>
      </div>
    </div>

    <template #action>
      <div class="wizard-actions">
        <NButton v-if="currentStep > 1" @click="prevStep">
          <template #icon>
            <NIcon><i class="i-material-symbols:arrow-back"></i></NIcon>
          </template>
          上一步
        </NButton>

        <NButton v-if="currentStep < 5" type="primary" :loading="validating" @click="nextStep">
          下一步
          <template #icon>
            <NIcon><i class="i-material-symbols:arrow-forward"></i></NIcon>
          </template>
        </NButton>

        <NButton v-if="currentStep === 5" type="primary" :loading="creating" @click="createRule">
          <template #icon>
            <NIcon><i class="i-material-symbols:check"></i></NIcon>
          </template>
          创建规则
        </NButton>

        <NButton @click="closeWizard">取消</NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.alert-rule-wizard :deep(.n-dialog) {
  max-width: 900px;
  width: 90vw;
}

.wizard-content {
  max-height: 70vh;
  overflow-y: auto;
}

.step-content {
  min-height: 400px;
  padding: 20px 0;
}

.step-panel {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.step-title {
  text-align: center;
  margin-bottom: 24px;
}

.step-title h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

/* 规则类型卡片 */
.rule-type-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 24px;
}

.rule-type-card {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.rule-type-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.rule-type-card.active {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.card-header h4 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  flex: 1;
}

.card-content .description {
  color: #6b7280;
  margin-bottom: 16px;
  line-height: 1.5;
}

.features {
  margin-bottom: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #374151;
}

.use-cases {
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  font-size: 13px;
  color: #4b5563;
}

/* 表单样式 */
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.form-item-full {
  grid-column: 1 / -1;
}

.basic-config-form {
  background: #f9fafb;
  padding: 24px;
  border-radius: 8px;
}

/* 复合条件样式 */
.composite-conditions {
  background: #f9fafb;
  padding: 24px;
  border-radius: 8px;
}

.conditions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.conditions-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.condition-item {
  margin-bottom: 16px;
}

.condition-card {
  border: 1px solid #d1d5db;
  border-radius: 8px;
}

.condition-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.logical-operator {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 12px;
  background: white;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  margin: 8px 0;
}

/* 通知配置样式 */
.notification-config {
  background: #f9fafb;
  padding: 24px;
  border-radius: 8px;
}

.channel-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  margin-bottom: 8px;
}

.message-preview {
  background: #f3f4f6;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
}

.message-preview h5 {
  margin-bottom: 8px;
  font-weight: 600;
  color: #374151;
}

.preview-content {
  background: white;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  font-family: monospace;
  color: #1f2937;
}

/* 确认页面样式 */
.config-summary {
  background: #f9fafb;
}

.summary-sections {
  display: grid;
  gap: 20px;
}

.summary-section {
  background: white;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.summary-section h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.summary-items {
  display: grid;
  gap: 8px;
}

.summary-item {
  display: flex;
  align-items: center;
}

.summary-item .label {
  font-weight: 500;
  color: #6b7280;
  min-width: 100px;
}

.summary-item .value {
  color: #1f2937;
  font-weight: 500;
}

/* 操作按钮样式 */
.wizard-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 16px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .rule-type-cards {
    grid-template-columns: 1fr;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .condition-form {
    grid-template-columns: 1fr;
  }

  .wizard-actions {
    justify-content: center;
    flex-wrap: wrap;
  }
}
</style>
