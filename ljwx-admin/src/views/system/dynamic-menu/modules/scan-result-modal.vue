<script setup lang="ts">
import { computed, h, ref, watch } from 'vue';
import type { DataTableColumn } from 'naive-ui';
import { NButton, NTag, NTooltip } from 'naive-ui';
import SvgIcon from '@/components/custom/svg-icon.vue';

interface RouteInfo {
  path: string;
  name?: string;
  title?: string;
  component?: string;
  filePath: string;
  lastModified?: string;
  fileSize?: number;
  routeType: string;
  isNew: boolean;
  level?: number;
  suggestedParent?: string;
  suggestedIcon?: string;
  suggestedSort?: number;
  metadata?: any;
}

interface ScanStats {
  totalFiles: number;
  vueFiles: number;
  tsFiles: number;
  jsFiles: number;
  changedFiles: number;
  newRoutes: number;
  existingRoutes: number;
  scanDuration: number;
  processedDirectories: number;
  skippedFiles: number;
  errorFiles: number;
}

interface Props {
  visible: boolean;
  scanResult?: {
    scanTime: string;
    foundFiles: string[];
    changedFiles: string[];
    newRoutes: RouteInfo[];
    scanStats: ScanStats;
    scanTag?: string;
    messages?: string[];
    warnings?: string[];
    errors?: string[];
  };
}

interface Emits {
  (e: 'update:visible', visible: boolean): void;
  (e: 'sync-menus', routes: RouteInfo[]): void;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false
});

const emit = defineEmits<Emits>();

// 响应式数据
const modalVisible = computed({
  get: () => props.visible,
  set: value => emit('update:visible', value)
});

const showDetails = ref(false);
const selectedRoutes = ref<string[]>([]);

// 计算属性
const newRoutes = computed(() => props.scanResult?.newRoutes || []);
const scanStats = computed(
  () =>
    props.scanResult?.scanStats || {
      totalFiles: 0,
      vueFiles: 0,
      tsFiles: 0,
      jsFiles: 0,
      changedFiles: 0,
      newRoutes: 0,
      existingRoutes: 0,
      scanDuration: 0,
      processedDirectories: 0,
      skippedFiles: 0,
      errorFiles: 0
    }
);

const hasMessages = computed(() => {
  return (props.scanResult?.errors?.length || 0) > 0 || (props.scanResult?.warnings?.length || 0) > 0;
});

const allSelected = computed(() => {
  return selectedRoutes.value.length === newRoutes.value.length && newRoutes.value.length > 0;
});

// 表格列配置
const routeColumns: DataTableColumn<RouteInfo>[] = [
  {
    type: 'selection',
    width: 50
  },
  {
    key: 'path',
    title: '路由路径',
    width: 200,
    ellipsis: {
      tooltip: true
    },
    render: (row: RouteInfo) => {
      return h('div', { class: 'flex-y-center gap-8px' }, [
        h(SvgIcon, { icon: row.suggestedIcon || 'mdi:file-outline', class: 'text-16px text-gray-400' }),
        h('code', { class: 'text-primary' }, row.path)
      ]);
    }
  },
  {
    key: 'title',
    title: '页面标题',
    width: 120,
    ellipsis: {
      tooltip: true
    },
    render: (row: RouteInfo) => {
      return row.title || h('span', { class: 'text-gray-400' }, '未设置');
    }
  },
  {
    key: 'component',
    title: '组件',
    width: 180,
    ellipsis: {
      tooltip: true
    },
    render: (row: RouteInfo) => {
      return row.component || row.filePath;
    }
  },
  {
    key: 'routeType',
    title: '类型',
    width: 80,
    render: (row: RouteInfo) => {
      const typeMap = {
        page: { label: '页面', type: 'success' as const },
        component: { label: '组件', type: 'info' as const }
      };
      const config = typeMap[row.routeType as keyof typeof typeMap] || { label: '未知', type: 'default' as const };
      return h(NTag, { type: config.type, size: 'small' }, () => config.label);
    }
  },
  {
    key: 'level',
    title: '层级',
    width: 60,
    align: 'center',
    render: (row: RouteInfo) => {
      return row.level || 1;
    }
  },
  {
    key: 'fileSize',
    title: '文件大小',
    width: 80,
    align: 'right',
    render: (row: RouteInfo) => {
      if (!row.fileSize) return '-';
      return formatFileSize(row.fileSize);
    }
  }
];

// 如果显示详情，添加更多列
watch(showDetails, show => {
  if (show) {
    // TODO: 添加更多详情列
  }
});

