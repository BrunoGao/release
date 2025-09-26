<script setup lang="tsx">
import { NButton, NCard, NSelect, NSpace, NTag, NBadge, NModal, NSwitch, NSlider, useMessage, NGrid, NGridItem, NStatistic, NProgress } from 'naive-ui';
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import AMapLoader from '@amap/amap-jsapi-loader';
import { 
  fetchQueryHistoryTrack, 
  fetchQueryRealtimeTrack, 
  fetchGetLatestLocation, 
  fetchGetUserList,
  fetchGetGeofenceList,
  fetchGetGeofenceAlertStats
} from '@/service/api';
import type { Api } from '@/typings';
import { AMapContainer, TrackRenderer, GeofenceRenderer } from '@/components/common';

defineOptions({
  name: 'MapTrackMonitor'
});

const message = useMessage();

// 地图相关
const mapContainer = ref();
const map = ref<AMap.Map | null>(null);
const trackRenderer = ref();
const geofenceRenderer = ref();

// 数据状态
const userList = ref<Api.SystemManage.User[]>([]);
const selectedUsers = ref<number[]>([]);
const trackData = ref<Map<number, Api.Track.TrackPoint[]>>(new Map());
const geofenceData = ref<Api.Geofence.Geofence[]>([]);
const alertStats = ref<Api.Geofence.GeofenceAlertStats | null>(null);
const onlineUsers = ref<Set<number>>(new Set());

// 控制状态
const isRealTimeMode = ref(false);
const showGeofences = ref(true);
const showTracks = ref(true);
const trackHistoryHours = ref(2);
const autoRefreshInterval = ref(30); // 秒
const showUserLabels = ref(true);

// 监控统计
const monitorStats = ref({
  totalUsers: 0,
  onlineUsers: 0,
  activeAlerts: 0,
  trackedUsers: 0
});

// 定时器
let refreshTimer: NodeJS.Timeout | null = null;

// 地图初始化
function handleMapReady(mapInstance: AMap.Map) {
  map.value = mapInstance;
  loadInitialData();
  startAutoRefresh();
}

// 加载初始数据
async function loadInitialData() {
  try {
    // 加载用户列表
    const userResult = await fetchGetUserList({ pageSize: 1000 });
    if (userResult.data?.records) {
      userList.value = userResult.data.records;
      monitorStats.value.totalUsers = userList.value.length;
      
      // 默认选择前10个活跃用户
      selectedUsers.value = userList.value.slice(0, 10).map(u => u.id);
    }
    
    // 加载围栏数据
    if (showGeofences.value) {
      const geofenceResult = await fetchGetGeofenceList({ pageSize: 100 });
      if (geofenceResult.data?.records) {
        geofenceData.value = geofenceResult.data.records;
      }
    }
    
    // 加载告警统计
    const alertResult = await fetchGetGeofenceAlertStats({});
    if (alertResult.data) {
      alertStats.value = alertResult.data;
      monitorStats.value.activeAlerts = alertResult.data.pending + alertResult.data.processing;
    }
    
    // 加载用户轨迹
    await loadUserTracks();
    
  } catch (error) {
    console.error('加载初始数据失败:', error);
    message.error('数据加载失败');
  }
}

// 加载用户轨迹数据
async function loadUserTracks() {
  if (selectedUsers.value.length === 0) return;
  
  const newTrackData = new Map();
  const onlineUserSet = new Set<number>();
  
  for (const userId of selectedUsers.value) {
    try {
      let tracks: Api.Track.TrackPoint[] = [];
      
      if (isRealTimeMode.value) {
        // 实时模式：获取最近轨迹
        const result = await fetchQueryRealtimeTrack({
          userId,
          startTime: new Date(Date.now() - trackHistoryHours.value * 60 * 60 * 1000).toISOString(),
          endTime: new Date().toISOString(),
          pageSize: 100
        });
        tracks = result.data || [];
      } else {
        // 历史模式：获取指定时间范围的轨迹
        const result = await fetchQueryHistoryTrack({
          userId,
          startTime: new Date(Date.now() - trackHistoryHours.value * 60 * 60 * 1000).toISOString(),
          endTime: new Date().toISOString(),
          pageSize: 200
        });
        tracks = result.data || [];
      }
      
      if (tracks.length > 0) {
        newTrackData.set(userId, tracks);
        
        // 检查用户是否在线（最近5分钟有数据）
        const latestTime = new Date(tracks[tracks.length - 1].timestamp).getTime();
        if (Date.now() - latestTime < 5 * 60 * 1000) {
          onlineUserSet.add(userId);
        }
      }
      
    } catch (error) {
      console.error(`加载用户${userId}轨迹失败:`, error);
    }
  }
  
  trackData.value = newTrackData;
  onlineUsers.value = onlineUserSet;
  
  // 更新统计信息
  monitorStats.value.onlineUsers = onlineUserSet.size;
  monitorStats.value.trackedUsers = newTrackData.size;
}

