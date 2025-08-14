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

package com.ljwx.modules.health.facade.impl;

import com.alibaba.fastjson.JSON;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.infrastructure.util.RedisUtil;
import com.ljwx.modules.health.domain.bo.TAlertRulesBO;
import com.ljwx.modules.health.domain.dto.alert.rules.TAlertRulesAddDTO;
import com.ljwx.modules.health.domain.dto.alert.rules.TAlertRulesDeleteDTO;
import com.ljwx.modules.health.domain.dto.alert.rules.TAlertRulesSearchDTO;
import com.ljwx.modules.health.domain.dto.alert.rules.TAlertRulesUpdateDTO;
import com.ljwx.modules.health.domain.entity.TAlertRules;
import com.ljwx.modules.health.domain.vo.TAlertRulesVO;
import com.ljwx.modules.health.facade.ITAlertRulesFacade;
import com.ljwx.modules.health.service.ITAlertRulesService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 *  门面接口实现层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.TAlertRulesFacadeImpl
 * @CreateTime 2024-10-27 - 13:03:58
 */

@Service
@RequiredArgsConstructor
public class TAlertRulesFacadeImpl implements ITAlertRulesFacade {

    @NonNull
    private ITAlertRulesService tAlertRulesService;

    @Override
    public RPage<TAlertRulesVO> listTAlertRulesPage(PageQuery pageQuery, TAlertRulesSearchDTO tAlertRulesSearchDTO) {
        TAlertRulesBO tAlertRulesBO = CglibUtil.convertObj(tAlertRulesSearchDTO, TAlertRulesBO::new);
        IPage<TAlertRules> tAlertRulesIPage = tAlertRulesService.listTAlertRulesPage(pageQuery, tAlertRulesBO);
        return RPage.build(tAlertRulesIPage, TAlertRulesVO::new);
    }

    @Override
    public TAlertRulesVO get(Long id) {
        TAlertRules byId = tAlertRulesService.getById(id);
        return CglibUtil.convertObj(byId, TAlertRulesVO::new);
    }

    @Override
    @Transactional
    public boolean add(TAlertRulesAddDTO tAlertRulesAddDTO) {
        TAlertRulesBO tAlertRulesBO = CglibUtil.convertObj(tAlertRulesAddDTO, TAlertRulesBO::new);
        boolean result = tAlertRulesService.save(tAlertRulesBO);
        if (result) {
            // 更新Redis缓存
            List<TAlertRules> list = tAlertRulesService.list();
            // 转换为 JSON 字符串存储
            String jsonString = JSON.toJSONString(list);
            RedisUtil.set("alert_rules", jsonString);
            // 发布更新消息
            RedisUtil.publish("alert_rules_channel", "update");
        }
        return result;
    }

    @Override
    @Transactional
    public boolean update(TAlertRulesUpdateDTO tAlertRulesUpdateDTO) {
        TAlertRulesBO tAlertRulesBO = CglibUtil.convertObj(tAlertRulesUpdateDTO, TAlertRulesBO::new);
        boolean result = tAlertRulesService.updateById(tAlertRulesBO);
        System.out.println("更新缓存" + tAlertRulesBO.toString());
        if (result) {
            // 更新Redis缓存
            List<TAlertRules> list = tAlertRulesService.list();
            // 转换为 JSON 字符串存储
            String jsonString = JSON.toJSONString(list);
            RedisUtil.set("alert_rules", jsonString);
            // 发布更新消息
            RedisUtil.publish("alert_rules_channel", "update");
        }
        return result;
    }

    @Override
    @Transactional
    public boolean batchDelete(TAlertRulesDeleteDTO tAlertRulesDeleteDTO) {
        TAlertRulesBO tAlertRulesBO = CglibUtil.convertObj(tAlertRulesDeleteDTO, TAlertRulesBO::new);
        boolean result = tAlertRulesService.removeBatchByIds(tAlertRulesBO.getIds(), true);
        if (result) {
            // 更新Redis缓存
            List<TAlertRules> list = tAlertRulesService.list();
            // 转换为 JSON 字符串存储
            String jsonString = JSON.toJSONString(list);
            RedisUtil.set("alert_rules", jsonString);
            // 发布更新消息
            RedisUtil.publish("alert_rules_channel", "update");
        }
        return result;
    }

}