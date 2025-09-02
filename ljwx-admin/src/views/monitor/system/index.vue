<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, h } from 'vue';
import { 
  NCard, NGrid, NGridItem, NProgress, NH4, NDescriptions, NDescriptionsItem, 
  NTable, NStatistic, NBadge, NTag, NAlert, NButton, NSpace, NTime, NIcon,
  useThemeVars
} from 'naive-ui';
import { 
  ServerOutline, 
  HardwareChipOutline, 
  SpeedometerOutline,
  DocumentOutline as StorageOutline,
  RefreshOutline,
  TrendingUpOutline,
  TrendingDownOutline,
  CheckmarkCircleOutline,
  WarningOutline,
  AlertCircleOutline
} from '@vicons/ionicons5';
import { $t } from '@/locales';
import { fetchGetSystemInfo } from '@/service/api';

defineOptions({
  name: 'MonitorSystem'
});

const themeVars = useThemeVars();
const systemInfo = ref<Api.Monitor.SystemInfo>();
const loading = ref(false);
const lastUpdateTime = ref<Date>(new Date());
const autoRefresh = ref(true);
const refreshInterval = ref<NodeJS.Timeout>();

// 实时数据更新
async function getSystemInfo() {
  loading.value = true;
  try {
    const { error, data } = await fetchGetSystemInfo();
    if (!error) {
      systemInfo.value = data;
      lastUpdateTime.value = new Date();
    }
  } catch (error) {
    console.error('获取系统信息失败:', error);
  } finally {
    loading.value = false;
  }
}

// 手动刷新
function handleRefresh() {
  getSystemInfo();
}

// 自动刷新控制
function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value;
  if (autoRefresh.value) {
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }
}

function startAutoRefresh() {
  refreshInterval.value = setInterval(() => {
    getSystemInfo();
  }, 30000); // 30秒刷新一次
}

function stopAutoRefresh() {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value);
  }
}

// 系统健康状态计算
const systemHealthScore = computed(() => {
  if (!systemInfo.value) return 0;
  
  const { centralProcessor, globalMemory, jvm } = systemInfo.value;
  let score = 100;
  
  // CPU使用率评分 (权重30%)
  const cpuUsage = centralProcessor.userPercent + centralProcessor.systemPercent;
  if (cpuUsage > 90) score -= 30;
  else if (cpuUsage > 75) score -= 20;
  else if (cpuUsage > 60) score -= 10;
  
  // 内存使用率评分 (权重40%)
  if (globalMemory.memoryUsedRate > 90) score -= 40;
  else if (globalMemory.memoryUsedRate > 80) score -= 25;
  else if (globalMemory.memoryUsedRate > 70) score -= 15;
  
  // JVM内存评分 (权重30%)
  if (jvm.memoryUsageRate > 85) score -= 30;
  else if (jvm.memoryUsageRate > 70) score -= 20;
  else if (jvm.memoryUsageRate > 60) score -= 10;
  
  return Math.max(score, 0);
});

const systemHealthStatus = computed(() => {
  const score = systemHealthScore.value;
  if (score >= 90) return { status: 'excellent', color: 'success', icon: CheckmarkCircleOutline, text: '优秀' };
  if (score >= 75) return { status: 'good', color: 'info', icon: TrendingUpOutline, text: '良好' };
  if (score >= 60) return { status: 'warning', color: 'warning', icon: WarningOutline, text: '警告' };
  return { status: 'critical', color: 'error', icon: AlertCircleOutline, text: '危险' };
});

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatPercentage = (value: number) => `${value?.toFixed(1)}%`;

onMounted(() => {
  getSystemInfo();
  if (autoRefresh.value) {
    startAutoRefresh();
  }
});

