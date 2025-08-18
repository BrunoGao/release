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

package com.ljwx.modules.health.domain.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.ljwx.infrastructure.domain.BaseEntity;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

/**
* Table to store WeChat alert configuration Entity 实体类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.entity.TWechatAlertConfig
* @CreateTime 2025-01-02 - 13:17:05
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_wechat_alert_config")
public class TWechatAlertConfig extends BaseEntity {

    /**
     * 租户ID
     */
    private Long tenantId;

    /**
     * 微信类型: enterprise/official
     */
    private String type;

    /**
     * 企业微信企业ID
     */
    private String corpId;

    /**
     * 企业微信应用ID
     */
    private String agentId;

    /**
     * 企业微信应用Secret
     */
    private String secret;

    /**
     * 微信公众号AppID
     */
    private String appid;

    /**
     * 微信公众号AppSecret
     */
    private String appsecret;

    /**
     * 微信模板ID
     */
    private String templateId;

    /**
     * 是否启用
     */
    private Boolean enabled;

}