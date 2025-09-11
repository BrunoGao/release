<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { NDrawer, NDrawerContent, NForm, NFormItem, NInput, NSelect, NInputNumber, NSwitch, NButton, NSpace, NDivider, NAlert, NCard, NDescriptions, NDescriptionsItem, NTag } from 'naive-ui';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
// Using createRequiredRule from useFormRules hook instead
import { $t } from '@/locales';
import { fetchAddAlertAutoProcess, fetchUpdateAlertAutoProcess } from '@/service/api/health/alert-auto-process';

defineOptions({
  name: 'AlertAutoProcessOperateDrawer'
});

interface Props {
  /** 弹窗可见性 */
  visible: boolean;
  /** 操作类型 */
  operateType: NaiveUI.TableOperateType;
  /** 编辑的表格行数据 */
  rowData?: Api.Health.AlertAutoProcess | null;
}

interface Emits {
  (e: 'update:visible', visible: boolean): void;
  (e: 'submitted'): void;
}

const emit = defineEmits<Emits>();
const props = withDefaults(defineProps<Props>(), {
  rowData: null
});

const visible = defineModel<boolean>('visible', {
  default: false
});

const { formRef, validate, restoreValidation } = useNaiveForm();
const { createRequiredRule } = useFormRules();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: '新增自动处理规则',
    edit: '编辑自动处理规则',
    view: '查看自动处理规则'
  };
  return titles[props.operateType];
});

const isEdit = computed(() => props.operateType === 'edit');
const isView = computed(() => props.operateType === 'view');

// 表单数据
const model: Api.Health.AlertAutoProcessEdit = reactive(createDefaultModel());

function createDefaultModel(): Api.Health.AlertAutoProcessEdit {
  return {
    physicalSign: '',
    eventType: '',
    level: 'minor',
    thresholdMin: null,
    thresholdMax: null,
    alertDesc: '',
    isEnabled: true,
    autoProcessEnabled: false,
    autoProcessAction: '',
    autoProcessDelaySeconds: 0,
    autoResolveThresholdCount: 1,
    suppressDurationMinutes: 60,
    timeWindowSeconds: null,
    remark: ''
  };
}

// 表单验证规则
const rules = computed(() => {
  return {
    physicalSign: createRequiredRule('请选择生理指标'),
    eventType: createRequiredRule('请选择告警类型'),
    level: createRequiredRule('请选择严重程度'),
    autoProcessAction: [
      {
        required: model.autoProcessEnabled,
        message: '启用自动处理时必须选择处理动作'
      }
    ]
  };
});

// 选项数据
const physicalSignOptions = [
  { label: '心率', value: 'heart_rate' },
  { label: '血氧', value: 'blood_oxygen' },
  { label: '体温', value: 'temperature' },
  { label: '收缩压', value: 'pressure_high' },
  { label: '舒张压', value: 'pressure_low' },
  { label: '步数', value: 'step' },
  { label: '卡路里', value: 'calorie' },
  { label: '距离', value: 'distance' },
  { label: '压力指数', value: 'stress' }
];

const alertTypeOptions = [
  { label: '设备离线', value: 'device_offline' },
  { label: '心率异常', value: 'heart_rate_abnormal' },
  { label: '血氧偏低', value: 'blood_oxygen_low' },
  { label: '体温异常', value: 'temperature_abnormal' },
  { label: '血压异常', value: 'blood_pressure_abnormal' },
  { label: '电池电量低', value: 'battery_low' },
  { label: '步数不足', value: 'step_insufficient' }
];

const severityOptions = [
  { label: 'Critical', value: 'critical' },
  { label: 'Major', value: 'major' },
  { label: 'Minor', value: 'minor' },
  { label: 'Info', value: 'info' }
];

const autoProcessActionOptions = [
  { label: '自动解决', value: 'AUTO_RESOLVE' },
  { label: '自动确认', value: 'AUTO_ACKNOWLEDGE' },
  { label: '自动升级', value: 'AUTO_ESCALATE' },
  { label: '自动抑制', value: 'AUTO_SUPPRESS' }
];

// 获取严重程度标签颜色
function getSeverityColor(severity: string) {
  const colors = {
    'critical': 'error',
    'major': 'warning',
    'minor': 'info',
    'info': 'default'
  };
  return colors[severity as keyof typeof colors] || 'default';
}

// 获取动作标签颜色
function getActionColor(action: string) {
  const colors = {
    'AUTO_RESOLVE': 'success',
    'AUTO_ACKNOWLEDGE': 'info',
    'AUTO_ESCALATE': 'warning',
    'AUTO_SUPPRESS': 'error'
  };
  return colors[action as keyof typeof colors] || 'default';
}

// 监听弹窗显示状态
watch(
  visible,
  () => {
    if (visible.value) {
      handleInitModel();
    }
  },
  { immediate: true }
);

