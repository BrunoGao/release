<script setup lang="tsx">
import { NButton, NCard, NDataTable, NForm, NFormItem, NInput, NSelect, NModal, NSpace, NTag, NSwitch, NPopconfirm, useMessage, useDialog } from 'naive-ui';
import type { Ref } from 'vue';
import { computed, onMounted, ref, reactive } from 'vue';
import type { DataTableColumns } from 'naive-ui';
import AMapLoader from '@amap/amap-jsapi-loader';
import { $t } from '@/locales';
import { fetchAddGeofence, fetchDeleteGeofence, fetchGetGeofenceList, fetchUpdateGeofenceInfo } from '@/service/api';
import type { Api } from '@/typings';

defineOptions({
  name: 'GeofencePage'
});

const message = useMessage();
const dialog = useDialog();

// 地图相关
const map = ref<AMap.Map | null>(null);
const polygon = ref<AMap.Polygon | null>(null);
const polyEditor = ref<AMap.PolygonEditor | null>(null);
const loadedPolygons = ref<AMap.Polygon[]>([]);
const currentEditingGeofence = ref<Api.Geofence.Geofence | null>(null);

// 数据状态
const geofenceData = ref<Api.Geofence.Geofence[]>([]);
const loading = ref(false);
const total = ref(0);

// 查询参数
const searchParams = ref<Api.Geofence.GeofenceSearchParams>({
  pageNum: 1,
  pageSize: 20,
  name: undefined,
  status: undefined
});

// 模态框状态
const showModal = ref(false);
const modalTitle = ref('');
const modalMode = ref<'add' | 'edit'>('add');

// 表单数据
const formData = reactive<Api.Geofence.GeofenceEdit>({
  id: undefined,
  name: '',
  description: '',
  status: 'active',
  area: '',
  fenceType: 'POLYGON',
  alertOnEnter: true,
  alertOnExit: true,
  alertOnStay: false,
  stayDurationMinutes: 30,
  alertLevel: 'MEDIUM',
  isActive: true
});

// 选项配置
const statusOptions = [
  { label: '全部', value: '' },
  { label: '活跃', value: 'active' },
  { label: '不活跃', value: 'inactive' }
];

const fenceTypeOptions = [
  { label: '多边形', value: 'POLYGON' },
  { label: '圆形', value: 'CIRCLE' },
  { label: '矩形', value: 'RECTANGLE' }
];

const alertLevelOptions = [
  { label: '低级', value: 'LOW' },
  { label: '中级', value: 'MEDIUM' },
  { label: '高级', value: 'HIGH' }
];

// 初始化地图
function initMap() {
  AMapLoader.load({
    key: '7de0c6b90cb13571ce931ca75a66c6e7',
    version: '2.0',
    plugins: ['AMap.Polygon', 'AMap.PolygonEditor', 'AMap.Circle', 'AMap.Rectangle']
  }).then(AMap => {
    map.value = new AMap.Map('map-container', {
      zoom: 12,
      center: [116.397428, 39.90923]
    });

    polyEditor.value = new AMap.PolygonEditor(map.value);
    
    // 地图加载完成后，加载现有围栏
    loadExistingGeofences();
  });
}

