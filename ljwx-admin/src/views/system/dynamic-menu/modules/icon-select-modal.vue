<template>
  <NModal
    v-model:show="modalVisible"
    :mask-closable="false"
    preset="card"
    title="选择图标"
    class="w-800px max-h-600px"
  >
    <div class="h-full flex-col gap-16px">
      <!-- 搜索和筛选 -->
      <div class="flex-y-center gap-12px">
        <NInput
          v-model:value="searchQuery"
          placeholder="搜索图标名称"
          clearable
          class="flex-1"
          @input="handleSearch"
        >
          <template #prefix>
            <SvgIcon icon="mdi:magnify" class="text-icon" />
          </template>
        </NInput>
        <NSelect
          v-model:value="categoryFilter"
          placeholder="图标分类"
          clearable
          class="w-160px"
          :options="categoryOptions"
          @update:value="handleCategoryChange"
        />
        <NButton @click="handleRefresh">
          <template #icon>
            <SvgIcon icon="mdi:refresh" />
          </template>
          刷新
        </NButton>
      </div>

      <!-- 常用图标 -->
      <div v-if="showCommonIcons" class="space-y-8px">
        <div class="text-sm font-medium">常用图标</div>
        <div class="grid grid-cols-8 gap-8px">
          <div
            v-for="icon in commonIcons"
            :key="icon"
            class="flex-center h-48px border border-gray-200 rounded-8px cursor-pointer hover:border-primary hover:bg-primary-50 transition-colors"
            :class="{ 'border-primary bg-primary-50': selectedIcon === icon }"
            @click="handleIconSelect(icon)"
          >
            <NTooltip>
              <template #trigger>
                <SvgIcon :icon="icon" class="text-24px" />
              </template>
              {{ icon }}
            </NTooltip>
          </div>
        </div>
      </div>

      <!-- 图标列表 -->
      <div class="flex-1-hidden">
        <div v-if="loading" class="flex-center h-200px">
          <NSpin />
        </div>
        <div v-else-if="filteredIcons.length === 0" class="flex-center h-200px text-gray-500">
          <NEmpty description="未找到图标" />
        </div>
        <div v-else class="h-full overflow-auto">
          <div class="grid grid-cols-8 gap-8px p-4px">
            <div
              v-for="icon in displayedIcons"
              :key="icon.name"
              class="flex-col-center gap-4px p-8px border border-gray-200 rounded-8px cursor-pointer hover:border-primary hover:bg-primary-50 transition-colors"
              :class="{ 'border-primary bg-primary-50': selectedIcon === icon.name }"
              @click="handleIconSelect(icon.name)"
            >
              <SvgIcon :icon="icon.name" class="text-24px" />
              <NTooltip>
                <template #trigger>
                  <div class="text-xs text-gray-600 truncate w-full text-center">
                    {{ icon.displayName }}
                  </div>
                </template>
                {{ icon.name }}
              </NTooltip>
            </div>
          </div>
          
          <!-- 分页 -->
          <div v-if="totalPages > 1" class="flex-center py-16px">
            <NPagination
              v-model:page="currentPage"
              :page-count="totalPages"
              :page-size="pageSize"
              size="small"
              show-size-picker
              :page-sizes="[48, 96, 144]"
              @update:page-size="handlePageSizeChange"
            />
          </div>
        </div>
      </div>

      <!-- 预览区域 -->
      <div v-if="selectedIcon" class="p-12px bg-gray-50 rounded-8px">
        <div class="flex-y-center gap-12px">
          <SvgIcon :icon="selectedIcon" class="text-32px" />
          <div>
            <div class="font-medium">{{ selectedIcon }}</div>
            <div class="text-sm text-gray-500">点击确定使用此图标</div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex gap-12px justify-end">
        <NButton @click="modalVisible = false">取消</NButton>
        <NButton
          type="primary"
          :disabled="!selectedIcon"
          @click="handleConfirm"
        >
          确定
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import SvgIcon from '@/components/custom/svg-icon.vue';

interface IconItem {
  name: string;
  displayName: string;
  category: string;
  tags: string[];
}

interface Props {
  visible: boolean;
}

interface Emits {
  (e: 'update:visible', visible: boolean): void;
  (e: 'confirm', icon: string): void;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false
});

const emit = defineEmits<Emits>();

// 响应式数据
const loading = ref(false);
const searchQuery = ref('');
const categoryFilter = ref<string>();
const selectedIcon = ref<string>();
const currentPage = ref(1);
const pageSize = ref(96);

const modalVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
});

// 常用图标
const commonIcons = [
  'mdi:menu',
  'mdi:home',
  'mdi:account',
  'mdi:cog',
  'mdi:database',
  'mdi:chart-line',
  'mdi:monitor-dashboard',
  'mdi:file-document-outline',
  'mdi:heart-pulse',
  'mdi:shield-check',
  'mdi:bell',
  'mdi:message-text',
  'mdi:calendar',
  'mdi:folder',
  'mdi:image',
  'mdi:download'
];

// 模拟图标数据
const allIcons = ref<IconItem[]>([]);

// 分类选项
const categoryOptions = [
  { label: '全部', value: '' },
  { label: '通用', value: 'general' },
  { label: '导航', value: 'navigation' },
  { label: '系统', value: 'system' },
  { label: '用户', value: 'user' },
  { label: '文件', value: 'file' },
  { label: '图表', value: 'chart' },
  { label: '设备', value: 'device' },
  { label: '网络', value: 'network' },
  { label: '社交', value: 'social' },
  { label: '媒体', value: 'media' }
];