// 自动刷新控制
function startAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
  
  if (autoRefreshInterval.value > 0) {
    refreshTimer = setInterval(() => {
      if (isRealTimeMode.value) {
        loadUserTracks();
      }
    }, autoRefreshInterval.value * 1000);
  }
}

// 用户选择相关
const userOptions = computed(() => [
  { label: '全选', value: -1 },
  ...userList.value.map(user => ({
    label: `${user.userName}(${user.phone || user.deviceSn || 'N/A'})`,
    value: user.id,
    disabled: false
  }))
]);

function handleUserSelectionChange(users: number[]) {
  if (users.includes(-1)) {
    // 全选/取消全选
    selectedUsers.value = users.length > 1 ? [] : userList.value.map(u => u.id);
  } else {
    selectedUsers.value = users.filter(id => id !== -1);
  }
  
  loadUserTracks();
}

// 实时模式切换
function handleRealtimeModeChange(realtime: boolean) {
  isRealTimeMode.value = realtime;
  if (realtime) {
    message.info('已切换到实时监控模式');
    startAutoRefresh();
  } else {
    message.info('已切换到历史查询模式');
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  }
  loadUserTracks();
}

// 用户状态获取
function getUserStatus(userId: number) {
  const isOnline = onlineUsers.value.has(userId);
  const hasTrack = trackData.value.has(userId);
  
  if (isOnline) return { text: '在线', type: 'success' };
  if (hasTrack) return { text: '离线', type: 'warning' };
  return { text: '无数据', type: 'default' };
}

// 定位到用户
function locateUser(userId: number) {
  const tracks = trackData.value.get(userId);
  if (tracks && tracks.length > 0) {
    const latestPoint = tracks[tracks.length - 1];
    map.value?.setCenter([latestPoint.longitude, latestPoint.latitude]);
    map.value?.setZoom(16);
    message.success(`已定位到用户: ${getUserName(userId)}`);
  } else {
    message.warning('该用户暂无轨迹数据');
  }
}

function getUserName(userId: number): string {
  const user = userList.value.find(u => u.id === userId);
  return user?.userName || `用户${userId}`;
}

// 监听属性变化
watch(() => trackHistoryHours.value, () => {
  loadUserTracks();
});

watch(() => autoRefreshInterval.value, () => {
  startAutoRefresh();
});

watch(() => showGeofences.value, (show) => {
  if (show) {
    loadInitialData();
  }
});

// 围栏点击处理
function handleGeofenceClick(geofence: Api.Geofence.Geofence) {
  message.info(`围栏: ${geofence.name}`, {
    duration: 2000
  });
}

onMounted(() => {
  // 地图将通过 AMapContainer 组件初始化
});

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
});
</script>

