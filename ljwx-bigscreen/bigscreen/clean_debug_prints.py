#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理代码中的调试print语句"""
import os,re,argparse
from pathlib import Path

class PrintCleaner:#print清理器
    """代码中print语句的清理器"""
    def __init__(self,dry_run=True):
        self.dry_run=dry_run#试运行模式
        self.debug_patterns=[#调试print模式
            r'print\s*\(\s*["\']debug',
            r'print\s*\(\s*["\']DEBUG',
            r'print\s*\(\s*["\']测试',
            r'print\s*\(\s*["\']临时',
            r'print\s*\(\s*f?["\'][^"\']*debug',
            r'print\s*\([^)]*[,\s]+debug',
        ]
        self.exclude_patterns=[#排除模式(保留重要print)
            r'print\s*\(\s*["\']🚀',#启动信息
            r'print\s*\(\s*["\']✅',#成功信息  
            r'print\s*\(\s*["\']❌',#错误信息
            r'print\s*\(\s*["\']⚠️',#警告信息
        ]
        
    def should_exclude(self,line):#是否应该排除
        """检查是否应该排除这行print"""
        return any(re.search(pattern,line,re.IGNORECASE) for pattern in self.exclude_patterns)
        
    def is_debug_print(self,line):#是否是调试print
        """检查是否是调试相关的print"""
        if self.should_exclude(line):
            return False
        return any(re.search(pattern,line,re.IGNORECASE) for pattern in self.debug_patterns)
        
    def clean_file(self,file_path):#清理文件
        """清理文件中的调试print语句"""
        try:
            with open(file_path,'r',encoding='utf-8') as f:
                lines=f.readlines()
                
            cleaned_lines=[]
            changes=0
            
            for i,line in enumerate(lines):
                stripped=line.strip()
                
                if self.is_debug_print(stripped):
                    # 注释掉调试print
                    indent=' '*(len(line)-len(line.lstrip()))
                    commented_line=f"{indent}# {stripped}  # 已禁用调试输出\n"
                    cleaned_lines.append(commented_line)
                    changes+=1
                    print(f"  行{i+1}: {stripped}")
                else:
                    cleaned_lines.append(line)
                    
            if changes>0 and not self.dry_run:
                with open(file_path,'w',encoding='utf-8') as f:
                    f.writelines(cleaned_lines)
                    
            return changes
            
        except Exception as e:
            print(f"❌ 处理文件失败 {file_path}: {e}")
            return 0
            
    def clean_directory(self,directory):#清理目录
        """递归清理目录中的Python文件"""
        total_changes=0
        directory=Path(directory)
        
        for py_file in directory.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
                
            print(f"\n📄 检查文件: {py_file}")
            changes=self.clean_file(py_file)
            
            if changes>0:
                print(f"✅ 发现{changes}个调试print")
                total_changes+=changes
            else:
                print("  无调试print")
                
        return total_changes

def main():#主函数
    parser=argparse.ArgumentParser(description='清理代码中的调试print语句')
    parser.add_argument('--path',default='.',help='要清理的路径')
    parser.add_argument('--execute',action='store_true',help='执行清理(默认为预览模式)')
    parser.add_argument('--pattern',action='append',help='添加自定义调试模式')
    
    args=parser.parse_args()
    
    cleaner=PrintCleaner(dry_run=not args.execute)
    
    if args.pattern:
        cleaner.debug_patterns.extend(args.pattern)
        
    mode="执行模式" if args.execute else "预览模式"
    print(f"🧹 开始清理调试print语句 ({mode})")
    print("="*50)
    
    total_changes=cleaner.clean_directory(args.path)
    
    print("="*50)
    if total_changes>0:
        action="已注释" if args.execute else "将注释"
        print(f"🎉 完成! {action} {total_changes}个调试print语句")
    else:
        print("✨ 未发现需要清理的调试print")
        
    if not args.execute and total_changes>0:
        print("\n💡 使用 --execute 参数执行实际清理")

if __name__=="__main__":
    main() 