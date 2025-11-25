# AI助手集成说明 - OpenRouter Claude Sonnet 4.5

## 🤖 集成概述

灵境万象健康监测大屏V2.0已成功集成OpenRouter的Claude Sonnet 4.5 AI模型,提供智能对话和数据分析能力。

---

## 🔑 API配置

### OpenRouter设置
- **API Key**: `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`
- **模型**: `anthropic/claude-3.5-sonnet`
- **端点**: `https://openrouter.ai/api/v1/chat/completions`
- **超时**: 30秒

### 请求参数
```json
{
  "model": "anthropic/claude-3.5-sonnet",
  "messages": [
    {"role": "system", "content": "系统提示词"},
    {"role": "user", "content": "用户消息"}
  ],
  "max_tokens": 500,
  "temperature": 0.7
}
```

---

## 🎯 功能特性

### 1. 智能上下文感知
AI助手会自动获取当前系统状态作为上下文:
- ✅ 在线设备数量
- ✅ 异常设备数量
- ✅ 今日告警数量
- ✅ 监测用户数量

### 2. 专业健康分析
系统提示词确保AI助手:
- 📊 提供基于实际数据的分析
- 💡 给出可操作的健康建议
- 🎯 直接回答问题,不重复提问
- 📝 控制回答长度(150字以内)
- 😊 保持专业友好的语气

### 3. 智能回退机制
如果OpenRouter API失败,系统会自动回退到关键词匹配模式:
- ⚡ 零延迟响应
- 📚 预设常见问题答案
- 🔄 平滑的用户体验

---

## 💬 使用示例

### 在大屏中使用

1. **打开AI助手**: 点击右上角🤖按钮
2. **输入问题**:
   - "分析最近的健康趋势"
   - "显示血压异常最多的区域"
   - "推荐需要重点关注的人员"
   - "当前系统运行状态如何"

### API调用示例

```bash
curl -X POST http://192.168.1.83:5225/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "1939964806110937090",
    "message": "分析最近的健康趋势"
  }'
```

### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "response": "根据最近7天的数据,整体健康指标保持稳定...",
    "timestamp": "2025-11-25T08:00:00",
    "model": "claude-3.5-sonnet"
  }
}
```

---

## 🛠️ 技术实现

### 核心函数

#### 1. `ai_chat()` - AI对话主函数
```python
@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """AI对话接口 - 集成OpenRouter Claude Sonnet 4.5"""
    # 1. 获取用户消息和客户ID
    # 2. 获取系统上下文数据
    # 3. 构建系统提示词
    # 4. 调用OpenRouter API
    # 5. 返回AI响应或回退响应
```

#### 2. `get_ai_context_data()` - 获取系统上下文
```python
def get_ai_context_data(customer_id):
    """获取AI对话的上下文数据"""
    # 查询数据库获取:
    # - 在线设备数
    # - 异常设备数
    # - 今日告警数
    # - 监测用户数
```

#### 3. `get_fallback_response()` - 回退响应
```python
def get_fallback_response(message, customer_id):
    """AI API失败时的回退响应 - 基于关键词匹配"""
    # 关键词匹配逻辑:
    # - 血压 → 血压分析建议
    # - 趋势/分析 → 健康趋势分析
    # - 人员/排名 → 人员管理建议
    # - 区域/地图 → 地理分布分析
    # - 设备 → 设备状态建议
```

---

## 🎨 系统提示词模板

```
你是灵境万象健康监测系统的AI助手。你的任务是帮助用户分析健康数据和回答问题。

当前系统状态:
- 在线设备: {online_devices}台
- 异常设备: {abnormal_devices}台
- 今日告警: {today_alerts}条
- 监测用户: {monitored_users}人

请基于以上数据回答用户问题,给出专业、简洁、有价值的建议。回答要点:
1. 直接回答问题,不要重复用户的问题
2. 提供具体的数据支持
3. 给出可操作的建议
4. 保持专业和友好的语气
5. 回答控制在150字以内
```

---

## 🔒 安全性说明

### API Key保护
- ⚠️ **当前状态**: API Key硬编码在代码中
- ✅ **建议改进**: 移至环境变量或配置文件

### 改进方案

#### 方法1: 使用环境变量
```python
# 在 .env 文件中添加
OPENROUTER_API_KEY=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

# 在代码中使用
import os
from dotenv import load_dotenv
load_dotenv()

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
```

#### 方法2: 使用配置文件
```python
# 在 config.py 中添加
OPENROUTER_API_KEY = 'sk-or-v1-...'

# 在 bigScreen.py 中导入
from config import OPENROUTER_API_KEY
```

---

## 📊 性能优化

### 当前配置
- **超时时间**: 30秒
- **最大Token**: 500
- **温度参数**: 0.7 (平衡创造性和准确性)

### 优化建议

1. **缓存常见问题**
   ```python
   # 使用Redis缓存常见问题的答案
   cache_key = f"ai_chat:{hash(message)}"
   cached_response = redis.get(cache_key)
   if cached_response:
       return cached_response
   ```

2. **异步处理**
   ```python
   # 使用异步请求提升响应速度
   import asyncio
   import aiohttp

   async def call_openrouter_async(message):
       async with aiohttp.ClientSession() as session:
           async with session.post(url, json=data) as response:
               return await response.json()
   ```

3. **批量处理**
   - 对于多个问题,可以批量发送到OpenRouter
   - 减少网络往返次数

---

## 📈 监控指标

### 关键指标
- ✅ API调用成功率
- ✅ 平均响应时间
- ✅ 回退频率
- ✅ 用户满意度

### 日志记录
所有AI对话都会记录到日志:
```
2025-11-25 08:00:00 [INFO] AI对话成功 - 模型: claude-3.5-sonnet
2025-11-25 08:00:05 [ERROR] OpenRouter API超时 - 使用回退响应
```

---

## 🐛 故障排查

### 常见问题

#### 1. API调用失败
**症状**: 返回500错误或回退响应
**检查**:
- OpenRouter API Key是否有效
- 网络连接是否正常
- API额度是否用尽

#### 2. 响应缓慢
**症状**: 超过30秒无响应
**解决**:
- 检查网络延迟
- 降低max_tokens参数
- 考虑使用更快的模型

#### 3. 回答不准确
**症状**: AI回答与上下文不符
**解决**:
- 检查系统提示词是否正确
- 验证上下文数据是否准确
- 调整temperature参数

---

## 🔄 版本历史

### V1.0 (2025-11-25)
- ✅ 集成OpenRouter Claude Sonnet 4.5
- ✅ 实现智能上下文感知
- ✅ 添加回退机制
- ✅ 完善错误处理

### 未来计划
- [ ] 迁移API Key到环境变量
- [ ] 实现Redis缓存
- [ ] 添加对话历史记录
- [ ] 支持多轮对话
- [ ] 集成语音识别

---

## 📞 支持

如有问题,请查看:
- 📖 OpenRouter文档: https://openrouter.ai/docs
- 🤖 Claude API文档: https://docs.anthropic.com/
- 💬 技术支持: 灵境万象团队

---

**版本**: V1.0
**更新时间**: 2025-11-25
**集成模型**: Claude Sonnet 4.5
**API提供商**: OpenRouter

🎉 **AI助手已就绪,开始智能对话吧!**
