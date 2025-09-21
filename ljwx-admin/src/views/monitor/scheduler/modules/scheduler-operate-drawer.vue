<script setup lang="ts">
import { computed, reactive, watch, ref } from 'vue';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { fetchAddScheduler, fetchGetEditScheduler, fetchUpdateSchedulerInfo } from '@/service/api';
import { $t } from '@/locales';

defineOptions({
  name: 'SchedulerOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Monitor.Scheduler | null;
}

const props = defineProps<Props>();

interface Emits {
  (e: 'submitted'): void;
}

const emit = defineEmits<Emits>();

const visible = defineModel<boolean>('visible', {
  default: false
});

const { formRef, validate, restoreValidation } = useNaiveForm();
const { defaultRequiredRule } = useFormRules();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: $t('page.monitor.scheduler.addJob'),
    edit: $t('page.monitor.scheduler.editJob')
  };
  return titles[props.operateType];
});

type Model = Api.Monitor.SchedulerEdit;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    id: '',
    jobName: '',
    jobGroup: '',
    jobClassName: '',
    description: '',
    cronExpression: '',
    jobData: [],
    triggerName: '',
    triggerGroup: '',
    triggerDescription: '',
    triggerData: []
  };
}

type RuleKey = Extract<keyof Model, 'jobName' | 'jobGroup' | 'jobClassName' | 'triggerName' | 'triggerGroup'>;

const rules: Record<RuleKey, App.Global.FormRule[]> = {
  jobName: [defaultRequiredRule],
  jobGroup: [defaultRequiredRule],
  jobClassName: [defaultRequiredRule],
  triggerName: [defaultRequiredRule],
  triggerGroup: [defaultRequiredRule]
};

const isEdit = computed(() => props.operateType === 'edit');
const submitting = ref(false);

const enhancedTitle = computed(() => {
  const icon = !isEdit.value ? '⏰' : '✏️';
  return `${icon} ${title.value}`;
});

async function handleInitModel() {
  Object.assign(model, createDefaultModel());

  if (props.operateType === 'edit' && props.rowData) {
    const { error, data } = await fetchGetEditScheduler(props.rowData?.id);
    if (!error) {
      Object.assign(model, data);
    }
  }
  if (!model.jobData) {
    model.jobData = [];
  }
  if (!model.triggerData) {
    model.triggerData = [];
  }
}

function closeDrawer() {
  visible.value = false;
}

