#!/usr/bin/env python3
import requests,json,time,threading,random,sys,os
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor,as_completed
import warnings
warnings.filterwarnings('ignore')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import STRESS_TEST_CONFIG,HEALTH_DATA_RANGES

class PerformanceStressTest:#高性能压力测试
    def __init__(self):
        self.url='http://localhost:5001/upload_health_data_optimized'#优化接口
        self.base_id=STRESS_TEST_CONFIG['BASE_ID']#基础设备ID
        self.device_count=1000#目标设备数
        self.max_workers=100#最大线程数(减少避免资源耗尽)
        self.timeout=5#请求超时(增加避免timeout)
        self.session_pool=[]#会话池
        self.stats={'total':0,'success':0,'error':0,'times':[],'errors':{}}#统计数据
        self.test_results=[]#测试结果历史
        self._init_session_pool()#初始化会话池
        
    def _init_session_pool(self):#初始化会话池
        pool_size=min(self.max_workers,100)#限制会话池大小
        print(f'🔧初始化会话池: {pool_size}个会话')
        
        for i in range(pool_size):
            session=requests.Session()
            
            #配置连接池(优化网络稳定性)
            adapter=HTTPAdapter(
                pool_connections=10,#进一步减少连接池大小
                pool_maxsize=10,#进一步减少最大连接数
                max_retries=Retry(total=2,backoff_factor=0.3,status_forcelist=[500,502,503,504]),#增加重试次数
                pool_block=True#阻塞模式更稳定
            )
            session.mount('http://',adapter)
            session.mount('https://',adapter)
            
            #优化headers减少传输
            session.headers.update({
                'Connection':'keep-alive',
                'Content-Type':'application/json',
                'User-Agent':'PerfTest/1.0',
                'Accept-Encoding':'gzip'#启用压缩
            })
            
            self.session_pool.append(session)
            
    def get_session(self,idx):#获取会话
        return self.session_pool[idx%len(self.session_pool)]
        
    def gen_device_id(self,idx):#生成设备ID
        return f'A5GTQ24B{int(self.base_id[-8:])+idx:08d}'
        
    def gen_health_data(self,device_id):#生成健康数据(最小化)
        r=HEALTH_DATA_RANGES
        return {'data':{
            'id':device_id,'upload_method':'wifi',
            'heart_rate':random.randint(*r['heart_rate']),
            'blood_oxygen':random.randint(*r['blood_oxygen']),
            'body_temperature':f'{random.uniform(*r["body_temperature"]):.1f}',
            'blood_pressure_systolic':random.randint(*r['blood_pressure_systolic']),
            'blood_pressure_diastolic':random.randint(*r['blood_pressure_diastolic']),
            'step':random.randint(*r['step']),
            'distance':f'{random.uniform(*r["distance"]):.1f}',
            'calorie':f'{random.uniform(*r["calorie"]):.1f}',
            'latitude':f'{random.uniform(*r["latitude"]):.6f}',#进一步减少精度
            'longitude':f'{random.uniform(*r["longitude"]):.6f}',
            'altitude':'0','stress':random.randint(*r['stress'])}}
            
    def upload_single(self,args):#单个上传(增强错误处理)
        idx,device_id=args
        session=self.get_session(idx)
        start=time.time()
        
        try:
            data=self.gen_health_data(device_id)
            resp=session.post(self.url,json=data,timeout=self.timeout,stream=False)
            elapsed=time.time()-start
            
            if resp.status_code==200:
                return 1,elapsed,'SUCCESS'
            else:
                return 0,elapsed,f'HTTP_{resp.status_code}'
                
        except requests.exceptions.Timeout:
            return 0,time.time()-start,'TIMEOUT'
        except requests.exceptions.ConnectionError as e:
            if 'Broken pipe' in str(e) or 'Connection aborted' in str(e):
                return 0,time.time()-start,'BROKEN_PIPE'
            return 0,time.time()-start,'CONN_ERROR'
        except Exception as e:
            error_type=type(e).__name__
            return 0,time.time()-start,f'{error_type}'
            
    def batch_upload_optimized(self):#优化批量上传
        device_ids=[(i,self.gen_device_id(i)) for i in range(self.device_count)]
        start_time=time.time()
        
        results=[]
        error_counts={}#错误统计
        
        #使用线程池并发上传
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_device={executor.submit(self.upload_single,device_id):device_id for device_id in device_ids}
            
            for future in as_completed(future_to_device):
                try:
                    success,elapsed,status=future.result()
                    results.append((success,elapsed,status))
                    self.stats['times'].append(elapsed)
                    
                    #统计错误类型
                    if not success:
                        error_counts[status]=error_counts.get(status,0)+1
                        
                except Exception as e:
                    results.append((0,0,f'FUTURE_ERROR:{str(e)[:15]}'))
                    error_counts['FUTURE_ERROR']=error_counts.get('FUTURE_ERROR',0)+1
                    
        total_elapsed=time.time()-start_time
        success_count=sum(r[0] for r in results)
        error_count=self.device_count-success_count
        
        self.stats['total']+=self.device_count
        self.stats['success']+=success_count
        self.stats['error']+=error_count
        self.stats['errors'].update(error_counts)#更新错误统计
        
        return total_elapsed,success_count,error_count,error_counts
        
    def extreme_test(self):#极限性能测试
        print('🔥启动极限性能测试 - 寻找系统极限')
        print('⚠️注意: 测试过程中会大量消耗系统资源，请确保服务器有足够性能')
        
        #极限测试配置(优化参数减少资源消耗)
        test_configs=[
            {'devices':1000,'workers':100,'name':'基准测试'},#减少线程数
            {'devices':1500,'workers':120,'name':'1.5倍负载'},
            {'devices':2000,'workers':150,'name':'双倍负载'},
            {'devices':2500,'workers':180,'name':'2.5倍负载'},#提前停止避免服务崩溃
        ]
        
        extreme_results=[]
        
        for config in test_configs:
            print(f'\n🎯{config["name"]}: {config["devices"]}设备 {config["workers"]}线程')
            
            #更新配置
            self.device_count=config['devices']
            self.max_workers=min(config['workers'],500)#限制最大线程
            self._update_session_pool()
            
            #重置统计
            self.stats={'total':0,'success':0,'error':0,'times':[],'errors':{}}
            
            #执行测试
            elapsed,success,error,error_counts=self.batch_upload_optimized()
            qps=success/elapsed if elapsed>0 else 0
            success_rate=success/self.device_count*100
            
            #计算性能指标
            avg_response=sum(self.stats['times'])/len(self.stats['times'])*1000 if self.stats['times'] else 0
            p95_response=sorted(self.stats['times'])[int(len(self.stats['times'])*0.95)]*1000 if self.stats['times'] else 0
            p99_response=sorted(self.stats['times'])[int(len(self.stats['times'])*0.99)]*1000 if self.stats['times'] else 0
            
            result={
                'name':config['name'],
                'devices':config['devices'],
                'workers':config['workers'],
                'elapsed':elapsed,
                'success':success,
                'error':error,
                'qps':qps,
                'success_rate':success_rate,
                'avg_response':avg_response,
                'p95_response':p95_response,
                'p99_response':p99_response,
                'error_counts':error_counts,#错误详情
                'timestamp':time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            extreme_results.append(result)
            
            #保存实时进度
            self.save_progress({
                'current_test':config['name'],
                'progress':len(extreme_results)/len(test_configs)*100,
                'qps':qps,
                'avg_response':avg_response,
                'success_rate':success_rate,
                'devices':config['devices'],
                'timestamp':time.time()
            })
            
            #显示结果和错误统计
            status='✅通过' if success_rate>=95 and qps>=100 else '❌失败'
            print(f'{status} 耗时:{elapsed:.2f}s QPS:{qps:.1f} 成功率:{success_rate:.1f}% 响应:{avg_response:.0f}ms')
            
            #显示错误详情
            if error_counts:
                error_details=' '.join([f'{k}:{v}' for k,v in error_counts.items()])
                print(f'🔍错误统计: {error_details}')
            
            #失败则停止测试
            if success_rate<85:
                print(f'❌成功率过低({success_rate:.1f}%)，停止极限测试')
                break
                
            #系统恢复时间
            print('⏳等待系统恢复...')
            time.sleep(5)#增加休息时间让系统恢复
            
            #检查服务器健康状态
            if self._check_server_health():
                print('✅服务器状态正常，继续测试')
            else:
                print('⚠️服务器响应异常，停止测试避免崩溃')
                break
            
        self.test_results=extreme_results
        
        #保存极限测试性能参数
        if extreme_results:
            extreme_data={
                'test_time':time.strftime('%Y-%m-%d %H:%M:%S'),
                'test_type':'极限压力测试',
                'total_rounds':len(extreme_results),
                'max_qps':max(r['qps'] for r in extreme_results),
                'max_devices':max(r['devices'] for r in extreme_results),
                'overall_success_rate':sum(r['success_rate'] for r in extreme_results)/len(extreme_results),
                'avg_response_time':sum(r['avg_response'] for r in extreme_results)/len(extreme_results),
                'p95_response_time':sum(r['p95_response'] for r in extreme_results)/len(extreme_results),
                'total_requests':sum(r['devices'] for r in extreme_results),
                'total_success':sum(r['success'] for r in extreme_results),
                'total_errors':sum(r['error'] for r in extreme_results),
                'detailed_results':extreme_results
            }
            
            with open('extreme_performance_data.json','w',encoding='utf-8') as f:
                json.dump(extreme_data,f,ensure_ascii=False,indent=2)
            print(f'📈极限测试数据已保存到 extreme_performance_data.json')
        
        self._save_web_report()
        print(f'\n📊极限测试完成，报告已保存到 test_report.html')
        
        #测试完成后深度清理资源
        self._cleanup_resources()
        
        #提供服务器恢复建议
        print('\n🎯极限测试结束')
        print('📋服务器恢复建议:')
        print('1. 检查服务器内存使用率')
        print('2. 重启Flask服务释放数据库连接')
        print('3. 检查数据库连接池状态')
        print('4. 清理异步队列积压')
        print('5. 等待5-10分钟让系统完全恢复')
        
        #发送清理请求到服务器
        self._request_server_cleanup()
        
    def _check_server_health(self):#检查服务器健康状态
        try:
            #简单的健康检查请求
            test_session=requests.Session()
            test_session.timeout=2
            resp=test_session.get('http://localhost:5001/',timeout=2)
            test_session.close()
            return resp.status_code==200
        except:
            return False
            
    def _cleanup_resources(self):#资源深度清理
        print('🧹开始深度资源清理...')
        
        #清理会话池
        self.close_sessions()
        
        #清理统计数据
        self.stats={'total':0,'success':0,'error':0,'times':[],'errors':{}}
        
        #等待系统稳定
        time.sleep(2)
        print('✅资源清理完成')
        
    def _request_server_cleanup(self):#请求服务器清理资源
        try:
            print('🧹请求服务器清理资源...')
            cleanup_session=requests.Session()
            cleanup_session.timeout=10
            
            #尝试触发服务器垃圾回收(如果有对应接口)
            resp=cleanup_session.get('http://localhost:5001/health',timeout=5)
            cleanup_session.close()
            
            if resp.status_code==200:
                print('✅服务器响应正常，资源清理请求已发送')
            else:
                print(f'⚠️服务器状态异常: HTTP {resp.status_code}')
                
        except Exception as e:
            print(f'❌服务器清理请求失败: {str(e)[:50]}')
            print('💡建议手动重启服务: sudo systemctl restart flask-app')
        
    def _update_session_pool(self):#更新会话池
        #关闭旧会话
        print('🔄更新会话池...')
        for i,session in enumerate(self.session_pool):
            try:
                session.close()
            except Exception as e:
                print(f'关闭会话{i}失败:{e}')
        self.session_pool.clear()
        
        #等待连接释放
        time.sleep(1)
        
        #创建新会话池
        self._init_session_pool()
        print(f'✅会话池已更新，新池大小:{len(self.session_pool)}')
        
    def _save_web_report(self,results_data=None):#保存Web报告(统一模板)
        if not self.test_results:#检查数据
            print('⚠️警告: 没有测试结果数据，无法生成图表')
            return
            
        #计算错误统计
        all_errors={}
        for result in self.test_results:
            for error_type,count in result.get('error_counts',{}).items():
                all_errors[error_type]=all_errors.get(error_type,0)+count
                
        error_summary=', '.join([f'{k}: {v}次' for k,v in all_errors.items()]) if all_errors else '无错误'
        
        #生成简化的HTML报告，与UI模板保持一致
        html_content=f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>性能测试报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body{{font-family:'Microsoft YaHei',sans-serif;margin:0;padding:20px;background:linear-gradient(135deg,#0c1445,#1e3c72,#2a5298);color:#fff;}}
        .container{{max-width:1400px;margin:0 auto;}}
        .header{{text-align:center;margin-bottom:30px;padding:20px;background:rgba(255,255,255,0.05);border-radius:15px;}}
        .header h1{{color:#64ffda;text-shadow:0 0 20px rgba(100,255,218,0.5);margin-bottom:10px;}}
        .summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-bottom:25px;}}
        .card{{background:rgba(255,255,255,0.08);border:1px solid rgba(100,255,218,0.2);border-radius:12px;padding:15px;text-align:center;}}
        .card h3{{color:#64ffda;margin:0 0 8px 0;font-size:1em;}}
        .metric{{font-size:1.8em;font-weight:bold;color:#fff;}}
        .charts{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:25px;}}
        .chart-container{{background:rgba(255,255,255,0.08);border-radius:12px;padding:15px;height:350px;}}
        .chart-title{{color:#64ffda;text-align:center;margin-bottom:10px;}}
        .table{{width:100%;border-collapse:collapse;background:rgba(255,255,255,0.08);border-radius:8px;overflow:hidden;}}
        .table th,.table td{{padding:6px;text-align:center;border-bottom:1px solid rgba(255,255,255,0.1);font-size:0.85em;}}
        .table th{{background:rgba(100,255,218,0.2);color:#64ffda;}}
        .status-pass{{color:#4caf50;}}
        .status-fail{{color:#f44336;}}
        .error-info{{background:rgba(255,152,0,0.1);border:1px solid rgba(255,152,0,0.3);border-radius:8px;padding:12px;margin:15px 0;}}
        .error-info h4{{color:#ff9800;margin:0 0 8px 0;font-size:1.1em;}}
        @media(max-width:768px){{.charts{{grid-template-columns:1fr;}}}}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 {"极限" if len(self.test_results)>3 else "常规"}性能测试报告</h1>
            <p>测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="card">
                <h3>最高QPS</h3>
                <div class="metric">{max(r['qps'] for r in self.test_results):.0f}</div>
            </div>
            <div class="card">
                <h3>最大并发</h3>
                <div class="metric">{max(r['devices'] for r in self.test_results):,}</div>
            </div>
            <div class="card">
                <h3>平均成功率</h3>
                <div class="metric">{sum(r['success_rate'] for r in self.test_results)/len(self.test_results):.1f}%</div>
            </div>
            <div class="card">
                <h3>测试轮次</h3>
                <div class="metric">{len(self.test_results)}</div>
            </div>
        </div>
        
        <div class="error-info">
            <h4>🔍 错误类型统计</h4>
            <p>{error_summary}</p>
            <small>TIMEOUT:请求超时 | BROKEN_PIPE:连接断开 | CONN_ERROR:连接错误 | HTTP_xxx:HTTP状态码错误</small>
        </div>
        
        <div class="charts">
            <div class="chart-container">
                <div class="chart-title">QPS性能曲线</div>
                <canvas id="qpsChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">响应时间分析</div>
                <canvas id="responseChart"></canvas>
            </div>
        </div>
        
        <div class="card">
            <h3>详细测试结果</h3>
            <table class="table">
                <thead>
                    <tr>
                        <th>测试名称</th>
                        <th>设备数</th>
                        <th>线程数</th>
                        <th>耗时(s)</th>
                        <th>QPS</th>
                        <th>成功率</th>
                        <th>平均响应(ms)</th>
                        <th>P95响应(ms)</th>
                        <th>主要错误</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''<tr>
                        <td>{r['name']}</td>
                        <td>{r['devices']:,}</td>
                        <td>{r['workers']}</td>
                        <td>{r['elapsed']:.2f}</td>
                        <td>{r['qps']:.1f}</td>
                        <td>{r['success_rate']:.1f}%</td>
                        <td>{r['avg_response']:.0f}</td>
                        <td>{r['p95_response']:.0f}</td>
                        <td style="font-size:0.8em;">{list(r.get('error_counts',{}).keys())[:1] if r.get('error_counts') else '无'}</td>
                        <td class="{('status-pass' if r['success_rate']>=95 else 'status-fail')}">
                            {'✅通过' if r['success_rate']>=95 else '❌失败'}
                        </td>
                    </tr>''' for r in self.test_results)}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        //数据准备和验证
        const testResults={json.dumps(self.test_results)};
        console.log('测试结果数据:',testResults);
        
        if(testResults && testResults.length>0){{
            const qpsData=testResults.map(r=>Math.round(r.qps*10)/10);
            const responseData=testResults.map(r=>[Math.round(r.avg_response),Math.round(r.p95_response),Math.round(r.p99_response||0)]);
            const labels=testResults.map(r=>r.name);
            
            //QPS图表
            new Chart(document.getElementById('qpsChart'), {{
                type: 'line',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'QPS性能',
                        data: qpsData,
                        borderColor: '#64ffda',
                        backgroundColor: 'rgba(100,255,218,0.1)',
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#64ffda',
                        pointBorderColor: '#fff',
                        pointRadius: 5
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{labels: {{color: '#fff',fontSize: 12}}}},
                        title: {{display: true,text: 'QPS性能趋势',color: '#64ffda',fontSize: 14}}
                    }},
                    scales: {{
                        x: {{ticks: {{color: '#fff',fontSize: 10}},grid: {{color: 'rgba(255,255,255,0.2)'}}}},
                        y: {{ticks: {{color: '#fff',fontSize: 10}},grid: {{color: 'rgba(255,255,255,0.2)'}}}}
                    }}
                }}
            }});
            
            //响应时间图表
            new Chart(document.getElementById('responseChart'), {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [
                        {{
                            label: '平均响应时间',
                            data: responseData.map(r=>r[0]),
                            backgroundColor: 'rgba(76,175,80,0.8)',
                            borderColor: 'rgba(76,175,80,1)',
                            borderWidth: 1
                        }},
                        {{
                            label: 'P95响应时间',
                            data: responseData.map(r=>r[1]),
                            backgroundColor: 'rgba(255,193,7,0.8)',
                            borderColor: 'rgba(255,193,7,1)',
                            borderWidth: 1
                        }},
                        {{
                            label: 'P99响应时间',
                            data: responseData.map(r=>r[2]),
                            backgroundColor: 'rgba(244,67,54,0.8)',
                            borderColor: 'rgba(244,67,54,1)',
                            borderWidth: 1
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{labels: {{color: '#fff',fontSize: 10}}}},
                        title: {{display: true,text: '响应时间分布',color: '#64ffda',fontSize: 14}}
                    }},
                    scales: {{
                        x: {{ticks: {{color: '#fff',fontSize: 9}},grid: {{color: 'rgba(255,255,255,0.2)'}}}},
                        y: {{ticks: {{color: '#fff',fontSize: 9}},grid: {{color: 'rgba(255,255,255,0.2)'}}}}
                    }}
                }}
            }});
        }}else{{
            //无数据时显示提示
            document.getElementById('qpsChart').parentElement.innerHTML='<div style="text-align:center;color:#ff9800;padding:40px;">📊 暂无QPS数据</div>';
            document.getElementById('responseChart').parentElement.innerHTML='<div style="text-align:center;color:#ff9800;padding:40px;">📈 暂无响应时间数据</div>';
        }}
    </script>
</body>
</html>'''
        
        with open('test_report.html','w',encoding='utf-8') as f:
            f.write(html_content)
            
    def save_progress(self,data):#保存测试进度
        try:
            import json
            with open('test_progress.json','w',encoding='utf-8') as f:
                json.dump(data,f,ensure_ascii=False,indent=2)
        except Exception as e:
            print(f'保存进度失败: {e}')
    
    def performance_test(self,target_time=3.0):#性能测试
        print(f'🚀启动高性能测试: 目标{target_time}秒内完成{self.device_count}个请求')
        print(f'⚡参数: 最大线程{self.max_workers} 超时{self.timeout}秒 会话池{len(self.session_pool)}')
        
        #预热测试
        print('🔥预热测试...')
        self.device_count=100
        elapsed,success,error,error_counts=self.batch_upload_optimized()
        warmup_qps=success/elapsed
        print(f'预热结果: {success}/{self.device_count} 成功 耗时{elapsed:.2f}s QPS:{warmup_qps:.1f}')
        
        #正式测试
        print('\n🎯正式性能测试...')
        self.device_count=1000
        self.stats={'total':0,'success':0,'error':0,'times':[],'errors':{}}#重置统计
        
        test_rounds=3#测试轮次
        best_time=float('inf')
        best_qps=0
        performance_results=[]#保存性能测试结果
        
        for round_num in range(1,test_rounds+1):
            print(f'\n第{round_num}轮测试...')
            elapsed,success,error,error_counts=self.batch_upload_optimized()
            qps=success/elapsed if elapsed>0 else 0
            
            if elapsed<best_time:
                best_time=elapsed
                best_qps=qps
                
            #计算性能指标
            avg_response=sum(self.stats['times'])/len(self.stats['times'])*1000 if self.stats['times'] else 0
            p95_response=sorted(self.stats['times'])[int(len(self.stats['times'])*0.95)]*1000 if self.stats['times'] else 0
            p99_response=sorted(self.stats['times'])[int(len(self.stats['times'])*0.99)]*1000 if self.stats['times'] else 0
            success_rate=success/self.device_count*100
            
            #保存结果数据
            performance_results.append({
                'name':f'第{round_num}轮测试',
                'devices':self.device_count,
                'workers':self.max_workers,
                'elapsed':elapsed,
                'success':success,
                'error':error,
                'qps':qps,
                'success_rate':success_rate,
                'avg_response':avg_response,
                'p95_response':p95_response,
                'p99_response':p99_response,
                'error_counts':error_counts,
                'timestamp':time.strftime('%Y-%m-%d %H:%M:%S')
            })
            
            #保存实时进度
            self.save_progress({
                'current_test':f'常规测试-第{round_num}轮',
                'progress':round_num/test_rounds*100,
                'qps':qps,
                'avg_response':avg_response,
                'success_rate':success_rate,
                'devices':self.device_count,
                'timestamp':time.time()
            })
                
            status='✅达标' if elapsed<=target_time else '❌超时'
            print(f'{status} 耗时:{elapsed:.2f}s 成功:{success}/{self.device_count} QPS:{qps:.1f}')
            
            #显示错误统计
            if error_counts:
                error_details=' '.join([f'{k}:{v}' for k,v in error_counts.items()])
                print(f'🔍错误: {error_details}')
            
            time.sleep(2)#间隔2秒
            
        #保存测试结果并生成报告
        self.test_results=performance_results
        
        #保存性能参数到JSON文件
        performance_data={
            'test_time':time.strftime('%Y-%m-%d %H:%M:%S'),
            'test_type':'常规性能测试',
            'total_rounds':len(performance_results),
            'max_qps':best_qps,
            'overall_success_rate':sum(r['success_rate'] for r in performance_results)/len(performance_results),
            'avg_response_time':sum(r['avg_response'] for r in performance_results)/len(performance_results),
            'p95_response_time':sum(r['p95_response'] for r in performance_results)/len(performance_results),
            'p99_response_time':sum(r['p99_response'] for r in performance_results)/len(performance_results),
            'total_requests':sum(r['devices'] for r in performance_results),
            'total_success':sum(r['success'] for r in performance_results),
            'total_errors':sum(r['error'] for r in performance_results),
            'detailed_results':performance_results
        }
        
        with open('performance_data.json','w',encoding='utf-8') as f:
            json.dump(performance_data,f,ensure_ascii=False,indent=2)
        
        self._save_web_report()
        print(f'\n📊性能测试完成，报告已保存到 test_report.html')
        print(f'📈性能数据已保存到 performance_data.json')
            
        #性能分析
        self._print_performance_analysis(target_time,best_time,best_qps)
        
        #测试完成后清理资源
        self._cleanup_resources()
        print('🎯性能测试结束，资源已清理')
        
    def _print_performance_analysis(self,target_time,best_time,best_qps):#性能分析
        avg_response=sum(self.stats['times'])/len(self.stats['times'])*1000 if self.stats['times'] else 0
        min_response=min(self.stats['times'])*1000 if self.stats['times'] else 0
        max_response=max(self.stats['times'])*1000 if self.stats['times'] else 0
        p95_response=sorted(self.stats['times'])[int(len(self.stats['times'])*0.95)]*1000 if self.stats['times'] else 0
        
        print(f'\n📊性能测试分析:')
        print(f'目标时间: {target_time}s | 最佳时间: {best_time:.2f}s | {"✅达标" if best_time<=target_time else "❌未达标"}')
        print(f'最佳QPS: {best_qps:.1f} | 总成功率: {self.stats["success"]/self.stats["total"]*100:.1f}%')
        print(f'响应时间: 平均{avg_response:.0f}ms | P95:{p95_response:.0f}ms | 最快{min_response:.0f}ms | 最慢{max_response:.0f}ms')
        
        #错误分析
        if self.stats['errors']:
            print(f'🔍错误分析: {self.stats["errors"]}')
        
        #性能优化建议
        print(f'\n💡性能优化建议:')
        if best_time>target_time:
            if 'TIMEOUT' in self.stats.get('errors',{}):
                print('- 服务器响应慢，检查数据库和Redis性能')
            if 'BROKEN_PIPE' in self.stats.get('errors',{}):
                print('- 网络连接不稳定，考虑增加重试机制')
            if best_qps<300:
                print('- 增加服务器资源或优化算法')
        else:
            print('- 性能已达标，可考虑增加设备数测试极限')
            
    def close_sessions(self):#关闭会话池
        print('🔄正在清理资源...')
        for i,session in enumerate(self.session_pool):
            try:
                session.close()
                if i%50==0:print(f'已关闭{i+1}/{len(self.session_pool)}个会话')
            except Exception as e:
                print(f'关闭会话{i}失败:{e}')
        self.session_pool.clear()#清空列表
        print('✅会话池已清理完成')
        
        #强制垃圾回收
        import gc
        gc.collect()
        print('🗑️垃圾回收完成')

if __name__=='__main__':
    test=PerformanceStressTest()
    try:
        if len(sys.argv)>1 and sys.argv[1]=='extreme':
            test.extreme_test()#极限测试
        else:
            test.performance_test(target_time=3.0)#常规测试
    finally:
        test.close_sessions()#确保关闭连接 