// 表格列定义
const columns: DataTableColumns<Api.Geofence.Geofence> = [
  {
    key: 'id',
    title: 'ID',
    width: 80
  },
  {
    key: 'name',
    title: '围栏名称',
    width: 150,
    ellipsis: {
      tooltip: true
    }
  },
  {
    key: 'fenceType',
    title: '围栏类型',
    width: 100,
    render: (row) => {
      const typeMap = {
        'POLYGON': '多边形',
        'CIRCLE': '圆形',
        'RECTANGLE': '矩形'
      };
      return typeMap[row.fenceType || 'POLYGON'] || '多边形';
    }
  },
  {
    key: 'alertLevel',
    title: '告警级别',
    width: 100,
    render: (row) => {
      const levelMap = {
        'LOW': { text: '低级', type: 'success' },
        'MEDIUM': { text: '中级', type: 'warning' },
        'HIGH': { text: '高级', type: 'error' }
      };
      const level = levelMap[row.alertLevel || 'MEDIUM'];
      return <NTag type={level.type}>{level.text}</NTag>;
    }
  },
  {
    key: 'isActive',
    title: '状态',
    width: 80,
    render: (row) => (
      <NTag type={row.isActive ? 'success' : 'default'}>
        {row.isActive ? '启用' : '禁用'}
      </NTag>
    )
  },
  {
    key: 'alertSettings',
    title: '告警设置',
    width: 120,
    render: (row) => {
      const alerts = [];
      if (row.alertOnEnter) alerts.push('进入');
      if (row.alertOnExit) alerts.push('离开');
      if (row.alertOnStay) alerts.push('停留');
      return alerts.join('、') || '无';
    }
  },
  {
    key: 'createTime',
    title: '创建时间',
    width: 160,
    render: (row) => row.createTime ? new Date(row.createTime).toLocaleString() : '-'
  },
  {
    key: 'actions',
    title: '操作',
    width: 200,
    render: (row) => (
      <NSpace>
        <NButton size="small" type="primary" onClick={() => editGeofence(row)}>
          编辑
        </NButton>
        <NButton size="small" type="info" onClick={() => showOnMap(row)}>
          地图显示
        </NButton>
        <NPopconfirm
          onPositiveClick={() => deleteGeofence(row.id!)}
        >{{
          trigger: () => (
            <NButton size="small" type="error">
              删除
            </NButton>
          ),
          default: () => '确定删除该围栏吗？'
        }}</NPopconfirm>
      </NSpace>
    )
  }
];

// 创建新的多边形围栏
function createPolygon() {
  clearCurrentPolygon();

  polygon.value = new AMap.Polygon({
    path: [
      [116.397428, 39.90923],
      [116.407428, 39.90923],
      [116.407428, 39.91923]
    ],
    strokeColor: '#ff4444',
    strokeOpacity: 1,
    strokeWeight: 3,
    fillColor: '#ff4444',
    fillOpacity: 0.3,
    zIndex: 100
  });

  map.value?.add(polygon.value);
  polyEditor.value?.setTarget(polygon.value);
  polyEditor.value?.open();

  message.info('请在地图上编辑围栏区域');
}

// 开始编辑围栏
function startEdit() {
  if (polygon.value) {
    polyEditor.value?.setTarget(polygon.value);
    polyEditor.value?.open();
    message.info('开始编辑围栏，拖拽顶点调整形状');
  } else {
    message.warning('请先创建或选择一个围栏');
  }
}

// 结束编辑
function endEdit() {
  polyEditor.value?.close();
  message.success('编辑完成');
}

// 保存当前绘制的围栏到表单
function saveCurrentArea() {
  if (polygon.value) {
    const path = polygon.value.getPath();
    const coordinates = path.map((point: any) => [point.lng, point.lat]);
    
    // 转换为GeoJSON格式
    const geoJson = {
      type: 'Polygon',
      coordinates: [coordinates]
    };
    
    formData.area = JSON.stringify(geoJson);
    message.success('围栏区域已保存到表单中');
  } else {
    message.warning('当前没有围栏区域');
  }
}

// 清除当前编辑的多边形
function clearCurrentPolygon() {
  if (polygon.value) {
    map.value?.remove(polygon.value);
    polygon.value = null;
  }
  polyEditor.value?.close();
}

// 查询围栏数据
async function queryGeofenceData() {
  loading.value = true;
  try {
    const result = await fetchGetGeofenceList(searchParams.value);
    if (result.data) {
      geofenceData.value = result.data.records || [];
      total.value = result.data.total || 0;
    }
    message.success(`查询完成，获取到 ${geofenceData.value.length} 个围栏`);
  } catch (error) {
    message.error('查询失败：' + error);
    console.error('Query geofence data error:', error);
  } finally {
    loading.value = false;
  }
}

