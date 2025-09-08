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
import com.ljwx.modules.health.domain.bo.TDeviceMessageBO;
import com.ljwx.modules.health.domain.entity.TDeviceMessage;
import com.ljwx.modules.health.domain.vo.TDeviceMessageVO;
import com.ljwx.modules.health.repository.mapper.TDeviceMessageMapper;
import com.ljwx.modules.health.service.ITDeviceMessageService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.stream.Collectors;

/**
 * TDeviceMessage Service 服务接口实现层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.impl.TDeviceMessageServiceImpl
 * @CreateTime 2025-09-08
 */

@Slf4j
@Service
public class TDeviceMessageServiceImpl extends ServiceImpl<TDeviceMessageMapper, TDeviceMessage> implements ITDeviceMessageService {

    @Override
    public IPage<TDeviceMessageVO> listTDeviceMessagePage(PageQuery pageQuery, TDeviceMessageBO tDeviceMessageBO) {
        log.debug("分页查询设备消息：pageQuery={}, tDeviceMessageBO={}", pageQuery, tDeviceMessageBO);
        
        LambdaQueryWrapper<TDeviceMessage> queryWrapper = new LambdaQueryWrapper<>();
        
        // 根据BO构建查询条件
        if (tDeviceMessageBO != null) {
            queryWrapper.eq(tDeviceMessageBO.getOrgId() != null, TDeviceMessage::getOrgId, tDeviceMessageBO.getOrgId())
                    .eq(tDeviceMessageBO.getCustomerId() != null, TDeviceMessage::getCustomerId, tDeviceMessageBO.getCustomerId())
                    .eq(StringUtils.hasText(tDeviceMessageBO.getUserId()), TDeviceMessage::getUserId, tDeviceMessageBO.getUserId())
                    .eq(StringUtils.hasText(tDeviceMessageBO.getDeviceSn()), TDeviceMessage::getDeviceSn, tDeviceMessageBO.getDeviceSn())
                    .eq(StringUtils.hasText(tDeviceMessageBO.getMessageType()), TDeviceMessage::getMessageType, tDeviceMessageBO.getMessageType())
                    .eq(StringUtils.hasText(tDeviceMessageBO.getMessageStatus()), TDeviceMessage::getMessageStatus, tDeviceMessageBO.getMessageStatus())
                    .like(StringUtils.hasText(tDeviceMessageBO.getMessage()), TDeviceMessage::getMessage, tDeviceMessageBO.getMessage());
            
            // 如果有指定的ID列表，使用IN查询
            if (tDeviceMessageBO.getIds() != null && !tDeviceMessageBO.getIds().isEmpty()) {
                queryWrapper.in(TDeviceMessage::getId, tDeviceMessageBO.getIds());
            }
        }
        
        // 按创建时间倒序排列
        queryWrapper.orderByDesc(TDeviceMessage::getCreateTime);
        
        // 执行分页查询
        IPage<TDeviceMessage> entityPage = baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
        
        // 转换为VO对象
        List<TDeviceMessageVO> voList = entityPage.getRecords().stream()
                .map(this::convertToVO)
                .collect(Collectors.toList());
        
        // 构建返回的分页结果
        IPage<TDeviceMessageVO> voPage = entityPage.convert(entity -> null);
        voPage.setRecords(voList);
        
        log.debug("设备消息分页查询完成，总记录数：{}", voPage.getTotal());
        return voPage;
    }
    
    /**
     * 将Entity转换为VO
     */
    private TDeviceMessageVO convertToVO(TDeviceMessage entity) {
        TDeviceMessageVO vo = TDeviceMessageVO.builder().build();
        BeanUtils.copyProperties(entity, vo);
        
        // 这里可以添加额外的属性设置，比如用户名、部门名等
        // 由于需要关联查询其他表，暂时保持简单实现
        
        return vo;
    }
}