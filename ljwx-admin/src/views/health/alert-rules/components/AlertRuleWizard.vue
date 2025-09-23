<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue';
import { useMessage } from 'naive-ui';
import { fetchAddAlertRules, fetchUpdateAlertRulesInfo } from '@/service/api/health/alert-rules';

const props = defineProps<{
  visible: boolean;
  editRule?: any;
}>();

const emit = defineEmits<{
  'update:visible': [value: boolean];
  success: [];
}>();

const message = useMessage();
const formRef = ref();
const loading = ref(false);
const currentStep = ref(0);

// 表单数据
const formData = reactive({
  id: null as any,
  customerId: null as any,
  ruleType: 'metric',
  ruleCategory: 'SINGLE',
  physicalSign: '',
  thresholdMin: null as any,
  thresholdMax: null as any,
  alertMessage: '',
  severityLevel: 'moderate',
  level: 'moderate',
  isEnabled: true,
  timeWindowSeconds: 300,
  cooldownSeconds: 600,
  priorityLevel: 3,
  effectiveDays: '1,2,3,4,5,6,7',
  trendDuration: 1,
  enabledChannels: ['message'] as string[],
  conditions: [] as any[]
});

// 生理指标选项
const physicalSignOptions = [
  { label: '心率', value: 'heart_rate' },
  { label: '血氧浓度', value: 'blood_oxygen' },
  { label: '体温', value: 'temperature' },
  { label: '收缩压', value: 'pressure_high' },
  { label: '舒张压', value: 'pressure_low' },
  { label: '步数', value: 'step' },
  { label: '卡路里', value: 'calorie' },
  { label: '距离', value: 'distance' },
  { label: '压力指数', value: 'stress' }
];

// 严重程度选项
const severityOptions = [
  { label: '信息', value: 'info' },
  { label: '一般', value: 'minor' },
  { label: '重要', value: 'major' },
  { label: '紧急', value: 'critical' }
];

// 通知渠道选项
const channelOptions = [
  { label: '内部消息', value: 'message' },
  { label: '微信', value: 'wechat' },
  { label: '短信', value: 'sms' },
  { label: '邮件', value: 'email' }
];

// 星期选项
const dayOptions = [
  { label: '周一', value: '1' },
  { label: '周二', value: '2' },
  { label: '周三', value: '3' },
  { label: '周四', value: '4' },
  { label: '周五', value: '5' },
  { label: '周六', value: '6' },
  { label: '周日', value: '7' }
];

// 操作符选项
const operatorOptions = [
  { label: '大于 >', value: '>' },
  { label: '小于 <', value: '<' },
  { label: '大于等于 >=', value: '>=' },
  { label: '小于等于 <=', value: '<=' },
  { label: '等于 ==', value: '==' },
  { label: '不等于 !=', value: '!=' }
];

// 表单验证规则
const formRules = {
  ruleCategory: {
    required: true,
    message: '请选择规则类型'
  },
  physicalSign: {
    required: true,
    message: '请选择监测指标',
    trigger: ['blur', 'change']
  },
  thresholdMin: {
    required: true,
    type: 'number',
    message: '请输入最小阈值',
    trigger: ['blur', 'change']
  },
  thresholdMax: {
    required: true,
    type: 'number',
    message: '请输入最大阈值',
    trigger: ['blur', 'change']
  },
  severityLevel: {
    required: true,
    message: '请选择严重程度'
  }
};

// 是否为编辑模式
const isEditMode = computed(() => !!props.editRule?.id);

// 步骤配置
const steps = [
  { title: '基础信息', description: '配置规则基本信息' },
  { title: '条件设置', description: '设置触发条件' },
  { title: '高级配置', description: '通知和时间设置' },
  { title: '确认保存', description: '确认规则配置' }
];

// 监听编辑规则变化
watch(() => props.editRule, (newRule) => {
  if (newRule) {
    Object.assign(formData, {
      ...newRule,
      enabledChannels: newRule.enabledChannels || ['message'],
      effectiveDays: newRule.effectiveDays || '1,2,3,4,5,6,7'
    });
  } else {
    resetForm();
  }
}, { immediate: true });

// 监听显示状态
watch(() => props.visible, (visible) => {
  if (visible) {
    currentStep.value = 0;
    if (!props.editRule) {
      resetForm();
    }
  }
});

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    id: null,
    customerId: null,
    ruleType: 'metric',
    ruleCategory: 'SINGLE',
    physicalSign: '',
    thresholdMin: null,
    thresholdMax: null,
    alertMessage: '',
    severityLevel: 'moderate',
    level: 'moderate',
    isEnabled: true,
    timeWindowSeconds: 300,
    cooldownSeconds: 600,
    priorityLevel: 3,
    effectiveDays: '1,2,3,4,5,6,7',
    trendDuration: 1,
    enabledChannels: ['message'],
    conditions: []
  });
};

// 添加复合条件
const addCondition = () => {
  formData.conditions.push({
    physical_sign: '',
    operator: '>',
    threshold: null,
    duration_seconds: 60
  });
};

