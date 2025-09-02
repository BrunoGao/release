# 矿山环境日志采集系统设计方案

## 🎯 系统目标
为ljwx-watch、ljwx-phone、ljwx-bigscreen构建完整的日志采集、传输、显示系统，适应矿山复杂网络环境。

## 🏗️ 系统架构

### 数据流向
```
ljwx-watch (HiLog) → 蓝牙 → ljwx-phone → HTTP/网络 → ljwx-bigscreen
```

### 核心组件
1. **ljwx-watch**: 日志采集+蓝牙传输
2. **ljwx-phone**: 蓝牙接收+网络上传+本地显示
3. **ljwx-bigscreen**: 日志接收+存储+专业显示

## 📱 ljwx-watch端设计

### 1. 日志采集模块
```typescript
// LogCollector.ets
export class LogCollector {
  private logBuffer: LogEntry[] = []
  private bluetoothService: BluetoothService
  
  // HiLog监听和汇总
  collectSystemLogs() {
    // 监听所有HiLog输出
    // 按级别过滤：DEBUG/INFO/WARN/ERROR
    // 缓存到本地队列
  }
  
  // 定时发送日志
  sendLogsViaBluetooth() {
    if (this.logBuffer.length > 0) {
      const logPacket = this.encodeLogPacket()
      this.bluetoothService.sendData(logPacket)
    }
  }
}
```

### 2. 蓝牙协议扩展
```typescript
// BleProtocolEncoder.ets 新增日志类型
export enum DataType {
  HEALTH_DATA = 0x01,
  DEVICE_INFO = 0x02,
  LOG_DATA = 0x03  // 新增日志类型
}

export interface LogPacket {
  type: DataType.LOG_DATA
  deviceSn: string
  timestamp: number
  logLevel: LogLevel
  logContent: string
  checksum: number
}

// TLV编码实现
export class LogTLVEncoder {
  encode(logPacket: LogPacket): Uint8Array {
    // T: 数据类型 (1字节)
    // L: 数据长度 (2字节)
    // V: 数据内容 (变长)
    return this.buildTLVPacket(logPacket)
  }
}
```

### 3. 配置管理
```typescript
// LogConfig.ets
export class LogConfig {
  static readonly LOG_LEVELS = {
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3
  }
  
  // 矿山环境优化配置
  static readonly MINING_CONFIG = {
    BATCH_SIZE: 50,        // 批量发送条数
    SEND_INTERVAL: 30000,  // 发送间隔30秒
    MAX_BUFFER_SIZE: 1000, // 最大缓存1000条
    RETRY_COUNT: 3,        // 重试次数
    COMPRESSION: true      // 启用压缩
  }
}
```

## 📱 ljwx-phone端设计

### 1. 蓝牙日志接收
```dart
// bluetooth_log_receiver.dart
class BluetoothLogReceiver {
  final StreamController<WatchLogEntry> _logController = StreamController();
  
  // 解析蓝牙日志数据
  void handleBluetoothData(Uint8List data) {
    try {
      final logEntry = TLVDecoder.decodeLogPacket(data);
      _logController.add(logEntry);
      
      // 本地存储
      _storeLogLocally(logEntry);
      
      // 上传到服务器
      _uploadLogToServer(logEntry);
    } catch (e) {
      print('日志解析失败: $e');
    }
  }
  
  // 批量上传优化
  void _uploadLogToServer(WatchLogEntry log) {
    _logUploadQueue.add(log);
    
    if (_logUploadQueue.length >= 20) {
      _batchUploadLogs();
    }
  }
}
```

### 2. 网络上传模块
```dart
// log_upload_service.dart
class LogUploadService {
  static const String UPLOAD_ENDPOINT = '/api/upload_watch_log';
  
  // 批量上传日志
  Future<bool> uploadWatchLogs(List<WatchLogEntry> logs) async {
    try {
      final payload = {
        'logs': logs.map((log) => log.toJson()).toList(),
        'upload_time': DateTime.now().millisecondsSinceEpoch,
        'phone_id': await DeviceInfo.getDeviceId(),
      };
      
      final response = await http.post(
        Uri.parse('$baseUrl$UPLOAD_ENDPOINT'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );
      
      return response.statusCode == 200;
    } catch (e) {
      // 网络失败时本地缓存
      await _cacheFailedUpload(logs);
      return false;
    }
  }
  
  // 矿山网络重连机制
  Future<void> retryFailedUploads() async {
    final cachedLogs = await _getCachedLogs();
    for (final logBatch in cachedLogs) {
      if (await uploadWatchLogs(logBatch)) {
        await _removeCachedBatch(logBatch);
      }
    }
  }
}
```

