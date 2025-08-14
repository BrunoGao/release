/*
 * All Rights Reserved: Copyright [2024] [Zhuang Pan (brunoGao@gmail.com)]
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

package com.ljwx.modules.health.util;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * 健康数据分表工具类
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.util.HealthDataTableUtil
 * @CreateTime 2024-12-15 - 22:04:51
 */
public class HealthDataTableUtil {

    private static final DateTimeFormatter MONTH_FORMATTER = DateTimeFormatter.ofPattern("yyyyMM"); // #月份格式化器

    /**
     * 根据时间获取分表名称
     */
    public static String getTableName(LocalDateTime dateTime) {
        return "t_user_health_data_" + dateTime.format(MONTH_FORMATTER);
    }

    /**
     * 获取时间范围内的所有分表名称
     */
    public static List<String> getTableNames(LocalDateTime startDate, LocalDateTime endDate) {
        List<String> tableNames = new ArrayList<>();
        LocalDateTime current = startDate.withDayOfMonth(1).withHour(0).withMinute(0).withSecond(0).withNano(0);
        LocalDateTime end = endDate.withDayOfMonth(1).withHour(0).withMinute(0).withSecond(0).withNano(0);
        
        while (!current.isAfter(end)) {
            tableNames.add(getTableName(current));
            current = current.plusMonths(1);
        }
        
        return tableNames;
    }
} 