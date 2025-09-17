<script setup lang="ts">
import { computed, h, onMounted, reactive, ref, watch } from 'vue';
import type { DataTableColumn } from 'naive-ui';
import { NButton, NPopconfirm, NTag, NTooltip, useMessage } from 'naive-ui';
import { useDynamicMenu } from '@/hooks/business/use-dynamic-menu';
import SvgIcon from '@/components/custom/svg-icon.vue';
import { $t } from '@/locales';
import ScanResultModal from './modules/scan-result-modal.vue';
import MenuEditModal from './modules/menu-edit-modal.vue';
import BatchUpdateModal from './modules/batch-update-modal.vue';

defineOptions({
  name: 'DynamicMenuManagement'
});

interface MenuRecord {
  id: number;
  parentId?: number;
  type: string;
  name: string;
  title: string;
  routePath: string;
  component: string;
  icon: string;
  status: string;
  hide: string;
  sort: number;
  level: number;
  permission: string;
  source: string;
  sourceFile?: string;
  lastScanTime?: string;
  isSystem: boolean;
  deletable: boolean;
  editable: boolean;
  children?: MenuRecord[];
  createTime: string;
  updateTime: string;
}

const message = useMessage();

// 响应式数据
const loading = ref(false);
const menuData = ref<MenuRecord[]>([]);
const totalCount = computed(() => {
  const count = (items: MenuRecord[]): number => {
    return items.reduce((acc, item) => {
      return acc + 1 + (item.children ? count(item.children) : 0);
    }, 0);
  };
  return count(menuData.value);
});

// 筛选条件
const searchQuery = ref('');
const statusFilter = ref<string>();
const typeFilter = ref<string>();
const sourceFilter = ref<string>();

// 选择的行
const selectedRowKeys = ref<number[]>([]);

// 模态框控制
const scanResultVisible = ref(false);
const editVisible = ref(false);
const batchVisible = ref(false);

// 操作数据
const scanResult = ref();
const editingMenu = ref<MenuRecord>();
const operationType = ref<'add' | 'edit'>('add');

// 使用动态菜单钩子
const { getDynamicMenus, scanRoutes, autoSyncMenus, updateMenuConfig, batchUpdateMenus } = useDynamicMenu();

// 筛选选项
const statusOptions = [
  { label: '启用', value: '1' },
  { label: '禁用', value: '0' }
];

const typeOptions = [
  { label: '目录', value: '1' },
  { label: '菜单', value: '2' },
  { label: '按钮', value: '3' }
];

const sourceOptions = [
  { label: '手动创建', value: 'manual' },
  { label: '路由扫描', value: 'scan' },
  { label: '配置导入', value: 'import' }
];

// 表格列配置
const columns: DataTableColumn<MenuRecord>[] = [
  {
    type: 'selection',
    disabled: (row: MenuRecord) => !row.deletable
  },
  {
    key: 'name',
    title: '菜单名称',
    minWidth: 200,
    render: (row: MenuRecord) => {
      return h('div', { class: 'flex-y-center gap-8px' }, [
        h(SvgIcon, { icon: row.icon || 'mdi:menu', class: 'text-16px' }),
        h('span', row.name),
        row.isSystem ? h(NTag, { type: 'info', size: 'small' }, () => '系统') : null
      ]);
    }
  },
  {
    key: 'title',
    title: '显示名称',
    width: 120,
    ellipsis: {
      tooltip: true
    }
  },
  {
    key: 'type',
    title: '类型',
    width: 80,
    render: (row: MenuRecord) => {
      const typeMap = {
        '1': { label: '目录', type: 'info' as const },
        '2': { label: '菜单', type: 'success' as const },
        '3': { label: '按钮', type: 'warning' as const }
      };
      const config = typeMap[row.type as keyof typeof typeMap] || { label: '未知', type: 'default' as const };
      return h(NTag, { type: config.type, size: 'small' }, () => config.label);
    }
  },
  {
    key: 'routePath',
    title: '路由路径',
    width: 200,
    ellipsis: {
      tooltip: true
    }
  },
  {
    key: 'component',
    title: '组件路径',
    width: 200,
    ellipsis: {
      tooltip: true
    }
  },
  {
    key: 'status',
    title: '状态',
    width: 80,
    render: (row: MenuRecord) => {
      const statusMap = {
        '1': { label: '启用', type: 'success' as const },
        '0': { label: '禁用', type: 'error' as const }
      };
      const config = statusMap[row.status as keyof typeof statusMap];
      return h(NTag, { type: config.type, size: 'small' }, () => config.label);
    }
  },
  {
    key: 'sort',
    title: '排序',
    width: 80,
    align: 'center'
  },
  {
    key: 'source',
    title: '来源',
    width: 100,
    render: (row: MenuRecord) => {
      const sourceMap = {
        manual: { label: '手动', type: 'default' as const },
        scan: { label: '扫描', type: 'info' as const },
        import: { label: '导入', type: 'warning' as const }
      };
      const config = sourceMap[row.source as keyof typeof sourceMap] || { label: '未知', type: 'default' as const };
      return h(NTag, { type: config.type, size: 'small' }, () => config.label);
    }
  },
  {
    key: 'actions',
    title: '操作',
    width: 200,
    align: 'center',
    render: (row: MenuRecord) => {
      return h('div', { class: 'flex-center gap-8px' }, [
        row.editable
          ? h(
              NButton,
              {
                size: 'small',
                type: 'primary',
                secondary: true,
                onClick: () => handleEdit(row)
              },
              () => '编辑'
            )
          : null,
        h(
          NButton,
          {
            size: 'small',
            type: 'info',
            secondary: true,
            onClick: () => handleViewDetails(row)
          },
          () => '详情'
        ),
        row.deletable
          ? h(
              NPopconfirm,
              {
                onPositiveClick: () => handleDelete(row)
              },
              {
                default: () => '确认删除这个菜单吗？',
                trigger: () =>
                  h(
                    NButton,
                    {
                      size: 'small',
                      type: 'error',
                      secondary: true
                    },
                    () => '删除'
                  )
              }
            )
          : null
      ]);
    }
  }
];