// 加载现有围栏到地图
function loadExistingGeofences() {
  queryGeofenceData().then(() => {
    clearAllPolygons();
    
    geofenceData.value.forEach(geofence => {
      if (geofence.area) {
        try {
          const area = JSON.parse(geofence.area);
          if (area.type === 'Polygon' && area.coordinates && area.coordinates[0]) {
            const poly = new AMap.Polygon({
              path: area.coordinates[0],
              strokeColor: geofence.isActive ? '#1b38d3' : '#999999',
              strokeOpacity: 1,
              strokeWeight: 2,
              fillColor: geofence.isActive ? '#1b38d3' : '#999999',
              fillOpacity: 0.2,
              zIndex: 50
            });
            
            // 添加点击事件
            poly.on('click', () => {
              showGeofenceInfo(geofence);
            });
            
            map.value?.add(poly);
            loadedPolygons.value.push(poly);
          }
        } catch (error) {
          console.error('解析围栏区域失败:', error);
        }
      }
    });
  });
}

// 清除所有加载的围栏
function clearAllPolygons() {
  if (loadedPolygons.value.length > 0) {
    map.value?.remove(loadedPolygons.value);
    loadedPolygons.value = [];
  }
  clearCurrentPolygon();
}

// 显示围栏信息
function showGeofenceInfo(geofence: Api.Geofence.Geofence) {
  dialog.info({
    title: '围栏信息',
    content: () => (
      <div>
        <p><strong>名称:</strong> {geofence.name}</p>
        <p><strong>描述:</strong> {geofence.description}</p>
        <p><strong>类型:</strong> {geofence.fenceType}</p>
        <p><strong>告警级别:</strong> {geofence.alertLevel}</p>
        <p><strong>状态:</strong> {geofence.isActive ? '启用' : '禁用'}</p>
        <p><strong>创建时间:</strong> {geofence.createTime ? new Date(geofence.createTime).toLocaleString() : '-'}</p>
      </div>
    )
  });
}

// 添加新围栏
function addGeofence() {
  modalMode.value = 'add';
  modalTitle.value = '新增围栏';
  resetFormData();
  showModal.value = true;
  
  // 创建多边形供用户绘制
  createPolygon();
}

// 编辑围栏
function editGeofence(geofence: Api.Geofence.Geofence) {
  modalMode.value = 'edit';
  modalTitle.value = '编辑围栏';
  currentEditingGeofence.value = geofence;
  
  // 填充表单数据
  Object.assign(formData, {
    id: geofence.id,
    name: geofence.name,
    description: geofence.description,
    status: geofence.status,
    area: geofence.area,
    fenceType: geofence.fenceType || 'POLYGON',
    alertOnEnter: geofence.alertOnEnter ?? true,
    alertOnExit: geofence.alertOnExit ?? true,
    alertOnStay: geofence.alertOnStay ?? false,
    stayDurationMinutes: geofence.stayDurationMinutes || 30,
    alertLevel: geofence.alertLevel || 'MEDIUM',
    isActive: geofence.isActive ?? true
  });
  
  showModal.value = true;
  
  // 在地图上显示围栏用于编辑
  if (geofence.area) {
    try {
      const area = JSON.parse(geofence.area);
      if (area.type === 'Polygon' && area.coordinates && area.coordinates[0]) {
        clearCurrentPolygon();
        
        polygon.value = new AMap.Polygon({
          path: area.coordinates[0],
          strokeColor: '#ff4444',
          strokeOpacity: 1,
          strokeWeight: 3,
          fillColor: '#ff4444',
          fillOpacity: 0.3,
          zIndex: 100
        });
        
        map.value?.add(polygon.value);
        polyEditor.value?.setTarget(polygon.value);
      }
    } catch (error) {
      console.error('解析围栏区域失败:', error);
    }
  }
}

