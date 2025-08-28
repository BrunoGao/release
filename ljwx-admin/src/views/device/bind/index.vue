<script setup lang="tsx">
import { onMounted, reactive, ref } from 'vue';
import type { Ref } from 'vue';
import { NButton, NCard, NForm, NFormItem, NInput, NModal, NPopconfirm, NSelect, NTag } from 'naive-ui';
import type { DataTableColumns, FormInst, FormRules } from 'naive-ui';
import { batchApproveBindingApplications, fetchDeviceBindingApplications } from '@/service/api';
import { useBoolean, useLoading } from '@/hooks/common';
import { useAppStore } from '@/store/modules/app';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { $t } from '@/locales';

defineOptions({
  name: 'DeviceBind',
  meta: {
    roles: ['R_ADMIN'],
    icon: 'ic:round-link',
    order: 1
  }
});

const appStore = useAppStore();
const { loading, startLoading, endLoading } = useLoading(false);
const { bool: showCommentModal, setTrue: openCommentModal, setFalse: closeCommentModal } = useBoolean();

// 搜索参数
const searchParams = reactive({
  status: ''
});

// 状态选项
const statusOptions = [
  { label: '待审批', value: 'PENDING' },
  { label: '已通过', value: 'APPROVED' },
  { label: '已拒绝', value: 'REJECTED' }
];

// 状态标签渲染
const statusTagMap: Record<string, { type: 'warning' | 'success' | 'error'; label: string }> = {
  PENDING: { type: 'warning', label: '待审批' },
  APPROVED: { type: 'success', label: '已通过' },
  REJECTED: { type: 'error', label: '已拒绝' }
};

// 表格列定义
const columns: Ref<DataTableColumns<Api.DeviceBinding.DeviceBindRequest>> = ref([
  {
    type: 'selection',
    align: 'center',
    width: 48
  },
  {
    key: 'id',
    title: '申请ID',
    align: 'center',
    width: 100
  },
  {
    key: 'deviceSn',
    title: '设备序列号',
    align: 'center',
    width: 180
  },
  {
    key: 'userId',
    title: '申请用户ID',
    align: 'center',
    width: 120
  },
  {
    key: 'userName',
    title: '用户姓名',
    align: 'center',
    width: 100
  },
  {
    key: 'phoneNumber',
    title: '手机号码',
    align: 'center',
    width: 140
  },
  {
    key: 'applyTime',
    title: '申请时间',
    align: 'center',
    width: 180,
    render: row => {
      return row.applyTime ? new Date(row.applyTime).toLocaleString() : '-';
    }
  },
  {
    key: 'status',
    title: '申请状态',
    align: 'center',
    width: 100,
    render: row => {
      if (row.status && statusTagMap[row.status]) {
        const tagInfo = statusTagMap[row.status];
        return <NTag type={tagInfo.type}>{tagInfo.label}</NTag>;
      }
      return '-';
    }
  },
  {
    key: 'approveTime',
    title: '审批时间',
    align: 'center',
    width: 180,
    render: row => {
      return row.approveTime ? new Date(row.approveTime).toLocaleString() : '-';
    }
  },
  {
    key: 'approverName',
    title: '审批人',
    align: 'center',
    width: 100
  },
  {
    key: 'comment',
    title: '审批备注',
    align: 'center',
    width: 150,
    ellipsis: true
  },
  {
    key: 'operate',
    title: $t('common.operate'),
    align: 'center',
    width: 180,
    fixed: 'right',
    render: row => (
      <div class="flex-center gap-8px">
        {row.status === 'PENDING' && (
          <>
            <NButton type="primary" ghost size="small" onClick={() => handleSingleApprove(row, 'APPROVED')}>
              通过
            </NButton>
            <NPopconfirm onPositiveClick={() => handleSingleApprove(row, 'REJECTED')}>
              {{
                default: () => '确定拒绝此申请？',
                trigger: () => (
                  <NButton type="error" ghost size="small">
                    拒绝
                  </NButton>
                )
              }}
            </NPopconfirm>
          </>
        )}
        {row.status !== 'PENDING' && (
          <NButton disabled size="small">
            已处理
          </NButton>
        )}
      </div>
    )
  }
]);

// 表格数据和操作
const { tableData, naiveTableRef, mobilePagination, searchQuery, resetSearchQuery } = useTable({
  apiFn: fetchDeviceBindingApplications,
  showTotal: true,
  apiParams: {
    current: 1,
    size: 10,
    status: searchParams.status || undefined
  }
});

const { checkedRowKeys } = useTableOperate(tableData, mobilePagination);

// 行键
function rowKey(row: Api.DeviceBinding.DeviceBindRequest) {
  return row.id;
}

// 获取表格数据
async function getTableData() {
  searchQuery();
}