// 数据加载
async function loadMenuData() {
  loading.value = true;
  try {
    const { data } = await getDynamicMenus();
    menuData.value = buildMenuTree(data || []);
  } catch (error) {
    message.error('加载菜单数据失败');
  } finally {
    loading.value = false;
  }
}

// 构建菜单树
function buildMenuTree(menus: MenuRecord[]): MenuRecord[] {
  const map = new Map<number, MenuRecord>();
  const roots: MenuRecord[] = [];

  // 第一遍遍历，建立映射
  menus.forEach(menu => {
    map.set(menu.id, { ...menu, children: [] });
  });

  // 第二遍遍历，构建树形结构
  menus.forEach(menu => {
    const currentMenu = map.get(menu.id)!;
    if (!menu.parentId || menu.parentId === 0) {
      roots.push(currentMenu);
    } else {
      const parent = map.get(menu.parentId);
      if (parent) {
        parent.children!.push(currentMenu);
      } else {
        roots.push(currentMenu); // 找不到父级时放到根级
      }
    }
  });

  // 排序
  const sortMenus = (menus: MenuRecord[]): MenuRecord[] => {
    return menus
      .sort((a, b) => (a.sort || 0) - (b.sort || 0))
      .map(menu => {
        if (menu.children && menu.children.length > 0) {
          menu.children = sortMenus(menu.children);
        }
        return menu;
      });
  };

  return sortMenus(roots);
}

// 事件处理
function refreshData() {
  loadMenuData();
}

function handleSearch() {
  // TODO: 实现搜索逻辑
  console.log('搜索:', searchQuery.value);
}

function handleFilterChange() {
  // TODO: 实现筛选逻辑
  console.log('筛选变更');
}

function handleCheckedRowKeysChange(keys: number[]) {
  selectedRowKeys.value = keys;
}

// 扫描路由
async function handleScanRoutes() {
  try {
    loading.value = true;
    const { data } = await scanRoutes({
      frontendPath: '/src/views', // 这里应该从配置中获取
      scanMode: 'auto',
      recursive: true,
      autoCreate: false
    });
    scanResult.value = data;
    scanResultVisible.value = true;
  } catch (error) {
    message.error('扫描路由失败');
  } finally {
    loading.value = false;
  }
}

// 自动同步
async function handleAutoSync() {
  try {
    loading.value = true;
    const { data } = await autoSyncMenus({
      frontendPath: '/src/views',
      scanMode: 'auto',
      recursive: true,
      autoCreate: true,
      overwriteExisting: false
    });
    message.success(data || '同步完成');
    loadMenuData();
  } catch (error) {
    message.error('自动同步失败');
  } finally {
    loading.value = false;
  }
}

// 同步菜单
async function handleSyncMenus(routes: any[]) {
  try {
    const { data } = await autoSyncMenus({
      frontendPath: '/src/views',
      scanMode: 'manual',
      autoCreate: true,
      overwriteExisting: true
    });
    message.success(data || '同步完成');
    loadMenuData();
    scanResultVisible.value = false;
  } catch (error) {
    message.error('同步菜单失败');
  }
}

// 新增菜单
function handleAddMenu() {
  editingMenu.value = undefined;
  operationType.value = 'add';
  editVisible.value = true;
}

// 编辑菜单
function handleEdit(menu: MenuRecord) {
  editingMenu.value = { ...menu };
  operationType.value = 'edit';
  editVisible.value = true;
}

