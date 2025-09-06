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
import java.io.Serializable;

/**
 * 健康评分查询 DTO 对象
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.dto.v1.health.HealthScoreQueryDTO
 * @CreateTime 2025-01-01 - 10:00:00
 */

@Getter
@Setter
@Builder
@Schema(name = "HealthScoreQueryDTO", description = "健康评分查询 DTO 对象")
public class HealthScoreQueryDTO implements Serializable {
    
    @Schema(description = "用户ID")
    private String userId;
    
    @Schema(description = "组织ID") 
    private String orgId;
    
    @Schema(description = "日期，格式: yyyy-MM-dd")
    private String date;
}