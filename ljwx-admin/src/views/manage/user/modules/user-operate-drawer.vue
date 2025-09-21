<script setup lang="ts">
import { computed, reactive, watch, ref } from 'vue';
import { NSelect, NInputNumber } from 'naive-ui';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { useAuthStore } from '@/store/modules/auth';
import { fetchAddUser, fetchGetEditUserInfo, fetchUpdateUserInfo } from '@/service/api';
import { $t } from '@/locales';
import { useDict } from '@/hooks/business/dict';
import { deviceOptions, handleUnbindDevice } from '@/utils/deviceUtils';

defineOptions({
  name: 'UserOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.SystemManage.User | null;
  /** the org ids */
  orgIds: string;
}

const props = defineProps<Props>();

interface Emits {
  (e: 'submitted'): void;
}

const emit = defineEmits<Emits>();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;
const { dictOptions } = useDict();

const visible = defineModel<boolean>('visible', {
  default: false
});

const { formRef, validate, restoreValidation } = useNaiveForm();
const { defaultRequiredRule, formRules } = useFormRules();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: $t('page.manage.user.addUser'),
    edit: $t('page.manage.user.editUser')
  };
  return titles[props.operateType];
});

type Model = Api.SystemManage.UserEdit;

const model: Model = reactive(createDefaultModel());

function createDefaultModel(): Model {
  return {
    id: '',
    userName: '',
    gender: '0',
    nickName: '',
    realName: '',
    phone: '',
    email: '',
    deviceSn: '',
    status: '1',
    orgIds: props.orgIds.match(/^\d+/)[0],
    userCardNumber: '',
    workingYears: 0
  };
}

type RuleKey = Extract<keyof Model, 'userName' | 'status' | 'realName' | 'phone' | 'email'>;

const rules: Record<RuleKey, App.Global.FormRule[]> = {
  userName: formRules.userName,
  status: [defaultRequiredRule],
  realName: [defaultRequiredRule],
  phone: formRules.phone,
  email: formRules.email
};

const isAdd = computed(() => props.operateType === 'add');
const submitting = ref(false);

const enhancedTitle = computed(() => {
  const icon = isAdd.value ? '👤' : '✏️';
  return `${icon} ${title.value}`;
});

