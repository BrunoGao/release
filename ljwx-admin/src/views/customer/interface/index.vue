<script setup lang="tsx">
import { NButton, NPopconfirm, NCard, NCollapse, NCollapseItem, NList, NListItem, NIcon, NSpace, NAlert } from 'naive-ui';
import type { Ref } from 'vue';
import { ref, shallowRef } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';
import { useAuth } from '@/hooks/business/auth';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';
import { transDeleteParams } from '@/utils/common';
import { fetchDeleteInterface, fetchGetInterfaceList, fetchGetOrgUnitsTree } from '@/service/api';
import { useDict } from '@/hooks/business/dict';
import InterfaceSearch from './modules/interface-search.vue';
import InterfaceOperateDrawer from './modules/interface-operate-drawer.vue';

defineOptions({
  name: 'TInterfacePage'
});

const operateType = ref<NaiveUI.TableOperateType>('add');

const appStore = useAppStore();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;
const { hasAuth } = useAuth();

const { dictTag } = useDict();

const editingData: Ref<Api.Customer.Interface | null> = ref(null);

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetInterfaceList,
  apiParams: {
    page: 1,
    pageSize: 20,
    name: null,
    customerId: customerId ?? 0
  },
  columns: () => [
    {
      key: 'index',
      title: $t('common.index'),
      width: 64,
      align: 'center'
    },
    {
      key: 'name',
      title: $t('page.customer.interface.name'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'url',
      title: $t('page.customer.interface.url'),
      align: 'center',
      width: 500
    },
    {
      key: 'callInterval',
      title: `${$t('page.customer.interface.callInterval')}(秒)`,
      align: 'center',
      minWidth: 100
    },
    {
      key: 'method',
      title: $t('page.customer.interface.method'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'description',
      title: $t('page.customer.interface.description'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'apiId',
      title: $t('page.customer.interface.apiId'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'apiAuth',
      title: $t('page.customer.interface.apiAuth'),
      align: 'center',
      minWidth: 100
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 200,
      minWidth: 200,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('t:interface:update') && (
            <NButton type="primary" quaternary size="small" onClick={() => edit(row)}>
              {$t('common.edit')}
            </NButton>
          )}
          {hasAuth('t:interface:delete') && (
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

function edit(item: Api.Customer.Interface) {
  operateType.value = 'edit';
  editingData.value = { ...item };
  console.log(editingData.value);
  openDrawer();
}

async function handleDelete(id: string) {
  // request
  const { error, data: result } = await fetchDeleteInterface(transDeleteParams([id]));
  if (!error && result) {
    await onDeleted();
  }
}

async function handleBatchDelete() {
  // request
  const { error, data: result } = await fetchDeleteInterface(transDeleteParams(checkedRowKeys.value));
  if (!error && result) {
    await onBatchDeleted();
  }
}


const manualExpanded = ref<string[]>([]);
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-8px overflow-hidden lt-sm:overflow-auto">
    <!-- 接口配置操作手册 -->
    <NCard :bordered="false" size="small" class="operation-manual">
      <NCollapse v-model:expanded-names="manualExpanded">
        <NCollapseItem name="manual" title="🔌 接口配置操作手册">
          <div class="space-y-4 text-sm max-h-400px overflow-y-auto">
            <!-- 接口类型说明 -->
            <NCard title="📡 接口配置说明" size="small">
              <NList>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#2080f0">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">接口名称</div>
                      <div class="text-gray-600">接口的标识名称，用于系统内部调用和管理</div>
                    </div>
                  </NSpace>
                </NListItem>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#18a058">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H6.99c-2.76 0-5 2.24-5 5s2.24 5 5 5H11v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm5-6h4.01c2.76 0 5 2.24 5 5s-2.24 5-5 5H13v1.9h4.01c2.76 0 5-2.24 5-5s-2.24-5-5-5H13V7z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">接口URL</div>
                      <div class="text-gray-600">外部系统的API接口地址，支持HTTP/HTTPS协议</div>
                    </div>
                  </NSpace>
                </NListItem>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#f0a020">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">调用间隔</div>
                      <div class="text-gray-600">系统调用该接口的时间间隔（秒），影响数据同步频率</div>
                    </div>
                  </NSpace>
                </NListItem>
                <NListItem>
                  <NSpace>
                    <NIcon size="16" color="#d03050">
                      <svg viewBox="0 0 24 24"><path fill="currentColor" d="M7.5 5.6L10 7L8.6 4.5L10 2L7.5 3.4L5 2l1.4 2.5L5 7l2.5-1.4zm12 9.8L17 14l1.4 2.5L17 19l2.5-1.4L22 19l-1.4-2.5L22 14l-2.5 1.4zM22 2l-2.5 1.4L17 2l1.4 2.5L17 7l2.5-1.4L22 7l-1.4-2.5L22 2zM13.34 12.78l-1.12-1.12l-6.01 6.01l1.12 1.12l6.01-6.01z"/></svg>
                    </NIcon>
                    <div>
                      <div class="font-medium">请求方法</div>
                      <div class="text-gray-600">HTTP请求方法：GET、POST、PUT、DELETE</div>
                    </div>
                  </NSpace>
                </NListItem>
              </NList>
            </NCard>

            <!-- 配置影响说明 -->
            <NCard title="⚙️ 配置项影响" size="small">
              <NList>
                <NListItem>
                  <div>
                    <div class="font-medium text-orange-600">⏱️ 调用间隔设置</div>
                    <div class="text-gray-600 mt-1">• 影响：数据同步实时性和系统负载</div>
                    <div class="text-gray-600">• 建议：实时数据3-30秒，统计数据60-300秒</div>
                    <div class="text-gray-600">• 风险：间隔过短增加网络负载，过长影响数据时效性</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium text-blue-600">🔒 API认证配置</div>
                    <div class="text-gray-600 mt-1">• 影响：外部接口访问权限和安全性</div>
                    <div class="text-gray-600">• 建议：使用Token或API Key进行身份验证</div>
                    <div class="text-gray-600">• 风险：认证失败将导致接口调用被拒绝</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium text-green-600">🌐 接口URL配置</div>
                    <div class="text-gray-600 mt-1">• 影响：决定数据来源和通信路径</div>
                    <div class="text-gray-600">• 建议：使用HTTPS确保传输安全，配置备用地址</div>
                    <div class="text-gray-600">• 风险：URL错误会导致数据同步中断</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium text-purple-600">🔧 请求方法选择</div>
                    <div class="text-gray-600 mt-1">• 影响：接口调用方式和数据传输格式</div>
                    <div class="text-gray-600">• 建议：GET用于查询，POST用于创建，PUT用于更新</div>
                    <div class="text-gray-600">• 风险：方法不匹配会导致接口调用失败</div>
                  </div>
                </NListItem>
              </NList>
            </NCard>

            <!-- 操作指南 -->
            <NCard title="📖 操作指南" size="small">
              <NList>
                <NListItem>
                  <div>
                    <div class="font-medium">1. 新增接口配置</div>
                    <div class="text-gray-600 mt-1">点击"新增"按钮 → 填写接口名称和URL → 设置调用间隔 → 配置认证信息 → 测试连通性 → 保存</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium">2. 编辑接口配置</div>
                    <div class="text-gray-600 mt-1">点击"编辑"按钮 → 修改配置参数 → 验证接口可用性 → 保存更改</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium">3. 接口测试</div>
                    <div class="text-gray-600 mt-1">配置完成后建议进行连通性测试，确保外部系统正常响应</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium">4. 监控调用状态</div>
                    <div class="text-gray-600 mt-1">定期检查接口调用日志，及时发现和处理异常情况</div>
                  </div>
                </NListItem>
              </NList>
            </NCard>

            <!-- 安全建议 -->
            <NCard title="🔐 安全建议" size="small">
              <NList>
                <NListItem>
                  <div>
                    <div class="font-medium">数据传输安全</div>
                    <div class="text-gray-600 mt-1">• 优先使用HTTPS协议加密传输</div>
                    <div class="text-gray-600">• 配置API密钥或Token认证</div>
                    <div class="text-gray-600">• 避免在URL中传递敏感信息</div>
                  </div>
                </NListItem>
                <NListItem>
                  <div>
                    <div class="font-medium">访问控制</div>
                    <div class="text-gray-600 mt-1">• 配置IP白名单限制访问来源</div>
                    <div class="text-gray-600">• 设置合理的调用频率限制</div>
                    <div class="text-gray-600">• 定期更新认证凭据</div>
                  </div>
                </NListItem>
              </NList>
            </NCard>

            <!-- 注意事项 -->
            <NAlert type="warning" title="⚠️ 重要提醒" show-icon class="mt-4">
              <div class="space-y-2">
                <div>• 修改接口配置可能影响数据同步，建议在维护窗口进行</div>
                <div>• 调用间隔过短可能被外部系统限流，请合理设置</div>
                <div>• 接口认证信息变更后需要同步更新相关配置</div>
                <div>• 删除接口配置前请确认没有业务流程依赖</div>
              </div>
            </NAlert>
          </div>
        </NCollapseItem>
      </NCollapse>
    </NCard>

    <InterfaceSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard :bordered="false" class="sm:flex-1-hidden card-wrapper" content-class="flex-col">
      <TableHeaderOperation
        v-model:columns="columnChecks"
        :checked-row-keys="checkedRowKeys"
        :loading="loading"
        add-auth="t:interface:add"
        delete-auth="t:interface:delete"
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
      <InterfaceOperateDrawer v-model:visible="drawerVisible" :operate-type="operateType" :row-data="editingData" @submitted="getDataByPage" />
    </NCard>
  </div>
</template>