// 在地图上显示围栏
function showOnMap(geofence: Api.Geofence.Geofence) {
  if (geofence.area) {
    try {
      const area = JSON.parse(geofence.area);
      if (area.type === 'Polygon' && area.coordinates && area.coordinates[0]) {
        // 聚焦到围栏区域
        const bounds = new AMap.Bounds();
        area.coordinates[0].forEach((coord: [number, number]) => {
          bounds.extend(coord);
        });
        map.value?.setBounds(bounds);
        
        message.success(`已在地图上定位到围栏：${geofence.name}`);
      }
    } catch (error) {
      message.error('无效的围栏区域数据');
    }
  } else {
    message.warning('该围栏没有区域数据');
  }
}

// 删除围栏
async function deleteGeofence(id: number) {
  try {
    const result = await fetchDeleteGeofence({ ids: [id] });
    if (result.data) {
      message.success('删除成功');
      queryGeofenceData();
      loadExistingGeofences();
    } else {
      message.error('删除失败');
    }
  } catch (error) {
    message.error('删除失败：' + error);
  }
}

// 保存围栏
async function saveGeofence() {
  // 如果正在编辑围栏区域，自动保存当前区域
  if (polygon.value) {
    saveCurrentArea();
  }
  
  if (!formData.name.trim()) {
    message.warning('请输入围栏名称');
    return;
  }
  
  if (!formData.area) {
    message.warning('请绘制围栏区域');
    return;
  }
  
  try {
    const result = modalMode.value === 'add' 
      ? await fetchAddGeofence(formData)
      : await fetchUpdateGeofenceInfo(formData);
      
    if (result.data) {
      message.success(modalMode.value === 'add' ? '添加成功' : '更新成功');
      showModal.value = false;
      clearCurrentPolygon();
      queryGeofenceData();
      loadExistingGeofences();
    } else {
      message.error('保存失败');
    }
  } catch (error) {
    message.error('保存失败：' + error);
  }
}

// 取消编辑
function cancelEdit() {
  showModal.value = false;
  clearCurrentPolygon();
  resetFormData();
}

// 重置表单数据
function resetFormData() {
  Object.assign(formData, {
    id: undefined,
    name: '',
    description: '',
    status: 'active',
    area: '',
    fenceType: 'POLYGON',
    alertOnEnter: true,
    alertOnExit: true,
    alertOnStay: false,
    stayDurationMinutes: 30,
    alertLevel: 'MEDIUM',
    isActive: true
  });
  currentEditingGeofence.value = null;
}

// 分页处理
function handlePageChange(page: number) {
  searchParams.value.pageNum = page;
  queryGeofenceData();
}

function handlePageSizeChange(pageSize: number) {
  searchParams.value.pageSize = pageSize;
  searchParams.value.pageNum = 1;
  queryGeofenceData();
}

onMounted(() => {
  initMap();
  queryGeofenceData();
});
</script>

