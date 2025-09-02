# 后端修复指南

## 问题概述

前端已经完成了告警配置三标签页的实现，但后端还需要进行以下修复：

### 1. 数据库问题
- 后端代码查询 `t_wechat_alert_config` 表，但使用了 `tenant_id` 字段
- 需要统一使用 `customer_id` 字段

### 2. 接口问题  
- 消息配置接口 `/t_message_config/page` 不存在

## 🔧 修复步骤

### 步骤1：执行数据库修复脚本

```bash
# 执行数据库修复脚本
mysql -u root -p < fix_table_structure_customer_id.sql
```

### 步骤2：修改后端实体类

需要修改 `TWechatAlertConfig` 实体类，将 `tenantId` 改为 `customerId`：

**文件位置**：`ljwx-boot-modules/src/main/java/.../entity/TWechatAlertConfig.java`

```java
@TableName("t_wechat_alert_config")
public class TWechatAlertConfig {
    @TableId(value = "id", type = IdType.AUTO)
    private Long id;
    
    // 将 tenantId 改为 customerId
    @TableField("customer_id")
    private Long customerId;  // 原来是 tenantId
    
    @TableField("type")
    private String type;
    
    // ... 其他字段保持不变
}
```

### 步骤3：修改Mapper XML

**文件位置**：`ljwx-boot-modules/src/main/resources/mapper/TWechatAlertConfigMapper.xml`

将所有的 `tenant_id` 替换为 `customer_id`：

```xml
<!-- 修改查询字段 -->
<select id="selectList" resultType="...">
    SELECT id, customer_id, type, corp_id, agent_id, secret, 
           appid, appsecret, template_id, enabled,
           create_user, create_user_id, create_time,
           update_user, update_user_id, update_time, is_deleted
    FROM t_wechat_alert_config
    WHERE is_deleted = 0
    <if test="customerId != null">
        AND customer_id = #{customerId}
    </if>
</select>
```

### 步骤4：修改Service层

**文件位置**：`ljwx-boot-modules/src/main/java/.../service/impl/TWechatAlertConfigServiceImpl.java`

```java
@Override
public IPage<TWechatAlertConfig> listTWechatAlertConfigPage(TWechatAlertConfigPageReqVO reqVO) {
    LambdaQueryWrapper<TWechatAlertConfig> wrapper = new LambdaQueryWrapper<>();
    
    // 将 tenantId 改为 customerId
    wrapper.eq(reqVO.getCustomerId() != null, TWechatAlertConfig::getCustomerId, reqVO.getCustomerId());
    wrapper.eq(StringUtils.hasText(reqVO.getType()), TWechatAlertConfig::getType, reqVO.getType());
    wrapper.eq(reqVO.getEnabled() != null, TWechatAlertConfig::getEnabled, reqVO.getEnabled());
    wrapper.eq(TWechatAlertConfig::getIsDeleted, false);
    
    return this.page(new Page<>(reqVO.getPage(), reqVO.getPageSize()), wrapper);
}
```

### 步骤5：创建消息配置相关类

#### 5.1 创建实体类

**文件位置**：`ljwx-boot-modules/src/main/java/.../entity/TMessageConfig.java`

```java
@Data
@TableName("t_message_config")
public class TMessageConfig extends BaseEntity {
    @TableId(value = "id", type = IdType.AUTO)
    private Long id;
    
    @TableField("customer_id")
    private Long customerId;
    
    @TableField("name")
    private String name;
    
    @TableField("type")
    private String type;
    
    @TableField("endpoint")
    private String endpoint;
    
    @TableField("access_key")
    private String accessKey;
    
    @TableField("secret_key")
    private String secretKey;
    
    @TableField("template_id")
    private String templateId;
    
    @TableField("enabled")
    private Boolean enabled;
    
    @TableField("description")
    private String description;
}
```

#### 5.2 创建Mapper

**文件位置**：`ljwx-boot-modules/src/main/java/.../mapper/TMessageConfigMapper.java`

```java
@Mapper
public interface TMessageConfigMapper extends BaseMapper<TMessageConfig> {
}
```

#### 5.3 创建Service

**文件位置**：`ljwx-boot-modules/src/main/java/.../service/TMessageConfigService.java`