// 审批备注表单
const commentFormRef = ref<FormInst | null>(null);
const commentForm = reactive({
  comment: ''
});
const commentRules: FormRules = {
  comment: [{ max: 500, message: '备注不能超过500个字符' }]
};

// 当前审批操作
let currentApproveAction: 'APPROVED' | 'REJECTED' = 'APPROVED';
let currentApproveIds: string[] = [];

// 单个审批
function handleSingleApprove(row: Api.DeviceBinding.DeviceBindRequest, action: 'APPROVED' | 'REJECTED') {
  currentApproveAction = action;
  currentApproveIds = [row.id.toString()];

  if (action === 'REJECTED') {
    // 拒绝时需要备注
    openCommentModal();
  } else {
    // 通过时直接执行
    performApprove();
  }
}

// 批量审批
function batchApprove(action: 'APPROVED' | 'REJECTED') {
  if (!checkedRowKeys.value.length) {
    $message.warning('请选择要审批的申请');
    return;
  }

  currentApproveAction = action;
  currentApproveIds = checkedRowKeys.value.map(key => key.toString());

  if (action === 'REJECTED') {
    // 拒绝时需要备注
    openCommentModal();
  } else {
    // 通过时直接执行
    performApprove();
  }
}

// 确认审批
async function confirmApprove() {
  await commentFormRef.value?.validate();
  performApprove();
  closeCommentModal();
}

// 执行审批操作
async function performApprove() {
  try {
    startLoading();

    const params = {
      ids: currentApproveIds,
      action: currentApproveAction,
      approverId: appStore.userInfo.userId.toString(),
      comment: commentForm.comment || undefined
    };

    await batchApproveBindingApplications(params);

    $message.success(
      currentApproveAction === 'APPROVED' ? `成功通过 ${currentApproveIds.length} 个申请` : `成功拒绝 ${currentApproveIds.length} 个申请`
    );

    // 重置表单和选择
    commentForm.comment = '';
    checkedRowKeys.value = [];

    // 刷新数据
    getTableData();
  } catch (error) {
    console.error('审批失败:', error);
    $message.error('审批操作失败，请重试');
  } finally {
    endLoading();
  }
}

onMounted(() => {
  getTableData();
});
</script>

<template>
  <div class="flex-vertical-stretch gap-16px overflow-hidden <sm:overflow-auto">
    <NCard title="设备绑定申请管理" :bordered="false" size="small" class="sm:flex-1-hidden card-wrapper">
      <!-- 搜索区域 -->
      <template #header-extra>
        <div class="flex-y-center gap-12px">
          <NSelect
            v-model:value="searchParams.status"
            :options="statusOptions"
            placeholder="申请状态"
            clearable
            class="w-120px"
            @update:value="getTableData"
          />
          <NButton type="primary" ghost @click="getTableData">
            <template #icon>
              <icon-ic-round-refresh class="text-icon" />
            </template>
            刷新
          </NButton>
        </div>
      </template>

      <!-- 批量操作 -->
      <div class="mb-16px flex-y-center gap-12px">
        <NButton type="primary" :disabled="!checkedRowKeys.length" @click="batchApprove('APPROVED')">
          <template #icon>
            <icon-ic-round-check class="text-icon" />
          </template>
          批量通过
        </NButton>
        <NButton type="error" :disabled="!checkedRowKeys.length" @click="batchApprove('REJECTED')">
          <template #icon>
            <icon-ic-round-close class="text-icon" />
          </template>
          批量拒绝
        </NButton>
        <span class="text-12px text-#666">已选择 {{ checkedRowKeys.length }} 项</span>
      </div>

      <!-- 数据表格 -->
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="tableData"
        size="small"
        :flex-height="true"
        :scroll-x="1200"
        :loading="loading"
        remote
        :row-key="rowKey"
        :pagination="mobilePagination"
        class="sm:h-full"
      />

      <!-- 审批备注弹窗 -->
      <NModal v-model:show="showCommentModal" :mask-closable="false">
        <NCard style="width: 500px" title="审批备注" :bordered="false" size="huge" role="dialog" aria-modal="true">
          <NForm ref="commentFormRef" :model="commentForm" :rules="commentRules">
            <NFormItem label="审批备注" path="comment">
              <NInput v-model:value="commentForm.comment" type="textarea" placeholder="请输入审批备注(可选)" :rows="4" />
            </NFormItem>
          </NForm>
          <template #footer>
            <div class="flex-y-center justify-end gap-12px">
              <NButton @click="showCommentModal = false">取消</NButton>
              <NButton type="primary" @click="confirmApprove">确认</NButton>
            </div>
          </template>
        </NCard>
      </NModal>
    </NCard>
  </div>
</template>

<style scoped>
.card-wrapper {
  @apply flex-1-hidden;
}
</style>