async function handleInitModel() {
  Object.assign(model, createDefaultModel());

  if (props.operateType === 'edit' && props.rowData) {
    const { error, data } = await fetchGetEditUserInfo(props.rowData?.id);
    if (!error) {
      Object.assign(model, data);
    }
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
    const func = isAdd.value ? fetchAddUser : fetchUpdateUserInfo;
    const { error, data } = await func(model);
    if (!error && data) {
      window.$message?.success(isAdd.value ? $t('common.addSuccess') : $t('common.updateSuccess'));
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
    handleUnbindDevice(customerId);
  }
});
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="420" class="enhanced-drawer">
    <NDrawerContent :title="enhancedTitle" :native-scrollbar="false" closable>
      <!-- 操作提示 -->
      <div class="operation-banner">
        <div class="banner-icon">
          <i class="i-material-symbols:person-add" v-if="isAdd"></i>
          <i class="i-material-symbols:person-edit" v-else></i>
        </div>
        <div class="banner-content">
          <h3 class="banner-title">{{ isAdd ? '新增用户' : '编辑用户' }}</h3>
          <p class="banner-desc">{{ isAdd ? '请填写完整的用户信息，标有 * 的为必填项' : '修改用户信息，部分字段不可编辑' }}</p>
        </div>
      </div>

      <NForm ref="formRef" :model="model" :rules="rules">
        <!-- 基本信息 -->
        <div class="form-section">
          <div class="section-title">
            <i class="i-material-symbols:badge"></i>
            基本信息
          </div>
          
          <NFormItem :label="$t('page.manage.user.userName')" path="userName">
            <NInput 
              v-model:value="model.userName" 
              :placeholder="$t('page.manage.user.form.userName')" 
              :disabled="!isAdd"
            >
              <template #prefix>
                <i class="i-material-symbols:account-circle"></i>
              </template>
            </NInput>
            <div class="help-text" v-if="!isAdd">用户名不可修改</div>
          </NFormItem>

          <NFormItem :label="$t('page.manage.user.realName')" path="realName">
            <NInput 
              v-model:value="model.realName" 
              :placeholder="$t('page.manage.user.form.realName')"
            >
              <template #prefix>
                <i class="i-material-symbols:person"></i>
              </template>
            </NInput>
          </NFormItem>

          <NFormItem :label="$t('page.manage.user.gender')" path="gender">
            <NRadioGroup v-model:value="model.gender">
              <NRadio v-for="item in dictOptions('gender')" :key="item.value" :value="item.value" :label="item.label" />
            </NRadioGroup>
          </NFormItem>

          <NFormItem :label="$t('page.manage.user.userCardNumber')" path="userCardNumber">
            <NInput 
              v-model:value="model.userCardNumber" 
              :placeholder="$t('page.manage.user.form.userCardNumber')"
            >
              <template #prefix>
                <i class="i-material-symbols:credit-card"></i>
              </template>
            </NInput>
          </NFormItem>
        </div>

        <!-- 联系信息 -->
        <div class="form-section">
          <div class="section-title">
            <i class="i-material-symbols:contact-phone"></i>
            联系信息
          </div>
          
          <NFormItem :label="$t('page.manage.user.phone')" path="phone">
            <NInput 
              v-model:value="model.phone" 
              :placeholder="$t('page.manage.user.form.phone')"
            >
              <template #prefix>
                <i class="i-material-symbols:phone"></i>
              </template>
            </NInput>
          </NFormItem>

          <NFormItem :label="$t('page.manage.user.email')" path="email">
            <NInput 
              v-model:value="model.email" 
              :placeholder="$t('page.manage.user.form.email')"
            >
              <template #prefix>
                <i class="i-material-symbols:email"></i>
              </template>
            </NInput>
          </NFormItem>
        </div>

        <!-- 工作信息 -->
        <div class="form-section">
          <div class="section-title">
            <i class="i-material-symbols:work"></i>
            工作信息
          </div>
          
          <NFormItem :label="$t('page.manage.user.workingYears')" path="workingYears">
            <NInputNumber 
              v-model:value="model.workingYears" 
              :placeholder="$t('page.manage.user.form.workingYears')"
              :min="0"
              :max="50"
              style="width: 100%"
            >
              <template #prefix>
                <i class="i-material-symbols:schedule"></i>
              </template>
            </NInputNumber>
            <div class="help-text">工作年限（0-50年）</div>
          </NFormItem>

          <NFormItem :label="$t('page.manage.user.status')" path="status">
            <NRadioGroup v-model:value="model.status">
              <NRadio v-for="item in dictOptions('status')" :key="item.value" :value="item.value">
                <span class="radio-label">
                  <span class="status-dot" :class="item.value === '1' ? 'active' : 'inactive'"></span>
                  {{ item.label }}
                </span>
              </NRadio>
            </NRadioGroup>
          </NFormItem>
        </div>

        <!-- 设备绑定 -->
        <div class="form-section">
          <div class="section-title">
            <i class="i-material-symbols:devices"></i>
            设备绑定
          </div>
          
          <NFormItem :label="$t('page.manage.user.deviceSn')" path="deviceSn">
            <NSelect 
              v-model:value="model.deviceSn" 
              :placeholder="$t('page.manage.user.form.deviceSn')" 
              :options="deviceOptions" 
              filterable
              clearable
            >
              <template #arrow>
                <i class="i-material-symbols:smartphone"></i>
              </template>
            </NSelect>
            <div class="help-text">选择要绑定的设备，可以为空</div>
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
            {{ isAdd ? $t('common.add') : $t('common.update') }}
          </NButton>
        </div>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped>
/* 组件特定样式 - 全局美化样式已通过 enhanced-drawer 类自动应用 */
</style>
