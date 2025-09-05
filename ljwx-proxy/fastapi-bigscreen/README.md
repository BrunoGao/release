# FastAPI 大屏业务服务

提供业务大屏所需的所有API接口，作为前端页面与ljwx-boot服务之间的代理层。

## 功能特性

✅ **业务大屏支持** - 完整支持bigscreen_main.html和personal.html页面  
✅ **API代理** - 标准化API接口，代理到ljwx-boot服务  
✅ **CORS支持** - 跨域请求支持  
✅ **自动文档** - Swagger/OpenAPI自动生成文档  
✅ **健康检查** - 服务状态监控  

## 快速启动

```bash
# 方式1: 使用启动脚本（推荐）
./start.sh

# 方式2: 手动启动
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## 访问地址

- **业务大屏**: http://localhost:8000/bigscreen
- **个人健康页面**: http://localhost:8000/personal  
- **API文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## API接口列表

### 健康相关API
- `GET /api/health/score/comprehensive` - 健康综合评分
- `GET /api/health/realtime_data` - 实时健康数据
- `GET /api/health/trends` - 健康趋势数据
- `GET /health_data/chart/baseline` - 基线健康数据图表
- `POST /api/baseline/generate` - 生成基线数据
- `GET /fetchHealthDataById` - 根据ID获取健康数据
- `GET /api/personal/health/scores` - 个人健康评分
- `GET /api/health/recommendations` - 健康建议
- `GET /api/health/predictions` - 健康预测

### 设备相关API
- `GET /api/device/user_info` - 设备用户信息
- `GET /api/device/info` - 设备状态信息
- `GET /api/device/user_org` - 设备用户组织信息

### 用户相关API
- `GET /api/user/profile` - 用户资料
- `GET /fetch_users` - 获取组织下的用户列表

### 组织相关API
- `GET /get_departments` - 获取部门信息
- `GET /get_total_info` - 获取总体信息

### 统计相关API
- `GET /api/statistics/overview` - 统计概览
- `GET /api/realtime_stats` - 实时统计数据

### 消息告警相关API
- `GET /api/messages/user` - 获取用户消息
- `GET /api/alerts/user` - 获取用户告警
- `GET /api/personal/alerts` - 获取个人告警
- `POST /acknowledge_alert` - 确认告警
- `GET /dealAlert` - 处理告警

## 配置说明

在`main.py`中修改ljwx-boot服务地址：

```python
LJWX_BOOT_BASE_URL = "http://localhost:8080"  # 修改为实际的ljwx-boot服务地址
```

## 项目结构

```
fastapi-bigscreen/
├── main.py              # 主应用文件
├── requirements.txt     # 依赖包列表
├── start.sh            # 启动脚本
├── templates/          # HTML模板目录
│   ├── bigscreen_main.html
│   └── personal.html
└── README.md           # 项目说明
```

## 开发说明

1. 所有API都会代理到ljwx-boot服务
2. 支持自动重载，修改代码后无需重启
3. 详细的API文档可访问 `/docs` 查看
4. 支持跨域请求，便于前端开发调试

## 注意事项

⚠️ **确保ljwx-boot服务正在运行**  
⚠️ **根据实际环境修改服务地址**  
⚠️ **生产环境请配置适当的CORS策略**