```java
public interface TMessageConfigService extends IService<TMessageConfig> {
    IPage<TMessageConfig> listTMessageConfigPage(TMessageConfigPageReqVO reqVO);
}
```

**实现类**：

```java
@Service
public class TMessageConfigServiceImpl extends ServiceImpl<TMessageConfigMapper, TMessageConfig> 
    implements TMessageConfigService {
    
    @Override
    public IPage<TMessageConfig> listTMessageConfigPage(TMessageConfigPageReqVO reqVO) {
        LambdaQueryWrapper<TMessageConfig> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(reqVO.getCustomerId() != null, TMessageConfig::getCustomerId, reqVO.getCustomerId());
        wrapper.like(StringUtils.hasText(reqVO.getName()), TMessageConfig::getName, reqVO.getName());
        wrapper.eq(StringUtils.hasText(reqVO.getType()), TMessageConfig::getType, reqVO.getType());
        wrapper.eq(reqVO.getEnabled() != null, TMessageConfig::getEnabled, reqVO.getEnabled());
        wrapper.eq(TMessageConfig::getIsDeleted, false);
        wrapper.orderByDesc(TMessageConfig::getCreateTime);
        
        return this.page(new Page<>(reqVO.getPage(), reqVO.getPageSize()), wrapper);
    }
}
```

#### 5.4 创建Controller

**文件位置**：`ljwx-boot-admin/src/main/java/.../controller/TMessageConfigController.java`

```java
@RestController
@RequestMapping("/t_message_config")
@RequiredArgsConstructor
public class TMessageConfigController {
    
    private final TMessageConfigService messageConfigService;
    
    @GetMapping("/page")
    public Result<PageResult<TMessageConfig>> page(TMessageConfigPageReqVO reqVO) {
        IPage<TMessageConfig> page = messageConfigService.listTMessageConfigPage(reqVO);
        return Result.success(PageResult.of(page));
    }
    
    @PostMapping("/")
    public Result<Boolean> create(@RequestBody TMessageConfigCreateReqVO reqVO) {
        TMessageConfig entity = BeanUtils.copyProperties(reqVO, TMessageConfig.class);
        return Result.success(messageConfigService.save(entity));
    }
    
    @PutMapping("/")
    public Result<Boolean> update(@RequestBody TMessageConfigUpdateReqVO reqVO) {
        TMessageConfig entity = BeanUtils.copyProperties(reqVO, TMessageConfig.class);
        return Result.success(messageConfigService.updateById(entity));
    }
    
    @DeleteMapping("/")
    public Result<Boolean> delete(@RequestBody DeleteReqVO reqVO) {
        return Result.success(messageConfigService.removeByIds(reqVO.getIds()));
    }
}
```

### 步骤6：修改前端API参数名称

确保前端API调用使用正确的参数名：

**文件位置**：前端已经修改完成，使用 `customerId` 而不是 `tenantId`

## 🧪 测试验证

### 1. 数据库验证
```sql
-- 检查表结构
DESCRIBE t_wechat_alert_config;
DESCRIBE t_message_config;

-- 检查数据
SELECT * FROM t_wechat_alert_config WHERE customer_id = 1;
SELECT * FROM t_message_config WHERE customer_id = 1;
```

### 2. API测试
```bash
# 测试微信配置接口
curl -X GET "http://localhost:9998/t_wechat_alarm_config/page?customerId=1"

# 测试消息配置接口  
curl -X GET "http://localhost:9998/t_message_config/page?customerId=1"
```

### 3. 前端测试
访问 `http://localhost:3333/alert/config` 验证三个标签页都能正常加载数据。

## 📝 检查清单

- [ ] 数据库脚本已执行
- [ ] TWechatAlertConfig实体类已修改
- [ ] Mapper XML已更新
- [ ] Service层已修改
- [ ] TMessageConfig相关类已创建
- [ ] Controller接口已实现
- [ ] API测试通过
- [ ] 前端页面正常显示

## 🔍 常见问题

1. **字段映射错误**：确保实体类字段名与数据库列名一致
2. **权限问题**：确保用户有对应的接口访问权限
3. **参数校验**：检查请求参数是否正确传递

完成以上修复后，告警配置页面应该能够正常工作。