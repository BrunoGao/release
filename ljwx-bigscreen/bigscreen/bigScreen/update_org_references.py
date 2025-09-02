#!/usr/bin/env python3
"""
更新ljwx-bigscreen中所有组织查询引用的脚本
将直接的数据库查询替换为统一的org_service封装
"""

import os
import re
import sys

def update_file_org_references(file_path):
    """更新单个文件中的组织查询引用"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        updated = False
        
        # 1. 添加org_service导入（如果还没有）
        if 'from .org_service import' not in content and 'fetch_departments_by_orgId' in content:
            # 找到其他org相关导入的位置
            if 'from .org import' in content:
                content = content.replace(
                    'from .org import',
                    'from .org import\nfrom .org_service import get_unified_org_service\n# from .org import'
                )
                updated = True
            elif 'import' in content:
                # 在文件开头添加导入
                lines = content.split('\n')
                import_index = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        import_index = i
                
                if import_index >= 0:
                    lines.insert(import_index + 1, 'from .org_service import get_unified_org_service')
                    content = '\n'.join(lines)
                    updated = True
        
        # 2. 替换直接的parent_id查询为统一服务
        pattern1 = r'db\.session\.query\(OrgInfo\)\\?\s*\.filter\(OrgInfo\.parent_id\s*==\s*(\w+)\)'
        if re.search(pattern1, content):
            content = re.sub(
                pattern1,
                r'get_unified_org_service().get_org_descendants_ids(\1)',
                content
            )
            updated = True
        
        # 3. 添加注释说明已优化
        if updated:
            if '# 组织查询已优化使用闭包表' not in content:
                content = f"# 组织查询已优化使用闭包表 - {os.path.basename(file_path)}\n" + content
        
        # 保存更新后的文件
        if updated and content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 更新文件: {file_path}")
            return True
        else:
            print(f"⚪ 无需更新: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ 更新文件失败 {file_path}: {str(e)}")
        return False

def main():
    """主函数 - 更新所有相关文件"""
    
    bigscreen_path = "/Users/brunogao/work/codes/health/ljwx/yunxiang/ljwx-bigscreen/bigscreen/bigScreen"
    
    # 需要检查的文件列表
    files_to_update = [
        f"{bigscreen_path}/user_health_data.py",
        f"{bigscreen_path}/device.py", 
        f"{bigscreen_path}/bigScreen.py",
        f"{bigscreen_path}/message.py",
        f"{bigscreen_path}/alert.py"
    ]
    
    updated_count = 0
    
    print("🔧 开始更新ljwx-bigscreen组织查询引用...")
    print("="*60)
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            if update_file_org_references(file_path):
                updated_count += 1
        else:
            print(f"⚠️  文件不存在: {file_path}")
    
    print("="*60)
    print(f"🎉 更新完成！共更新 {updated_count} 个文件")
    print("💡 建议运行测试验证功能正常")

if __name__ == "__main__":
    main()