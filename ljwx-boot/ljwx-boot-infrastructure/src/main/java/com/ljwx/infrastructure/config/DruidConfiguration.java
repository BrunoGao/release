/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ljwx.infrastructure.config;

import com.alibaba.druid.filter.Filter;
import com.alibaba.druid.pool.DruidDataSource;
import com.alibaba.druid.wall.WallConfig;
import com.alibaba.druid.wall.WallFilter;
import com.google.common.collect.Lists;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.sql.DataSource;
import java.util.List;

/**
 * Druid 数据源配置
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName config.com.ljwx.infrastructure.DruidConfiguration
 * @CreateTime 2024/11/29 - 14:14
 */

@Configuration
public class DruidConfiguration {

    /**
     * 配置 Druid 数据源
     *
     * @return {@link DataSource } 数据源
     * @author payne.zhuang
     * @CreateTime 2024-11-29 - 14:16:06
     */
    @Bean
    public DataSource druidPrimary(
            @Value("${spring.datasource.url}") String url,
            @Value("${spring.datasource.username}") String username,
            @Value("${spring.datasource.password}") String password,
            @Value("${spring.datasource.driver-class-name}") String driverClassName) {
        DruidDataSource druidDataSource = new DruidDataSource(); // 修复：移除try-with-resources，避免数据源被自动关闭
        druidDataSource.setUrl(url); // 直接设置URL
        druidDataSource.setUsername(username); // 直接设置用户名
        druidDataSource.setPassword(password); // 直接设置密码
        druidDataSource.setDriverClassName(driverClassName); // 直接设置驱动类名
        druidDataSource.setProxyFilters(getProxyFilters()); // 设置代理过滤器
        return druidDataSource;
    }

    /**
     * 获取代理过滤器
     *
     * @return {@link List<Filter> } 过滤器集合
     * @author payne.zhuang
     * @CreateTime 2024-11-29 - 14:16:55
     */
    private List<Filter> getProxyFilters() {
        List<Filter> filterList = Lists.newArrayList();
        filterList.add(wallFilter());
        return filterList;
    }

    /**
     * 配置 WallFilter
     *
     * @return {@link WallFilter } WallFilter 过滤器实例
     * @author payne.zhuang
     * @CreateTime 2024-11-29 - 14:16:28
     */
    @Bean
    public WallFilter wallFilter() {
        WallFilter wallFilter = new WallFilter();
        wallFilter.setConfig(wallConfig());
        return wallFilter;
    }

    /**
     * 配置 WallConfig
     *
     * @return {@link WallConfig } WallConfig 配置信息实例
     * @author payne.zhuang
     * @CreateTime 2024-11-29 - 14:17:22
     */
    @Bean
    public WallConfig wallConfig() {
        WallConfig config = new WallConfig();
        // 允许一次执行多条语句
        config.setMultiStatementAllow(true);
        // 允许非基本语句的执行（如存储过程、函数调用等）
        config.setNoneBaseStatementAllow(true);
        return config;
    }
}
