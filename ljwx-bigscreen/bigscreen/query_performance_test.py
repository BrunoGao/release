#!/usr/bin/env python3
#查询性能测试脚本 - 灵境万象系统
import time,mysql.connector,random,statistics
from datetime import datetime,timedelta
from concurrent.futures import ThreadPoolExecutor
from batch_config import DB_CONFIG

class QueryPerformanceTest: #查询性能测试器
    def __init__(self):
        self.db_config=DB_CONFIG
        self.test_results=[]
        
    def get_connection(self): #获取数据库连接
        return mysql.connector.connect(**self.db_config)
    
    def test_single_user_query(self,device_sn,iterations=100): #单用户查询测试
        """测试单个用户最新数据查询性能"""
        times=[]
        sql="SELECT * FROM t_user_health_data WHERE device_sn=%s ORDER BY timestamp DESC LIMIT 1"
        
        for i in range(iterations):
            start=time.time()
            try:
                db=self.get_connection()
                cursor=db.cursor()
                cursor.execute(sql,(device_sn,))
                result=cursor.fetchone()
                cursor.close()
                db.close()
                times.append(time.time()-start)
            except Exception as e:
                print(f"❌单用户查询失败:{e}")
                
        return {
            'test':'单用户查询',
            'iterations':iterations,
            'avg_time':statistics.mean(times)*1000,
            'min_time':min(times)*1000,
            'max_time':max(times)*1000,
            'success_rate':len(times)/iterations*100
        }
    
    def test_batch_user_query(self,device_sns,iterations=50): #批量用户查询测试
        """测试批量用户数据查询性能"""
        times=[]
        sql=f"SELECT * FROM t_user_health_data WHERE device_sn IN ({','.join(['%s']*len(device_sns))}) ORDER BY timestamp DESC"
        
        for i in range(iterations):
            start=time.time()
            try:
                db=self.get_connection()
                cursor=db.cursor()
                cursor.execute(sql,device_sns)
                results=cursor.fetchall()
                cursor.close()
                db.close()
                times.append(time.time()-start)
            except Exception as e:
                print(f"❌批量查询失败:{e}")
                
        return {
            'test':'批量用户查询',
            'user_count':len(device_sns),
            'iterations':iterations,
            'avg_time':statistics.mean(times)*1000,
            'min_time':min(times)*1000,
            'max_time':max(times)*1000,
            'success_rate':len(times)/iterations*100
        }
    
    def test_time_range_query(self,device_sn,hours=24,iterations=20): #时间范围查询测试
        """测试时间范围查询性能"""
        times=[]
        end_time=datetime.now()
        start_time=end_time-timedelta(hours=hours)
        sql="SELECT * FROM t_user_health_data WHERE device_sn=%s AND timestamp BETWEEN %s AND %s ORDER BY timestamp DESC"
        
        for i in range(iterations):
            start=time.time()
            try:
                db=self.get_connection()
                cursor=db.cursor()
                cursor.execute(sql,(device_sn,start_time,end_time))
                results=cursor.fetchall()
                cursor.close()
                db.close()
                times.append(time.time()-start)
            except Exception as e:
                print(f"❌时间范围查询失败:{e}")
                
        return {
            'test':'时间范围查询',
            'time_range':f'{hours}小时',
            'iterations':iterations,
            'avg_time':statistics.mean(times)*1000,
            'min_time':min(times)*1000,
            'max_time':max(times)*1000,
            'success_rate':len(times)/iterations*100
        }
    
    def test_aggregation_query(self,device_sns,iterations=10): #聚合查询测试
        """测试聚合统计查询性能"""
        times=[]
        sql=f"""
        SELECT 
            AVG(heart_rate) as avg_hr,
            AVG(blood_oxygen) as avg_bo,
            AVG(temperature) as avg_temp,
            COUNT(*) as total_count,
            MAX(timestamp) as latest_time
        FROM t_user_health_data 
        WHERE device_sn IN ({','.join(['%s']*len(device_sns))})
        AND timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """
        
        for i in range(iterations):
            start=time.time()
            try:
                db=self.get_connection()
                cursor=db.cursor()
                cursor.execute(sql,device_sns)
                result=cursor.fetchone()
                cursor.close()
                db.close()
                times.append(time.time()-start)
            except Exception as e:
                print(f"❌聚合查询失败:{e}")
                
        return {
            'test':'聚合统计查询',
            'user_count':len(device_sns),
            'iterations':iterations,
            'avg_time':statistics.mean(times)*1000,
            'min_time':min(times)*1000,
            'max_time':max(times)*1000,
            'success_rate':len(times)/iterations*100
        }
    
    def test_concurrent_query(self,device_sns,threads=10,queries_per_thread=20): #并发查询测试
        """测试并发查询性能"""
        def worker():
            times=[]
            sql="SELECT * FROM t_user_health_data WHERE device_sn=%s ORDER BY timestamp DESC LIMIT 10"
            for _ in range(queries_per_thread):
                device_sn=random.choice(device_sns)
                start=time.time()
                try:
                    db=self.get_connection()
                    cursor=db.cursor()
                    cursor.execute(sql,(device_sn,))
                    results=cursor.fetchall()
                    cursor.close()
                    db.close()
                    times.append(time.time()-start)
                except Exception as e:
                    print(f"❌并发查询失败:{e}")
            return times
        
        start_time=time.time()
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures=[executor.submit(worker) for _ in range(threads)]
            all_times=[]
            for future in futures:
                all_times.extend(future.result())
        total_time=time.time()-start_time
        
        return {
            'test':'并发查询',
            'threads':threads,
            'total_queries':len(all_times),
            'total_time':total_time*1000,
            'avg_time':statistics.mean(all_times)*1000 if all_times else 0,
            'qps':len(all_times)/total_time if total_time>0 else 0,
            'success_rate':len(all_times)/(threads*queries_per_thread)*100
        }
    
    def test_complex_join_query(self,iterations=10): #复杂关联查询测试
        """测试复杂关联查询性能"""
        times=[]
        sql="""
        SELECT 
            h.device_sn,
            h.heart_rate,
            h.blood_oxygen,
            h.temperature,
            h.timestamp,
            COUNT(*) OVER (PARTITION BY h.device_sn) as user_record_count
        FROM t_user_health_data h
        WHERE h.timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        ORDER BY h.timestamp DESC
        LIMIT 1000
        """
        
        for i in range(iterations):
            start=time.time()
            try:
                db=self.get_connection()
                cursor=db.cursor()
                cursor.execute(sql)
                results=cursor.fetchall()
                cursor.close()
                db.close()
                times.append(time.time()-start)
            except Exception as e:
                print(f"❌复杂查询失败:{e}")
                
        return {
            'test':'复杂关联查询',
            'iterations':iterations,
            'avg_time':statistics.mean(times)*1000,
            'min_time':min(times)*1000,
            'max_time':max(times)*1000,
            'success_rate':len(times)/iterations*100
        }
    
    def get_test_device_sns(self,count=100): #获取测试设备号
        """获取测试用的设备号"""
        try:
            db=self.get_connection()
            cursor=db.cursor()
            cursor.execute("SELECT DISTINCT device_sn FROM t_user_health_data WHERE device_sn IS NOT NULL LIMIT %s",(count,))
            device_sns=[row[0] for row in cursor.fetchall()]
            cursor.close()
            db.close()
            return device_sns
        except Exception as e:
            print(f"❌获取设备号失败:{e}")
            return []
    
    def run_all_tests(self): #运行所有测试
        """运行完整的查询性能测试"""
        print("🚀 开始查询性能测试...")
        print("="*50)
        
        #获取测试数据
        device_sns=self.get_test_device_sns(100)
        if not device_sns:
            print("❌ 没有找到测试数据")
            return
        
        print(f"📊 找到{len(device_sns)}个设备进行测试")
        
        #1.单用户查询测试
        print("\n📋 测试1: 单用户查询性能")
        result1=self.test_single_user_query(device_sns[0])
        self.test_results.append(result1)
        print(f"  平均响应时间: {result1['avg_time']:.2f}ms")
        print(f"  成功率: {result1['success_rate']:.1f}%")
        
        #2.批量用户查询测试
        print("\n📋 测试2: 批量用户查询性能")
        batch_devices=device_sns[:20]
        result2=self.test_batch_user_query(batch_devices)
        self.test_results.append(result2)
        print(f"  平均响应时间: {result2['avg_time']:.2f}ms")
        print(f"  成功率: {result2['success_rate']:.1f}%")
        
        #3.时间范围查询测试
        print("\n📋 测试3: 时间范围查询性能")
        result3=self.test_time_range_query(device_sns[0],24)
        self.test_results.append(result3)
        print(f"  平均响应时间: {result3['avg_time']:.2f}ms")
        print(f"  成功率: {result3['success_rate']:.1f}%")
        
        #4.聚合查询测试
        print("\n📋 测试4: 聚合统计查询性能")
        agg_devices=device_sns[:50]
        result4=self.test_aggregation_query(agg_devices)
        self.test_results.append(result4)
        print(f"  平均响应时间: {result4['avg_time']:.2f}ms")
        print(f"  成功率: {result4['success_rate']:.1f}%")
        
        #5.并发查询测试
        print("\n📋 测试5: 并发查询性能")
        concurrent_devices=device_sns[:30]
        result5=self.test_concurrent_query(concurrent_devices,10,20)
        self.test_results.append(result5)
        print(f"  QPS: {result5['qps']:.1f}查询/秒")
        print(f"  平均响应时间: {result5['avg_time']:.2f}ms")
        print(f"  成功率: {result5['success_rate']:.1f}%")
        
        #6.复杂查询测试
        print("\n📋 测试6: 复杂关联查询性能")
        result6=self.test_complex_join_query()
        self.test_results.append(result6)
        print(f"  平均响应时间: {result6['avg_time']:.2f}ms")
        print(f"  成功率: {result6['success_rate']:.1f}%")
        
        print("\n🎉 查询性能测试完成!")
        return self.test_results

if __name__=="__main__":
    tester=QueryPerformanceTest()
    results=tester.run_all_tests()
    
    #生成测试报告
    print("\n📊 查询性能测试报告")
    print("="*50)
    for result in results:
        print(f"\n{result['test']}:")
        if 'avg_time' in result:
            print(f"  平均响应时间: {result['avg_time']:.2f}ms")
        if 'qps' in result:
            print(f"  QPS: {result['qps']:.1f}查询/秒")
        print(f"  成功率: {result['success_rate']:.1f}%") 