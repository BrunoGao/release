package com.ljwx.modules.system.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.common.constants.SystemCacheConstant;
import com.ljwx.common.pool.StringPools;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.enums.MenuTypeEnum;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.util.RedisUtil;
import com.ljwx.modules.system.domain.bo.SysMenuBO;
import com.ljwx.modules.system.domain.entity.SysMenu;
import com.ljwx.modules.system.domain.entity.SysRoleMenu;
import com.ljwx.modules.system.repository.mapper.SysMenuMapper;
import com.ljwx.modules.system.service.ISysMenuService;
import com.ljwx.modules.system.service.ISysPermissionService;
import com.ljwx.modules.system.service.ISysRoleMenuService;
import jakarta.annotation.Resource;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.CollectionUtils;

import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * 菜单管理 Service 服务接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.domain.entity.SysMenu
 * @CreateTime 2023-08-05
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SysMenuServiceImpl extends ServiceImpl<SysMenuMapper, SysMenu> implements ISysMenuService {

    @Resource
    private ISysRoleMenuService sysRoleMenuService;

    @NonNull
    private ISysPermissionService sysPermissionService;

    @Override
    public IPage<SysMenu> listSysMenuPage(PageQuery pageQuery, SysMenuBO sysMenuBO) {
        LambdaQueryWrapper<SysMenu> queryWrapper = new LambdaQueryWrapper<SysMenu>()
                .eq(SysMenu::getParentId, sysMenuBO.getParentId());
        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }

    @Override
    public boolean updateMenu(SysMenuBO sysMenuBO) {
        boolean update = updateById(sysMenuBO);
        if (Boolean.TRUE.equals(update)) {
            sysRoleMenuService.deleteRoleMenuCacheWithMenuId(sysMenuBO);
        }
        return update;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean batchDeleteMenu(List<Long> menuIds) {
        if (CollectionUtils.isEmpty(menuIds)) {
            return false;
        }

        // 先获取要删除的菜单信息
        List<SysMenu> menuList = this.listByIds(menuIds);
        if (CollectionUtils.isEmpty(menuList)) {
            return false;
        }

    

        // 删除菜单
        boolean removeBatchByIds = super.removeBatchByIds(menuIds, true);
        
        if (Boolean.TRUE.equals(removeBatchByIds)) {
            // 软删除角色菜单关联
            sysRoleMenuService.update(
                new LambdaUpdateWrapper<SysRoleMenu>()
                    .set(SysRoleMenu::getDeleted, 1)
                    .in(SysRoleMenu::getMenuId, menuIds)
            );

                // 删除角色缓存（在删除之前处理缓存）
            menuList.forEach(menu -> {
                if (menu != null) {
                    sysRoleMenuService.deleteRoleMenuCacheWithMenuId(menu);
                }
            });

            // 删除权限按钮数据
            sysPermissionService.deletePermissionWithMenuIds(menuIds);
        }
        return removeBatchByIds;
    }

    @Override
    public List<SysMenuBO> queryList() {
        LambdaQueryWrapper<SysMenu> queryWrapper = new LambdaQueryWrapper<SysMenu>()
                .eq(SysMenu::getStatus, StringPools.ONE);
        return CglibUtil.convertList(baseMapper.selectList(queryWrapper), SysMenuBO::new);
    }

    @Override
    public List<SysMenuBO> queryListWithType(String type) {
        LambdaQueryWrapper<SysMenu> queryWrapper = new LambdaQueryWrapper<SysMenu>()
                .eq(SysMenu::getStatus, StringPools.ONE)
                .eq(SysMenu::getType, type)
                .orderByAsc(SysMenu::getSort);
        return CglibUtil.convertList(baseMapper.selectList(queryWrapper), SysMenuBO::new);
    }

    @Override
    public List<SysMenuBO> queryMenuListWithRoleId(Long roleId) {
        List<SysMenu> sysMenus = baseMapper.queryMenuListWithRoleId(roleId);
        // 构建父级目录菜单数据
        buildParentMenuData(sysMenus);
        return CglibUtil.convertList(sysMenus, SysMenuBO::new);
    }

    @Override
    public List<SysMenuBO> queryMenuListWithRoleIds(List<Long> roleIds) {
        if (CollectionUtils.isEmpty(roleIds)) {
            return Collections.emptyList();
        }
        // 根据角色查找所有菜单信息
        List<SysMenu> sysMenus = baseMapper.listMenuByRoleIds(roleIds);
        // 根据角色保存菜单规则，数据中只存储了菜单，并不存储目录数据，
        // 所以根据 parentId 进行提取所有目录数据，添加到菜单中进行一起返回，形成用户路由
        Set<Long> parentIds = sysMenus.stream().map(SysMenu::getParentId).collect(Collectors.toSet());
        List<SysMenu> directoryMenu = baseMapper.selectList(new LambdaQueryWrapper<SysMenu>().in(SysMenu::getId, parentIds));
        directoryMenu.stream()
                .filter(directory -> sysMenus.stream().noneMatch(menu -> menu.getId().equals(directory.getId())))
                .forEach(sysMenus::add);
        return CglibUtil.convertList(sysMenus, SysMenuBO::new);
    }

    @Override
    public List<String> queryAllPageRouteName() {
        LambdaQueryWrapper<SysMenu> queryWrapper = new LambdaQueryWrapper<SysMenu>()
                .select(SysMenu::getRouteName)
                .eq(SysMenu::getType, StringPools.TWO)
                .orderByAsc(SysMenu::getSort);
        List<SysMenu> sysMenus = baseMapper.selectList(queryWrapper);
        return sysMenus.stream().map(SysMenu::getRouteName).toList();
    }

    @Override
    public List<SysMenuBO> queryWithDirectoryList(List<Long> menuIds) {
        LambdaQueryWrapper<SysMenu> parentMenuQuery = new LambdaQueryWrapper<SysMenu>()
                .select(SysMenu::getId, SysMenu::getParentId, SysMenu::getName)
                .eq(SysMenu::getType, MenuTypeEnum.DIRECTORY.getValue())
                .in(SysMenu::getId, menuIds);
        return CglibUtil.convertList(baseMapper.selectList(parentMenuQuery), SysMenuBO::new);
    }

    @Override
    public void saveRoleMenuToCache(Long roleId, Set<Long> menuIds) {
        LambdaQueryWrapper<SysMenu> queryWrapper = new LambdaQueryWrapper<SysMenu>()
                .eq(SysMenu::getStatus, StringPools.ONE)
                .in(SysMenu::getId, menuIds);
        List<SysMenu> sysMenus = baseMapper.selectList(queryWrapper);
        String roleMenuListKey = SystemCacheConstant.roleMenuListKey(roleId);
        // 构建父级目录菜单数据
        buildParentMenuData(sysMenus);
        // 保存角色权限到缓存
        RedisUtil.set(roleMenuListKey, CglibUtil.convertList(sysMenus, SysMenuBO::new), 30L, TimeUnit.DAYS);
    }

    /**
     * 构建父级目录菜单数据
     *
     * @param sysMenus 系统菜单
     * @author payne.zhuang <payne.zhuang@gmail.com>
     * @CreateTime 2024-06-28 - 21:36:27
     */
    private void buildParentMenuData(List<SysMenu> sysMenus) {
        // 角色菜单表中不包含parentId目录菜单，所以单独提取出来查询获取，加入整体菜单列表中一起返回
        Set<Long> parentId = sysMenus.stream()
                .map(SysMenu::getParentId)
                .filter(id -> !id.equals(0L)).collect(Collectors.toSet());
        if (!CollectionUtils.isEmpty(parentId)) {
            List<SysMenu> parentMenus = baseMapper.selectBatchIds(parentId);
            sysMenus.addAll(parentMenus);
        }
    }
}
