package com.ljwx.test;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Arrays;
import java.util.List;
import java.util.Scanner;

/**
 * 30天历史数据上传测试工具主程序
 * 仿照 start_30day_upload.py 实现的Java版本
 * 
 * 使用方法:
 * java -jar ljwx-boot-test.jar [选项]
 * 
 * 选项:
 * --url <url>        API基础URL (默认: http://localhost:8080)
 * --threads <num>    线程数 (默认: 20)
 * --devices <list>   设备列表 (逗号分隔，默认: DEVICE_001,DEVICE_002,DEVICE_003)
 * --days <num>       上传天数 (默认: 通过交互选择)
 * --mode <mode>      运行模式: interactive(交互), full(30天), test(1小时), custom(自定义)
 */
public class Start30DayUploadApp {
    
    private static final Logger logger = LoggerFactory.getLogger(Start30DayUploadApp.class);
    
    // 默认配置
    private static final String DEFAULT_URL = "http://localhost:8080";
    private static final int DEFAULT_THREADS = 20;
    private static final List<String> DEFAULT_DEVICES = Arrays.asList(
        "DEVICE_001", "DEVICE_002", "DEVICE_003", "DEVICE_004", "DEVICE_005"
    );
    
    public static void main(String[] args) {
        printBanner();
        
        // 解析命令行参数
        Config config = parseArgs(args);
        
        // 验证配置
        if (!validateConfig(config)) {
            System.exit(1);
        }
        
        // 创建上传器
        HistoricalDataUploader uploader = new HistoricalDataUploader(
            config.getUrl(), 
            config.getThreads(), 
            config.getDevices()
        );
        
        // 添加关闭钩子
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            logger.info("\n\n⏸️  程序正在安全退出...");
            uploader.stop();
        }));
        
        try {
            // 根据模式运行
            double days = getDaysFromMode(config);
            if (days <= 0) {
                logger.info("已取消上传");
                return;
            }
            
            logger.info("🚀 开始高速上传...");
            logger.info("=" + "=".repeat(60));
            
            uploader.uploadHistoricalData(days);
            logger.info("✅ 上传完成!");
            
        } catch (Exception e) {
            logger.error("❌ 上传错误: {}", e.getMessage(), e);
        } finally {
            uploader.stop();
        }
    }
    
    /**
     * 打印程序横幅
     */
    private static void printBanner() {
        System.out.println("🚀 30天历史数据高速上传 (Java版)");
        System.out.println("=" + "=".repeat(60));
        System.out.println("🎯 模拟客户手表每分钟上传一次数据");
        System.out.println("⚡ 高并发模式，最大化上传速度");
        System.out.println("📊 预计统计:");
        System.out.println("   • 时间范围: 过去30天");
        System.out.println("   • 上传频率: 每分钟1次");
        System.out.println("   • 时间点数: 43,200个 (30天 × 24小时 × 60分钟)");
        System.out.println("   • 总操作数: ~130,000次 (假设5个设备)");
        System.out.println("   • 预计速度: 600+ 次/秒");
        System.out.println("   • 预计耗时: 3-5分钟");
        System.out.println();
    }
    
    /**
     * 解析命令行参数
     */
    private static Config parseArgs(String[] args) {
        Config config = new Config();
        
        for (int i = 0; i < args.length; i++) {
            String arg = args[i];
            
            switch (arg) {
                case "--url":
                    if (i + 1 < args.length) {
                        config.setUrl(args[++i]);
                    }
                    break;
                    
                case "--threads":
                    if (i + 1 < args.length) {
                        try {
                            config.setThreads(Integer.parseInt(args[++i]));
                        } catch (NumberFormatException e) {
                            logger.warn("无效的线程数参数: {}", args[i]);
                        }
                    }
                    break;
                    
                case "--devices":
                    if (i + 1 < args.length) {
                        String[] deviceArray = args[++i].split(",");
                        config.setDevices(Arrays.asList(deviceArray));
                    }
                    break;
                    
                case "--days":
                    if (i + 1 < args.length) {
                        try {
                            config.setDays(Double.parseDouble(args[++i]));
                        } catch (NumberFormatException e) {
                            logger.warn("无效的天数参数: {}", args[i]);
                        }
                    }
                    break;
                    
                case "--mode":
                    if (i + 1 < args.length) {
                        config.setMode(args[++i]);
                    }
                    break;
                    
                case "--help":
                case "-h":
                    printHelp();
                    System.exit(0);
                    break;
                    
                default:
                    if (arg.startsWith("--")) {
                        logger.warn("未知参数: {}", arg);
                    }
                    break;
            }
        }
        
        return config;
    }
    
    /**
     * 打印帮助信息
     */
    private static void printHelp() {
        System.out.println("ljwx-boot 30天历史数据上传测试工具");
        System.out.println();
        System.out.println("使用方法:");
        System.out.println("  java -jar ljwx-boot-test.jar [选项]");
        System.out.println();
        System.out.println("选项:");
        System.out.println("  --url <url>        API基础URL (默认: http://localhost:8080)");
        System.out.println("  --threads <num>    线程数 (默认: 20)");
        System.out.println("  --devices <list>   设备列表，逗号分隔 (默认: DEVICE_001,DEVICE_002,...)");
        System.out.println("  --days <num>       上传天数 (默认: 通过交互选择)");
        System.out.println("  --mode <mode>      运行模式:");
        System.out.println("                       interactive - 交互式选择 (默认)");
        System.out.println("                       full - 完整30天数据");
        System.out.println("                       test - 测试模式(1小时数据)");
        System.out.println("                       custom - 自定义天数");
        System.out.println("  --help, -h         显示此帮助信息");
        System.out.println();
        System.out.println("示例:");
        System.out.println("  java -jar ljwx-boot-test.jar --mode full");
        System.out.println("  java -jar ljwx-boot-test.jar --url http://192.168.1.83:8080 --threads 30");
        System.out.println("  java -jar ljwx-boot-test.jar --mode test --devices DEVICE_001,DEVICE_002");
    }
    
    /**
     * 验证配置
     */
    private static boolean validateConfig(Config config) {
        System.out.println("🔧 当前配置:");
        System.out.println("   • API地址: " + config.getUrl());
        System.out.println("   • 线程池: " + config.getThreads() + "个并发线程");
        System.out.println("   • 设备数量: " + config.getDevices().size());
        System.out.println("   • 设备列表: " + String.join(", ", config.getDevices()));
        System.out.println();
        
        // 测试API连接
        APIClient testClient = new APIClient(config.getUrl());
        if (!testClient.testConnection()) {
            logger.error("❌ API服务器连接失败: {}", config.getUrl());
            logger.error("   请检查:");
            logger.error("   • ljwx-boot服务是否启动");
            logger.error("   • URL地址是否正确");
            logger.error("   • 网络连接是否正常");
            return false;
        }
        
        logger.info("✅ API连接测试成功");
        
        // 显示服务统计
        var stats = testClient.getServiceStats();
        if (stats != null) {
            logger.info("📊 服务状态: {}", stats.get("service_status"));
            logger.info("📊 已处理: {} 条, 批次: {}, 错误: {}", 
                       stats.get("processed"), stats.get("batches"), stats.get("errors"));
        }
        
        System.out.println();
        return true;
    }
    
    /**
     * 根据模式获取天数
     */
    private static double getDaysFromMode(Config config) {
        String mode = config.getMode();
        
        switch (mode.toLowerCase()) {
            case "full":
                logger.info("🚀 完整模式 - 上传30天数据");
                return confirmAndReturn(30.0);
                
            case "test":
                logger.info("🧪 测试模式 - 上传1小时数据");
                return confirmAndReturn(1.0 / 24.0); // 1小时 = 1/24天
                
            case "custom":
                return getCustomDays();
                
            case "interactive":
            default:
                return getInteractiveDays();
        }
    }
    
    /**
     * 交互式选择天数
     */
    private static double getInteractiveDays() {
        System.out.println("⚠️  注意事项:");
        System.out.println("   • 这将生成大量测试数据");
        System.out.println("   • 请确保API服务器能承受高并发");
        System.out.println("   • 可以随时按 Ctrl+C 安全停止");
        System.out.println("   • 建议在测试环境中运行");
        System.out.println();
        
        Scanner scanner = new Scanner(System.in);
        System.out.print("选择运行方式:\n1. 完整30天上传\n2. 测试模式(1小时数据)\n3. 自定义天数\n请选择 (1-3): ");
        
        String choice = scanner.nextLine().trim();
        
        switch (choice) {
            case "1":
                logger.info("🚀 完整模式 - 上传30天数据");
                return confirmAndReturn(30.0);
                
            case "2":
                logger.info("🧪 测试模式 - 上传1小时数据");
                return confirmAndReturn(1.0 / 24.0);
                
            case "3":
                return getCustomDays();
                
            default:
                logger.error("❌ 无效选择");
                return -1;
        }
    }
    
    /**
     * 获取自定义天数
     */
    private static double getCustomDays() {
        Scanner scanner = new Scanner(System.in);
        System.out.print("请输入天数: ");
        
        try {
            double days = Double.parseDouble(scanner.nextLine().trim());
            if (days <= 0) {
                logger.error("❌ 天数必须大于0");
                return -1;
            }
            logger.info("📅 自定义模式 - 上传{}天数据", days);
            return confirmAndReturn(days);
        } catch (NumberFormatException e) {
            logger.error("❌ 无效输入");
            return -1;
        }
    }
    
    /**
     * 确认并返回天数
     */
    private static double confirmAndReturn(double days) {
        Scanner scanner = new Scanner(System.in);
        System.out.println();
        System.out.print("确认开始上传? (y/N): ");
        
        String confirm = scanner.nextLine().trim().toLowerCase();
        return "y".equals(confirm) ? days : -1;
    }
    
    /**
     * 配置类
     */
    private static class Config {
        private String url = DEFAULT_URL;
        private int threads = DEFAULT_THREADS;
        private List<String> devices = DEFAULT_DEVICES;
        private double days = -1; // -1表示未设置
        private String mode = "interactive";
        
        // Getters and Setters
        public String getUrl() {
            return url;
        }
        
        public void setUrl(String url) {
            this.url = url;
        }
        
        public int getThreads() {
            return threads;
        }
        
        public void setThreads(int threads) {
            this.threads = Math.max(1, Math.min(100, threads)); // 限制范围1-100
        }
        
        public List<String> getDevices() {
            return devices;
        }
        
        public void setDevices(List<String> devices) {
            this.devices = devices;
        }
        
        public double getDays() {
            return days;
        }
        
        public void setDays(double days) {
            this.days = days;
        }
        
        public String getMode() {
            return mode;
        }
        
        public void setMode(String mode) {
            this.mode = mode;
        }
    }
}