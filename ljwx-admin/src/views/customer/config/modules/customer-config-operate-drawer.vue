<script setup lang="ts">
import { computed, reactive, watch, ref } from 'vue';
import { useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { fetchAddCustomerConfig, fetchUpdateCustomerConfigInfo } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import { request } from '@/service/request';
import { NUpload, NPopconfirm, type UploadFileInfo } from 'naive-ui';

defineOptions({
  name: 'TCustomerConfigOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.Customer.CustomerConfig | null;
  /** the customer id */
  customerId?: number;
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

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: $t('common.add'),
    edit: $t('common.edit')
  };
  return titles[props.operateType];
});

interface EditModel {
  id?: number;
  customerName: string;
  description: string;
  uploadMethod: string;
  licenseKey: number;
  supportLicense: string;
  enableResume: string;
  uploadRetryCount: number;
  cacheMaxCount: number;
  logoUrl?: string;
  logoFileName?: string;
  logoUploadTime?: string;
}

const model: EditModel = reactive(createDefaultModel());

function createDefaultModel(): EditModel {
  return {
    id: undefined,
    customerName: '',
    description: '',
    uploadMethod: '',
    licenseKey: 0,
    supportLicense: 'false',
    enableResume: 'false',
    uploadRetryCount: 0,
    cacheMaxCount: 0,
    logoUrl: '',
    logoFileName: '',
    logoUploadTime: ''
  };
}

function handleInitModel() {
  Object.assign(model, createDefaultModel());

  if (!props.rowData) return;

  if (props.operateType === 'edit' && props.rowData) {
    Object.assign(model, {
      ...props.rowData,
      supportLicense: String(props.rowData.supportLicense),
      enableResume: String(props.rowData.enableResume)
    });
  }
}

function closeDrawer() {
  visible.value = false;
}

const isAdd = computed(() => props.operateType === 'add');

async function handleSubmit() {
  await validate();

  const submitData = {
    ...model,
    supportLicense: model.supportLicense === 'true',
    enableResume: model.enableResume === 'true'
  };

  const func = isAdd.value ? fetchAddCustomerConfig : fetchUpdateCustomerConfigInfo;
  const { error, data } = await func(submitData as any);
  if (!error && data) {
    window.$message?.success(isAdd.value ? $t('common.addSuccess') : $t('common.updateSuccess'));
    closeDrawer();
    emit('submitted');
  }
}

watch(visible, () => {
  if (visible.value) {
    handleInitModel();
    restoreValidation();
  }
});

const yesNoOptions = [
  { label: '是', value: 'true' },
  { label: '否', value: 'false' }
];

// Logo相关计算属性和方法
const logoSrc = computed(() => {
  const customerId = props.customerId ?? props.rowData?.id ?? (model as any).id;
  if (customerId === undefined || customerId === null) return '';
  
  // 添加时间戳防止缓存
  const timestamp = new Date().getTime();
  const baseUrl = `/t_customer_config/logo/${customerId}`;
  return `${baseUrl}?t=${timestamp}`;
});

function onLogoLoad() {
  console.log('Logo loaded successfully');
}

function onLogoError(e: Event) {
  console.log('Logo load failed, trying default:', e);
  const target = e.target as HTMLImageElement;
  if (!target.src.includes('logo/0')) {
    target.src = `/t_customer_config/logo/0?t=${new Date().getTime()}`;
  }
}

function formatDate(dateString?: string) {
  if (!dateString) return '';
  try {
    return new Date(dateString).toLocaleString('zh-CN');
  } catch {
    return dateString;
  }
}

// Logo上传相关
const logoUploading = ref(false);
const logoUploadRef = ref();

