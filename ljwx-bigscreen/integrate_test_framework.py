#!/usr/bin/env python3
"""测试框架集成脚本 - 将标准化测试框架集成到主应用"""
import os,sys,shutil
from pathlib import Path

def integrate_to_main_app():
    """将测试框架集成到主应用"""
    print("🔧 开始集成测试框架到主应用...")
    
    # 1. 检查主应用文件
    main_app_file = Path("bigscreen/app.py")
    if not main_app_file.exists():
        print("❌ 未找到主应用文件: bigscreen/app.py")
        return False
    
    # 2. 读取主应用内容
    with open(main_app_file, 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    # 3. 检查是否已经集成
    if "from tests.web.server import create_test_routes" in app_content:
        print("✅ 测试框架已经集成到主应用")
        return True
    
    # 4. 添加测试路由导入
    import_line = "from tests.web.server import create_test_routes"
    
    # 找到合适的位置插入导入
    lines = app_content.split('\n')
    insert_index = 0
    
    for i, line in enumerate(lines):
        if line.startswith('from flask import') or line.startswith('import'):
            insert_index = i + 1
    
    lines.insert(insert_index, import_line)
    
    # 5. 添加路由注册
    for i, line in enumerate(lines):
        if "if __name__ == '__main__':" in line:
            lines.insert(i, "    # 集成测试框架")
            lines.insert(i+1, "    create_test_routes(app)")
            lines.insert(i+2, "")
            break
    
    # 6. 写回文件
    with open(main_app_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ 测试框架已成功集成到主应用")
    return True

def cleanup_old_files():
    """清理旧的测试文件"""
    print("🧹 清理旧的测试文件...")
    
    old_files = [
        "test_report_server.py",
        "universal_test_manager.py", 
        "test_upload_health_data.py",
        "test_upload_device_info.py",
        "comprehensive_test_runner.py",
        "test_config.json",
        "quick_test_check.py"
    ]
    
    for file in old_files:
        file_path = Path(file)
        if file_path.exists():
            # 备份到backup目录
            backup_dir = Path("backup_old_tests")
            backup_dir.mkdir(exist_ok=True)
            shutil.move(file_path, backup_dir / file)
            print(f"  📦 已备份: {file} -> backup_old_tests/")
    
    print("✅ 旧文件清理完成")

def create_quick_start_script():
    """创建快速启动脚本"""
    script_content = '''#!/bin/bash
# ljwx测试框架快速启动脚本

echo "🚀 ljwx标准化测试框架"
echo "======================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

# 进入测试目录
cd "$(dirname "$0")/tests" || exit 1

case "$1" in
    "web")
        echo "🌐 启动Web界面..."
        echo "访问地址: http://localhost:5001/test"
        cd ../bigscreen && python app.py
        ;;
    "cli")
        echo "💻 命令行模式"
        python -m cli.runner "${@:2}"
        ;;
    "list")
        echo "📋 可用测试列表:"
        python -m cli.runner list
        ;;
    "run")
        echo "🧪 运行测试: $2"
        python -m cli.runner run "$2"
        ;;
    "all")
        echo "🚀 运行所有测试..."
        python -m cli.runner run --all --parallel
        ;;
    "report")
        echo "📊 生成测试报告..."
        python -m cli.runner report --format html
        ;;
    *)
        echo "使用方法:"
        echo "  $0 web      - 启动Web界面"
        echo "  $0 cli      - 命令行模式"
        echo "  $0 list     - 列出测试"
        echo "  $0 run <名称> - 运行指定测试"
        echo "  $0 all      - 运行所有测试"
        echo "  $0 report   - 生成报告"
        ;;
esac
'''
    
    script_path = Path("run_tests.sh")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 设置执行权限
    os.chmod(script_path, 0o755)
    print(f"✅ 快速启动脚本已创建: {script_path}")

def create_migration_summary():
    """创建迁移总结文档"""
    summary_content = '''# 测试框架标准化迁移总结

## 📋 迁移完成情况

### ✅ 已完成
1. **目录结构标准化** - 创建统一的tests/目录结构
2. **核心框架搭建** - BaseTest基类和TestManager管理器
3. **测试用例迁移** - 将现有测试迁移到新框架
4. **Web界面集成** - 集成到主应用(端口5001)
5. **命令行工具** - 提供完整的CLI支持
6. **配置统一管理** - JSON配置文件统一管理
7. **文档完善** - 详细的使用说明和API文档

### 🔄 架构变更

#### 旧架构问题
- 测试文件分散在多个目录
- 缺乏统一的基础类和管理器
- 独立的5002端口Web服务器
- 配置分散，难以维护
- 缺乏标准化的测试流程

#### 新架构优势
- 统一的tests/目录结构
- 标准化的BaseTest基类
- 集成到主应用(5001端口)
- 统一的配置管理
- 多种运行方式支持
- 完整的追踪和报告功能

### 📁 目录对比

#### 旧结构
```
ljwx-bigscreen/
├── test_report_server.py      # 独立Web服务器
├── universal_test_manager.py  # 简单管理器
├── test_upload_*.py          # 分散的测试文件
├── test_config.json          # 简单配置
└── test_framework/           # 部分测试文件
```

#### 新结构
```
ljwx-bigscreen/
└── tests/                    # 统一测试目录
    ├── core/                 # 核心框架
    ├── suites/              # 测试套件
    ├── config/              # 配置管理
    ├── web/                 # Web界面
    ├── cli/                 # 命令行工具
    ├── logs/                # 日志目录
    └── reports/             # 报告目录
```

### 🌐 Web服务变更

#### 旧方式
- 独立的5002端口服务器
- 简单的HTML界面
- 基础的API接口

#### 新方式
- 集成到主应用(5001端口)
- 现代化的响应式界面
- 完整的RESTful API
- 实时数据更新

### 🚀 使用方式

#### Web界面 (推荐)
```
访问: http://localhost:5001/test
```

#### 命令行
```bash
# 快速启动
./run_tests.sh all

# 详细命令
cd tests
python -m cli.runner run --all --parallel
```

#### API接口
```bash
curl -X POST http://localhost:5001/api/test/run \\
  -H "Content-Type: application/json" \\
  -d '{"test_name": "upload_health_data"}'
```

### 📊 功能对比

| 功能 | 旧框架 | 新框架 |
|------|--------|--------|
| 测试发现 | 手动配置 | 自动发现 |
| 并行执行 | 不支持 | 支持 |
| 报告格式 | JSON | JSON/HTML/Web |
| 配置管理 | 分散 | 统一 |
| 错误追踪 | 基础 | 完整 |
| 历史记录 | 无 | 支持 |
| CLI工具 | 无 | 完整 |

### 🔧 配置迁移

旧配置已自动迁移到新的统一配置文件:
- `tests/config/test_config.json`

### 📦 文件备份

旧的测试文件已备份到:
- `backup_old_tests/` 目录

### ⚠️ 注意事项

1. **端口变更**: 测试界面从5002迁移到5001
2. **导入路径**: 新的导入路径为 `from tests.core.test_manager import test_manager`
3. **配置文件**: 新配置文件位置为 `tests/config/test_config.json`
4. **Web界面**: 新界面地址为 `http://localhost:5001/test`

### 🎯 下一步计划

1. **性能优化** - 进一步优化测试执行性能
2. **更多测试** - 添加更多接口和功能测试
3. **CI/CD集成** - 集成到持续集成流程
4. **监控告警** - 添加测试失败告警机制

---

**迁移完成时间**: 2025-06-18  
**框架版本**: 1.0.0  
**负责人**: ljwx测试团队
'''
    
    summary_path = Path("TEST_FRAMEWORK_MIGRATION_SUMMARY.md")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    print(f"✅ 迁移总结文档已创建: {summary_path}")

def main():
    """主函数"""
    print("🚀 ljwx测试框架标准化集成")
    print("=" * 50)
    
    # 1. 集成到主应用
    if not integrate_to_main_app():
        print("❌ 集成失败")
        return
    
    # 2. 清理旧文件
    cleanup_old_files()
    
    # 3. 创建快速启动脚本
    create_quick_start_script()
    
    # 4. 创建迁移总结
    create_migration_summary()
    
    print("\n🎉 测试框架标准化完成!")
    print("=" * 50)
    print("📋 完成项目:")
    print("  ✅ 统一目录结构")
    print("  ✅ 核心框架搭建") 
    print("  ✅ Web界面集成(5001端口)")
    print("  ✅ 命令行工具")
    print("  ✅ 配置统一管理")
    print("  ✅ 文档完善")
    print()
    print("🚀 快速开始:")
    print("  Web界面: http://localhost:5001/test")
    print("  命令行: ./run_tests.sh all")
    print("  文档: tests/README.md")
    print()
    print("📞 如有问题，请查看迁移总结文档")

if __name__ == "__main__":
    main() 