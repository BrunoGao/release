<script setup lang="ts">
import { computed, reactive, watch, ref } from 'vue';
import { NSelect, NInputNumber, NSpace } from 'naive-ui';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { useAuthStore } from '@/store/modules/auth';
import { fetchAddUser, fetchGetEditUserInfo, fetchUpdateUserInfo, fetchCheckPhoneExists, fetchCheckDeviceSnExists } from '@/service/api';
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
    realName: '', // 后端需要，但前端不显示，自动设为与userName一致
    email: '', // 后端需要，设为空字符串
    gender: '0',
    nickName: '',
    phone: '',
    deviceSn: '',
    status: '1',
    orgIds: props.orgIds.match(/^\d+/)[0],
    userCardNumber: '',
    workingYears: 0
  };
}

type RuleKey = Extract<keyof Model, 'userName' | 'status' | 'phone'>;

const rules: Record<RuleKey, App.Global.FormRule[]> = {
  userName: formRules.userName,
  status: [defaultRequiredRule],
  phone: formRules.phone
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
      // 确保 realName 存在，如果不存在则设为与 userName 一致
      if (!model.realName && model.userName) {
        model.realName = model.userName;
      }
      // 确保 email 字段存在（可以为空字符串）
      if (model.email === undefined || model.email === null) {
        model.email = '';
      }
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
    
    // 检查手机号是否重复（仅检查未删除的用户）
    if (model.phone) {
      const shouldCheckPhone = isAdd.value || (props.rowData && model.phone !== props.rowData.phone);
      if (shouldCheckPhone) {
        const { data: phoneExists, error: phoneCheckError } = await fetchCheckPhoneExists(
          model.phone,
          isAdd.value ? undefined : model.id
        );
        
        if (phoneCheckError) {
          console.error('检查手机号失败:', phoneCheckError);
          window.$message?.error('检查手机号失败，请重试');
          return;
        }
        
        if (phoneExists) {
          window.$message?.error(`手机号 "${model.phone}" 已被其他用户使用，请更换手机号`);
          return;
        }
      }
    }
    
    // 检查设备序列号是否重复（仅检查未删除的用户）
    if (model.deviceSn) {
      const shouldCheckDevice = isAdd.value || (props.rowData && model.deviceSn !== props.rowData.deviceSn);
      if (shouldCheckDevice) {
        const { data: deviceExists, error: deviceCheckError } = await fetchCheckDeviceSnExists(
          model.deviceSn,
          isAdd.value ? undefined : model.id
        );
        
        if (deviceCheckError) {
          console.error('检查设备序列号失败:', deviceCheckError);
          window.$message?.error('检查设备序列号失败，请重试');
          return;
        }
        
        if (deviceExists) {
          window.$message?.error(`设备 "${model.deviceSn}" 已被其他用户绑定，请选择其他设备`);
          return;
        }
      }
    }
    
    // 确保 realName 与 userName 保持一致
    model.realName = model.userName;
    
    // 确保 email 字段存在（可以为空字符串）
    if (!model.email) {
      model.email = '';
    }
    
    console.log('[Debug] Submit model:', model);
    
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
  <NDrawer v-model:show="visible" display-directive="show" :width="480" :height="'90vh'" class="enhanced-drawer user-drawer">
    <NDrawerContent :title="enhancedTitle" :native-scrollbar="false" closable class="drawer-content-scrollable">
      <!-- 美化的操作横幅 -->
      <div class="operation-banner">
        <div class="banner-left">
          <div class="banner-icon">
            <div class="icon-wrapper">
              <i class="i-material-symbols:person-add" v-if="isAdd"></i>
              <i class="i-material-symbols:person-edit" v-else></i>
            </div>
          </div>
          <div class="banner-content">
            <h3 class="banner-title">{{ isAdd ? '新增用户' : '编辑用户' }}</h3>
            <p class="banner-desc">{{ isAdd ? '填写用户基本信息，快速创建新用户账号' : '修改用户资料，保持信息准确性' }}</p>
          </div>
        </div>
        <div class="banner-right">
          <div class="progress-indicator">
            <div class="step-circle active">
              <i class="i-material-symbols:person"></i>
            </div>
            <span class="step-label">用户信息</span>
          </div>
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

          <NFormItem :label="$t('page.manage.user.nickName')" path="nickName">
            <NInput 
              v-model:value="model.nickName" 
              :placeholder="$t('page.manage.user.form.nickName')"
            >
              <template #prefix>
                <i class="i-material-symbols:person"></i>
              </template>
            </NInput>
          </NFormItem>

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

          <NFormItem :label="$t('page.manage.user.gender')" path="gender">
            <NRadioGroup v-model:value="model.gender">
              <NRadio v-for="item in dictOptions('gender')" :key="item.value" :value="item.value" :label="item.label" />
            </NRadioGroup>
          </NFormItem>
        </div>

        <!-- 工作信息 -->
        <div class="form-section">
          <div class="section-title">
            <i class="i-material-symbols:work"></i>
            工作信息
          </div>
          
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

          <NFormItem :label="$t('page.manage.user.workingYears')" path="workingYears">
            <NInput 
              v-model:value="model.workingYears" 
              placeholder="请输入工作年限（年）"
              type="number"
              :allow-input="(value) => !value || /^\d{1,2}$/.test(value)"
            >
              <template #prefix>
                <i class="i-material-symbols:schedule"></i>
              </template>
              <template #suffix>
                <span class="input-suffix">年</span>
              </template>
            </NInput>
            <div class="help-text">请直接输入工作年限（0-99年）</div>
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
      
      <!-- 底部操作按钮 -->
      <div class="drawer-footer">
        <NButton @click="closeDrawer" size="medium">
          取消
        </NButton>
        <NButton 
          type="primary" 
          @click="handleSubmit" 
          :loading="submitting"
          size="medium"
        >
          {{ isAdd ? '新增用户' : '更新用户' }}
        </NButton>
      </div>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped>
/* 用户管理抽屉专属样式 */
.user-drawer {
  /* 操作横幅美化 - 更紧凑 */
  .operation-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    margin: -24px -24px 16px -24px;
    padding: 16px 20px;
    color: white;
    border-radius: 0 0 12px 12px;
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: -50%;
      right: -50%;
      width: 200%;
      height: 200%;
      background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
      pointer-events: none;
    }

    .banner-left {
      display: flex;
      align-items: center;
      gap: 12px;
      z-index: 1;
    }

    .banner-icon {
      .icon-wrapper {
        width: 40px;
        height: 40px;
        background: rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);

        i {
          font-size: 20px;
          color: white;
        }
      }
    }

    .banner-content {
      .banner-title {
        font-size: 16px;
        font-weight: 600;
        margin: 0 0 4px 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
      }

      .banner-desc {
        font-size: 13px;
        opacity: 0.9;
        margin: 0;
        font-weight: 400;
      }
    }

    .banner-right {
      z-index: 1;

      .progress-indicator {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;

        .step-circle {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.2);
          display: flex;
          align-items: center;
          justify-content: center;
          border: 2px solid rgba(255, 255, 255, 0.3);
          backdrop-filter: blur(10px);

          &.active {
            background: rgba(255, 255, 255, 0.25);
            border-color: rgba(255, 255, 255, 0.5);
          }

          i {
            font-size: 16px;
            color: white;
          }
        }

        .step-label {
          font-size: 11px;
          font-weight: 500;
          opacity: 0.9;
        }
      }
    }
  }

  /* 表单区域美化 - 更紧凑 */
  .form-section {
    margin-bottom: 20px;
    background: rgba(255, 255, 255, 0.6);
    border-radius: 8px;
    padding: 16px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);

    .section-title {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 14px;
      font-weight: 600;
      color: #374151;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid #e2e8f0;

      i {
        font-size: 16px;
        color: #667eea;
      }
    }

    /* 表单项样式优化 - 更紧凑 */
    :deep(.n-form-item) {
      margin-bottom: 14px;

      .n-form-item-label {
        font-weight: 500;
        color: #374151;
        font-size: 13px;
        padding-bottom: 4px;
      }

      .n-input, .n-base-selection {
        min-height: 32px;
        border-radius: 6px;
        transition: all 0.2s ease;

        &:hover {
          box-shadow: 0 1px 4px rgba(102, 126, 234, 0.12);
        }

        &.n-input--focus, &.n-base-selection--focused {
          box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.15);
        }
      }

      .n-radio-group {
        .n-radio {
          margin-right: 12px;
          
          .radio-label {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 13px;

            .status-dot {
              width: 6px;
              height: 6px;
              border-radius: 50%;
              
              &.active {
                background: #10b981;
                box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
              }
              
              &.inactive {
                background: #ef4444;
                box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2);
              }
            }
          }
        }
      }
    }

    .help-text {
      font-size: 11px;
      color: #6b7280;
      margin-top: 3px;
      font-style: italic;
    }

    .input-suffix {
      color: #6b7280;
      font-size: 11px;
      font-weight: 500;
    }
  }

  /* 底部按钮样式 */
  .drawer-footer {
    position: sticky;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 100;
    margin-top: 20px;
    padding: 12px 16px;
    background: linear-gradient(to top, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.9) 100%);
    backdrop-filter: blur(8px);
    border-top: 1px solid rgba(0,0,0,0.06);
    border-radius: 8px 8px 0 0;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    box-shadow: 0 -2px 8px rgba(0,0,0,0.04);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-drawer {
    .operation-banner {
      flex-direction: column;
      gap: 12px;
      text-align: center;
      padding: 12px 16px;

      .banner-left {
        justify-content: center;
      }
    }

    .form-section {
      padding: 12px;
      margin-bottom: 16px;
    }

    .drawer-footer {
      padding: 10px 12px;
      gap: 8px;
    }
  }
}
</style>