// 删除复合条件
const removeCondition = (index: number) => {
  formData.conditions.splice(index, 1);
};

// 下一步
const nextStep = async () => {
  if (currentStep.value === 0) {
    // 验证基础信息
    try {
      await formRef.value?.validate();
    } catch (error) {
      return;
    }
  }
  
  if (currentStep.value < steps.length - 1) {
    currentStep.value++;
  }
};

// 上一步
const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--;
  }
};

// 保存规则
const handleSave = async () => {
  loading.value = true;
  try {
    // 最终验证
    await formRef.value?.validate();
    
    // 准备提交数据
    const submitData = {
      ...formData,
      level: formData.severityLevel, // 同步严重程度字段
    };
    
    // 处理复合规则的条件表达式
    if (formData.ruleCategory === 'COMPOSITE' && formData.conditions.length > 0) {
      (submitData as any).conditionExpression = {
        conditions: formData.conditions,
        logical_operator: 'AND'
      };
    }
    
    // 调用API
    if (isEditMode.value) {
      await fetchUpdateAlertRulesInfo(submitData);
      message.success('规则更新成功');
    } else {
      await fetchAddAlertRules(submitData);
      message.success('规则创建成功');
    }
    
    emit('success');
    emit('update:visible', false);
  } catch (error: any) {
    message.error(`保存失败：${error.message || '未知错误'}`);
  } finally {
    loading.value = false;
  }
};

// 关闭向导
const handleClose = () => {
  emit('update:visible', false);
};
</script>