<template>
  <div class="geofence-management">
    <!-- 查询条件 -->
    <NCard title="查询条件" class="mb-4">
      <NSpace vertical>
        <NSpace align="center">
          <span class="label">围栏名称：</span>
          <NInput
            v-model:value="searchParams.name"
            placeholder="输入围栏名称"
            style="width: 200px"
            clearable
          />
          
          <span class="label">状态：</span>
          <NSelect
            v-model:value="searchParams.status"
            :options="statusOptions"
            style="width: 150px"
          />
        </NSpace>
        
        <NSpace>
          <NButton type="primary" @click="queryGeofenceData" :loading="loading">
            查询围栏
          </NButton>
          
          <NButton @click="loadExistingGeofences">
            刷新地图
          </NButton>
          
          <NButton @click="clearAllPolygons">
            清除地图
          </NButton>
          
          <NButton type="success" @click="addGeofence">
            新增围栏
          </NButton>
        </NSpace>
      </NSpace>
    </NCard>

    <!-- 地图显示 -->
    <NCard title="围栏地图" class="mb-4">
      <div class="map-controls mb-2">
        <NSpace>
          <NButton @click="createPolygon" type="primary" size="small">
            创建多边形
          </NButton>
          <NButton @click="startEdit" size="small">
            开始编辑
          </NButton>
          <NButton @click="endEdit" size="small">
            结束编辑
          </NButton>
          <NButton @click="saveCurrentArea" type="success" size="small">
            保存区域到表单
          </NButton>
          <NButton @click="clearCurrentPolygon" type="warning" size="small">
            清除当前区域
          </NButton>
        </NSpace>
      </div>
      <div id="map-container" class="map-container"></div>
    </NCard>

    <!-- 围栏数据表格 -->
    <NCard title="围栏列表">
      <NDataTable
        :data="geofenceData"
        :columns="columns"
        :row-key="(row) => row.id"
        :loading="loading"
        size="small"
        striped
        :pagination="{
          page: searchParams.pageNum,
          pageSize: searchParams.pageSize,
          itemCount: total,
          onUpdatePage: handlePageChange,
          onUpdatePageSize: handlePageSizeChange,
          showSizePicker: true,
          pageSizes: [20, 50, 100]
        }"
      />
    </NCard>

    <!-- 围栏编辑模态框 -->
    <NModal v-model:show="showModal" :title="modalTitle" preset="dialog" style="width: 800px">
      <NForm :model="formData" label-placement="left" label-width="120px">
        <NSpace vertical>
          <NFormItem label="围栏名称" required>
            <NInput v-model:value="formData.name" placeholder="请输入围栏名称" />
          </NFormItem>
          
          <NFormItem label="围栏描述">
            <NInput
              v-model:value="formData.description"
              type="textarea"
              :rows="3"
              placeholder="请输入围栏描述"
            />
          </NFormItem>
          
          <NSpace>
            <NFormItem label="围栏类型">
              <NSelect
                v-model:value="formData.fenceType"
                :options="fenceTypeOptions"
                style="width: 120px"
              />
            </NFormItem>
            
            <NFormItem label="告警级别">
              <NSelect
                v-model:value="formData.alertLevel"
                :options="alertLevelOptions"
                style="width: 120px"
              />
            </NFormItem>
          </NSpace>
          
          <NSpace>
            <NFormItem label="进入告警">
              <NSwitch v-model:value="formData.alertOnEnter" />
            </NFormItem>
            
            <NFormItem label="离开告警">
              <NSwitch v-model:value="formData.alertOnExit" />
            </NFormItem>
            
            <NFormItem label="停留告警">
              <NSwitch v-model:value="formData.alertOnStay" />
            </NFormItem>
          </NSpace>
          
          <NFormItem v-if="formData.alertOnStay" label="停留时长(分钟)">
            <NInput
              v-model:value="formData.stayDurationMinutes"
              type="number"
              style="width: 120px"
            />
          </NFormItem>
          
          <NFormItem label="启用状态">
            <NSwitch v-model:value="formData.isActive" />
          </NFormItem>
          
          <NFormItem label="围栏区域">
            <div class="area-info">
              <span v-if="formData.area">已设置围栏区域</span>
              <span v-else class="text-warning">请在地图上绘制围栏区域</span>
            </div>
          </NFormItem>
        </NSpace>
      </NForm>
      
      <template #action>
        <NSpace>
          <NButton @click="cancelEdit">取消</NButton>
          <NButton type="primary" @click="saveGeofence">
            {{ modalMode === 'add' ? '添加' : '更新' }}
          </NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.geofence-management {
  padding: 16px;
}

.map-container {
  height: 500px;
  width: 100%;
  border: 1px solid #e0e0e6;
  border-radius: 6px;
}

.map-controls {
  padding: 8px 0;
}

.label {
  font-weight: 500;
  color: #333;
  min-width: 80px;
  text-align: right;
}

.mb-2 {
  margin-bottom: 8px;
}

.mb-4 {
  margin-bottom: 16px;
}

.area-info {
  font-size: 14px;
}

.text-warning {
  color: #f0a020;
}
</style>
