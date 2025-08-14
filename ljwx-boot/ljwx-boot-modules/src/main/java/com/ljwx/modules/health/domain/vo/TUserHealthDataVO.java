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

package com.ljwx.modules.health.domain.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.ljwx.infrastructure.domain.BaseVO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Map;
/**
*  VO 展示类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.vo.TUserHealthDataVO
* @CreateTime 2024-12-16 - 19:56:12
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "TUserHealthDataVO", description = " VO 对象")
public class TUserHealthDataVO extends BaseVO {
    /**
     * 用户ID
     */
    private String userName;

    /**
     * 部门信息
     */
    private String departmentInfo;


    private String phoneNumber;

    private Integer heartRate;

    private Integer pressureHigh;

    private Integer pressureLow;

    private Integer bloodOxygen;

    private Integer stress;

    private Double temperature;

    private Integer step;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "Asia/Shanghai")
    private LocalDateTime timestamp;

    private Double latitude;

    private Double longitude;

    private Double altitude;

    private String deviceSn;

    private Double distance;

    private Double calorie;

    private Map<String, Object> sleepData;
    private Map<String, Object> workoutData;
    private Map<String, Object> exerciseDailyData;
    private Map<String, Object> exerciseWeekData;

    private String createUser;

    private LocalDateTime createTime;

}