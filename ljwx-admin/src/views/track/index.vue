<script setup lang="tsx">
import { NButton, NCard, NDataTable, NDatePicker, NInput, NSelect, NSpace, NTimePicker, useMessage } from 'naive-ui';
import type { Ref } from 'vue';
import { computed, onMounted, ref, watch } from 'vue';
import type { DataTableColumns } from 'naive-ui';
import AMapLoader from '@amap/amap-jsapi-loader';
import { $t } from '@/locales';
import { fetchQueryHistoryTrack, fetchQueryRealtimeTrack, fetchGetLatestLocation, fetchQueryTrackStats, fetchGetUserList } from '@/service/api';
import type { Api } from '@/typings';

defineOptions({
  name: 'TrackManagePage'
});

const message = useMessage();

// 地图相关
const map = ref<AMap.Map | null>(null);
const trackPolyline = ref<AMap.Polyline | null>(null);
const userMarkers = ref<AMap.Marker[]>([]);

// 查询参数
const searchParams = ref<Api.Track.TrackQueryParams>({
  userId: undefined,
  deviceSn: '',
  startTime: '',
  endTime: '',
  pageSize: 100,
  pageNum: 1
});

// 数据状态
const trackData = ref<Api.Track.TrackPoint[]>([]);
const trackStats = ref<Api.Track.TrackStats | null>(null);
const loading = ref(false);
const playbackMode = ref(false);
const playbackSpeed = ref(1000); // 毫秒

// 查询模式
const queryMode = ref<'history' | 'realtime' | 'latest'>('history');
const queryModeOptions = [
  { label: '历史轨迹', value: 'history' },
  { label: '实时轨迹', value: 'realtime' }, 
  { label: '最新位置', value: 'latest' }
];

// 用户选择列表
const userOptions = ref<Array<{ label: string; value: number }>>([]);

// 加载用户列表
async function loadUserOptions() {
  try {
    const result = await fetchGetUserList({ pageSize: 1000 });
    if (result.data?.records) {
      userOptions.value = [
        { label: '全部用户', value: 0 },
        ...result.data.records.map(user => ({
          label: `${user.userName}(${user.phone || user.deviceSn || 'N/A'})`,
          value: user.id
        }))
      ];
    }
  } catch (error) {
    console.error('加载用户列表失败:', error);
    message.error('加载用户列表失败');
  }
}

// 初始化地图
function initMap() {
  AMapLoader.load({
    key: '7de0c6b90cb13571ce931ca75a66c6e7',
    version: '2.0',
    plugins: ['AMap.Polyline', 'AMap.Marker']
  }).then(AMap => {
    map.value = new AMap.Map('track-map-container', {
      zoom: 15,
      center: [116.397428, 39.90923]
    });
  });
}

// 表格列定义
const columns: DataTableColumns<Api.Track.TrackPoint> = [
  {
    key: 'index',
    title: '序号',
    width: 80,
    render: (_, index) => index + 1
  },
  {
    key: 'timestamp',
    title: '时间',
    width: 150,
    render: (row) => new Date(row.timestamp).toLocaleString()
  },
  {
    key: 'longitude',
    title: '经度',
    width: 120,
    render: (row) => row.longitude.toFixed(6)
  },
  {
    key: 'latitude',
    title: '纬度', 
    width: 120,
    render: (row) => row.latitude.toFixed(6)
  },
  {
    key: 'speed',
    title: '速度(km/h)',
    width: 100,
    render: (row) => row.speed?.toFixed(2) || '0'
  },
  {
    key: 'accuracy',
    title: '精度(m)',
    width: 100,
    render: (row) => row.accuracy?.toFixed(0) || '-'
  },
  {
    key: 'distance',
    title: '距离(m)',
    width: 100,
    render: (row) => row.distance?.toFixed(0) || '-'
  }
];

// 查询轨迹数据
async function queryTrackData() {
  if (!searchParams.value.userId && !searchParams.value.deviceSn) {
    message.warning('请选择用户或输入设备序列号');
    return;
  }
  
  // 如果选择了"全部用户"，则清除userId参数
  if (searchParams.value.userId === 0) {
    searchParams.value.userId = undefined;
  }

  loading.value = true;
  try {
    let result;
    
    if (queryMode.value === 'history') {
      result = await fetchQueryHistoryTrack(searchParams.value);
      trackData.value = result.data || [];
    } else if (queryMode.value === 'realtime') {
      result = await fetchQueryRealtimeTrack(searchParams.value);
      trackData.value = result.data || [];
    } else if (queryMode.value === 'latest') {
      const latestResult = await fetchGetLatestLocation(
        searchParams.value.userId!,
        searchParams.value.deviceSn
      );
      trackData.value = latestResult.data ? [latestResult.data] : [];
    }
    
    // 获取统计信息
    if (searchParams.value.userId || searchParams.value.deviceSn) {
      const statsResult = await fetchQueryTrackStats(searchParams.value);
      trackStats.value = statsResult.data || null;
    }
    
    // 更新地图显示
    updateMapDisplay();
    
    message.success(`查询完成，获取到 ${trackData.value.length} 个轨迹点`);
  } catch (error) {
    message.error('查询失败：' + error);
    console.error('Query track data error:', error);
  } finally {
    loading.value = false;
  }
}

