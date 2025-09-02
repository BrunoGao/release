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

package com.ljwx.modules.health.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.IService;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.health.domain.bo.TWechatAlertConfigBO;
import com.ljwx.modules.health.domain.entity.TWechatAlertConfig;

/**
 * Table to store WeChat alert configuration Service 服务接口层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.ITWechatAlertConfigService
 * @CreateTime 2025-01-02 - 13:17:05
 */

public interface ITWechatAlertConfigService extends IService<TWechatAlertConfig> {

    /**
     * Table to store WeChat alert configuration - 分页查询
     *
     * @param pageQuery 分页对象
     * @param tWechatAlertConfigBO BO 查询对象
     * @return {@link IPage} 分页结果
     * @author payne.zhuang
     * @CreateTime 2025-01-02 - 13:17:05
     */
    IPage<TWechatAlertConfig> listTWechatAlertConfigPage(PageQuery pageQuery, TWechatAlertConfigBO tWechatAlertConfigBO);
}