// 事件处理
function handleToggleDetails() {
  showDetails.value = !showDetails.value;
}

function handleSelectAll() {
  if (allSelected.value) {
    selectedRoutes.value = [];
  } else {
    selectedRoutes.value = newRoutes.value.map(route => route.path);
  }
}

function handleRouteSelection(keys: string[]) {
  selectedRoutes.value = keys;
}

function handleSyncConfirm() {
  const selectedRouteData = newRoutes.value.filter(route => selectedRoutes.value.includes(route.path));
  emit('sync-menus', selectedRouteData);
}

// 工具函数
function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(1)}${units[unitIndex]}`;
}

// 监听visible变化，重置状态
watch(
  () => props.visible,
  visible => {
    if (visible) {
      selectedRoutes.value = [];
      showDetails.value = false;
    }
  }
);
</script>

<template>
  <NModal v-model:show="modalVisible" :mask-closable="false" preset="card" title="路由扫描结果" class="max-h-600px w-800px">
    <div class="h-full flex-col gap-16px">
      <!-- 扫描统计 -->
      <div class="grid grid-cols-4 gap-12px">
        <NCard size="small" embedded class="text-center">
          <div class="text-2xl text-primary font-bold">{{ scanStats.totalFiles }}</div>
          <div class="text-sm text-gray-500">总文件数</div>
        </NCard>
        <NCard size="small" embedded class="text-center">
          <div class="text-2xl text-success font-bold">{{ scanStats.newRoutes }}</div>
          <div class="text-sm text-gray-500">新路由</div>
        </NCard>
        <NCard size="small" embedded class="text-center">
          <div class="text-2xl text-warning font-bold">{{ scanStats.changedFiles }}</div>
          <div class="text-sm text-gray-500">变更文件</div>
        </NCard>
        <NCard size="small" embedded class="text-center">
          <div class="text-2xl text-info font-bold">{{ scanStats.existingRoutes }}</div>
          <div class="text-sm text-gray-500">已存在路由</div>
        </NCard>
      </div>

      <!-- 扫描信息 -->
      <div class="flex-y-center justify-between">
        <div class="flex-y-center gap-12px">
          <span class="text-sm text-gray-500">扫描时间: {{ scanResult?.scanTime }}</span>
          <span class="text-sm text-gray-500">耗时: {{ scanStats.scanDuration }}ms</span>
        </div>
        <div class="flex-y-center gap-8px">
          <NButton size="small" @click="handleToggleDetails">
            {{ showDetails ? '隐藏详情' : '显示详情' }}
          </NButton>
          <NButton size="small" type="primary" @click="handleSelectAll">
            {{ allSelected ? '取消全选' : '全选新路由' }}
          </NButton>
        </div>
      </div>

      <!-- 新路由列表 -->
      <div class="flex-1-hidden">
        <div v-if="newRoutes.length === 0" class="h-200px flex-center text-gray-500">
          <NEmpty description="未发现新路由" />
        </div>
        <div v-else class="h-full">
          <NDataTable
            :data="newRoutes"
            :columns="routeColumns"
            :max-height="300"
            size="small"
            striped
            :row-key="(row: RouteInfo) => row.path"
            :checked-row-keys="selectedRoutes"
            @update:checked-row-keys="handleRouteSelection"
          />
        </div>
      </div>

      <!-- 错误和警告信息 -->
      <div v-if="hasMessages" class="space-y-8px">
        <div v-if="scanResult?.errors?.length" class="border border-red-200 rounded-8px bg-red-50 p-12px">
          <div class="mb-4px text-sm text-red-700 font-medium">错误信息</div>
          <div v-for="error in scanResult.errors" :key="error" class="text-sm text-red-600">
            {{ error }}
          </div>
        </div>
        <div v-if="scanResult?.warnings?.length" class="border border-orange-200 rounded-8px bg-orange-50 p-12px">
          <div class="mb-4px text-sm text-orange-700 font-medium">警告信息</div>
          <div v-for="warning in scanResult.warnings" :key="warning" class="text-sm text-orange-600">
            {{ warning }}
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex-y-center justify-between">
        <div class="text-sm text-gray-500">已选择 {{ selectedRoutes.length }} / {{ newRoutes.length }} 个新路由</div>
        <div class="flex gap-12px">
          <NButton @click="modalVisible = false">取消</NButton>
          <NButton type="primary" :disabled="selectedRoutes.length === 0" @click="handleSyncConfirm">同步选中的路由</NButton>
        </div>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
:deep(.n-data-table-th) {
  font-weight: 500;
}

:deep(.n-data-table-td) {
  font-size: 13px;
}
</style>
