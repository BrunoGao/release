package com.ljwx.common.util;

import com.ljwx.common.pool.StringPools;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;
import org.lionsoul.ip2region.xdb.Searcher;
import org.springframework.util.FileCopyUtils;

import java.io.IOException;
import java.io.InputStream;

/**
 * IP 工具类
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName util.com.ljwx.common.IPUtil
 * @CreateTime 2024/5/5 - 16:40
 */

@Slf4j
public class IPUtil {

    private IPUtil() {

    }

    private static Searcher searcher = null;

    static {
        try (InputStream ris = IPUtil.class.getResourceAsStream("/ip2region/data.xdb")) {
            byte[] dbBinStr = FileCopyUtils.copyToByteArray(ris);
            searcher = Searcher.newWithBuffer(dbBinStr);
            log.info("Create content cached searcher success");
        } catch (IOException e) {
            log.error("Failed to create content cached searcher", e);
        }
    }

    /**
     * 获取 IP 地址（xdb模式实现）
     *
     * @param ip IP 地址
     * @return {@linkplain String} IP 地址
     * @author payne.zhuang
     * @CreateTime 2024-05-05 19:12
     */
    @SneakyThrows
    public static String getIpAddr(String ip) {
        // 处理空值或无效IP
        if (ip == null || ip.trim().isEmpty()) {
            return "未知|未知|未知|未知";
        }
        
        // 处理本地地址
        if (isLocalAddress(ip)) {
            return "本地|本地|本地|本地";
        }
        
        // 处理IPv6地址 - ip2region不支持IPv6
        if (isIPv6Address(ip)) {
            return "IPv6|IPv6|IPv6|IPv6";
        }
        
        // 3、查询
        try {
            String result = searcher.search(ip);
            // 如果查询结果为空或无效，返回默认值
            if (result == null || result.trim().isEmpty() || "0|0|0|内网IP|内网IP".equals(result)) {
                return "内网|内网|内网|内网";
            }
            return result;
        } catch (Exception e) {
            log.warn("Failed to search IP location for ({}): {}", ip, e.getMessage());
            return "未知|未知|未知|未知";
        }
    }
    
    /**
     * 判断是否为本地地址
     */
    private static boolean isLocalAddress(String ip) {
        if (ip == null) return false;
        return "127.0.0.1".equals(ip) || 
               "localhost".equals(ip) || 
               "0:0:0:0:0:0:0:1".equals(ip) || 
               "::1".equals(ip);
    }
    
    /**
     * 判断是否为IPv6地址
     */
    private static boolean isIPv6Address(String ip) {
        if (ip == null) return false;
        return ip.contains(":");
    }
}
