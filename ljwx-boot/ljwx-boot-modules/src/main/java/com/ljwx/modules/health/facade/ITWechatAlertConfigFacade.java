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

package com.ljwx.modules.health.facade;

import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.dto.alert.config.wechat.TWechatAlertConfigAddDTO;
import com.ljwx.modules.health.domain.dto.alert.config.wechat.TWechatAlertConfigDeleteDTO;
import com.ljwx.modules.health.domain.dto.alert.config.wechat.TWechatAlertConfigSearchDTO;
import com.ljwx.modules.health.domain.dto.alert.config.wechat.TWechatAlertConfigUpdateDTO;
import com.ljwx.modules.health.domain.vo.TWechatAlertConfigVO;

/**
 * Table to store WeChat alert configuration 门面接口层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.ITWechatAlertConfigFacade
 * @CreateTime 2025-01-02 - 13:17:05
 */

public interface ITWechatAlertConfigFacade {

    /**
     * Table to store WeChat alert configuration - 分页查询
     *
     * @param pageQuery        分页对象
     * @param tWechatAlertConfigSearchDTO 查询对象
     * @return {@link RPage} 查询结果
     * @author payne.zhuang
     * @CreateTime 2025-01-02 - 13:17:05
     */
    RPage<TWechatAlertConfigVO> listTWechatAlertConfigPage(PageQuery pageQuery, TWechatAlertConfigSearchDTO tWechatAlertConfigSearchDTO);

    /**
     * 根据 ID 获取详情信息
     *
     * @param id Table to store WeChat alert configurationID
     * @return {@link TWechatAlertConfigVO} Table to store WeChat alert configuration VO 对象
     * @author payne.zhuang
     * @CreateTime 2025-01-02 - 13:17:05
     */
    TWechatAlertConfigVO get(Long id);

    /**
     * 新增Table to store WeChat alert configuration
     *
     * @param tWechatAlertConfigAddDTO 新增Table to store WeChat alert configuration DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-01-02 - 13:17:05
     */
    boolean add(TWechatAlertConfigAddDTO tWechatAlertConfigAddDTO);

    /**
     * 编辑更新Table to store WeChat alert configuration信息
     *
     * @param tWechatAlertConfigUpdateDTO 编辑更新 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-01-02 - 13:17:05
     */
    boolean update(TWechatAlertConfigUpdateDTO tWechatAlertConfigUpdateDTO);

    /**
     * 批量删除Table to store WeChat alert configuration信息
     *
     * @param tWechatAlertConfigDeleteDTO 删除 DTO 对象
     * @return @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-01-02 - 13:17:05
     */
    boolean batchDelete(TWechatAlertConfigDeleteDTO tWechatAlertConfigDeleteDTO);

}