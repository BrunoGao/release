#!/usr/bin/env python3
"""
测试 upload_common_event 客户信息提取修复
"""

# 模拟修复后的客户信息提取逻辑
def extract_common_event_customer_info(data):
    """模拟修复后的upload_common_event客户信息提取逻辑"""
    # 优先使用直接传递的客户信息参数 - 支持两种字段名格式
    customerId = data.get("customer_id") or data.get("customerId")
    orgId = data.get("org_id") or data.get("orgId")
    userId = data.get("user_id") or data.get("userId")
    
    return customerId, orgId, userId

# 测试数据 - 与实际日志中的数据一致
test_data = {
    'eventType': 'com.tdtech.ohos.action.WEAR_STATUS_CHANGED', 
    'eventValue': '0', 
    'deviceSn': 'CRFTQ23409001890', 
    'customerId': '1939964806110937090', 
    'orgId': '1939964806110937090', 
    'userId': '1940034533382479873', 
    'timestamp': '2025-09-10 13:05:24'
}

print("=== 测试 upload_common_event 客户信息提取修复 ===")

print("\n1. 测试原始数据:")
print(f"   数据: {test_data}")

print("\n2. 测试修复前的逻辑 (只支持下划线格式):")
old_customerId = test_data.get("customer_id")
old_orgId = test_data.get("org_id") 
old_userId = test_data.get("user_id")
print(f"   修复前结果: customerId={old_customerId}, orgId={old_orgId}, userId={old_userId}")

print("\n3. 测试修复后的逻辑 (支持两种格式):")
new_customerId, new_orgId, new_userId = extract_common_event_customer_info(test_data)
print(f"   修复后结果: customerId={new_customerId}, orgId={new_orgId}, userId={new_userId}")

print("\n4. 测试结果验证:")
success = (new_customerId == "1939964806110937090" and 
          new_orgId == "1939964806110937090" and 
          new_userId == "1940034533382479873")

if success:
    print("   ✅ upload_common_event 修复成功！客户信息能够正确提取")
else:
    print("   ❌ upload_common_event 修复失败！客户信息提取仍有问题")

print("\n5. 测试下划线格式兼容性:")
test_data_underscore = {
    'eventType': 'com.tdtech.ohos.action.WEAR_STATUS_CHANGED', 
    'eventValue': '1', 
    'deviceSn': 'CRFTQ23409001890', 
    'customer_id': '1939964806110937090', 
    'org_id': '1939964806110937090', 
    'user_id': '1940034533382479873', 
    'timestamp': '2025-09-10 13:05:24'
}

under_customerId, under_orgId, under_userId = extract_common_event_customer_info(test_data_underscore)
print(f"   下划线格式: customerId={under_customerId}, orgId={under_orgId}, userId={under_userId}")

print("\n=== 测试完成 ===")