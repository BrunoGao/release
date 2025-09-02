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

package com.ljwx.modules.health.repository.mapper;

import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDateTime;
import java.util.List;

/**
 *  Mapper 接口层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.repository.mapper.TUserHealthDataMapper
 * @CreateTime 2024-12-15 - 22:04:51
 */

public interface TUserHealthDataMapper extends BaseMapper<TUserHealthData> {

    /**
     * 动态查询分表数据
     */
    @Select("SELECT * FROM ${tableName} WHERE device_sn IN (${deviceSnList}) AND timestamp BETWEEN #{startDate} AND #{endDate} ORDER BY timestamp ASC")
    List<TUserHealthData> selectFromShardedTable(@Param("tableName") String tableName, 
                                                  @Param("deviceSnList") String deviceSnList,
                                                  @Param("startDate") LocalDateTime startDate,
                                                  @Param("endDate") LocalDateTime endDate);
}