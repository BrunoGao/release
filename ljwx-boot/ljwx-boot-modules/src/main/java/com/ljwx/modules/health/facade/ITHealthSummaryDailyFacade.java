/*
 * All Rights Reserved: Copyright [2024] [ljwx (paynezhuang@gmail.com)]
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
import com.ljwx.modules.health.domain.dto.health.summary.daily.THealthSummaryDailyAddDTO;
import com.ljwx.modules.health.domain.dto.health.summary.daily.THealthSummaryDailyDeleteDTO;
import com.ljwx.modules.health.domain.dto.health.summary.daily.THealthSummaryDailySearchDTO;
import com.ljwx.modules.health.domain.dto.health.summary.daily.THealthSummaryDailyUpdateDTO;
import com.ljwx.modules.health.domain.vo.THealthSummaryDailyVO;

/**
 * 用户每日健康画像汇总表 门面接口层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.ITHealthSummaryDailyFacade
 * @CreateTime 2025-05-01 - 21:33:15
 */

public interface ITHealthSummaryDailyFacade {

    /**
     * 用户每日健康画像汇总表 - 分页查询
     *
     * @param pageQuery        分页对象
     * @param tHealthSummaryDailySearchDTO 查询对象
     * @return {@link RPage} 查询结果
     * @author payne.zhuang
     * @CreateTime 2025-05-01 - 21:33:15
     */
    RPage<THealthSummaryDailyVO> listTHealthSummaryDailyPage(PageQuery pageQuery, THealthSummaryDailySearchDTO tHealthSummaryDailySearchDTO);

    /**
     * 根据 ID 获取详情信息
     *
     * @param id 用户每日健康画像汇总表ID
     * @return {@link THealthSummaryDailyVO} 用户每日健康画像汇总表 VO 对象
     * @author payne.zhuang
     * @CreateTime 2025-05-01 - 21:33:15
     */
    THealthSummaryDailyVO get(Long id);

    /**
     * 新增用户每日健康画像汇总表
     *
     * @param tHealthSummaryDailyAddDTO 新增用户每日健康画像汇总表 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-05-01 - 21:33:15
     */
    boolean add(THealthSummaryDailyAddDTO tHealthSummaryDailyAddDTO);

    /**
     * 编辑更新用户每日健康画像汇总表信息
     *
     * @param tHealthSummaryDailyUpdateDTO 编辑更新 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-05-01 - 21:33:15
     */
    boolean update(THealthSummaryDailyUpdateDTO tHealthSummaryDailyUpdateDTO);

    /**
     * 批量删除用户每日健康画像汇总表信息
     *
     * @param tHealthSummaryDailyDeleteDTO 删除 DTO 对象
     * @return @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2025-05-01 - 21:33:15
     */
    boolean batchDelete(THealthSummaryDailyDeleteDTO tHealthSummaryDailyDeleteDTO);

}