<template>
  <div class="map-monitor">
    <!-- 顶部控制面板 -->
    <NCard class="control-panel mb-4">
      <NSpace vertical>
        <!-- 监控统计面板 -->
        <NGrid cols="4" x-gap="12">
          <NGridItem>
            <NStatistic label="总用户数" :value="monitorStats.totalUsers">
              <template #suffix>
                <span class="text-gray-500">人</span>
              </template>
            </NStatistic>
          </NGridItem>
          <NGridItem>
            <NStatistic label="在线用户" :value="monitorStats.onlineUsers">
              <template #suffix>
                <NBadge :value="monitorStats.onlineUsers" type="success">
                  <span class="text-gray-500">人</span>
                </NBadge>
              </template>
            </NStatistic>
          </NGridItem>
          <NGridItem>
            <NStatistic label="活跃告警" :value="monitorStats.activeAlerts">
              <template #suffix>
                <NBadge 
                  :value="monitorStats.activeAlerts" 
                  :type="monitorStats.activeAlerts > 0 ? 'error' : 'default'"
                >
                  <span class="text-gray-500">条</span>
                </NBadge>
              </template>
            </NStatistic>
          </NGridItem>
          <NGridItem>
            <NStatistic label="追踪用户" :value="monitorStats.trackedUsers">
              <template #suffix>
                <span class="text-gray-500">人</span>
              </template>
            </NStatistic>
          </NGridItem>
        </NGrid>
        
        <!-- 控制选项 -->
        <NSpace align="center" wrap>
          <NSpace align="center">
            <span class="label">监控模式：</span>
            <NSwitch
              v-model:value="isRealTimeMode"
              @update:value="handleRealtimeModeChange"
            >
              <template #checked>实时</template>
              <template #unchecked>历史</template>
            </NSwitch>
          </NSpace>
          
          <NSpace align="center">
            <span class="label">用户选择：</span>
            <NSelect
              v-model:value="selectedUsers"
              :options="userOptions"
              placeholder="选择要监控的用户"
              multiple
              max-tag-count="responsive"
              style="width: 300px"
              @update:value="handleUserSelectionChange"
            />
          </NSpace>
          
          <NSpace align="center">
            <span class="label">时间范围：</span>
            <NSlider
              v-model:value="trackHistoryHours"
              :min="0.5"
              :max="24"
              :step="0.5"
              style="width: 120px"
            />
            <span class="text-sm text-gray-600">{{ trackHistoryHours }}小时</span>
          </NSpace>
          
          <NSpace align="center">
            <span class="label">刷新间隔：</span>
            <NSelect
              v-model:value="autoRefreshInterval"
              :options="[
                { label: '不刷新', value: 0 },
                { label: '10秒', value: 10 },
                { label: '30秒', value: 30 },
                { label: '1分钟', value: 60 },
                { label: '5分钟', value: 300 }
              ]"
              style="width: 80px"
            />
          </NSpace>
        </NSpace>
        
        <!-- 显示控制 -->
        <NSpace align="center">
          <NSwitch v-model:value="showTracks" size="small">
            <template #checked>显示轨迹</template>
            <template #unchecked>隐藏轨迹</template>
          </NSwitch>
          
          <NSwitch v-model:value="showGeofences" size="small">
            <template #checked>显示围栏</template>
            <template #unchecked>隐藏围栏</template>
          </NSwitch>
          
          <NSwitch v-model:value="showUserLabels" size="small">
            <template #checked>显示标签</template>
            <template #unchecked>隐藏标签</template>
          </NSwitch>
          
          <NButton type="primary" @click="loadUserTracks" :loading="false">
            手动刷新
          </NButton>
        </NSpace>
      </NSpace>
    </NCard>

    <!-- 用户状态面板 -->
    <NCard v-if="selectedUsers.length > 0" class="user-panel mb-4" size="small">
      <template #header>
        <span>监控用户状态 ({{ selectedUsers.length }})</span>
        <NBadge 
          :value="onlineUsers.size" 
          :type="onlineUsers.size > 0 ? 'success' : 'default'"
          class="ml-2"
        />
      </template>
      
      <NSpace size="small" wrap>
        <div
          v-for="userId in selectedUsers" 
          :key="userId"
          class="user-status-item"
          @click="locateUser(userId)"
        >
          <NSpace size="small">
            <NTag 
              :type="getUserStatus(userId).type"
              size="small"
              round
            >
              {{ getUserName(userId) }}
            </NTag>
            <span class="text-xs text-gray-500">{{ getUserStatus(userId).text }}</span>
          </NSpace>
        </div>
      </NSpace>
    </NCard>

    <!-- 地图容器 -->
    <NCard class="map-card">
      <AMapContainer
        ref="mapContainer"
        height="600px"
        :center="[116.397428, 39.90923]"
        :zoom="12"
        :show-zoom-control="true"
        :show-map-type-control="true"
        @map-ready="handleMapReady"
      />
      
      <!-- 轨迹渲染器 -->
      <TrackRenderer
        v-if="showTracks"
        v-for="[userId, tracks] in trackData.entries()"
        :key="`track-${userId}`"
        ref="trackRenderer"
        :map="map"
        :track-data="tracks"
        :show-markers="true"
        :stroke-color="onlineUsers.has(userId) ? '#00ff00' : '#1b38d3'"
        :stroke-weight="onlineUsers.has(userId) ? 6 : 4"
      />
      
      <!-- 围栏渲染器 -->
      <GeofenceRenderer
        v-if="showGeofences"
        ref="geofenceRenderer"
        :map="map"
        :geofence-data="geofenceData"
        :active-color="'#1b38d3'"
        :inactive-color="'#999999'"
        :fill-opacity="0.15"
        @geofence-click="handleGeofenceClick"
      />
    </NCard>

    <!-- 实时状态指示器 -->
    <div v-if="isRealTimeMode" class="realtime-indicator">
      <NSpace align="center" size="small">
        <div class="pulse-dot"></div>
        <span class="text-sm">实时监控中</span>
        <span class="text-xs text-gray-500">
          下次更新: {{ autoRefreshInterval }}秒
        </span>
      </NSpace>
    </div>
  </div>
