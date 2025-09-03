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

package com.ljwx.modules.customer.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.IService;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.customer.domain.bo.THealthDataConfigBO;
import com.ljwx.modules.customer.domain.entity.THealthDataConfig;

import java.util.List;

/**
 *  Service 服务接口层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.customer.service.ITHealthDataConfigService
 * @CreateTime 2024-12-29 - 15:02:31
 */

public interface ITHealthDataConfigService extends IService<THealthDataConfig> {

    /**
     *  - 分页查询
     *
     * @param pageQuery 分页对象
     * @param tHealthDataConfigBO BO 查询对象
     * @return {@link IPage} 分页结果
     * @author payne.zhuang
     * @CreateTime 2024-12-29 - 15:02:31
     */
    IPage<THealthDataConfig> listTHealthDataConfigPage(PageQuery pageQuery, THealthDataConfigBO tHealthDataConfigBO);

    /**
     * 根据 customerId 查询启用的健康数据配置
     *
     * @param customerId 客户ID
     * @return {@link List} 启用的健康数据配置列表
     * @author jjgao
     * @CreateTime 2025-01-15
     */
    List<THealthDataConfig> getEnabledConfigsByCustomerId(Long customerId);

    /**
     * 根据 customerId 查询基础健康数据配置（t_user_health_data主表字段）
     *
     * @param customerId 客户ID
     * @return {@link List} 基础健康数据配置列表
     * @author jjgao
     * @CreateTime 2025-01-15
     */
    List<THealthDataConfig> getBaseConfigsByCustomerId(Long customerId);

    /**
     * 根据 orgId 查询启用的健康数据配置
     *
     * @param orgId 组织ID
     * @return {@link List} 启用的健康数据配置列表
     * @author jjgao
     * @CreateTime 2025-08-18
     */
    List<THealthDataConfig> getEnabledConfigsByOrgId(Long orgId);

    /**
     * 根据 orgId 查询基础健康数据配置（过滤掉不需要的字段）
     *
     * @param orgId 组织ID
     * @return {@link List} 基础健康数据配置列表
     * @author jjgao
     * @CreateTime 2025-08-18
     */
    List<THealthDataConfig> getBaseConfigsByOrgId(Long orgId);
}