onUnmounted(() => {
  stopAutoRefresh();
});
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Header -->
    <div class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 p-6 mb-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <NIcon size="24" color="white">
              <ServerOutline />
            </NIcon>
          </div>
          <div>
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">企业级系统监控中心</h1>
            <p class="text-sm text-gray-500 dark:text-gray-400">实时监控系统性能与健康状态</p>
          </div>
        </div>
        
        <div class="flex items-center gap-4">
          <!-- 系统健康状态 -->
          <NBadge 
            :type="systemHealthStatus.color" 
            :value="systemHealthScore"
            :max="100"
            show-zero
          >
            <div class="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700">
              <NIcon :component="systemHealthStatus.icon" />
              <span class="font-medium">{{ systemHealthStatus.text }}</span>
            </div>
          </NBadge>
          
          <!-- 刷新控制 -->
          <NSpace>
            <NButton 
              :type="autoRefresh ? 'primary' : 'default'"
              @click="toggleAutoRefresh"
              size="small"
            >
              {{ autoRefresh ? '自动刷新: 开' : '自动刷新: 关' }}
            </NButton>
            <NButton 
              @click="handleRefresh" 
              :loading="loading"
              size="small"
              secondary
            >
              <template #icon>
                <NIcon><RefreshOutline /></NIcon>
              </template>
              手动刷新
            </NButton>
          </NSpace>
          
          <!-- 最后更新时间 -->
          <div class="text-xs text-gray-500 dark:text-gray-400">
            更新时间: <NTime :time="lastUpdateTime" format="HH:mm:ss" />
          </div>
        </div>
      </div>
    </div>

    <div class="px-6 pb-6">
      <!-- 核心指标卡片 -->
      <NGrid :x-gap="24" :y-gap="24" :cols="4" responsive="screen" class="mb-8">
        <!-- CPU使用率 -->
        <NGridItem>
          <NCard class="h-48 relative overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-cyan-500/10"></div>
            <div class="relative z-10 h-full flex flex-col">
              <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                  <NIcon size="20" color="white">
                    <HardwareChipOutline />
                  </NIcon>
                </div>
                <div>
                  <h3 class="font-semibold text-gray-900 dark:text-white">CPU 使用率</h3>
                  <p class="text-sm text-gray-500">处理器负载</p>
                </div>
              </div>
              
              <div class="flex-1 flex items-center justify-center">
                <NProgress
                  type="dashboard"
                  gap-position="bottom"
                  :color="themeVars.primaryColor"
                  :percentage="(systemInfo?.centralProcessor.userPercent || 0) + (systemInfo?.centralProcessor.systemPercent || 0)"
                  :show-indicator="false"
                  :stroke-width="8"
                />
              </div>
              
              <div class="mt-4 text-center">
                <div class="text-2xl font-bold text-gray-900 dark:text-white">
                  {{ formatPercentage((systemInfo?.centralProcessor.userPercent || 0) + (systemInfo?.centralProcessor.systemPercent || 0)) }}
                </div>
                <div class="text-sm text-gray-500">
                  用户: {{ formatPercentage(systemInfo?.centralProcessor.userPercent || 0) }} | 
                  系统: {{ formatPercentage(systemInfo?.centralProcessor.systemPercent || 0) }}
                </div>
              </div>
            </div>
          </NCard>
        </NGridItem>

        <!-- 系统内存 -->
        <NGridItem>
          <NCard class="h-48 relative overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-br from-green-500/10 to-emerald-500/10"></div>
            <div class="relative z-10 h-full flex flex-col">
              <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center">
                  <NIcon size="20" color="white">
                    <StorageOutline />
                  </NIcon>
                </div>
                <div>
                  <h3 class="font-semibold text-gray-900 dark:text-white">系统内存</h3>
                  <p class="text-sm text-gray-500">物理内存使用</p>
                </div>
              </div>
              
              <div class="flex-1 flex items-center justify-center">
                <NProgress
                  type="dashboard"
                  gap-position="bottom"
                  color="#10b981"
                  :percentage="systemInfo?.globalMemory.memoryUsedRate || 0"
                  :show-indicator="false"
                  :stroke-width="8"
                />
              </div>
              
              <div class="mt-4 text-center">
                <div class="text-2xl font-bold text-gray-900 dark:text-white">
                  {{ formatPercentage(systemInfo?.globalMemory.memoryUsedRate || 0) }}
                </div>
                <div class="text-sm text-gray-500">
                  已用: {{ systemInfo?.globalMemory.used }} / {{ systemInfo?.globalMemory.total }}
                </div>
              </div>
            </div>
          </NCard>
        </NGridItem>

        <!-- JVM内存 -->
        <NGridItem>
          <NCard class="h-48 relative overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-pink-500/10"></div>
            <div class="relative z-10 h-full flex flex-col">
              <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center">
                  <NIcon size="20" color="white">
                    <SpeedometerOutline />
                  </NIcon>
                </div>
                <div>
                  <h3 class="font-semibold text-gray-900 dark:text-white">JVM 内存</h3>
                  <p class="text-sm text-gray-500">Java虚拟机</p>
                </div>
              </div>
              
              <div class="flex-1 flex items-center justify-center">
                <NProgress
                  type="dashboard"
                  gap-position="bottom"
                  color="#8b5cf6"
                  :percentage="systemInfo?.jvm.memoryUsageRate || 0"
                  :show-indicator="false"
                  :stroke-width="8"
                />
              </div>
              
              <div class="mt-4 text-center">
                <div class="text-2xl font-bold text-gray-900 dark:text-white">
                  {{ formatPercentage(systemInfo?.jvm.memoryUsageRate || 0) }}
                </div>
                <div class="text-sm text-gray-500">
                  堆内存: {{ systemInfo?.jvm.heapMemoryUsed }} / {{ systemInfo?.jvm.heapMemoryMax }}
                </div>
              </div>
            </div>
          </NCard>
        </NGridItem>

        <!-- 系统健康评分 -->
        <NGridItem>
          <NCard class="h-48 relative overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-br from-yellow-500/10 to-orange-500/10"></div>
            <div class="relative z-10 h-full flex flex-col">
              <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 bg-yellow-500 rounded-lg flex items-center justify-center">
                  <NIcon size="20" color="white" :component="systemHealthStatus.icon" />
                </div>
                <div>
                  <h3 class="font-semibold text-gray-900 dark:text-white">健康评分</h3>
                  <p class="text-sm text-gray-500">综合系统状态</p>
                </div>
              </div>
              
              <div class="flex-1 flex items-center justify-center">
                <div class="text-center">
                  <div class="text-4xl font-bold" :class="{
                    'text-green-500': systemHealthScore >= 90,
                    'text-blue-500': systemHealthScore >= 75 && systemHealthScore < 90,
                    'text-yellow-500': systemHealthScore >= 60 && systemHealthScore < 75,
                    'text-red-500': systemHealthScore < 60
                  }">
                    {{ systemHealthScore }}
                  </div>
                  <div class="text-lg mt-2">
                    <NTag :type="systemHealthStatus.color" size="large">
                      {{ systemHealthStatus.text }}
                    </NTag>
                  </div>
                </div>
              </div>
            </div>
          </NCard>
        </NGridItem>
      </NGrid>

      <!-- 详细信息区域 -->
      <NGrid :x-gap="24" :y-gap="24" :cols="2" responsive="screen" class="mb-8">
        <!-- 操作系统信息 -->
        <NGridItem>
          <NCard title="操作系统信息" size="small" class="h-full">
            <template #header-extra>
              <NIcon size="20" color="rgb(var(--primary-color))">
                <ServerOutline />
              </NIcon>
            </template>
            
            <NDescriptions label-placement="left" bordered :column="1" size="small">
              <NDescriptionsItem label="系统名称">
                <div class="flex items-center gap-2">
                  <span class="font-medium">{{ systemInfo?.operatingSystem.name }}</span>
                  <NTag size="small" type="info">{{ systemInfo?.operatingSystem.arch }}</NTag>
                </div>
              </NDescriptionsItem>
              <NDescriptionsItem label="制造商">
                {{ systemInfo?.operatingSystem.manufacturer || 'N/A' }}
              </NDescriptionsItem>
              <NDescriptionsItem label="启动时间">
                <div class="flex items-center gap-2">
                  <span>{{ systemInfo?.operatingSystem.systemBootTime }}</span>
                </div>
              </NDescriptionsItem>
              <NDescriptionsItem label="运行时长">
                <div class="flex items-center gap-2">
                  <NBadge :value="systemInfo?.operatingSystem.systemUptime" type="success" />
                </div>
              </NDescriptionsItem>
            </NDescriptions>
          </NCard>
        </NGridItem>

        <!-- CPU详细信息 -->
        <NGridItem>
          <NCard title="处理器详情" size="small" class="h-full">
            <template #header-extra>
              <NIcon size="20" color="rgb(var(--primary-color))">
                <HardwareChipOutline />
              </NIcon>
            </template>
            
            <NDescriptions label-placement="left" bordered :column="1" size="small">
              <NDescriptionsItem label="处理器型号">
                <span class="font-medium">{{ systemInfo?.centralProcessor.name }}</span>
              </NDescriptionsItem>
              <NDescriptionsItem label="物理核心">
                <NTag type="info">{{ systemInfo?.centralProcessor.physicalProcessorCount }} 核</NTag>
              </NDescriptionsItem>
              <NDescriptionsItem label="逻辑核心">
                <NTag type="success">{{ systemInfo?.centralProcessor.logicalProcessorCount }} 线程</NTag>
              </NDescriptionsItem>
              <NDescriptionsItem label="主频">
                {{ systemInfo?.centralProcessor.vendorFreq }}
              </NDescriptionsItem>
              <NDescriptionsItem label="空闲率">
                <div class="flex items-center gap-2">
                  <span>{{ formatPercentage(systemInfo?.centralProcessor.idlePercent || 0) }}</span>
                  <div class="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      class="h-full bg-green-500 transition-all duration-300"
                      :style="{ width: `${systemInfo?.centralProcessor.idlePercent || 0}%` }"
                    ></div>
                  </div>
                </div>
              </NDescriptionsItem>
            </NDescriptions>
          </NCard>
        </NGridItem>
      </NGrid>

      <!-- 内存详情和JVM详情 -->
      <NGrid :x-gap="24" :y-gap="24" :cols="2" responsive="screen" class="mb-8">
        <!-- 系统内存详情 -->
        <NGridItem>
          <NCard title="系统内存详情" size="small">
            <div class="space-y-4">
              <!-- 内存使用情况可视化 -->
              <div class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div class="flex justify-between items-center mb-2">
                  <span class="text-sm font-medium">内存使用情况</span>
                  <span class="text-sm text-gray-500">{{ formatPercentage(systemInfo?.globalMemory.memoryUsedRate || 0) }}</span>
                </div>
                <div class="w-full h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    class="h-full bg-gradient-to-r from-green-400 to-blue-500 transition-all duration-500"
                    :style="{ width: `${systemInfo?.globalMemory.memoryUsedRate || 0}%` }"
                  ></div>
                </div>
                <div class="flex justify-between mt-2 text-xs text-gray-500">
                  <span>已用: {{ systemInfo?.globalMemory.used }}</span>
                  <span>可用: {{ systemInfo?.globalMemory.available }}</span>
                </div>
              </div>

              <!-- Swap使用情况 -->
              <div class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div class="flex justify-between items-center mb-2">
                  <span class="text-sm font-medium">交换空间</span>
                  <span class="text-sm text-gray-500">{{ formatPercentage(systemInfo?.globalMemory.swapUsedRate || 0) }}</span>
                </div>
                <div class="w-full h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    class="h-full bg-gradient-to-r from-yellow-400 to-red-500 transition-all duration-500"
                    :style="{ width: `${systemInfo?.globalMemory.swapUsedRate || 0}%` }"
                  ></div>
                </div>
                <div class="flex justify-between mt-2 text-xs text-gray-500">
                  <span>已用: {{ systemInfo?.globalMemory.swapUsed }}</span>
                  <span>总计: {{ systemInfo?.globalMemory.swapTotal }}</span>
                </div>
              </div>
            </div>
          </NCard>
        </NGridItem>

        <!-- JVM详情 -->
        <NGridItem>
          <NCard title="Java 虚拟机" size="small">
            <div class="space-y-4">
              <!-- JVM基本信息 -->
              <div class="grid grid-cols-2 gap-4">
                <div class="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                  <div class="text-lg font-bold text-purple-600 dark:text-purple-400">
                    {{ systemInfo?.jvm.vmName?.split(' ')[0] }}
                  </div>
                  <div class="text-xs text-gray-500">JVM类型</div>
                </div>
                <div class="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div class="text-lg font-bold text-blue-600 dark:text-blue-400">
                    {{ systemInfo?.jvm.uptime }}
                  </div>
                  <div class="text-xs text-gray-500">运行时长</div>
                </div>
              </div>

              <!-- JVM内存使用 -->
              <div class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div class="flex justify-between items-center mb-2">
                  <span class="text-sm font-medium">堆内存使用</span>
                  <span class="text-sm text-gray-500">{{ formatPercentage(systemInfo?.jvm.memoryUsageRate || 0) }}</span>
                </div>
                <div class="w-full h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    class="h-full bg-gradient-to-r from-purple-400 to-pink-500 transition-all duration-500"
                    :style="{ width: `${systemInfo?.jvm.memoryUsageRate || 0}%` }"
                  ></div>
                </div>
                <div class="flex justify-between mt-2 text-xs text-gray-500">
                  <span>已用: {{ systemInfo?.jvm.heapMemoryUsed }}</span>
                  <span>最大: {{ systemInfo?.jvm.heapMemoryMax }}</span>
                </div>
              </div>

              <!-- 非堆内存 -->
              <div class="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                <div class="text-sm text-gray-500">非堆内存</div>
                <div class="font-medium">{{ systemInfo?.jvm.nonHeapMemoryUsed }}</div>
              </div>
            </div>
          </NCard>
        </NGridItem>
      </NGrid>

      <!-- 进程和磁盘信息 -->
      <NGrid :x-gap="24" :y-gap="24" :cols="1" responsive="screen">
        <!-- 系统进程 -->
        <NGridItem>
          <NCard title="系统进程 TOP 10" size="small">
            <template #header-extra>
              <div class="flex items-center gap-2">
                <NTag size="small" type="info">
                  共 {{ systemInfo?.processes?.length || 0 }} 个进程
                </NTag>
              </div>
            </template>
            
            <NTable :single-line="false" striped size="small" class="rounded-lg overflow-hidden">
              <thead class="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th class="font-semibold">#</th>
                  <th class="font-semibold">进程ID</th>
                  <th class="font-semibold">进程名称</th>
                  <th class="font-semibold">CPU负载</th>
                  <th class="font-semibold">状态</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="(process, index) in systemInfo?.processes?.slice(0, 10)" 
                  :key="process.processID"
                  class="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                >
                  <td class="font-mono">{{ index + 1 }}</td>
                  <td class="font-mono">{{ process.processID }}</td>
                  <td>
                    <div class="flex items-center gap-2">
                      <span class="font-medium">{{ process.name }}</span>
                      <NTag 
                        v-if="process.cpuLoad > 10"
                        size="small" 
                        :type="process.cpuLoad > 50 ? 'error' : 'warning'"
                      >
                        高负载
                      </NTag>
                    </div>
                  </td>
                  <td>
                    <div class="flex items-center gap-2">
                      <span>{{ formatPercentage(process.cpuLoad) }}</span>
                      <div class="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          class="h-full transition-all duration-300"
                          :class="{
                            'bg-green-500': process.cpuLoad < 30,
                            'bg-yellow-500': process.cpuLoad >= 30 && process.cpuLoad < 70,
                            'bg-red-500': process.cpuLoad >= 70
                          }"
                          :style="{ width: `${Math.min(process.cpuLoad, 100)}%` }"
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <NTag 
                      size="small"
                      :type="process.cpuLoad > 50 ? 'error' : process.cpuLoad > 20 ? 'warning' : 'success'"
                    >
                      {{ process.cpuLoad > 50 ? '繁忙' : process.cpuLoad > 20 ? '活跃' : '正常' }}
                    </NTag>
                  </td>
                </tr>
              </tbody>
            </NTable>
          </NCard>
        </NGridItem>

        <!-- 磁盘使用情况 -->
        <NGridItem>
          <NCard title="存储设备使用情况" size="small">
            <template #header-extra>
              <div class="flex items-center gap-2">
                <NTag size="small" type="info">
                  {{ systemInfo?.fileStores?.length || 0 }} 个设备
                </NTag>
              </div>
            </template>
            
            <div class="space-y-4">
              <div 
                v-for="disk in systemInfo?.fileStores" 
                :key="disk.name"
                class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-shadow"
              >
                <div class="flex justify-between items-start mb-3">
                  <div>
                    <h4 class="font-semibold text-gray-900 dark:text-white">{{ disk.name }}</h4>
                    <p class="text-sm text-gray-500">{{ disk.mount }} ({{ disk.type }})</p>
                  </div>
                  <div class="text-right">
                    <div class="text-lg font-bold" :class="{
                      'text-green-500': disk.usedPercentage < 70,
                      'text-yellow-500': disk.usedPercentage >= 70 && disk.usedPercentage < 90,
                      'text-red-500': disk.usedPercentage >= 90
                    }">
                      {{ formatPercentage(disk.usedPercentage) }}
                    </div>
                    <div class="text-xs text-gray-500">{{ disk.usedSpace }} / {{ disk.totalSpace }}</div>
                  </div>
                </div>
                
                <!-- 磁盘使用率进度条 -->
                <div class="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    class="h-full transition-all duration-500"
                    :class="{
                      'bg-gradient-to-r from-green-400 to-green-500': disk.usedPercentage < 70,
                      'bg-gradient-to-r from-yellow-400 to-orange-500': disk.usedPercentage >= 70 && disk.usedPercentage < 90,
                      'bg-gradient-to-r from-red-400 to-red-600': disk.usedPercentage >= 90
                    }"
                    :style="{ width: `${disk.usedPercentage}%` }"
                  ></div>
                </div>
                
                <div class="flex justify-between mt-2 text-xs text-gray-500">
                  <span>可用: {{ disk.usableSpace }}</span>
                  <span v-if="disk.usedPercentage >= 90" class="text-red-500 font-medium">
                    ⚠️ 存储空间不足
                  </span>
                  <span v-else-if="disk.usedPercentage >= 70" class="text-yellow-500">
                    ⚡ 建议清理
                  </span>
                  <span v-else class="text-green-500">
                    ✓ 空间充足
                  </span>
                </div>
              </div>
            </div>
          </NCard>
        </NGridItem>
      </NGrid>

      <!-- 系统警告和建议 -->
      <div v-if="systemHealthScore < 75" class="mb-6">
        <NAlert 
          :type="systemHealthScore < 60 ? 'error' : 'warning'"
          :title="systemHealthScore < 60 ? '⚠️ 系统性能严重告警' : '⚡ 系统性能警告'"
          show-icon
        >
          <template #default>
            <div class="space-y-2">
              <p v-if="(systemInfo?.centralProcessor.userPercent || 0) + (systemInfo?.centralProcessor.systemPercent || 0) > 80">
                • CPU使用率过高 ({{ formatPercentage((systemInfo?.centralProcessor.userPercent || 0) + (systemInfo?.centralProcessor.systemPercent || 0)) }})，建议检查高负载进程
              </p>
              <p v-if="(systemInfo?.globalMemory.memoryUsedRate || 0) > 85">
                • 系统内存使用率过高 ({{ formatPercentage(systemInfo?.globalMemory.memoryUsedRate || 0) }})，建议释放内存或增加物理内存
              </p>
              <p v-if="(systemInfo?.jvm.memoryUsageRate || 0) > 80">
                • JVM内存使用率过高 ({{ formatPercentage(systemInfo?.jvm.memoryUsageRate || 0) }})，建议调整JVM参数或优化应用程序
              </p>
              <p v-if="systemInfo?.fileStores?.some(disk => disk.usedPercentage > 90)">
                • 发现磁盘空间不足的存储设备，请及时清理或扩容
              </p>
            </div>
          </template>
        </NAlert>
      </div>

      <!-- 系统优化建议 -->
      <div v-else-if="systemHealthScore >= 75 && systemHealthScore < 90">
        <NAlert type="info" title="💡 系统优化建议" show-icon>
          <ul class="space-y-1 text-sm">
            <li v-if="(systemInfo?.globalMemory.memoryUsedRate || 0) > 70">
              • 内存使用率较高，建议监控应用程序内存使用情况
            </li>
            <li v-if="(systemInfo?.jvm.memoryUsageRate || 0) > 60">
              • JVM内存使用稳定，可考虑调优GC参数以提升性能
            </li>
            <li>• 系统整体运行良好，建议定期监控关键指标</li>
          </ul>
        </NAlert>
      </div>

      <!-- 系统状态优秀提示 -->
      <div v-else>
        <NAlert type="success" title="✅ 系统状态优秀" show-icon>
          系统各项指标运行正常，性能状态良好。继续保持当前的运维策略。
        </NAlert>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 自定义样式 */
.gradient-bg {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
}

/* 进度条动画 */
.n-progress .n-progress-graph-line .n-progress-graph-line-fill {
  transition: width 0.5s ease-in-out;
}

/* 悬停效果 */
.n-card:hover {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
  transition: all 0.3s ease;
}

/* 数据表格优化 */
.n-data-table .n-data-table-th {
  font-weight: 600;
  background: rgba(99, 102, 241, 0.05);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .enterprise-grid {
    grid-template-columns: 1fr;
  }
}

/* 状态指示器 */
.status-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
}

.status-excellent { background-color: #10b981; }
.status-good { background-color: #3b82f6; }
.status-warning { background-color: #f59e0b; }
.status-critical { background-color: #ef4444; }

/* 动画效果 */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>