// 初始化表单数据
function handleInitModel() {
  Object.assign(model, createDefaultModel());
  
  if (props.operateType === 'edit' && props.rowData) {
    Object.assign(model, {
      id: props.rowData.id,
      physicalSign: props.rowData.physicalSign,
      eventType: props.rowData.eventType,
      level: props.rowData.level,
      thresholdMin: props.rowData.thresholdMin,
      thresholdMax: props.rowData.thresholdMax,
      alertDesc: props.rowData.alertDesc,
      isEnabled: props.rowData.isEnabled,
      autoProcessEnabled: props.rowData.autoProcessEnabled,
      autoProcessAction: props.rowData.autoProcessAction,
      autoProcessDelaySeconds: props.rowData.autoProcessDelaySeconds,
      autoResolveThresholdCount: props.rowData.autoResolveThresholdCount,
      suppressDurationMinutes: props.rowData.suppressDurationMinutes,
      timeWindowSeconds: props.rowData.timeWindowSeconds,
      remark: props.rowData.remark
    });
  }
}

// 关闭抽屉
function closeDrawer() {
  visible.value = false;
  restoreValidation();
}

// 提交表单
async function handleSubmit() {
  await validate();
  
  let result;
  if (props.operateType === 'add') {
    result = await fetchAddAlertAutoProcess(model);
  } else {
    result = await fetchUpdateAlertAutoProcess(model);
  }
  
  if (!result.error) {
    window.$message?.success(props.operateType === 'add' ? '新增成功' : '更新成功');
    closeDrawer();
    emit('submitted');
  }
}

// 自动处理开关变化处理
function handleAutoProcessChange(enabled: boolean) {
  if (!enabled) {
    model.autoProcessAction = '';
    model.autoProcessDelaySeconds = 0;
  }
}

// 动作标签文本
function getActionText(action: string) {
  const option = autoProcessActionOptions.find(opt => opt.value === action);
  return option ? option.label : action;
}
</script>

