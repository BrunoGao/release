<script setup lang="ts">
import { NButton, NForm, NFormItem, NGi, NGrid, NInput, NSelect, NDatePicker } from 'naive-ui';
import { computed } from 'vue';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({
  name: 'AlertAutoProcessSearch'
});

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const { formRef, validate, restoreValidation } = useNaiveForm();

const model = defineModel<Api.Health.AlertAutoProcessSearchParams>('model', { required: true });

// 严重程度选项
const severityOptions = [
  { label: 'Critical', value: 'critical' },
  { label: 'Major', value: 'major' }, 
  { label: 'Minor', value: 'minor' },
  { label: 'Info', value: 'info' }
];

// 告警类型选项
const alertTypeOptions = [
  { label: '设备离线', value: 'device_offline' },
  { label: '心率异常', value: 'heart_rate_abnormal' },
  { label: '血氧偏低', value: 'blood_oxygen_low' },
  { label: '体温异常', value: 'temperature_abnormal' },
  { label: '血压异常', value: 'blood_pressure_abnormal' },
  { label: '电池电量低', value: 'battery_low' },
  { label: '步数不足', value: 'step_insufficient' }
];

// 生理指标选项
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

// 自动处理动作选项
const autoProcessActionOptions = [
  { label: '自动解决', value: 'AUTO_RESOLVE' },
  { label: '自动确认', value: 'AUTO_ACKNOWLEDGE' },
  { label: '自动升级', value: 'AUTO_ESCALATE' },
  { label: '自动抑制', value: 'AUTO_SUPPRESS' }
];

// 启用状态选项
const enabledOptions = [
  { label: '启用', value: true },
  { label: '禁用', value: false }
];

async function reset() {
  await restoreValidation();
  emit('reset');
}

async function search() {
  await validate();
  emit('search');
}

// 时间范围处理
const timeRange = computed({
  get() {
    if (model.value.createTimeStart && model.value.createTimeEnd) {
      return [
        new Date(model.value.createTimeStart).getTime(),
        new Date(model.value.createTimeEnd).getTime()
      ];
    }
    return null;
  },
  set(value: [number, number] | null) {
    if (value) {
      model.value.createTimeStart = new Date(value[0]).toISOString().slice(0, 19);
      model.value.createTimeEnd = new Date(value[1]).toISOString().slice(0, 19);
    } else {
      model.value.createTimeStart = undefined;
      model.value.createTimeEnd = undefined;
    }
  }
});
</script>

<template>
  <NForm ref="formRef" :model="model" label-placement="left" :label-width="80">
    <NGrid responsive="screen" item-responsive cols="1 s:1 m:2 l:3 xl:4 2xl:4" :x-gap="12" :y-gap="8">
      <!-- 规则名称 -->
      <NGi>
        <NFormItem label="规则名称" path="ruleName">
          <NInput 
            v-model:value="model.ruleName" 
            placeholder="请输入规则名称"
            clearable
          />
        </NFormItem>
      </NGi>

      <!-- 告警类型 -->
      <NGi>
        <NFormItem label="告警类型" path="alertType">
          <NSelect
            v-model:value="model.alertType"
            :options="alertTypeOptions"
            placeholder="请选择告警类型"
            clearable
            filterable
          />
        </NFormItem>
      </NGi>

      <!-- 生理指标 -->
      <NGi>
        <NFormItem label="生理指标" path="physicalSign">
          <NSelect
            v-model:value="model.physicalSign"
            :options="physicalSignOptions"
            placeholder="请选择生理指标"
            clearable
            filterable
          />
        </NFormItem>
      </NGi>

      <!-- 严重程度 -->
      <NGi>
        <NFormItem label="严重程度" path="severityLevel">
          <NSelect
            v-model:value="model.severityLevel"
            :options="severityOptions"
            placeholder="请选择严重程度"
            clearable
          />
        </NFormItem>
      </NGi>

      <!-- 规则状态 -->
      <NGi>
        <NFormItem label="规则状态" path="isEnabled">
          <NSelect
            v-model:value="model.isEnabled"
            :options="enabledOptions"
            placeholder="请选择规则状态"
            clearable
          />
        </NFormItem>
      </NGi>

      <!-- 自动处理启用 -->
      <NGi>
        <NFormItem label="自动处理" path="autoProcessEnabled">
          <NSelect
            v-model:value="model.autoProcessEnabled"
            :options="enabledOptions"
            placeholder="请选择自动处理状态"
            clearable
          />
        </NFormItem>
      </NGi>

      <!-- 自动处理动作 -->
      <NGi>
        <NFormItem label="处理动作" path="autoProcessAction">
          <NSelect
            v-model:value="model.autoProcessAction"
            :options="autoProcessActionOptions"
            placeholder="请选择处理动作"
            clearable
          />
        </NFormItem>
      </NGi>

      <!-- 创建时间范围 -->
      <NGi>
        <NFormItem label="创建时间" path="createTimeRange">
          <NDatePicker
            v-model:value="timeRange"
            type="daterange"
            placeholder="选择时间范围"
            clearable
            format="yyyy-MM-dd"
            value-format="yyyy-MM-dd HH:mm:ss"
            class="w-full"
          />
        </NFormItem>
      </NGi>

      <!-- 操作按钮 -->
      <NGi suffix class="flex items-end">
        <NFormItem>
          <div class="flex gap-12px">
            <NButton type="primary" ghost @click="search">
              <template #icon>
                <icon-ic-round-search class="text-icon" />
              </template>
              {{ $t('common.search') }}
            </NButton>
            <NButton @click="reset">
              <template #icon>
                <icon-ic-round-refresh class="text-icon" />
              </template>
              {{ $t('common.reset') }}
            </NButton>
          </div>
        </NFormItem>
      </NGi>
    </NGrid>
  </NForm>
</template>

<style scoped></style>