async function handleSubmit() {
  try {
    submitting.value = true;
    await validate();
    
    // request
    const func = isEdit.value ? fetchUpdateSchedulerInfo : fetchAddScheduler;
    const { error, data } = await func(model);
    if (!error && data) {
      window.$message?.success(isEdit.value ? $t('common.updateSuccess') : $t('common.addSuccess'));
      closeDrawer();
      emit('submitted');
    }
  } catch (error) {
    console.error('Submit error:', error);
  } finally {
    submitting.value = false;
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
  <NDrawer v-model:show="visible" display-directive="show" width="480" class="enhanced-drawer scheduler-theme">
    <NDrawerContent :title="enhancedTitle" :native-scrollbar="false" closable>
      <!-- 操作提示 -->
      <div class="operation-banner">
        <div class="banner-icon">
          <i class="i-material-symbols:schedule" v-if="!isEdit"></i>
          <i class="i-material-symbols:edit-calendar" v-else></i>
        </div>
        <div class="banner-content">
          <h3 class="banner-title">{{ !isEdit ? '新增定时任务' : '编辑定时任务' }}</h3>
          <p class="banner-desc">{{ !isEdit ? '配置新的定时任务，请仔细填写相关参数' : '修改任务配置，部分核心字段不可修改' }}</p>
        </div>
      </div>

      <NForm ref="formRef" :model="model" :rules="rules">
        <!-- 任务基本信息 -->
        <div class="form-section">
          <div class="section-title">
            <i class="i-material-symbols:work"></i>
            任务基本信息
          </div>
          
          <NFormItem :label="$t('page.monitor.scheduler.jobName')" path="jobName">
            <NInput 
              v-model:value="model.jobName" 
              :placeholder="$t('page.monitor.scheduler.form.jobName')" 
              :disabled="isEdit"
            >
              <template #prefix>
                <i class="i-material-symbols:task"></i>
              </template>
            </NInput>
            <div class="help-text" v-if="isEdit">任务名称不可修改</div>
          </NFormItem>

          <NFormItem :label="$t('page.monitor.scheduler.jobGroup')" path="jobGroup">
            <NInput 
              v-model:value="model.jobGroup" 
              :placeholder="$t('page.monitor.scheduler.form.jobGroup')" 
              :disabled="isEdit"
            >
              <template #prefix>
                <i class="i-material-symbols:folder"></i>
              </template>
            </NInput>
            <div class="help-text" v-if="isEdit">任务组不可修改</div>
          </NFormItem>

          <NFormItem :label="$t('page.monitor.scheduler.jobClassName')" path="jobClassName">
            <NInput 
              v-model:value="model.jobClassName" 
              :placeholder="$t('page.monitor.scheduler.form.jobClassName')"
            >
              <template #prefix>
                <i class="i-material-symbols:code"></i>
              </template>
            </NInput>
            <div class="help-text">Java类的全限定名</div>
          </NFormItem>

          <NFormItem :label="$t('page.monitor.scheduler.description')" path="description">
            <NInput 
              v-model:value="model.description" 
              :placeholder="$t('page.monitor.scheduler.form.description')"
              type="textarea"
              :rows="3"
            >
            </NInput>
            <div class="help-text">任务描述信息</div>
          </NFormItem>
        </div>
        <!-- 执行配置 -->
        <div class="form-section">
          <div class="section-title">
            <i class="i-material-symbols:schedule"></i>
            执行配置
          </div>
          
          <NFormItem :label="$t('page.monitor.scheduler.cronExpression')" path="cronExpression">
            <NInput 
              v-model:value="model.cronExpression" 
              :placeholder="$t('page.monitor.scheduler.form.cronExpression')"
            >
              <template #prefix>
                <i class="i-material-symbols:timer"></i>
              </template>
            </NInput>
            <div class="help-text">
              Cron表达式，例如: 0 0/5 * * * ? （每5分钟执行一次）
              <a href="https://cron.qqe2.com/" target="_blank" class="cron-help">在线生成器</a>
            </div>
          </NFormItem>

          <NFormItem span="24" :label="$t('page.monitor.scheduler.jobData')">
            <div class="dynamic-input-wrapper">
              <div class="dynamic-input-header">
                <span class="input-label">任务参数</span>
                <span class="input-desc">键值对形式的任务参数</span>
              </div>
              <NDynamicInput
                v-model:value="model.jobData"
                preset="pair"
                :key-placeholder="$t('page.monitor.scheduler.form.jobDataKey')"
                :value-placeholder="$t('page.monitor.scheduler.form.jobDataValue')"
              >
                <template #action="{ index, create, remove }">
                  <NSpace class="ml-8px">
                    <NButton size="small" type="primary" @click="() => create(index)">
                      <template #icon>
                        <i class="i-material-symbols:add"></i>
                      </template>
                    </NButton>
                    <NButton size="small" type="error" @click="() => remove(index)">
                      <template #icon>
                        <i class="i-material-symbols:remove"></i>
                      </template>
                    </NButton>
                  </NSpace>
                </template>
              </NDynamicInput>
            </div>
          </NFormItem>
        </div>
        <!-- 触发器配置 -->
        <div class="form-section">
          <div class="section-title">
            <i class="i-material-symbols:play-arrow"></i>
            触发器配置
          </div>
          
          <NFormItem :label="$t('page.monitor.scheduler.triggerName')" path="triggerName">
            <NInput 
              v-model:value="model.triggerName" 
              :placeholder="$t('page.monitor.scheduler.form.triggerName')" 
              :disabled="isEdit"
            >
              <template #prefix>
                <i class="i-material-symbols:label"></i>
              </template>
            </NInput>
            <div class="help-text" v-if="isEdit">触发器名称不可修改</div>
          </NFormItem>

          <NFormItem :label="$t('page.monitor.scheduler.triggerGroup')" path="triggerGroup">
            <NInput 
              v-model:value="model.triggerGroup" 
              :placeholder="$t('page.monitor.scheduler.form.triggerGroup')" 
              :disabled="isEdit"
            >
              <template #prefix>
                <i class="i-material-symbols:folder"></i>
              </template>
            </NInput>
            <div class="help-text" v-if="isEdit">触发器组不可修改</div>
          </NFormItem>

          <NFormItem :label="$t('page.monitor.scheduler.triggerDescription')" path="triggerDescription">
            <NInput 
              v-model:value="model.triggerDescription" 
              :placeholder="$t('page.monitor.scheduler.form.triggerDescription')"
              type="textarea"
              :rows="2"
            >
            </NInput>
            <div class="help-text">触发器描述信息</div>
          </NFormItem>

          <NFormItem span="24" :label="$t('page.monitor.scheduler.triggerData')">
            <div class="dynamic-input-wrapper">
              <div class="dynamic-input-header">
                <span class="input-label">触发器参数</span>
                <span class="input-desc">触发器的附加参数配置</span>
              </div>
              <NDynamicInput
                v-model:value="model.triggerData"
                preset="pair"
                :key-placeholder="$t('page.monitor.scheduler.form.triggerDataKey')"
                :value-placeholder="$t('page.monitor.scheduler.form.triggerDataValue')"
              >
                <template #action="{ index, create, remove }">
                  <NSpace class="ml-8px">
                    <NButton size="small" type="primary" @click="() => create(index)">
                      <template #icon>
                        <i class="i-material-symbols:add"></i>
                      </template>
                    </NButton>
                    <NButton size="small" type="error" @click="() => remove(index)">
                      <template #icon>
                        <i class="i-material-symbols:remove"></i>
                      </template>
                    </NButton>
                  </NSpace>
                </template>
              </NDynamicInput>
            </div>
          </NFormItem>
        </div>
      </NForm>
      <template #footer>
        <div class="drawer-footer">
          <NButton @click="closeDrawer" class="cancel-btn">
            <template #icon>
              <i class="i-material-symbols:close"></i>
            </template>
            {{ $t('common.cancel') }}
          </NButton>
          <NButton type="primary" @click="handleSubmit" class="submit-btn" :loading="submitting">
            <template #icon>
              <i class="i-material-symbols:check" v-if="!submitting"></i>
            </template>
            {{ !isEdit ? $t('common.add') : $t('common.update') }}
          </NButton>
        </div>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped>
/* 组件特定样式 - 调度任务特有的样式 */

/* Cron 帮助链接 */
.cron-help {
  color: #3b82f6;
  text-decoration: none;
  margin-left: 8px;
  font-weight: 500;
}

.cron-help:hover {
  text-decoration: underline;
}

/* 动态输入组件的按钮样式 */
:deep(.n-dynamic-input) {
  .n-button {
    border-radius: 6px;
    
    &.n-button--primary-type {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }
    
    &.n-button--error-type {
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
  }
}
</style>
