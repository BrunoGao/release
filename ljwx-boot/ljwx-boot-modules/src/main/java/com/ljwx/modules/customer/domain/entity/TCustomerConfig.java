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

package com.ljwx.modules.customer.domain.entity;

import com.baomidou.mybatisplus.annotation.TableField;
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
* @ClassName com.ljwx.modules.customer.domain.entity.TCustomerConfig
* @CreateTime 2024-12-29 - 15:33:30
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_customer_config")
public class TCustomerConfig extends BaseEntity {

    private String customerName;

    private String description;

    private String uploadMethod;

    private Integer licenseKey;

    @TableField("is_support_license")
    private Boolean isSupportLicense;

    private Long id;

    private Integer isDeleted;


    /** 是否支持断点续传 */
    @TableField("enable_resume")
    private Boolean enableResume;

    /** HTTP 上传失败后重试次数 */
    @TableField("upload_retry_count")
    private Integer uploadRetryCount;

    /** 本地缓存队列最大条数 */
    @TableField("cache_max_count")
    private Integer cacheMaxCount;

    /** 上传失败后重试间隔 */
    @TableField("upload_retry_interval")
    private Integer uploadRetryInterval;

}