// 计算属性
const showCommonIcons = computed(() => {
  return !searchQuery.value && !categoryFilter.value;
});

const filteredIcons = computed(() => {
  let filtered = allIcons.value;
  
  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter(icon => 
      icon.name.toLowerCase().includes(query) ||
      icon.displayName.toLowerCase().includes(query) ||
      icon.tags.some(tag => tag.toLowerCase().includes(query))
    );
  }
  
  // 分类过滤
  if (categoryFilter.value) {
    filtered = filtered.filter(icon => icon.category === categoryFilter.value);
  }
  
  return filtered;
});

const totalPages = computed(() => {
  return Math.ceil(filteredIcons.value.length / pageSize.value);
});

const displayedIcons = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return filteredIcons.value.slice(start, end);
});

// 事件处理
function handleSearch() {
  currentPage.value = 1;
}

function handleCategoryChange() {
  currentPage.value = 1;
}

function handlePageSizeChange(size: number) {
  pageSize.value = size;
  currentPage.value = 1;
}

function handleIconSelect(icon: string) {
  selectedIcon.value = icon;
}

function handleConfirm() {
  if (selectedIcon.value) {
    emit('confirm', selectedIcon.value);
  }
}

function handleRefresh() {
  loadIcons();
}

// 加载图标数据
async function loadIcons() {
  loading.value = true;
  
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 生成模拟图标数据
    const iconNames = [
      // MDI图标
      'mdi:account', 'mdi:account-group', 'mdi:account-settings', 'mdi:account-circle',
      'mdi:home', 'mdi:home-outline', 'mdi:home-variant', 'mdi:home-city',
      'mdi:menu', 'mdi:menu-open', 'mdi:menu-down', 'mdi:menu-up',
      'mdi:cog', 'mdi:cog-outline', 'mdi:settings', 'mdi:tune',
      'mdi:database', 'mdi:database-outline', 'mdi:server', 'mdi:cloud',
      'mdi:chart-line', 'mdi:chart-bar', 'mdi:chart-pie', 'mdi:analytics',
      'mdi:monitor-dashboard', 'mdi:view-dashboard', 'mdi:desktop-mac',
      'mdi:file-document', 'mdi:file-document-outline', 'mdi:folder', 'mdi:folder-open',
      'mdi:heart-pulse', 'mdi:medical-bag', 'mdi:hospital-building', 'mdi:pill',
      'mdi:shield-check', 'mdi:security', 'mdi:lock', 'mdi:key',
      'mdi:bell', 'mdi:bell-outline', 'mdi:notification-clear-all', 'mdi:alert',
      'mdi:message-text', 'mdi:email', 'mdi:chat', 'mdi:comment',
      'mdi:calendar', 'mdi:calendar-today', 'mdi:clock', 'mdi:timer',
      'mdi:image', 'mdi:camera', 'mdi:video', 'mdi:music',
      'mdi:download', 'mdi:upload', 'mdi:sync', 'mdi:refresh'
    ];
    
    allIcons.value = iconNames.map(name => {
      const displayName = name.replace('mdi:', '').replace(/-/g, ' ');
      return {
        name,
        displayName,
        category: getCategoryFromName(name),
        tags: displayName.split(' ')
      };
    });
    
  } catch (error) {
    console.error('加载图标失败:', error);
  } finally {
    loading.value = false;
  }
}

// 根据图标名称推断分类
function getCategoryFromName(name: string): string {
  const lowerName = name.toLowerCase();
  
  if (lowerName.includes('account') || lowerName.includes('user') || lowerName.includes('person')) {
    return 'user';
  }
  if (lowerName.includes('home') || lowerName.includes('menu') || lowerName.includes('navigation')) {
    return 'navigation';
  }
  if (lowerName.includes('cog') || lowerName.includes('settings') || lowerName.includes('config')) {
    return 'system';
  }
  if (lowerName.includes('file') || lowerName.includes('folder') || lowerName.includes('document')) {
    return 'file';
  }
  if (lowerName.includes('chart') || lowerName.includes('graph') || lowerName.includes('analytics')) {
    return 'chart';
  }
  if (lowerName.includes('monitor') || lowerName.includes('desktop') || lowerName.includes('device')) {
    return 'device';
  }
  if (lowerName.includes('network') || lowerName.includes('wifi') || lowerName.includes('internet')) {
    return 'network';
  }
  if (lowerName.includes('heart') || lowerName.includes('medical') || lowerName.includes('health')) {
    return 'general';
  }
  if (lowerName.includes('image') || lowerName.includes('camera') || lowerName.includes('video') || lowerName.includes('music')) {
    return 'media';
  }
  
  return 'general';
}

// 监听visible变化，重置状态
watch(() => props.visible, (visible) => {
  if (visible) {
    selectedIcon.value = undefined;
    searchQuery.value = '';
    categoryFilter.value = undefined;
    currentPage.value = 1;
    
    if (allIcons.value.length === 0) {
      loadIcons();
    }
  }
});

onMounted(() => {
  if (props.visible) {
    loadIcons();
  }
});
</script>

<style scoped>
:deep(.n-pagination) {
  justify-content: center;
}
</style>