// 更新地图显示
function updateMapDisplay() {
  if (!map.value || trackData.value.length === 0) return;

  // 清除之前的轨迹
  clearTrackDisplay();

  // 构建轨迹路径
  const path = trackData.value.map(point => [point.longitude, point.latitude]);
  
  if (path.length === 1) {
    // 单点显示
    const marker = new AMap.Marker({
      position: path[0],
      title: '最新位置'
    });
    map.value.add(marker);
    userMarkers.value.push(marker);
    map.value.setCenter(path[0]);
  } else if (path.length > 1) {
    // 轨迹线显示
    trackPolyline.value = new AMap.Polyline({
      path: path,
      strokeColor: '#1b38d3',
      strokeWeight: 5,
      strokeOpacity: 0.8,
      showDir: true
    });
    
    map.value.add(trackPolyline.value);
    
    // 起点终点标记
    const startMarker = new AMap.Marker({
      position: path[0],
      title: '起点',
      content: '<div style="background-color: green; width: 10px; height: 10px; border-radius: 50%;"></div>'
    });
    
    const endMarker = new AMap.Marker({
      position: path[path.length - 1],
      title: '终点',
      content: '<div style="background-color: red; width: 10px; height: 10px; border-radius: 50%;"></div>'
    });
    
    map.value.add([startMarker, endMarker]);
    userMarkers.value.push(startMarker, endMarker);
    
    // 自适应视野
    map.value.setFitView([trackPolyline.value], false, [50, 50, 50, 50]);
  }
}

// 清除轨迹显示
function clearTrackDisplay() {
  if (trackPolyline.value) {
    map.value?.remove(trackPolyline.value);
    trackPolyline.value = null;
  }
  
  if (userMarkers.value.length > 0) {
    map.value?.remove(userMarkers.value);
    userMarkers.value = [];
  }
}

// 轨迹回放
let playbackTimer: NodeJS.Timeout | null = null;
let playbackIndex = 0;

function startPlayback() {
  if (trackData.value.length < 2) {
    message.warning('轨迹点数量不足，无法回放');
    return;
  }
  
  playbackMode.value = true;
  playbackIndex = 0;
  clearTrackDisplay();
  
  const playedPath: [number, number][] = [];
  let currentMarker: AMap.Marker | null = null;
  
  playbackTimer = setInterval(() => {
    if (playbackIndex >= trackData.value.length) {
      stopPlayback();
      return;
    }
    
    const currentPoint = trackData.value[playbackIndex];
    const position: [number, number] = [currentPoint.longitude, currentPoint.latitude];
    playedPath.push(position);
    
    // 更新当前位置标记
    if (currentMarker) {
      map.value?.remove(currentMarker);
    }
    
    currentMarker = new AMap.Marker({
      position: position,
      title: `时间: ${new Date(currentPoint.timestamp).toLocaleString()}`,
      content: '<div style="background-color: blue; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>'
    });
    
    map.value?.add(currentMarker);
    
    // 更新已播放的轨迹
    if (trackPolyline.value) {
      map.value?.remove(trackPolyline.value);
    }
    
    if (playedPath.length > 1) {
      trackPolyline.value = new AMap.Polyline({
        path: playedPath,
        strokeColor: '#1b38d3',
        strokeWeight: 5,
        strokeOpacity: 0.8
      });
      map.value?.add(trackPolyline.value);
    }
    
    map.value?.setCenter(position);
    playbackIndex++;
  }, playbackSpeed.value);
}

function stopPlayback() {
  playbackMode.value = false;
  if (playbackTimer) {
    clearInterval(playbackTimer);
    playbackTimer = null;
  }
  updateMapDisplay(); // 恢复完整轨迹显示
}

