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

package com.ljwx.modules.health.domain.dto.v1.health;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import jakarta.validation.constraints.NotBlank;
import java.io.Serializable;

/**
 * 基线生成请求 DTO 对象
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.dto.v1.health.BaselineGenerateRequestDTO
 * @CreateTime 2025-01-01 - 10:00:00
 */

@Getter
@Setter
@Builder
@Schema(name = "BaselineGenerateRequestDTO", description = "基线生成请求 DTO 对象")
public class BaselineGenerateRequestDTO implements Serializable {
    
    @NotBlank(message = "组织ID不能为空")
    @Schema(description = "组织ID", required = true)
    private String orgId;
    
    @Schema(description = "开始日期，格式: yyyy-MM-dd")
    private String startDate;
    
    @Schema(description = "结束日期，格式: yyyy-MM-dd")
    private String endDate;
}