// 查看详情
function handleViewDetails(menu: MenuRecord) {
  // TODO: 实现查看详情
  console.log('查看详情:', menu);
}

// 删除菜单
async function handleDelete(menu: MenuRecord) {
  try {
    // TODO: 实现删除逻辑
    message.success('删除成功');
    loadMenuData();
  } catch (error) {
    message.error('删除失败');
  }
}

// 编辑确认
async function handleEditConfirm(menuData: any) {
  try {
    const { data } = await updateMenuConfig(menuData);
    message.success(data || '保存成功');
    loadMenuData();
    editVisible.value = false;
  } catch (error) {
    message.error('保存失败');
  }
}

// 批量操作
function handleBatchUpdate() {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请先选择要操作的菜单');
    return;
  }
  batchVisible.value = true;
}

// 批量操作确认
async function handleBatchConfirm(batchData: any) {
  try {
    const { data } = await batchUpdateMenus({
      menuIds: selectedRowKeys.value,
      ...batchData
    });
    message.success(data || '批量操作完成');
    loadMenuData();
    batchVisible.value = false;
    selectedRowKeys.value = [];
  } catch (error) {
    message.error('批量操作失败');
  }
}

// 监听筛选条件变化
watch([searchQuery, statusFilter, typeFilter, sourceFilter], () => {
  // TODO: 实现筛选逻辑
});

onMounted(() => {
  loadMenuData();
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <NCard title="动态菜单管理" :bordered="false" size="small" class="sm:flex-1-hidden card-wrapper">
      <template #header-extra>
        <div class="flex-y-center gap-12px">
          <NButton type="primary" ghost @click="handleScanRoutes">
            <template #icon>
              <SvgIcon icon="mdi:magnify-scan" />
            </template>
            扫描路由
          </NButton>
          <NButton type="info" ghost @click="handleAutoSync">
            <template #icon>
              <SvgIcon icon="mdi:sync" />
            </template>
            自动同步
          </NButton>
          <NButton type="success" ghost @click="handleAddMenu">
            <template #icon>
              <SvgIcon icon="mdi:plus" />
            </template>
            新增菜单
          </NButton>
          <NButton type="warning" ghost @click="handleBatchUpdate">
            <template #icon>
              <SvgIcon icon="mdi:format-list-checks" />
            </template>
            批量操作
          </NButton>
          <NButton secondary @click="refreshData">
            <template #icon>
              <SvgIcon icon="mdi:refresh" />
            </template>
            刷新
          </NButton>
        </div>
      </template>

      <div class="h-full flex-col">
        <!-- 筛选区域 -->
        <div class="flex-y-center justify-between pb-12px">
          <div class="flex-y-center gap-12px">
            <NInput v-model:value="searchQuery" placeholder="搜索菜单名称、路径" clearable class="w-240px" @input="handleSearch">
              <template #prefix>
                <SvgIcon icon="mdi:magnify" class="text-icon" />
              </template>
            </NInput>
            <NSelect
              v-model:value="statusFilter"
              placeholder="状态筛选"
              clearable
              class="w-120px"
              :options="statusOptions"
              @update:value="handleFilterChange"
            />
            <NSelect
              v-model:value="typeFilter"
              placeholder="类型筛选"
              clearable
              class="w-120px"
              :options="typeOptions"
              @update:value="handleFilterChange"
            />
            <NSelect
              v-model:value="sourceFilter"
              placeholder="来源筛选"
              clearable
              class="w-120px"
              :options="sourceOptions"
              @update:value="handleFilterChange"
            />
          </div>
          <div class="flex-y-center gap-8px">
            <span class="text-sm text-gray">共 {{ totalCount }} 项</span>
          </div>
        </div>

        <!-- 菜单树形表格 -->
        <div class="flex-1-hidden">
          <NDataTable
            remote
            striped
            size="small"
            class="h-full"
            :data="menuData"
            :columns="columns"
            :loading="loading"
            :row-key="(row: MenuRecord) => row.id"
            :default-expand-all="false"
            :cascade="false"
            children-key="children"
            :indent="24"
            flex-height
            @update:checked-row-keys="handleCheckedRowKeysChange"
          />
        </div>
      </div>
    </NCard>

    <!-- 扫描结果模态框 -->
    <ScanResultModal v-model:visible="scanResultVisible" :scan-result="scanResult" @sync-menus="handleSyncMenus" />

    <!-- 菜单编辑模态框 -->
    <MenuEditModal v-model:visible="editVisible" :menu-data="editingMenu" :operation-type="operationType" @confirm="handleEditConfirm" />

    <!-- 批量操作模态框 -->
    <BatchUpdateModal v-model:visible="batchVisible" :selected-keys="selectedRowKeys" @confirm="handleBatchConfirm" />
  </div>
</template>

<style scoped>
.card-wrapper {
  @apply h-full;
}
</style>
