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

package com.ljwx.modules.geofence.domain.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.ljwx.infrastructure.domain.BaseEntity;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

/**
*  Entity 实体类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.geofence.domain.entity.TGeofence
* @CreateTime 2025-01-07 - 19:44:06
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_geofence")
public class TGeofence extends BaseEntity {

    /**
    * 电子围栏名称
    */
    private String name;

    /**
    * 围栏区域
    */

    private String area;

    /**
    * 围栏描述
    */
    private String description;

    /**
    * 围栏状态
    */
    private String status;

}