// 导出轨迹数据
function exportTrackData() {
  if (trackData.value.length === 0) {
    message.warning('没有轨迹数据可导出');
    return;
  }
  
  const csvContent = 'data:text/csv;charset=utf-8,' + 
    '时间,经度,纬度,海拔,速度,方向,精度,距离\n' +
    trackData.value.map(point => [
      new Date(point.timestamp).toLocaleString(),
      point.longitude,
      point.latitude,
      point.altitude || '',
      point.speed || '',
      point.bearing || '',
      point.accuracy || '',
      point.distance || ''
    ].join(',')).join('\n');
  
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `track_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  message.success('轨迹数据已导出');
}

// 获取默认时间范围（最近24小时）
function getDefaultTimeRange(): [number, number] {
  const end = new Date();
  const start = new Date(end.getTime() - 24 * 60 * 60 * 1000);
  return [start.getTime(), end.getTime()];
}

// 时间范围处理
function handleTimeRangeChange(value: [number, number] | null) {
  if (value) {
    searchParams.value.startTime = new Date(value[0]).toISOString();
    searchParams.value.endTime = new Date(value[1]).toISOString();
  } else {
    searchParams.value.startTime = '';
    searchParams.value.endTime = '';
  }
}

onMounted(() => {
  initMap();
  loadUserOptions();
  // 设置默认时间范围
  const defaultRange = getDefaultTimeRange();
  handleTimeRangeChange(defaultRange);
});
</script>

<template>
  <div class="track-management">
    <!-- 查询条件 -->
    <NCard title="轨迹查询" class="mb-4">
      <NSpace vertical>
        <NSpace align="center">
          <span class="label">查询模式：</span>
          <NSelect
            v-model:value="queryMode"
            :options="queryModeOptions"
            style="width: 150px"
          />
          
          <span class="label">用户：</span>
          <NSelect
            v-model:value="searchParams.userId"
            :options="userOptions"
            placeholder="选择用户"
            style="width: 150px"
            clearable
          />
          
          <span class="label">设备序列号：</span>
          <NInput
            v-model:value="searchParams.deviceSn"
            placeholder="输入设备序列号"
            style="width: 200px"
          />
        </NSpace>
        
        <NSpace align="center" v-if="queryMode !== 'latest'">
          <span class="label">时间范围：</span>
          <NDatePicker
            :value="searchParams.startTime && searchParams.endTime ? [new Date(searchParams.startTime).getTime(), new Date(searchParams.endTime).getTime()] : null"
            type="datetimerange"
            @update:value="handleTimeRangeChange"
            style="width: 350px"
          />
          
          <span class="label">数量限制：</span>
          <NSelect
            v-model:value="searchParams.pageSize"
            :options="[
              { label: '100', value: 100 },
              { label: '500', value: 500 },
              { label: '1000', value: 1000 },
              { label: '5000', value: 5000 }
            ]"
            style="width: 100px"
          />
        </NSpace>
        
        <NSpace>
          <NButton type="primary" @click="queryTrackData" :loading="loading">
            查询轨迹
          </NButton>
          
          <NButton @click="clearTrackDisplay">
            清除显示
          </NButton>
          
          <NButton v-if="trackData.length > 1" @click="startPlayback" :disabled="playbackMode">
            开始回放
          </NButton>
          
          <NButton v-if="playbackMode" @click="stopPlayback" type="error">
            停止回放
          </NButton>
          
          <NButton @click="exportTrackData" :disabled="trackData.length === 0">
            导出数据
          </NButton>
        </NSpace>
        
        <!-- 回放控制 -->
        <NSpace v-if="playbackMode" align="center">
          <span class="label">回放速度：</span>
          <NSelect
            v-model:value="playbackSpeed"
            :options="[
              { label: '0.5x', value: 2000 },
              { label: '1x', value: 1000 },
              { label: '2x', value: 500 },
              { label: '5x', value: 200 }
            ]"
            style="width: 100px"
          />
        </NSpace>
      </NSpace>
    </NCard>
    
    <!-- 统计信息 -->
    <NCard v-if="trackStats" title="轨迹统计" class="mb-4">
      <NSpace>
        <span>总距离: {{ trackStats.totalDistance.toFixed(0) }}米</span>
        <span>总时长: {{ trackStats.totalDuration.toFixed(0) }}分钟</span>
        <span>最大速度: {{ trackStats.maxSpeed.toFixed(1) }}km/h</span>
        <span>平均速度: {{ trackStats.avgSpeed.toFixed(1) }}km/h</span>
        <span>轨迹点数: {{ trackStats.pointCount }}个</span>
      </NSpace>
    </NCard>

    <!-- 地图显示 -->
    <NCard title="轨迹地图" class="mb-4">
      <div id="track-map-container" class="track-map"></div>
    </NCard>

    <!-- 轨迹数据表格 -->
    <NCard title="轨迹数据">
      <NDataTable
        :data="trackData"
        :columns="columns"
        :row-key="(row, index) => index"
        :loading="loading"
        size="small"
        striped
        max-height="400"
      />
    </NCard>
  </div>
</template>

<style scoped>
.track-management {
  padding: 16px;
}

.track-map {
  height: 500px;
  width: 100%;
  border: 1px solid #e0e0e6;
  border-radius: 6px;
}

.label {
  font-weight: 500;
  color: #333;
  min-width: 80px;
  text-align: right;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>