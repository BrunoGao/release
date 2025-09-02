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

package com.ljwx.modules.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.health.domain.entity.TAlertRules;
import com.ljwx.modules.health.repository.mapper.TAlertRulesMapper;
import com.ljwx.modules.health.service.ITAlertRulesService;
import com.ljwx.modules.health.domain.bo.TAlertRulesBO;
import org.apache.commons.lang3.ObjectUtils;
import org.springframework.stereotype.Service;

/**
 *  Service 服务接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.service.impl.TAlertRulesServiceImpl
 * @CreateTime 2025-02-13 - 14:59:34
 */

@Service
public class TAlertRulesServiceImpl extends ServiceImpl<TAlertRulesMapper, TAlertRules> implements ITAlertRulesService {

    @Override
    public IPage<TAlertRules> listTAlertRulesPage(PageQuery pageQuery, TAlertRulesBO tAlertRulesBO) {
        LambdaQueryWrapper<TAlertRules> queryWrapper = new LambdaQueryWrapper<TAlertRules>()
            .eq(ObjectUtils.isNotEmpty(tAlertRulesBO.getRuleType()), TAlertRules::getRuleType, tAlertRulesBO.getRuleType())
            .eq(ObjectUtils.isNotEmpty(tAlertRulesBO.getPhysicalSign()), TAlertRules::getPhysicalSign, tAlertRulesBO.getPhysicalSign())
            .eq(ObjectUtils.isNotEmpty(tAlertRulesBO.getThresholdMin()), TAlertRules::getThresholdMin, tAlertRulesBO.getThresholdMin())
            .eq(ObjectUtils.isNotEmpty(tAlertRulesBO.getThresholdMax()), TAlertRules::getThresholdMax, tAlertRulesBO.getThresholdMax())
            .eq(ObjectUtils.isNotEmpty(tAlertRulesBO.getTrendDuration()), TAlertRules::getTrendDuration, tAlertRulesBO.getTrendDuration())
            .eq(ObjectUtils.isNotEmpty(tAlertRulesBO.getNotificationType()), TAlertRules::getNotificationType, tAlertRulesBO.getNotificationType())
            .eq(ObjectUtils.isNotEmpty(tAlertRulesBO.getCustomerId()), TAlertRules::getCustomerId, tAlertRulesBO.getCustomerId())
            .orderByDesc(TAlertRules::getCreateTime);
        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }

}