### 3. 蓝牙调试页面
```dart
// bluetooth_debug_page.dart
class BluetoothDebugPage extends StatefulWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('蓝牙日志调试')),
      body: Column(
        children: [
          // 连接状态
          _buildConnectionStatus(),
          
          // 日志过滤器
          _buildLogFilter(),
          
          // 实时日志显示
          Expanded(
            child: StreamBuilder<WatchLogEntry>(
              stream: BluetoothLogReceiver.logStream,
              builder: (context, snapshot) {
                return ListView.builder(
                  itemCount: _filteredLogs.length,
                  itemBuilder: (context, index) {
                    return _buildLogItem(_filteredLogs[index]);
                  },
                );
              },
            ),
          ),
          
          // 操作按钮
          _buildActionButtons(),
        ],
      ),
    );
  }
  
  Widget _buildLogItem(WatchLogEntry log) {
    return Card(
      child: ListTile(
        leading: _getLogLevelIcon(log.level),
        title: Text(log.content),
        subtitle: Text('${log.deviceSn} - ${_formatTime(log.timestamp)}'),
        trailing: IconButton(
          icon: Icon(Icons.share),
          onPressed: () => _shareLog(log),
        ),
      ),
    );
  }
}
```

## 🖥️ ljwx-bigscreen端设计

### 1. 日志接收API
```python
# log_api.py
from flask import Blueprint, request, jsonify
from datetime import datetime
import json

log_bp = Blueprint('log', __name__)

@log_bp.route('/api/upload_watch_log', methods=['POST'])
def upload_watch_log():
    """接收手机上传的手表日志"""
    try:
        data = request.get_json()
        logs = data.get('logs', [])
        upload_time = data.get('upload_time')
        phone_id = data.get('phone_id')
        
        # 批量插入数据库
        log_entries = []
        for log_data in logs:
            log_entry = WatchLogEntry(
                device_sn=log_data['deviceSn'],
                timestamp=log_data['timestamp'],
                log_level=log_data['logLevel'],
                content=log_data['content'],
                phone_id=phone_id,
                upload_time=upload_time
            )
            log_entries.append(log_entry)
        
        # 使用批量插入优化性能
        db.session.bulk_save_objects(log_entries)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'成功接收{len(logs)}条日志',
            'processed_count': len(logs)
        })
        
    except Exception as e:
        system_logger.error(f"日志上传失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 2. 数据库模型
```python
# models/watch_log.py
from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, Index
from database import db

