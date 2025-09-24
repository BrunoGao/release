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

package com.ljwx.modules.health.domain.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 健康数据周报慢字段表 Entity 实体类
 * 存储周运动等JSON格式的慢字段数据
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.entity.THealthDataSlowWeekly
 * @CreateTime 2024-12-15 - 22:04:51
 */

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_health_data_slow_weekly")
public class THealthDataSlowWeekly { // #不继承BaseEntity，避免字段不匹配

    @TableId(type = IdType.AUTO)
    private Long id; // #主键ID
    
    private String deviceSn; // #设备序列号
    private Long orgId;
    private Long userId;

    /**
     * 租户ID，继承自用户所属租户
     */
    private Long customerId;
    
    @TableField("week_start")
    private LocalDate timestamp; // #周开始日期(映射到数据库week_start字段)
    
    private String exerciseWeekData; // #每周运动数据
    
    @TableField("create_time")
    private LocalDateTime createTime; // #创建时间
    
    @TableField("update_time") 
    private LocalDateTime updateTime; // #更新时间
} 