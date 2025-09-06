# LJWX系统统一配置管理

本目录包含LJWX系统的统一配置管理工具，支持所有服务统一读取配置信息。

## 文件结构

```
client/config/
├── ljwx-config.yaml           # 主配置文件（YAML格式）
├── config_loader.py           # Python配置加载器
├── config-loader.js           # JavaScript配置加载器  
├── LJWXConfigLoader.java      # Java配置加载器
├── package.json               # JavaScript依赖配置
└── README.md                  # 本文档
```

## 主配置文件

`ljwx-config.yaml` 是系统的核心配置文件，包含：

- **系统信息**: 系统名称、版本、环境
- **数据库配置**: MySQL、Redis连接信息
- **服务端口**: 各服务的端口配置
- **镜像版本**: Docker镜像版本信息
- **网络配置**: Docker网络设置
- **日志配置**: 日志级别和格式
- **安全配置**: JWT密钥、CORS设置
- **业务配置**: 业务相关的参数

## 各语言配置加载器

### Python (ljwx-bigscreen)

```python
# 导入配置加载器
from config_loader import get_config, get_database_config, get_service_config

# 获取配置
config = get_config()
mysql_config = get_database_config('mysql')
service_config = get_service_config('ljwx-bigscreen')

# 获取具体配置值
db_host = config.get('database.mysql.host')
service_port = config.get('services.ljwx-bigscreen.port')
```

### JavaScript (ljwx-admin)

```javascript
// 导入配置加载器
const { getConfig, getDatabaseConfig, getServiceConfig } = require('./config-loader');

// 获取配置
const config = getConfig();
const mysqlConfig = getDatabaseConfig('mysql');
const serviceConfig = getServiceConfig('ljwx-admin');

// 获取具体配置值
const dbHost = config.get('database.mysql.host');
const servicePort = config.get('services.ljwx-admin.port');
```

### Java (ljwx-boot)

```java
// Spring Boot中使用
@Autowired
private LJWXConfigLoader configLoader;

// 获取配置
Map<String, Object> mysqlConfig = configLoader.getDatabaseConfig("mysql");
Map<String, Object> serviceConfig = configLoader.getServiceConfig("ljwx-boot");

// 获取具体配置值
String dbHost = configLoader.getString("database.mysql.host", "localhost");
Integer servicePort = configLoader.getInt("services.ljwx-boot.port", 8082);
```

## 环境变量覆盖

配置支持环境变量覆盖，优先级：**环境变量 > 配置文件**

### 数据库配置覆盖

- `MYSQL_HOST` - MySQL主机地址
- `MYSQL_PORT` - MySQL端口
- `MYSQL_DATABASE` - 数据库名
- `MYSQL_USERNAME` - 数据库用户名
- `MYSQL_PASSWORD` - 数据库密码
- `REDIS_HOST` - Redis主机地址
- `REDIS_PORT` - Redis端口
- `REDIS_PASSWORD` - Redis密码

### 服务端口覆盖

- `SERVER_PORT` + `SERVICE_NAME` - 特定服务的端口

## 配置文件路径查找顺序

各配置加载器会按以下顺序查找配置文件：

1. `/app/config/ljwx-config.yaml` (容器内路径)
2. `/client/config/ljwx-config.yaml` (挂载路径)
3. `client/config/ljwx-config.yaml` (相对路径)
4. `config/ljwx-config.yaml` (简化路径)
5. 指定的自定义路径

## 使用方法

### 1. 安装依赖

**Python依赖:**
```bash
pip install PyYAML
```

**JavaScript依赖:**
```bash
cd client/config
npm install
```

**Java依赖:**
在`pom.xml`或`build.gradle`中添加SnakeYAML依赖。

### 2. 配置文件挂载

在Docker容器中挂载配置文件：

```yaml
# docker-compose.yml
volumes:
  - ./client/config/ljwx-config.yaml:/app/config/ljwx-config.yaml:ro
```

### 3. 在应用中使用

各服务在启动时自动加载配置，无需额外配置。

## 配置生成工具

使用 `generate-config.sh` 可以从统一配置生成各服务的运行时配置：

```bash
cd client
./generate-config.sh
```

生成的文件：
- `docker-compose.yml` - Docker Compose配置
- `.env` - 环境变量文件
- `config/bigscreen/config.py` - Bigscreen配置
- `config/boot/application-prod.yml` - Boot配置

## 配置更新

1. 修改 `ljwx-config.yaml` 文件
2. 重新生成配置: `./generate-config.sh`
3. 重启相关服务: `docker-compose restart`

## 安全注意事项

- 配置文件包含敏感信息（数据库密码等），请妥善保管
- 生产环境建议使用环境变量覆盖敏感配置
- 配置文件应使用只读挂载到容器中

## 故障排除

### 配置文件未找到

确保配置文件路径正确，检查容器内挂载是否成功：

```bash
docker exec -it ljwx-bigscreen ls -la /app/config/
```

### 配置加载失败

检查YAML文件格式是否正确：

```bash
python3 -c "import yaml; yaml.safe_load(open('client/config/ljwx-config.yaml'))"
```

### 环境变量不生效

确认环境变量名称正确，并在容器启动时传入：

```yaml
environment:
  - MYSQL_HOST=new-mysql-host
  - MYSQL_PORT=3307
```