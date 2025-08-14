#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""专业日志分析工具"""
import json,argparse,re
from datetime import datetime,timedelta
from pathlib import Path
from collections import defaultdict,Counter
from typing import List,Dict,Any

class LogAnalyzer:#日志分析器
    """专业日志分析器"""
    def __init__(self,logs_dir:str='logs'):
        self.logs_dir=Path(logs_dir)
        self.json_files=list(self.logs_dir.glob('*_json.log'))#JSON日志文件
        
    def parse_json_log(self,file_path:Path)->List[Dict[str,Any]]:#解析JSON日志
        """解析JSON格式日志文件"""
        logs=[]
        try:
            with open(file_path,'r',encoding='utf-8') as f:
                for line in f:
                    line=line.strip()
                    if line:
                        try:
                            log_entry=json.loads(line)
                            logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            print(f"⚠️ 日志文件不存在: {file_path}")
        return logs
        
    def filter_logs(self,logs:List[Dict],**filters)->List[Dict]:#过滤日志
        """根据条件过滤日志记录"""
        filtered=[]
        for log in logs:
            match=True
            for key,value in filters.items():
                if key=='start_time' and value:
                    log_time=datetime.fromisoformat(log.get('timestamp',''))
                    if log_time<value:match=False
                elif key=='end_time' and value:
                    log_time=datetime.fromisoformat(log.get('timestamp',''))
                    if log_time>value:match=False
                elif key=='level' and value:
                    if log.get('level')!=value:match=False
                elif key=='device_sn' and value:
                    if log.get('device_sn')!=value:match=False
                elif key=='module' and value:
                    if log.get('module')!=value:match=False
                elif key=='keyword' and value:
                    if value.lower() not in log.get('message','').lower():match=False
            if match:
                filtered.append(log)
        return filtered
        
    def get_error_summary(self)->Dict[str,Any]:#获取错误汇总
        """获取错误日志汇总"""
        errors=[]
        for file_path in self.json_files:
            logs=self.parse_json_log(file_path)
            errors.extend([log for log in logs if log.get('level') in ['ERROR','CRITICAL']])
            
        error_stats=Counter()
        error_devices=defaultdict(int)
        error_modules=defaultdict(int)
        recent_errors=[]
        
        for error in errors:
            error_stats[error.get('message','Unknown')]+=1
            if 'device_sn' in error:
                error_devices[error['device_sn']]+=1
            if 'module' in error:
                error_modules[error['module']]+=1
            recent_errors.append(error)
            
        #按时间排序，取最近的
        recent_errors.sort(key=lambda x:x.get('timestamp',''),reverse=True)
        
        return {
            'total_errors':len(errors),
            'error_stats':dict(error_stats.most_common(10)),
            'error_devices':dict(error_devices),
            'error_modules':dict(error_modules),
            'recent_errors':recent_errors[:20]
        }
        
    def get_api_performance(self)->Dict[str,Any]:#获取API性能统计
        """获取API接口性能统计"""
        api_file=self.logs_dir/'api_json.log'
        if not api_file.exists():
            return {'message':'API日志文件不存在'}
            
        logs=self.parse_json_log(api_file)
        api_stats=defaultdict(list)
        
        for log in logs:
            if 'api_endpoint' in log and 'processing_time' in log:
                endpoint=log['api_endpoint']
                proc_time=log['processing_time']
                api_stats[endpoint].append(proc_time)
                
        performance={}
        for endpoint,times in api_stats.items():
            if times:
                performance[endpoint]={
                    'count':len(times),
                    'avg_time':round(sum(times)/len(times),4),
                    'min_time':round(min(times),4),
                    'max_time':round(max(times),4)
                }
                
        return performance
        
    def get_health_data_stats(self)->Dict[str,Any]:#获取健康数据统计
        """获取健康数据处理统计"""
        health_file=self.logs_dir/'health_data_json.log'
        if not health_file.exists():
            return {'message':'健康数据日志文件不存在'}
            
        logs=self.parse_json_log(health_file)
        device_stats=defaultdict(int)
        batch_stats=[]
        
        for log in logs:
            if 'device_sn' in log:
                device_stats[log['device_sn']]+=1
            if 'batch_id' in log and 'data_count' in log:
                batch_stats.append({
                    'batch_id':log['batch_id'],
                    'data_count':log['data_count'],
                    'timestamp':log['timestamp']
                })
                
        return {
            'total_devices':len(device_stats),
            'total_records':sum(device_stats.values()),
            'top_devices':dict(Counter(device_stats).most_common(10)),
            'recent_batches':sorted(batch_stats,key=lambda x:x['timestamp'],reverse=True)[:10]
        }
        
    def search_logs(self,keyword:str,module:str=None,level:str=None,hours:int=24)->List[Dict]:#搜索日志
        """搜索日志记录"""
        end_time=datetime.now()
        start_time=end_time-timedelta(hours=hours)
        
        all_logs=[]
        for file_path in self.json_files:
            logs=self.parse_json_log(file_path)
            all_logs.extend(logs)
            
        filtered=self.filter_logs(all_logs,
            keyword=keyword,
            module=module,
            level=level,
            start_time=start_time,
            end_time=end_time
        )
        
        return sorted(filtered,key=lambda x:x.get('timestamp',''),reverse=True)
        
    def generate_report(self)->str:#生成分析报告
        """生成日志分析报告"""
        report=[]
        report.append("📊 大屏服务日志分析报告")
        report.append("="*50)
        report.append(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        #错误汇总
        error_summary=self.get_error_summary()
        report.append("🚨 错误汇总:")
        report.append(f"  总错误数: {error_summary['total_errors']}")
        if error_summary['error_modules']:
            report.append("  错误模块分布:")
            for module,count in error_summary['error_modules'].items():
                report.append(f"    {module}: {count}次")
        if error_summary['error_devices']:
            report.append("  错误设备TOP5:")
            top_devices=Counter(error_summary['error_devices']).most_common(5)
            for device,count in top_devices:
                report.append(f"    {device}: {count}次")
        report.append("")
        
        #API性能
        api_perf=self.get_api_performance()
        if 'message' not in api_perf:
            report.append("⚡ API性能统计:")
            for endpoint,stats in api_perf.items():
                report.append(f"  {endpoint}:")
                report.append(f"    调用次数: {stats['count']}")
                report.append(f"    平均响应: {stats['avg_time']}s")
                report.append(f"    最慢响应: {stats['max_time']}s")
        report.append("")
        
        #健康数据统计
        health_stats=self.get_health_data_stats()
        if 'message' not in health_stats:
            report.append("💊 健康数据统计:")
            report.append(f"  设备总数: {health_stats['total_devices']}")
            report.append(f"  记录总数: {health_stats['total_records']}")
            if health_stats['top_devices']:
                report.append("  活跃设备TOP5:")
                for device,count in list(health_stats['top_devices'].items())[:5]:
                    report.append(f"    {device}: {count}条")
        report.append("")
        
        #最近错误
        if error_summary['recent_errors']:
            report.append("🔍 最近错误详情:")
            for error in error_summary['recent_errors'][:5]:
                timestamp=error.get('timestamp','')
                message=error.get('message','')
                device=error.get('device_sn','N/A')
                report.append(f"  [{timestamp}] {device}: {message}")
        
        return "\n".join(report)

def main():#主函数
    """命令行主函数"""
    parser=argparse.ArgumentParser(description='大屏服务日志分析工具')
    parser.add_argument('--logs-dir',default='logs',help='日志目录路径')
    parser.add_argument('--report',action='store_true',help='生成分析报告')
    parser.add_argument('--errors',action='store_true',help='显示错误汇总')
    parser.add_argument('--api-perf',action='store_true',help='显示API性能')
    parser.add_argument('--health-stats',action='store_true',help='显示健康数据统计')
    parser.add_argument('--search',help='搜索关键词')
    parser.add_argument('--module',help='指定模块')
    parser.add_argument('--level',help='指定日志级别')
    parser.add_argument('--hours',type=int,default=24,help='搜索时间范围(小时)')
    
    args=parser.parse_args()
    
    analyzer=LogAnalyzer(args.logs_dir)
    
    if args.report:
        print(analyzer.generate_report())
    elif args.errors:
        errors=analyzer.get_error_summary()
        print("🚨 错误汇总:")
        print(f"总错误数: {errors['total_errors']}")
        print("\n错误统计:")
        for msg,count in errors['error_stats'].items():
            print(f"  {msg}: {count}次")
    elif args.api_perf:
        perf=analyzer.get_api_performance()
        print("⚡ API性能统计:")
        for endpoint,stats in perf.items():
            print(f"{endpoint}: {stats['count']}次调用, 平均{stats['avg_time']}s")
    elif args.health_stats:
        stats=analyzer.get_health_data_stats()
        print("💊 健康数据统计:")
        print(f"设备总数: {stats['total_devices']}")
        print(f"记录总数: {stats['total_records']}")
    elif args.search:
        results=analyzer.search_logs(args.search,args.module,args.level,args.hours)
        print(f"🔍 搜索结果 (关键词: {args.search}, 最近{args.hours}小时):")
        for result in results[:20]:
            timestamp=result.get('timestamp','')
            message=result.get('message','')
            device=result.get('device_sn','N/A')
            print(f"[{timestamp}] {device}: {message}")
    else:
        print("请指定操作选项，使用 --help 查看帮助")

if __name__=="__main__":
    main() 