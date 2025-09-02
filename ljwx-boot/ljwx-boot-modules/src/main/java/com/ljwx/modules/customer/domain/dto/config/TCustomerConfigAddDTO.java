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

package com.ljwx.modules.customer.domain.dto.config;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;
import java.io.Serializable;
import java.time.LocalDateTime;

/**
*  新增 DTO 对象
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.customer.domain.dto.customer.config.TCustomerConfigAddDTO
* @CreateTime 2024-12-29 - 15:33:30
*/

@Getter
@Setter
@Schema(name = "TCustomerConfigAddDTO", description = " 新增 DTO 对象")
public class TCustomerConfigAddDTO implements Serializable {

    @Schema(description = "客户名称")
    private String customerName;
    
    @Schema(description = "描述")
    private String description;
    
    @Schema(description = "上传方式")
    private String uploadMethod;
    
    @Schema(description = "许可证密钥")
    private Integer licenseKey;
    
    @Schema(description = "是否支持许可证")
    private Boolean supportLicense;
    
    @Schema(description = "租户ID")
    private Long customerId;
    
    @Schema(description = "是否支持断点续传")
    private Boolean enableResume;
    
    @Schema(description = "上传重试次数")
    private Integer uploadRetryCount;
    
    @Schema(description = "缓存最大条数")
    private Integer cacheMaxCount;
    
    @Schema(description = "上传重试间隔")
    private Integer uploadRetryInterval;

    @Schema(description = "客户自定义logo地址")
    private String logoUrl;

    @Schema(description = "logo文件名")
    private String logoFileName;

    @Schema(description = "logo上传时间")
    private LocalDateTime logoUploadTime;

}