class WatchLogEntry(db.Model):
    __tablename__ = 'watch_logs'
    
    id = Column(Integer, primary_key=True)
    device_sn = Column(String(50), nullable=False, index=True)
    timestamp = Column(BigInteger, nullable=False, index=True)  # 手表时间戳
    log_level = Column(String(10), nullable=False, index=True)
    content = Column(Text, nullable=False)
    phone_id = Column(String(100), nullable=True)
    upload_time = Column(BigInteger, nullable=False)  # 上传时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 复合索引优化查询
    __table_args__ = (
        Index('idx_device_time', 'device_sn', 'timestamp'),
        Index('idx_level_time', 'log_level', 'timestamp'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'deviceSn': self.device_sn,
            'timestamp': self.timestamp,
            'logLevel': self.log_level,
            'content': self.content,
            'phoneId': self.phone_id,
            'uploadTime': self.upload_time,
            'createdAt': self.created_at.isoformat()
        }
```

### 3. 专业日志显示页面
```python
# routes/log_viewer.py
@app.route('/log_viewer')
def log_viewer():
    """专业日志查看页面"""
    return render_template('log_viewer.html')

@app.route('/api/watch_logs')
def get_watch_logs():
    """获取手表日志API"""
    try:
        # 查询参数
        device_sn = request.args.get('deviceSn')
        start_time = request.args.get('startTime', type=int)
        end_time = request.args.get('endTime', type=int)
        log_level = request.args.get('logLevel')
        keyword = request.args.get('keyword')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('perPage', 50, type=int)
        
        # 构建查询
        query = WatchLogEntry.query
        
        if device_sn:
            query = query.filter(WatchLogEntry.device_sn == device_sn)
        if start_time:
            query = query.filter(WatchLogEntry.timestamp >= start_time)
        if end_time:
            query = query.filter(WatchLogEntry.timestamp <= end_time)
        if log_level:
            query = query.filter(WatchLogEntry.log_level == log_level)
        if keyword:
            query = query.filter(WatchLogEntry.content.contains(keyword))
        
        # 分页查询
        pagination = query.order_by(WatchLogEntry.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 4. 前端日志查看器
```html
<!-- templates/log_viewer.html -->
<!DOCTYPE html>
<html>
<head>
    <title>手表日志查看器</title>
    <link rel="stylesheet" href="/static/css/log-viewer.css">
    <script src="https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.js"></script>
</head>
<body>
    <div id="logViewer">
        <!-- 搜索过滤器 -->
        <div class="filter-panel">
            <div class="filter-row">
                <select v-model="filters.deviceSn" @change="loadLogs">
                    <option value="">所有设备</option>
                    <option v-for="device in devices" :value="device">{{device}}</option>
                </select>
                
                <select v-model="filters.logLevel" @change="loadLogs">
                    <option value="">所有级别</option>
                    <option value="DEBUG">DEBUG</option>
                    <option value="INFO">INFO</option>
                    <option value="WARN">WARN</option>
                    <option value="ERROR">ERROR</option>
                </select>
                
                <input type="text" v-model="filters.keyword" @keyup.enter="loadLogs" 
                       placeholder="搜索关键词">
                
                <button @click="loadLogs" class="search-btn">搜索</button>
                <button @click="clearFilters" class="clear-btn">清除</button>
            </div>
            
            <div class="time-range">
                <input type="datetime-local" v-model="filters.startTime">
                <span>至</span>
                <input type="datetime-local" v-model="filters.endTime">
            </div>
        </div>
        
        <!-- 日志列表 -->
        <div class="log-container">
            <div class="log-header">
                <span class="col-time">时间</span>
                <span class="col-device">设备</span>
                <span class="col-level">级别</span>
                <span class="col-content">内容</span>
                <span class="col-actions">操作</span>
            </div>
            
            <div class="log-list">
                <div v-for="log in logs" :key="log.id" 
                     :class="['log-item', 'level-' + log.logLevel.toLowerCase()]">
                    <span class="col-time">{{formatTime(log.timestamp)}}</span>
                    <span class="col-device">{{log.deviceSn}}</span>
                    <span class="col-level">
                        <span :class="'level-badge level-' + log.logLevel.toLowerCase()">
                            {{log.logLevel}}
                        </span>
                    </span>
                    <span class="col-content" :title="log.content">{{log.content}}</span>
                    <span class="col-actions">
                        <button @click="copyLog(log)" class="action-btn">复制</button>
                        <button @click="exportLog(log)" class="action-btn">导出</button>
                    </span>
                </div>
            </div>
        </div>
        
        <!-- 分页 -->
        <div class="pagination">
            <button @click="prevPage" :disabled="currentPage <= 1">上一页</button>
            <span>第 {{currentPage}} 页，共 {{totalPages}} 页</span>
            <button @click="nextPage" :disabled="currentPage >= totalPages">下一页</button>
        </div>
        
        <!-- 实时日志开关 -->
        <div class="realtime-panel">
            <label>
                <input type="checkbox" v-model="realtimeMode" @change="toggleRealtime">
                实时日志
            </label>
            <span v-if="realtimeMode" class="realtime-status">●</span>
        </div>
    </div>
    
    <script src="/static/js/log-viewer.js"></script>
</body>
</html>
```

## 🔧 矿山环境优化

### 1. 网络适应性
```python
# network_adapter.py
class MiningNetworkAdapter:
    """矿山网络环境适配器"""
    
    def __init__(self):
        self.retry_config = {
            'max_retries': 5,
            'backoff_factor': 2,
            'timeout': 30
        }
        self.compression_enabled = True
        self.batch_size = 100
    
    def upload_with_retry(self, logs):
        """带重试的上传机制"""
        for attempt in range(self.retry_config['max_retries']):
            try:
                if self.compression_enabled:
                    logs = self.compress_logs(logs)
                
                response = self.send_logs(logs)
                if response.status_code == 200:
                    return True
                    
            except Exception as e:
                wait_time = self.retry_config['backoff_factor'] ** attempt
                time.sleep(wait_time)
                
        return False
    
    def compress_logs(self, logs):
        """日志压缩"""
        import gzip
        import json
        
        json_data = json.dumps(logs)
        compressed = gzip.compress(json_data.encode())
        return compressed
```

### 2. 离线缓存机制
```dart
// offline_cache.dart
class OfflineLogCache {
  static const String CACHE_TABLE = 'cached_logs';
  
  // 缓存失败的日志
  Future<void> cacheFailedLogs(List<WatchLogEntry> logs) async {
    final db = await DatabaseHelper.database;
    
    for (final log in logs) {
      await db.insert(CACHE_TABLE, {
        'device_sn': log.deviceSn,
        'timestamp': log.timestamp,
        'log_level': log.logLevel,
        'content': log.content,
        'retry_count': 0,
        'cached_at': DateTime.now().millisecondsSinceEpoch,
      });
    }
  }
  
  // 网络恢复时重新上传
  Future<void> retryCachedLogs() async {
    final db = await DatabaseHelper.database;
    final cachedLogs = await db.query(
      CACHE_TABLE,
      where: 'retry_count < ?',
      whereArgs: [5], // 最多重试5次
    );
    
    for (final logData in cachedLogs) {
      final success = await LogUploadService.uploadSingleLog(logData);
      
      if (success) {
        await db.delete(CACHE_TABLE, where: 'id = ?', whereArgs: [logData['id']]);
      } else {
        await db.update(
          CACHE_TABLE,
          {'retry_count': logData['retry_count'] + 1},
          where: 'id = ?',
          whereArgs: [logData['id']],
        );
      }
    }
  }
}
```

### 3. 数据压缩和优化
```typescript
// 手表端数据压缩
export class LogCompressor {
  // 简单的日志压缩算法
  static compressLogs(logs: LogEntry[]): Uint8Array {
    // 1. 去重相似日志
    const uniqueLogs = this.deduplicateLogs(logs);
    
    // 2. 压缩时间戳（使用差值编码）
    const compressedLogs = this.compressTimestamps(uniqueLogs);
    
    // 3. 字符串压缩
    return this.compressStrings(compressedLogs);
  }
  
  private static deduplicateLogs(logs: LogEntry[]): LogEntry[] {
    const seen = new Set<string>();
    return logs.filter(log => {
      const key = `${log.logLevel}_${log.content}`;
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  }
}
```

## 📊 监控和统计

### 1. 日志统计API
```python
# log_statistics.py
@app.route('/api/log_statistics')
def get_log_statistics():
    """获取日志统计信息"""
    try:
        # 按设备统计
        device_stats = db.session.query(
            WatchLogEntry.device_sn,
            func.count(WatchLogEntry.id).label('total_logs'),
            func.count(case([(WatchLogEntry.log_level == 'ERROR', 1)])).label('error_count'),
            func.max(WatchLogEntry.timestamp).label('last_log_time')
        ).group_by(WatchLogEntry.device_sn).all()
        
        # 按时间统计
        time_stats = db.session.query(
            func.date(WatchLogEntry.created_at).label('date'),
            func.count(WatchLogEntry.id).label('count')
        ).group_by(func.date(WatchLogEntry.created_at)).all()
        
        return jsonify({
            'device_statistics': [
                {
                    'deviceSn': stat.device_sn,
                    'totalLogs': stat.total_logs,
                    'errorCount': stat.error_count,
                    'lastLogTime': stat.last_log_time
                } for stat in device_stats
            ],
            'time_statistics': [
                {
                    'date': stat.date.isoformat(),
                    'count': stat.count
                } for stat in time_stats
            ]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 2. 实时监控
```javascript
// 实时日志监控
class RealtimeLogMonitor {
    constructor() {
        this.socket = null;
        this.isConnected = false;
    }
    
    connect() {
        this.socket = new WebSocket('ws://localhost:8001/ws/logs');
        
        this.socket.onopen = () => {
            this.isConnected = true;
            console.log('实时日志连接已建立');
        };
        
        this.socket.onmessage = (event) => {
            const logData = JSON.parse(event.data);
            this.handleNewLog(logData);
        };
        
        this.socket.onclose = () => {
            this.isConnected = false;
            // 自动重连
            setTimeout(() => this.connect(), 5000);
        };
    }
    
    handleNewLog(logData) {
        // 更新页面显示
        this.addLogToDisplay(logData);
        
        // 错误日志告警
        if (logData.logLevel === 'ERROR') {
            this.showErrorAlert(logData);
        }
    }
}
```

这个方案提供了完整的日志采集、传输、显示系统，特别针对矿山环境的网络复杂性进行了优化，包括离线缓存、重试机制、数据压缩等功能。 