</template>

<style scoped>
.map-monitor {
  padding: 16px;
  background: #f8f9fa;
  min-height: calc(100vh - 100px);
}

.control-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.user-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.map-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
}

.user-status-item {
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-status-item:hover {
  background-color: #f0f0f0;
  transform: translateY(-1px);
}

.label {
  font-weight: 500;
  color: #333;
  font-size: 14px;
  min-width: 80px;
}

.mb-4 {
  margin-bottom: 16px;
}

.ml-2 {
  margin-left: 8px;
}

.text-sm {
  font-size: 12px;
}

.text-xs {
  font-size: 11px;
}

.text-gray-500 {
  color: #6b7280;
}

.text-gray-600 {
  color: #4b5563;
}

/* 实时状态指示器 */
.realtime-indicator {
  position: fixed;
  top: 120px;
  right: 20px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 20px;
  font-size: 12px;
  z-index: 1000;
  backdrop-filter: blur(10px);
}

/* 脉冲点动画 */
.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00ff00;
  animation: pulse 2s infinite;
  box-shadow: 0 0 4px rgba(0, 255, 0, 0.5);
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(0, 255, 0, 0.7);
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(0, 255, 0, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(0, 255, 0, 0);
    transform: scale(1);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .map-monitor {
    padding: 8px;
  }
  
  .control-panel :deep(.n-space) {
    flex-direction: column;
    align-items: stretch;
  }
  
  .realtime-indicator {
    position: static;
    margin-top: 12px;
    text-align: center;
  }
}

/* 统计卡片样式增强 */
:deep(.n-statistic) {
  padding: 8px;
  border-radius: 6px;
  background: #fafafa;
  transition: all 0.2s ease;
}

:deep(.n-statistic:hover) {
  background: #f0f8ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 卡片标题样式 */
:deep(.n-card-header) {
  padding: 12px 20px;
  border-bottom: 1px solid #f0f0f0;
  font-weight: 600;
}

/* 选择器样式优化 */
:deep(.n-select) {
  border-radius: 6px;
}

:deep(.n-switch) {
  --n-rail-color-active: #18a058;
}

/* 滑块样式 */
:deep(.n-slider) {
  margin: 0 8px;
}

/* 标签样式 */
:deep(.n-tag) {
  border-radius: 12px;
  font-weight: 500;
}

/* 徽章样式 */
:deep(.n-badge) {
  --n-color: #18a058;
}

:deep(.n-badge[data-type="error"]) {
  --n-color: #d03050;
}
</style>
