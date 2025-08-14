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

import com.ljwx.infrastructure.domain.BaseVO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

/**
*  VO 展示类
*
* @Author brunoGao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.vo.TDeviceConfigVO
* @CreateTime 2024-10-21 - 19:44:31
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "TDeviceConfigVO", description = " VO 对象")
public class TDeviceConfigVO extends BaseVO {

    private Integer spo2measureperiod;

    private Integer stressmeasureperiod;

    private Integer bodytemperaturemeasureperiod;

    private Integer heartratewarninghigh;

    private Integer heartratewarninglow;

    private Integer spo2warning;

    private Integer stresswarning;

    private Float bodytemperaturehighwarning;

    private Float bodytemperaturelowwarning;

    private String httpurl;

    private String logo;

    private String uitype;

    private Integer bodytemperaturewarningcnt;

    private Integer heartwarningcnt;

    private Integer heartratemeasureperiod;

    private Integer spo2warningcnt;

}