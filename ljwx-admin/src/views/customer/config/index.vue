<script setup lang="tsx">
import { NButton, NPopconfirm, NUpload, type UploadFileInfo } from 'naive-ui';
import type { Ref } from 'vue';
import { ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';
import { useAuth } from '@/hooks/business/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteCustomerConfig, fetchGetCustomerConfigList, fetchGetOrgUnitsTree } from '@/service/api';
import { request } from '@/service/request';
import { useDict } from '@/hooks/business/dict';
import CustomerConfigSearch from './modules/customer-config-search.vue';
import CustomerConfigOperateDrawer from './modules/customer-config-operate-drawer.vue';

defineOptions({
  name: 'TCustomerConfigPage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;
const { hasAuth } = useAuth();

const { dictTag } = useDict();

const editingData: Ref<Api.Customer.CustomerConfig | null> = ref(null);

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetCustomerConfigList,
  apiParams: {
    page: 1,
    pageSize: 20,
    id: customerId
  },
  columns: () => [
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },
    {
      key: 'id',
      title: '租户ID',
      align: 'center',
      minWidth: 150
    },
    {
      key: 'customerName',
      title: '租户名称',
      align: 'center',
      minWidth: 100
    },
    {
      key: 'description',
      title: '租户描述',
      align: 'center',
      minWidth: 100
    },
    {
      key: 'uploadMethod',
      title: '上传方法',
      align: 'center',
      minWidth: 100,
      render: row => dictTag('upload_method', row.uploadMethod)
    },
    {
      key: 'licenseKey',
      title: '许可证',
      align: 'center',
      minWidth: 100
    },
    {
      key: 'supportLicense',
      title: '支持许可证',
      align: 'center',
      minWidth: 100,
      render: row => (row.supportLicense ? '是' : '否')
    },
    {
      key: 'enableResume',
      title: '是否启用续传',
      align: 'center',
      minWidth: 100,
      render: row => (row.enableResume ? '是' : '否')
    },
    {
      key: 'uploadRetryCount',
      title: '上传重试次数',
      align: 'center',
      minWidth: 100
    },
    {
      key: 'cacheMaxCount',
      title: '缓存最大数量',
      align: 'center',
      minWidth: 100
    },
    {
      key: 'logo',
      title: 'Logo',
      align: 'center',
      minWidth: 120,
      render: row => {
        // 通过代理访问静态文件
        let logoSrc = '';
        if (row.logoUrl) {
          // 使用代理路径访问logo文件
          logoSrc = `${row.logoUrl}?t=${Date.now()}`;
        } else {
          // 没有logoUrl，使用默认logo
          logoSrc = `/uploads/logos/defaults/default-logo.svg?t=${Date.now()}`;
        }
          
        return (
          <div class="flex items-center gap-8px">
            <div style="width: 40px; height: 24px; border: 1px solid #e0e0e0; border-radius: 4px; overflow: hidden; display: flex; align-items: center; justify-content: center; background: #fafafa;">
              <img 
                src={logoSrc}
                alt="客户Logo"
                style="max-width: 100%; max-height: 100%; object-fit: contain;"
                onError={(e: Event) => {
                  const target = e.target as HTMLImageElement;
                  // 如果加载失败，尝试加载默认logo
                  if (!target.src.includes('default-logo.svg')) {
                    target.src = `/uploads/logos/defaults/default-logo.svg?t=${Date.now()}`;
                  } else {
                    // 默认logo也加载失败，显示文本
                    target.style.display = 'none';
                    target.parentElement!.innerHTML = '<div class="text-xs text-gray-400">无</div>';
                  }
                }}
                onLoad={(e: Event) => {
                  const target = e.target as HTMLImageElement;
                  console.log(`Logo loaded for customer ${row.id}: ${target.src}`);
                }}
              />
            </div>
            <div class="text-xs text-gray-500 truncate" style="max-width: 60px;">
              {row.logoFileName || '默认'}
            </div>
          </div>
        );
      }
    },

    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 280,
      minWidth: 280,
      render: row => (
        <div class="flex-center gap-4px flex-wrap">
          {hasAuth('t:customer:config:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:customer:config:logo:upload') && (
            <NButton type="info" quaternary size="small" onClick={() => handleLogoUpload(row)}>
              Logo
            </NButton>
          )}
          {hasAuth('t:customer:config:logo:delete') && row.logoUrl && (
            <NPopconfirm onPositiveClick={() => handleLogoDelete(row.id)}>
              {{
                default: () => '确认删除Logo并恢复默认？',
                trigger: () => (
                  <NButton type="warning" quaternary size="small">
                    重置
                  </NButton>
                )
              }}
            </NPopconfirm>
          )}
          {hasAuth('t:customer:config:delete') && (
            <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
              {{
                default: () => $t('common.confirmDelete'),
                trigger: () => (
                  <NButton type="error" quaternary size="small">
                    {$t('common.delete')}
                  </NButton>
                )
              }}
            </NPopconfirm>
          )}
        </div>
      )
    }
  ]
});