<template>
  <div class="alert-rule-wizard">
    <!-- 步骤条 -->
    <div class="steps-container mb-6">
      <NSteps :current="currentStep" size="small">
        <NStep v-for="(step, index) in steps" :key="index" :title="step.title" :description="step.description" />
      </NSteps>
    </div>

    <!-- 表单内容 -->
    <NForm ref="formRef" :model="formData" :rules="formRules" label-placement="left" label-width="120px">
      <!-- 第一步：基础信息 -->
      <div v-show="currentStep === 0" class="step-content">
        <NDivider title-placement="left">基础信息</NDivider>
        
        <NFormItem label="规则类型" path="ruleCategory">
          <NRadioGroup v-model:value="formData.ruleCategory">
            <NRadio value="SINGLE">单体征规则</NRadio>
            <NRadio value="COMPOSITE">复合规则</NRadio>
          </NRadioGroup>
        </NFormItem>

        <NFormItem v-if="formData.ruleCategory === 'SINGLE'" label="监测指标" path="physicalSign">
          <NSelect
            v-model:value="formData.physicalSign"
            :options="physicalSignOptions"
            placeholder="请选择监测指标"
            clearable
          />
        </NFormItem>

        <NFormItem label="严重程度" path="severityLevel">
          <NSelect
            v-model:value="formData.severityLevel"
            :options="severityOptions"
            placeholder="请选择严重程度"
            @update:value="formData.level = formData.severityLevel"
          />
        </NFormItem>

        <NFormItem label="优先级">
          <NRate v-model:value="formData.priorityLevel" :count="5" />
          <span class="ml-2 text-sm text-gray-500">{{ formData.priorityLevel }} 星</span>
        </NFormItem>

        <NFormItem label="启用状态">
          <NSwitch v-model:value="formData.isEnabled">
            <template #checked>启用</template>
            <template #unchecked>禁用</template>
          </NSwitch>
        </NFormItem>
      </div>

      <!-- 第二步：条件设置 -->
      <div v-show="currentStep === 1" class="step-content">
        <NDivider title-placement="left">条件设置</NDivider>

        <!-- 单体征规则 -->
        <div v-if="formData.ruleCategory === 'SINGLE'">
          <NFormItem label="最小阈值" path="thresholdMin">
            <NInputNumber v-model:value="formData.thresholdMin" placeholder="请输入最小阈值" style="width: 100%" />
          </NFormItem>

          <NFormItem label="最大阈值" path="thresholdMax">
            <NInputNumber v-model:value="formData.thresholdMax" placeholder="请输入最大阈值" style="width: 100%" />
          </NFormItem>

          <NFormItem label="连续次数">
            <NInputNumber v-model:value="formData.trendDuration" placeholder="连续触发次数" :min="1" style="width: 100%" />
            <div class="text-sm text-gray-500 mt-1">连续多少次超出阈值后触发告警</div>
          </NFormItem>
        </div>

        <!-- 复合规则 -->
        <div v-if="formData.ruleCategory === 'COMPOSITE'">
          <NFormItem label="复合条件">
            <div class="w-full">
              <div v-for="(condition, index) in formData.conditions" :key="index" class="condition-item mb-4 p-4 border border-gray-200 rounded">
                <div class="grid grid-cols-4 gap-4 items-center">
                  <NSelect
                    v-model:value="condition.physical_sign"
                    :options="physicalSignOptions"
                    placeholder="监测指标"
                  />
                  <NSelect
                    v-model:value="condition.operator"
                    :options="operatorOptions"
                    placeholder="操作符"
                  />
                  <NInputNumber
                    v-model:value="condition.threshold"
                    placeholder="阈值"
                  />
                  <NButton type="error" size="small" @click="removeCondition(index)">删除</NButton>
                </div>
                <div class="mt-2">
                  <NInputNumber
                    v-model:value="condition.duration_seconds"
                    placeholder="持续时间(秒)"
                    :min="1"
                    style="width: 200px"
                  />
                  <span class="ml-2 text-sm text-gray-500">持续时间</span>
                </div>
              </div>
              <NButton type="dashed" @click="addCondition" class="w-full">
                <template #icon>
                  <NIcon><icon-ic:baseline-add /></NIcon>
                </template>
                添加条件
              </NButton>
            </div>
          </NFormItem>
        </div>
      </div>

      <!-- 第三步：高级配置 -->
      <div v-show="currentStep === 2" class="step-content">
        <NDivider title-placement="left">高级配置</NDivider>

        <NFormItem label="通知渠道">
          <NCheckboxGroup v-model:value="formData.enabledChannels">
            <NCheckbox v-for="channel in channelOptions" :key="channel.value" :value="channel.value">
              {{ channel.label }}
            </NCheckbox>
          </NCheckboxGroup>
        </NFormItem>

        <NFormItem label="生效时间">
          <NCheckboxGroup v-model:value="formData.effectiveDays" style="flex-wrap: wrap;">
            <NCheckbox v-for="day in dayOptions" :key="day.value" :value="day.value">
              {{ day.label }}
            </NCheckbox>
          </NCheckboxGroup>
        </NFormItem>

        <NFormItem label="时间窗口">
          <NInputNumber v-model:value="formData.timeWindowSeconds" placeholder="时间窗口(秒)" :min="60" style="width: 100%" />
          <div class="text-sm text-gray-500 mt-1">规则评估的时间窗口，单位：秒</div>
        </NFormItem>

        <NFormItem label="冷却时间">
          <NInputNumber v-model:value="formData.cooldownSeconds" placeholder="冷却时间(秒)" :min="60" style="width: 100%" />
          <div class="text-sm text-gray-500 mt-1">告警触发后的冷却时间，避免重复告警</div>
        </NFormItem>

        <NFormItem label="告警消息">
          <NInput
            v-model:value="formData.alertMessage"
            type="textarea"
            placeholder="请输入告警消息模板，支持变量：{device_sn}, {value}, {timestamp}"
            :rows="3"
          />
        </NFormItem>
      </div>

      <!-- 第四步：确认保存 -->
      <div v-show="currentStep === 3" class="step-content">
        <NDivider title-placement="left">确认配置</NDivider>
        
        <NDescriptions :column="2" bordered>
          <NDescriptionsItem label="规则类型">
            {{ formData.ruleCategory === 'SINGLE' ? '单体征规则' : '复合规则' }}
          </NDescriptionsItem>
          <NDescriptionsItem label="严重程度">
            {{ severityOptions.find(item => item.value === formData.severityLevel)?.label }}
          </NDescriptionsItem>
          <NDescriptionsItem label="优先级">
            <NRate :value="formData.priorityLevel" readonly :count="5" size="small" />
          </NDescriptionsItem>
          <NDescriptionsItem label="状态">
            {{ formData.isEnabled ? '启用' : '禁用' }}
          </NDescriptionsItem>
          <NDescriptionsItem v-if="formData.ruleCategory === 'SINGLE'" label="监测指标">
            {{ physicalSignOptions.find(item => item.value === formData.physicalSign)?.label }}
          </NDescriptionsItem>
          <NDescriptionsItem v-if="formData.ruleCategory === 'SINGLE'" label="阈值范围">
            {{ formData.thresholdMin }} ~ {{ formData.thresholdMax }}
          </NDescriptionsItem>
          <NDescriptionsItem label="通知渠道" :span="2">
            <NSpace>
              <NTag v-for="channel in formData.enabledChannels" :key="channel" size="small">
                {{ channelOptions.find(item => item.value === channel)?.label }}
              </NTag>
            </NSpace>
          </NDescriptionsItem>
        </NDescriptions>
      </div>
    </NForm>

    <!-- 操作按钮 -->
    <div class="action-buttons mt-6 flex justify-between">
      <div>
        <NButton v-if="currentStep > 0" @click="prevStep">上一步</NButton>
      </div>
      <NSpace>
        <NButton @click="handleClose">取消</NButton>
        <NButton v-if="currentStep < steps.length - 1" type="primary" @click="nextStep">下一步</NButton>
        <NButton v-else type="primary" :loading="loading" @click="handleSave">
          {{ isEditMode ? '更新规则' : '创建规则' }}
        </NButton>
      </NSpace>
    </div>
  </div>
</template>

<style scoped>
.text-primary {
  color: #18a058;
}
</style>