<template>
  <NDrawer v-model:show="visible" :width="600" :mask-closable="false">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      
      <!-- 查看模式 -->
      <template v-if="isView">
        <NCard>
          <NDescriptions bordered :column="2">
            <NDescriptionsItem label="生理指标">
              {{ props.rowData?.physicalSign || '-' }}
            </NDescriptionsItem>
            <NDescriptionsItem label="告警类型">
              {{ props.rowData?.eventType || '-' }}
            </NDescriptionsItem>
            <NDescriptionsItem label="严重程度">
              <NTag v-if="props.rowData?.level" :type="getSeverityColor(props.rowData.level) as any">
                {{ props.rowData.level }}
              </NTag>
              <span v-else>-</span>
            </NDescriptionsItem>
            <NDescriptionsItem label="阈值范围">
              <template v-if="props.rowData?.thresholdMin !== null && props.rowData?.thresholdMax !== null">
                {{ props.rowData.thresholdMin }} - {{ props.rowData.thresholdMax }}
              </template>
              <template v-else-if="props.rowData?.thresholdMin !== null">
                ≥ {{ props.rowData.thresholdMin }}
              </template>
              <template v-else-if="props.rowData?.thresholdMax !== null">
                ≤ {{ props.rowData.thresholdMax }}
              </template>
              <template v-else>-</template>
            </NDescriptionsItem>
            <NDescriptionsItem label="规则状态">
              <NTag :type="props.rowData?.isEnabled ? 'success' : 'default'">
                {{ props.rowData?.isEnabled ? '启用' : '禁用' }}
              </NTag>
            </NDescriptionsItem>
            <NDescriptionsItem label="自动处理">
              <NTag :type="props.rowData?.autoProcessEnabled ? 'success' : 'default'">
                {{ props.rowData?.autoProcessEnabled ? '启用' : '禁用' }}
              </NTag>
            </NDescriptionsItem>
            <NDescriptionsItem v-if="props.rowData?.autoProcessAction" label="处理动作">
              <NTag :type="getActionColor(props.rowData.autoProcessAction) as any">
                {{ getActionText(props.rowData.autoProcessAction) }}
              </NTag>
            </NDescriptionsItem>
            <NDescriptionsItem v-if="props.rowData?.autoProcessDelaySeconds" label="延迟时间">
              {{ props.rowData.autoProcessDelaySeconds }}秒
            </NDescriptionsItem>
            <NDescriptionsItem v-if="props.rowData?.autoResolveThresholdCount" label="自动解决阈值">
              {{ props.rowData.autoResolveThresholdCount }}次
            </NDescriptionsItem>
            <NDescriptionsItem v-if="props.rowData?.suppressDurationMinutes" label="抑制时长">
              {{ props.rowData.suppressDurationMinutes }}分钟
            </NDescriptionsItem>
            <NDescriptionsItem v-if="props.rowData?.alertDesc" label="告警描述">
              {{ props.rowData.alertDesc }}
            </NDescriptionsItem>
            <NDescriptionsItem v-if="props.rowData?.remark" label="备注">
              {{ props.rowData.remark }}
            </NDescriptionsItem>
          </NDescriptions>
        </NCard>
      </template>

      <!-- 编辑模式 -->
      <template v-else>
        <NForm ref="formRef" :model="model" :rules="rules" label-placement="left" :label-width="120">
          
          <!-- 基础配置 -->
          <NCard title="基础配置" style="margin-bottom: 16px;">
            <NFormItem label="生理指标" path="physicalSign">
              <NSelect
                v-model:value="model.physicalSign"
                :options="physicalSignOptions"
                placeholder="请选择生理指标"
                filterable
              />
            </NFormItem>

            <NFormItem label="告警类型" path="eventType">
              <NSelect
                v-model:value="model.eventType"
                :options="alertTypeOptions"
                placeholder="请选择告警类型"
                filterable
              />
            </NFormItem>

            <NFormItem label="严重程度" path="level">
              <NSelect
                v-model:value="model.level"
                :options="severityOptions"
                placeholder="请选择严重程度"
              />
            </NFormItem>

            <NFormItem label="阈值最小值" path="thresholdMin">
              <NInputNumber
                v-model:value="model.thresholdMin"
                placeholder="请输入阈值最小值"
                :min="0"
                :precision="2"
              />
            </NFormItem>

            <NFormItem label="阈值最大值" path="thresholdMax">
              <NInputNumber
                v-model:value="model.thresholdMax"
                placeholder="请输入阈值最大值"
                :min="0"
                :precision="2"
              />
            </NFormItem>

            <NFormItem label="告警描述" path="alertDesc">
              <NInput
                v-model:value="model.alertDesc"
                type="textarea"
                placeholder="请输入告警描述"
                :rows="2"
              />
            </NFormItem>

            <NFormItem label="规则状态" path="isEnabled">
              <NSwitch v-model:value="model.isEnabled">
                <template #checked>启用</template>
                <template #unchecked>禁用</template>
              </NSwitch>
            </NFormItem>
          </NCard>

          <!-- 自动处理配置 -->
          <NCard title="自动处理配置">
            <NFormItem label="启用自动处理" path="autoProcessEnabled">
              <NSwitch 
                v-model:value="model.autoProcessEnabled"
                @update:value="handleAutoProcessChange"
              >
                <template #checked>启用</template>
                <template #unchecked>禁用</template>
              </NSwitch>
            </NFormItem>

            <template v-if="model.autoProcessEnabled">
              <NAlert type="info" style="margin-bottom: 16px;">
                启用自动处理后，系统将根据配置的动作自动处理告警，请谨慎配置。
              </NAlert>

              <NFormItem label="处理动作" path="autoProcessAction">
                <NSelect
                  v-model:value="model.autoProcessAction"
                  :options="autoProcessActionOptions"
                  placeholder="请选择自动处理动作"
                />
              </NFormItem>

              <NFormItem label="延迟时间(秒)" path="autoProcessDelaySeconds">
                <NInputNumber
                  v-model:value="model.autoProcessDelaySeconds"
                  placeholder="延迟执行时间"
                  :min="0"
                  :max="86400"
                />
              </NFormItem>

              <NFormItem 
                v-if="model.autoProcessAction === 'AUTO_RESOLVE'"
                label="自动解决阈值" 
                path="autoResolveThresholdCount"
              >
                <NInputNumber
                  v-model:value="model.autoResolveThresholdCount"
                  placeholder="24小时内自动解决次数上限"
                  :min="1"
                  :max="100"
                />
              </NFormItem>

              <NFormItem 
                v-if="model.autoProcessAction === 'AUTO_SUPPRESS'"
                label="抑制时长(分钟)" 
                path="suppressDurationMinutes"
              >
                <NInputNumber
                  v-model:value="model.suppressDurationMinutes"
                  placeholder="抑制持续时间"
                  :min="1"
                  :max="1440"
                />
              </NFormItem>

              <NFormItem label="时间窗口(秒)" path="timeWindowSeconds">
                <NInputNumber
                  v-model:value="model.timeWindowSeconds"
                  placeholder="规则生效时间窗口"
                  :min="60"
                />
              </NFormItem>
            </template>

            <NFormItem label="备注" path="remark">
              <NInput
                v-model:value="model.remark"
                type="textarea"
                placeholder="请输入备注信息"
                :rows="2"
              />
            </NFormItem>
          </NCard>

        </NForm>
      </template>

      <template #footer>
        <NSpace>
          <NButton @click="closeDrawer">{{ $t('common.cancel') }}</NButton>
          <NButton v-if="!isView" type="primary" @click="handleSubmit">
            {{ $t('common.confirm') }}
          </NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>