const { drawerVisible, openDrawer, checkedRowKeys, onDeleted, onBatchDeleted } = useTableOperate(data, getData);

function handleAdd() {
  operateType.value = 'add';
  openDrawer();
}

function edit(item: Api.Customer.CustomerConfig) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteCustomerConfig(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteCustomerConfig(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}

// Logo管理相关
function handleLogoUpload(row: Api.Customer.CustomerConfig) {
  console.log('开始上传Logo，客户ID:', row.id);
  
  // 创建一个隐藏的文件输入框
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/png,image/jpg,image/jpeg,image/svg+xml,image/webp';
  input.style.display = 'none';
  input.multiple = false;
  
  // 添加change事件监听器
  const handleFileSelect = async (e: Event) => {
    console.log('文件选择事件触发');
    const target = e.target as HTMLInputElement;
    const file = target.files?.[0];
    
    if (!file) {
      console.log('未选择文件');
      return;
    }
    
    console.log('选择的文件:', file.name, '大小:', file.size, '类型:', file.type);
    
    // 验证文件类型
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      window.$message?.error('不支持的文件格式，请选择 PNG, JPG, JPEG, SVG 或 WEBP 格式');
      cleanup();
      return;
    }
    
    // 验证文件大小（2MB）
    if (file.size > 2 * 1024 * 1024) {
      window.$message?.error('文件大小不能超过2MB');
      cleanup();
      return;
    }
    
    // 显示加载提示
    const loadingMessage = window.$message?.loading('正在上传Logo...', { duration: 0 });
    
    try {
      // 上传文件
      const formData = new FormData();
      formData.append('file', file);
      formData.append('customerId', row.id.toString());
      
      console.log('开始上传文件...');
      const response = await request({
        url: '/t_customer_config/logo/upload',
        method: 'POST',
        data: formData,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      loadingMessage?.destroy();
      
      if (response.data) {
        console.log('上传成功:', response.data);
        window.$message?.success('Logo上传成功');
        await getData(); // 刷新表格数据
      } else {
        throw new Error('服务器未返回数据');
      }
    } catch (error: any) {
      loadingMessage?.destroy();
      console.error('Logo上传失败:', error);
      const errorMsg = error?.response?.data?.message || error?.message || 'Logo上传失败';
      window.$message?.error(errorMsg);
    }
    
    cleanup();
  };
  
  const cleanup = () => {
    if (document.body.contains(input)) {
      input.removeEventListener('change', handleFileSelect);
      document.body.removeChild(input);
    }
  };
  
  input.addEventListener('change', handleFileSelect);
  document.body.appendChild(input);
  
  // 触发文件选择对话框
  console.log('触发文件选择对话框');
  input.click();
}

async function handleLogoDelete(customerId: string) {
  try {
    const response = await request({
      url: `/t_customer_config/logo/${customerId}`,
      method: 'DELETE'
    });
    
    if (response.data) {
      window.$message?.success('Logo已重置为默认');
      await getData(); // 刷新表格数据
    }
  } catch (error) {
    console.error('Logo删除失败:', error);
    window.$message?.error('Logo删除失败');
  }
}

const orgUnitsName = ref<{ label: string; value: string }[]>([]);

async function handleInitOptions() {
  fetchGetOrgUnitsTree(customerId).then(({ error: err, data: treeData }) => {
    if (!err && treeData) {
      // 提取 parentId 为 0 的选项
      orgUnitsName.value = treeData
        .filter(item => item.parentId === 0)
        .map(item => ({
          label: item.name,
          value: item.id
        }));
    }
  });
}
handleInitOptions();
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <CustomerConfigSearch v-model:model="searchParams" :org-units-name="orgUnitsName" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="t:customer:config:add"
        delete-auth="t:customer:config:delete"
        @add="handleAdd"
        @delete="handleBatchDelete"
        @refresh="getData"
      />
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        remote
        striped
        size="small"
        class="sm:h-full"
        :data="data"
        :scroll-x="962"
        :columns="columns"
        :flex-height="!appStore.isMobile"
        :loading="loading"
        :single-line="false"
        :row-key="row => row.id"
        :pagination="mobilePagination"
      />
      <CustomerConfigOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" :customer-id="customerId" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>