// 上传logo文件
async function handleLogoUpload(file: File) {
  // 使用传入的customerId或从rowData中获取ID
  const customerId = props.customerId ?? props.rowData?.id ?? (model as any).id;
  if (customerId === undefined || customerId === null) {
    window.$message?.error('请先保存客户配置后再上传Logo');
    return false;
  }
  
  // 验证文件类型
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    window.$message?.error('不支持的文件格式，请选择 PNG, JPG, JPEG, SVG 或 WEBP 格式');
    return false;
  }
  
  // 验证文件大小（2MB）
  if (file.size > 2 * 1024 * 1024) {
    window.$message?.error('文件大小不能超过2MB');
    return false;
  }

  logoUploading.value = true;
  
  try {
    // 上传文件
    const formData = new FormData();
    formData.append('file', file);
    formData.append('customerId', customerId.toString());
    
    console.log('开始上传文件...');
    const response = await request({
      url: '/t_customer_config/logo/upload',
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    if (response.data) {
      console.log('上传成功:', response.data);
      window.$message?.success('Logo上传成功');
      
      // 更新模型数据
      Object.assign(model, {
        logoUrl: response.data.logoUrl,
        logoFileName: response.data.fileName,
        logoUploadTime: response.data.uploadTime
      });
      
      // 触发提交事件让父组件刷新数据
      emit('submitted');
      
      return true;
    } else {
      throw new Error('服务器未返回数据');
    }
  } catch (error: any) {
    console.error('Logo上传失败:', error);
    const errorMsg = error?.response?.data?.message || error?.message || 'Logo上传失败';
    window.$message?.error(errorMsg);
    return false;
  } finally {
    logoUploading.value = false;
  }
}

// 删除logo
async function handleLogoDelete() {
  const customerId = props.customerId ?? props.rowData?.id ?? (model as any).id;
  if (customerId === undefined || customerId === null) {
    return;
  }
  
  try {
    const response = await request({
      url: `/t_customer_config/logo/${customerId}`,
      method: 'DELETE'
    });
    
    if (response.data) {
      window.$message?.success('Logo已重置为默认');
      
      // 清除模型中的logo数据
      Object.assign(model, {
        logoUrl: null,
        logoFileName: null,
        logoUploadTime: null
      });
      
      // 触发提交事件让父组件刷新数据
      emit('submitted');
    }
  } catch (error) {
    console.error('Logo删除失败:', error);
    window.$message?.error('Logo删除失败');
  }
}

// 处理上传前的钩子
function beforeUpload(data: { file: UploadFileInfo; fileList: UploadFileInfo[] }) {
  const file = data.file.file;
  if (!file) return false;
  
  return handleLogoUpload(file);
}
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="360">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model">
        <NFormItem :label="$t('page.customer.config.customerName')" path="customerName">
          <NInput v-model:value="model.customerName" :placeholder="$t('page.customer.config.form.customerName')" :disabled="!isAdd" />
        </NFormItem>
        <NFormItem :label="$t('page.customer.config.description')" path="description">
          <NInput v-model:value="model.description" :placeholder="$t('page.customer.config.form.description')" />
        </NFormItem>
        <NFormItem :label="$t('page.customer.config.uploadMethod')" path="uploadMethod">
          <NSelect
            v-model:value="model.uploadMethod"
            size="small"
            :placeholder="$t('page.customer.config.form.uploadMethod')"
            :options="dictOptions('upload_method')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.customer.config.licenseKey')" path="licenseKey">
          <NInputNumber v-model:value="model.licenseKey" :placeholder="$t('page.customer.config.form.licenseKey')" />
        </NFormItem>
        <NFormItem :label="$t('page.customer.config.supportLicense')" path="supportLicense">
          <NSelect
            v-model:value="model.supportLicense"
            size="small"
            :placeholder="$t('page.customer.config.form.supportLicense')"
            :options="yesNoOptions"
          />
        </NFormItem>
        <NFormItem :label="$t('page.customer.config.enableResume')" path="enableResume">
          <NSelect
            v-model:value="model.enableResume"
            size="small"
            :placeholder="$t('page.customer.config.form.enableResume')"
            :options="yesNoOptions"
          />
        </NFormItem>
        <NFormItem :label="$t('page.customer.config.uploadRetryCount')" path="uploadRetryCount">
          <NInputNumber v-model:value="model.uploadRetryCount" :placeholder="$t('page.customer.config.form.uploadRetryCount')" />
        </NFormItem>
        <NFormItem :label="$t('page.customer.config.cacheMaxCount')" path="cacheMaxCount">
          <NInputNumber v-model:value="model.cacheMaxCount" :placeholder="$t('page.customer.config.form.cacheMaxCount')" />
        </NFormItem>
        
        <!-- Logo管理功能 - 临时隐藏 -->
        <!-- 
        <NDivider title-placement="left">Logo管理</NDivider>
        
        <NFormItem label="当前Logo">
          <div class="flex flex-col gap-12px w-full">
            <div class="flex items-center gap-12px">
              <div class="logo-preview-container" style="width: 80px; height: 48px; border: 1px solid #e0e0e0; border-radius: 6px; background: #fafafa; display: flex; align-items: center; justify-content: center;">
                <img 
                  v-if="logoSrc"
                  :src="logoSrc"
                  alt="客户Logo预览"
                  style="max-width: 100%; max-height: 100%; object-fit: contain;"
                  @load="onLogoLoad"
                  @error="onLogoError"
                />
                <div v-else class="text-xs text-gray-400">暂无Logo</div>
              </div>
              <div class="flex flex-col gap-4px flex-1">
                <div class="text-sm text-gray-700">
                  {{ model.logoFileName || '使用默认Logo' }}
                </div>
                <div v-if="model.logoUploadTime" class="text-xs text-gray-500">
                  上传时间: {{ formatDate(model.logoUploadTime) }}
                </div>
              </div>
            </div>
            
            <div class="flex items-center gap-8px">
              <template v-if="!isAdd">
                <NUpload
                  ref="logoUploadRef"
                  :show-file-list="false"
                  :multiple="false"
                  accept="image/png,image/jpg,image/jpeg,image/svg+xml,image/webp"
                  :max="1"
                  :on-before-upload="beforeUpload"
                >
                  <NButton 
                    type="primary" 
                    size="small" 
                    :loading="logoUploading"
                    :disabled="logoUploading"
                  >
                    <template #icon>
                      <i class="i-carbon-cloud-upload" />
                    </template>
                    {{ logoUploading ? '上传中...' : '上传Logo' }}
                  </NButton>
                </NUpload>
                
                <NPopconfirm 
                  v-if="model.logoUrl" 
                  @positive-click="handleLogoDelete"
                >
                  <template #trigger>
                    <NButton type="warning" size="small" quaternary>
                      <template #icon>
                        <i class="i-carbon-trash-can" />
                      </template>
                      重置
                    </NButton>
                  </template>
                  确认删除自定义Logo并恢复默认？
                </NPopconfirm>
              </template>
              
              <div v-else class="text-xs text-orange-600">
                💡 请先保存客户配置，然后可以上传自定义Logo
              </div>
            </div>
            
            <div class="text-xs text-gray-500 bg-gray-50 p-8px rounded">
              <div class="font-medium mb-4px">Logo要求：</div>
              <div>• 支持格式：PNG, JPG, JPEG, SVG, WEBP</div>
              <div>• 文件大小：不超过2MB</div>
              <div>• 建议尺寸：建议使用正方形或横向矩形logo，保证最佳显示效果</div>
            </div>
          </div>
        </NFormItem>
        -->
      </NForm>
      <template #footer>
        <NSpace>
          <NButton quaternary @click="closeDrawer">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
