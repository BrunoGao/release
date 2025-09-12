package com.ljwx.modules.system.service.impl;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.common.exception.BizException;
import com.ljwx.modules.system.domain.dto.menu.DynamicMenuConfigDTO;
import com.ljwx.modules.system.domain.dto.menu.DynamicMenuScanDTO;
import com.ljwx.modules.system.domain.dto.menu.MenuBatchUpdateDTO;
import com.ljwx.modules.system.domain.entity.SysMenu;
import com.ljwx.modules.system.domain.vo.DynamicMenuVO;
import com.ljwx.modules.system.domain.vo.MenuScanResultVO;
import com.ljwx.modules.system.repository.mapper.SysMenuMapper;
import com.ljwx.modules.system.service.IDynamicMenuService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.io.IOException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * 动态菜单管理服务实现
 * 提供前端路由扫描、菜单自动同步、灵活配置等功能
 * 
 * @author bruno.gao
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DynamicMenuServiceImpl extends ServiceImpl<SysMenuMapper, SysMenu> implements IDynamicMenuService {

    private final SysMenuMapper sysMenuMapper;
    
    // 缓存前端文件扫描结果
    private final Map<String, Long> fileLastModified = new ConcurrentHashMap<>();
    
    // 支持的前端文件扩展名
    private static final Set<String> SUPPORTED_EXTENSIONS = Set.of(".vue", ".tsx", ".jsx", ".ts", ".js");
    
    // 路由提取正则表达式
    private static final Pattern ROUTE_PATTERN = Pattern.compile("(?:path|name)\\s*:\\s*['\"]([^'\"]+)['\"]");
    private static final Pattern TITLE_PATTERN = Pattern.compile("(?:title|label)\\s*:\\s*['\"]([^'\"]+)['\"]");
    private static final Pattern COMPONENT_PATTERN = Pattern.compile("component\\s*:\\s*['\"]([^'\"]+)['\"]");

    @Override
    public MenuScanResultVO scanFrontendRoutes(DynamicMenuScanDTO scanDTO) {
        log.info("开始扫描前端路由文件，路径: {}", scanDTO.getFrontendPath());
        
        MenuScanResultVO result = new MenuScanResultVO();
        result.setScanTime(LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
        result.setFoundFiles(new ArrayList<>());
        result.setNewRoutes(new ArrayList<>());
        result.setChangedFiles(new ArrayList<>());
        
        // 解析前端项目路径
        String frontendPath = resolveFrontendPath(scanDTO.getFrontendPath());
        Path basePath = Paths.get(frontendPath);
        
        if (!Files.exists(basePath)) {
            log.error("前端项目路径不存在: {}, 解析后路径: {}", scanDTO.getFrontendPath(), frontendPath);
            throw new BizException("前端项目路径不存在: " + frontendPath);
        }
        
        log.info("成功找到前端项目路径: {}", frontendPath);

        try {
            // 扫描文件
            Files.walkFileTree(basePath, new SimpleFileVisitor<Path>() {
                @Override
                public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                    String fileName = file.getFileName().toString();
                    String fileExtension = fileName.substring(fileName.lastIndexOf('.'));
                    
                    // 检查文件类型
                    if (!SUPPORTED_EXTENSIONS.contains(fileExtension)) {
                        return FileVisitResult.CONTINUE;
                    }
                    
                    // 检查包含/排除模式
                    String relativePath = basePath.relativize(file).toString();
                    if (!isFileIncluded(relativePath, scanDTO)) {
                        return FileVisitResult.CONTINUE;
                    }
                    
                    result.getFoundFiles().add(relativePath);
                    
                    // 检查文件是否修改
                    long lastModified = attrs.lastModifiedTime().toMillis();
                    Long cachedTime = fileLastModified.get(relativePath);
                    if (cachedTime == null || lastModified > cachedTime) {
                        result.getChangedFiles().add(relativePath);
                        fileLastModified.put(relativePath, lastModified);
                        
                        // 解析文件中的路由信息
                        parseRouteFromFile(file, relativePath, result, scanDTO);
                    }
                    
                    return FileVisitResult.CONTINUE;
                }
                
                @Override
                public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) throws IOException {
                    if (!scanDTO.getRecursive() && !dir.equals(basePath)) {
                        return FileVisitResult.SKIP_SUBTREE;
                    }
                    return FileVisitResult.CONTINUE;
                }
            });
            
            log.info("扫描完成，发现文件: {}, 变更文件: {}, 新路由: {}", 
                    result.getFoundFiles().size(), 
                    result.getChangedFiles().size(), 
                    result.getNewRoutes().size());
            
        } catch (IOException e) {
            log.error("扫描前端路由文件失败", e);
            throw new BizException("扫描前端路由文件失败: " + e.getMessage());
        }
        
        return result;
    }

    @Override
    @Transactional
    public String autoSyncMenus(DynamicMenuScanDTO scanDTO) {
        log.info("开始自动同步菜单配置");
        
        MenuScanResultVO scanResult = scanFrontendRoutes(scanDTO);
        if (scanResult.getNewRoutes().isEmpty()) {
            return "未发现新的路由，无需同步";
        }
        
        List<DynamicMenuConfigDTO> newMenus = new ArrayList<>();
        int sortValue = scanDTO.getSortStartValue() != null ? scanDTO.getSortStartValue() : 100;
        int increment = scanDTO.getSortIncrement() != null ? scanDTO.getSortIncrement() : 10;
        
        for (MenuScanResultVO.RouteInfo routeInfo : scanResult.getNewRoutes()) {
            if (!scanDTO.getAutoCreate()) {
                continue;
            }
            
            // 检查菜单是否已存在
            if (isMenuExists(routeInfo.getPath())) {
                if (!scanDTO.getOverwriteExisting()) {
                    continue;
                }
            }
            
            // 生成菜单配置
            DynamicMenuConfigDTO menuConfig = autoGenerateMenu(routeInfo.getPath(), routeInfo.getFilePath());
            menuConfig.setParentId(scanDTO.getDefaultParentId());
            menuConfig.setSort(sortValue);
            menuConfig.setSource("scan");
            menuConfig.setSourceFile(routeInfo.getFilePath());
            menuConfig.setLastScanTime(scanResult.getScanTime());
            menuConfig.setVersion("1.0");
            
            if (StringUtils.hasText(routeInfo.getTitle())) {
                menuConfig.setTitle(routeInfo.getTitle());
            }
            if (StringUtils.hasText(routeInfo.getComponent())) {
                menuConfig.setComponent(routeInfo.getComponent());
            }
            
            newMenus.add(menuConfig);
            sortValue += increment;
        }
        
        // 批量创建菜单
        if (!newMenus.isEmpty()) {
            String result = importMenuConfig(newMenus);
            clearMenuCache(null);
            return String.format("成功同步 %d 个新菜单: %s", newMenus.size(), result);
        }
        
        return "未创建新菜单";
    }

    @Override
    @Cacheable(value = "dynamic_menus", key = "#customerId")
    public List<DynamicMenuVO> getDynamicMenuConfig(Long customerId) {
        log.info("获取动态菜单配置，租户ID: {}", customerId);
        
        LambdaQueryWrapper<SysMenu> queryWrapper = new LambdaQueryWrapper<SysMenu>()
                .orderByAsc(SysMenu::getSort)
                .orderByAsc(SysMenu::getId);
        
        List<SysMenu> menus = list(queryWrapper);
        return menus.stream()
                .map(this::convertToMenuVO)
                .collect(Collectors.toList());
    }

    @Override
    @Transactional
    @CacheEvict(value = "dynamic_menus", allEntries = true)
    public String updateDynamicMenuConfig(DynamicMenuConfigDTO configDTO) {
        log.info("更新动态菜单配置，菜单ID: {}", configDTO.getId());
        
        // 验证配置
        List<String> validationErrors = validateMenuConfig(configDTO);
        if (!validationErrors.isEmpty()) {
            throw new BizException("菜单配置验证失败: " + String.join(", ", validationErrors));
        }
        
        SysMenu menu;
        if (configDTO.getId() != null) {
            // 更新现有菜单
            menu = getById(configDTO.getId());
            if (menu == null) {
                throw new BizException("菜单不存在");
            }
            updateMenuFromDTO(menu, configDTO);
        } else {
            // 创建新菜单
            menu = createMenuFromDTO(configDTO);
        }
        
        saveOrUpdate(menu);
        return "菜单配置更新成功";
    }

    @Override
    @Transactional
    @CacheEvict(value = "dynamic_menus", allEntries = true)
    public String batchUpdateMenus(MenuBatchUpdateDTO batchDTO) {
        log.info("批量更新菜单，操作类型: {}, 菜单数量: {}", 
                batchDTO.getOperation(), batchDTO.getMenuIds().size());
        
        List<SysMenu> menusToUpdate = listByIds(batchDTO.getMenuIds());
        if (menusToUpdate.isEmpty()) {
            return "未找到需要更新的菜单";
        }
        
        switch (batchDTO.getOperation()) {
            case "update":
                return batchUpdateFields(menusToUpdate, batchDTO);
            case "enable":
                return batchUpdateStatus(menusToUpdate, "1");
            case "disable":
                return batchUpdateStatus(menusToUpdate, "0");
            case "delete":
                return batchDeleteMenus(menusToUpdate, batchDTO);
            default:
                throw new BizException("不支持的操作类型: " + batchDTO.getOperation());
        }
    }

    @Override
    @Transactional
    @CacheEvict(value = "dynamic_menus", allEntries = true)
    public String reorderMenus(List<Long> menuIds) {
        log.info("重新排序菜单，菜单数量: {}", menuIds.size());
        
        List<SysMenu> menus = listByIds(menuIds);
        if (menus.size() != menuIds.size()) {
            throw new BizException("部分菜单不存在");
        }
        
        // 按照传入的顺序重新设置排序值
        for (int i = 0; i < menuIds.size(); i++) {
            Long menuId = menuIds.get(i);
            SysMenu menu = menus.stream()
                    .filter(m -> m.getId().equals(menuId))
                    .findFirst()
                    .orElseThrow(() -> new BizException("菜单不存在: " + menuId));
            
            menu.setSort(i + 1);
        }
        
        updateBatchById(menus);
        return String.format("成功重新排序 %d 个菜单", menus.size());
    }

    @Override
    @Transactional
    public String applyPresetTemplate(String templateName, Long customerId) {
        log.info("应用预设模板: {}, 租户ID: {}", templateName, customerId);
        
        List<DynamicMenuConfigDTO> templateMenus = loadPresetTemplate(templateName);
        if (templateMenus.isEmpty()) {
            throw new BizException("预设模板不存在: " + templateName);
        }
        
        String result = importMenuConfig(templateMenus);
        clearMenuCache(customerId);
        
        return String.format("成功应用预设模板 '%s': %s", templateName, result);
    }

    @Override
    @CacheEvict(value = "dynamic_menus", allEntries = true)
    public String clearMenuCache(Long customerId) {
        log.info("清除菜单缓存，租户ID: {}", customerId);
        return "菜单缓存已清除";
    }

    @Override
    public List<DynamicMenuVO> previewMenuConfig(Long customerId, Long roleId) {
        log.info("预览菜单配置，租户ID: {}, 角色ID: {}", customerId, roleId);
        
        List<DynamicMenuVO> allMenus = getDynamicMenuConfig(customerId);
        
        // 如果没有指定角色，返回所有菜单
        if (roleId == null) {
            return allMenus;
        }
        
        // TODO: 根据角色权限过滤菜单
        return allMenus;
    }

    @Override
    @Transactional
    public String importMenuConfig(List<DynamicMenuConfigDTO> configList) {
        log.info("导入菜单配置，数量: {}", configList.size());
        
        List<SysMenu> menusToSave = new ArrayList<>();
        List<String> errors = new ArrayList<>();
        
        for (DynamicMenuConfigDTO config : configList) {
            try {
                // 验证配置
                List<String> validationErrors = validateMenuConfig(config);
                if (!validationErrors.isEmpty()) {
                    errors.addAll(validationErrors);
                    continue;
                }
                
                SysMenu menu = createMenuFromDTO(config);
                menusToSave.add(menu);
                
            } catch (Exception e) {
                log.error("处理菜单配置失败: {}", config.getName(), e);
                errors.add("菜单 '" + config.getName() + "' 处理失败: " + e.getMessage());
            }
        }
        
        if (!menusToSave.isEmpty()) {
            saveBatch(menusToSave);
        }
        
        String result = String.format("成功导入 %d 个菜单", menusToSave.size());
        if (!errors.isEmpty()) {
            result += String.format("，%d 个错误: %s", errors.size(), String.join("; ", errors));
        }
        
        return result;
    }

    @Override
    public List<DynamicMenuConfigDTO> exportMenuConfig(Long customerId) {
        log.info("导出菜单配置，租户ID: {}", customerId);
        
        List<DynamicMenuVO> menus = getDynamicMenuConfig(customerId);
        return menus.stream()
                .map(this::convertToConfigDTO)
                .collect(Collectors.toList());
    }

    @Override
    public List<String> detectPageChanges() {
        log.info("检测前端页面文件变化");
        return new ArrayList<>();
    }

    @Override
    public DynamicMenuConfigDTO autoGenerateMenu(String routePath, String filePath) {
        log.debug("自动生成菜单配置，路由: {}, 文件: {}", routePath, filePath);
        
        DynamicMenuConfigDTO config = new DynamicMenuConfigDTO();
        
        // 基于文件路径生成菜单名称
        String fileName = Paths.get(filePath).getFileName().toString();
        String menuName = fileName.replaceAll("\\.(vue|tsx|jsx|ts|js)$", "");
        menuName = menuName.replaceAll("[-_]", " ");
        menuName = capitalizeWords(menuName);
        
        config.setName(menuName);
        config.setTitle(menuName);
        config.setRoutePath(routePath);
        config.setComponent(filePath);
        
        // 根据路径层级确定菜单类型
        String[] pathParts = routePath.split("/");
        if (pathParts.length <= 2) {
            config.setType("1"); // 目录
        } else {
            config.setType("2"); // 菜单
        }
        
        // 自动生成图标
        config.setIcon(generateIcon(routePath, fileName));
        config.setIconType("1");
        
        // 默认配置
        config.setStatus("1");
        config.setHide("N");
        
        return config;
    }

    @Override
    public List<String> validateMenuConfig(DynamicMenuConfigDTO config) {
        List<String> errors = new ArrayList<>();
        
        if (!StringUtils.hasText(config.getName())) {
            errors.add("菜单名称不能为空");
        }
        
        if (!StringUtils.hasText(config.getType()) || 
            !Set.of("1", "2", "3").contains(config.getType())) {
            errors.add("菜单类型必须是1(目录)、2(菜单)、3(按钮)");
        }
        
        if ("2".equals(config.getType()) && !StringUtils.hasText(config.getRoutePath())) {
            errors.add("菜单类型为菜单时，路由路径不能为空");
        }
        
        if ("2".equals(config.getType()) && !StringUtils.hasText(config.getComponent())) {
            errors.add("菜单类型为菜单时，组件路径不能为空");
        }
        
        // 检查父菜单是否存在
        if (config.getParentId() != null && config.getParentId() > 0) {
            SysMenu parent = getById(config.getParentId());
            if (parent == null) {
                errors.add("父菜单不存在");
            }
        }
        
        return errors;
    }

    @Override
    public Object getMenuUsageStats(Long customerId) {
        log.info("获取菜单使用统计，租户ID: {}", customerId);
        
        Map<String, Object> stats = new HashMap<>();
        stats.put("totalMenus", countMenus());
        stats.put("enabledMenus", countEnabledMenus());
        stats.put("disabledMenus", countDisabledMenus());
        stats.put("lastScanTime", getLastScanTime());
        
        return stats;
    }

    // ================== 私有方法 ==================

    private boolean isFileIncluded(String filePath, DynamicMenuScanDTO scanDTO) {
        // 检查排除模式
        if (scanDTO.getExcludePatterns() != null) {
            for (String pattern : scanDTO.getExcludePatterns()) {
                if (filePath.matches(pattern.replace("*", ".*"))) {
                    return false;
                }
            }
        }
        
        // 检查包含模式
        if (scanDTO.getIncludePatterns() != null && !scanDTO.getIncludePatterns().isEmpty()) {
            for (String pattern : scanDTO.getIncludePatterns()) {
                if (filePath.matches(pattern.replace("*", ".*"))) {
                    return true;
                }
            }
            return false;
        }
        
        return true;
    }

    private void parseRouteFromFile(Path file, String relativePath, MenuScanResultVO result, DynamicMenuScanDTO scanDTO) {
        try {
            String content = Files.readString(file);
            
            // 提取路由信息
            MenuScanResultVO.RouteInfo routeInfo = new MenuScanResultVO.RouteInfo();
            routeInfo.setFilePath(relativePath);
            
            Matcher routeMatcher = ROUTE_PATTERN.matcher(content);
            if (routeMatcher.find()) {
                routeInfo.setPath(routeMatcher.group(1));
            }
            
            Matcher titleMatcher = TITLE_PATTERN.matcher(content);
            if (titleMatcher.find()) {
                routeInfo.setTitle(titleMatcher.group(1));
            }
            
            Matcher componentMatcher = COMPONENT_PATTERN.matcher(content);
            if (componentMatcher.find()) {
                routeInfo.setComponent(componentMatcher.group(1));
            }
            
            // 如果没有找到路由信息，尝试从文件路径生成
            if (!StringUtils.hasText(routeInfo.getPath())) {
                routeInfo.setPath(generateRouteFromPath(relativePath));
            }
            
            // 检查是否为新路由
            if (StringUtils.hasText(routeInfo.getPath()) && !isMenuExists(routeInfo.getPath())) {
                result.getNewRoutes().add(routeInfo);
            }
            
        } catch (IOException e) {
            log.warn("解析文件失败: {}", relativePath, e);
        }
    }

    private String generateRouteFromPath(String filePath) {
        // 移除文件扩展名
        String route = filePath.replaceAll("\\.(vue|tsx|jsx|ts|js)$", "");
        
        // 移除常见的前缀路径
        route = route.replaceAll("^(src/|views/|pages/|components/)", "");
        
        // 如果是 index 文件，使用父目录名
        if (route.endsWith("/index")) {
            route = route.substring(0, route.length() - 6);
        }
        
        // 确保以 / 开头
        if (!route.startsWith("/")) {
            route = "/" + route;
        }
        
        return route;
    }

    private boolean isMenuExists(String routePath) {
        LambdaQueryWrapper<SysMenu> queryWrapper = new LambdaQueryWrapper<SysMenu>()
                .eq(SysMenu::getRoutePath, routePath);
        
        return count(queryWrapper) > 0;
    }

    private DynamicMenuVO convertToMenuVO(SysMenu menu) {
        DynamicMenuVO vo = new DynamicMenuVO();
        vo.setId(menu.getId());
        vo.setParentId(menu.getParentId());
        vo.setType(menu.getType());
        vo.setName(menu.getName());
        vo.setTitle(menu.getName()); // 使用name作为title
        vo.setI18nKey(menu.getI18nKey());
        vo.setRouteName(menu.getRouteName());
        vo.setRoutePath(menu.getRoutePath());
        vo.setComponent(menu.getComponent());
        vo.setIcon(menu.getIcon());
        vo.setIconType(menu.getIconType());
        vo.setStatus(menu.getStatus());
        vo.setHide(menu.getHide());
        vo.setHref(menu.getHref());
        vo.setSort(menu.getSort());
        vo.setLevel(calculateMenuLevel(menu.getParentId()));
        vo.setIsSystem(false);
        vo.setDeletable(true);
        vo.setEditable(true);
        
        return vo;
    }

    private DynamicMenuConfigDTO convertToConfigDTO(DynamicMenuVO vo) {
        DynamicMenuConfigDTO dto = new DynamicMenuConfigDTO();
        dto.setId(vo.getId());
        dto.setParentId(vo.getParentId());
        dto.setType(vo.getType());
        dto.setName(vo.getName());
        dto.setTitle(vo.getTitle());
        dto.setI18nKey(vo.getI18nKey());
        dto.setRouteName(vo.getRouteName());
        dto.setRoutePath(vo.getRoutePath());
        dto.setComponent(vo.getComponent());
        dto.setIcon(vo.getIcon());
        dto.setIconType(vo.getIconType());
        dto.setStatus(vo.getStatus());
        dto.setHide(vo.getHide());
        dto.setHref(vo.getHref());
        dto.setSort(vo.getSort());
        dto.setLevel(vo.getLevel());
        dto.setIsSystem(vo.getIsSystem());
        dto.setDeletable(vo.getDeletable());
        dto.setEditable(vo.getEditable());
        
        return dto;
    }

    private SysMenu createMenuFromDTO(DynamicMenuConfigDTO dto) {
        SysMenu menu = new SysMenu();
        updateMenuFromDTO(menu, dto);
        return menu;
    }

    private void updateMenuFromDTO(SysMenu menu, DynamicMenuConfigDTO dto) {
        menu.setParentId(dto.getParentId());
        menu.setType(dto.getType());
        menu.setName(dto.getName());
        menu.setI18nKey(dto.getI18nKey());
        menu.setRouteName(dto.getRouteName());
        menu.setRoutePath(dto.getRoutePath());
        menu.setComponent(dto.getComponent());
        menu.setIcon(dto.getIcon());
        menu.setIconType(dto.getIconType());
        menu.setStatus(dto.getStatus());
        menu.setHide(dto.getHide());
        menu.setHref(dto.getHref());
        menu.setIframeUrl(dto.getIframeUrl());
        menu.setSort(dto.getSort());
    }

    private String batchUpdateFields(List<SysMenu> menus, MenuBatchUpdateDTO batchDTO) {
        if (batchDTO.getUpdateFields() == null || batchDTO.getUpdateFields().isEmpty()) {
            return "未指定更新字段";
        }
        
        for (SysMenu menu : menus) {
            batchDTO.getUpdateFields().forEach((field, value) -> {
                switch (field) {
                    case "name":
                        menu.setName(String.valueOf(value));
                        break;
                    case "icon":
                        menu.setIcon(String.valueOf(value));
                        break;
                    case "status":
                        menu.setStatus(String.valueOf(value));
                        break;
                    case "hide":
                        menu.setHide(String.valueOf(value));
                        break;
                    case "sort":
                        menu.setSort(Integer.valueOf(String.valueOf(value)));
                        break;
                    default:
                        log.warn("不支持的更新字段: {}", field);
                }
            });
        }
        
        updateBatchById(menus);
        return String.format("成功批量更新 %d 个菜单的字段", menus.size());
    }

    private String batchUpdateStatus(List<SysMenu> menus, String status) {
        menus.forEach(menu -> menu.setStatus(status));
        updateBatchById(menus);
        return String.format("成功%s %d 个菜单", "1".equals(status) ? "启用" : "禁用", menus.size());
    }

    private String batchDeleteMenus(List<SysMenu> menus, MenuBatchUpdateDTO batchDTO) {
        removeByIds(menus.stream().map(SysMenu::getId).collect(Collectors.toList()));
        return String.format("成功删除 %d 个菜单", menus.size());
    }

    private List<DynamicMenuConfigDTO> loadPresetTemplate(String templateName) {
        // TODO: 从配置文件或数据库加载预设模板
        return new ArrayList<>();
    }

    private Integer calculateMenuLevel(Long parentId) {
        if (parentId == null || parentId == 0) {
            return 1;
        }
        
        SysMenu parent = getById(parentId);
        if (parent == null) {
            return 1;
        }
        
        return calculateMenuLevel(parent.getParentId()) + 1;
    }

    private String capitalizeWords(String str) {
        if (str == null || str.isEmpty()) {
            return str;
        }
        
        return Arrays.stream(str.split(" "))
                .map(word -> word.substring(0, 1).toUpperCase() + word.substring(1).toLowerCase())
                .collect(Collectors.joining(" "));
    }

    private String generateIcon(String routePath, String fileName) {
        // 根据路径和文件名自动生成图标
        String lowerPath = routePath.toLowerCase();
        
        if (lowerPath.contains("user")) return "mdi:account";
        if (lowerPath.contains("system")) return "mdi:cog";
        if (lowerPath.contains("monitor")) return "mdi:monitor-dashboard";
        if (lowerPath.contains("health")) return "mdi:heart-pulse";
        if (lowerPath.contains("data")) return "mdi:database";
        if (lowerPath.contains("report")) return "mdi:chart-line";
        if (lowerPath.contains("setting")) return "mdi:settings";
        if (lowerPath.contains("log")) return "mdi:file-document-outline";
        
        return "mdi:menu"; // 默认图标
    }

    private Long countMenus() {
        return count();
    }

    private Long countEnabledMenus() {
        return count(new LambdaQueryWrapper<SysMenu>()
                .eq(SysMenu::getStatus, "1"));
    }

    private Long countDisabledMenus() {
        return count(new LambdaQueryWrapper<SysMenu>()
                .eq(SysMenu::getStatus, "0"));
    }

    private String getLastScanTime() {
        return LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
    }
    
    /**
     * 解析前端项目路径，支持相对路径和绝对路径
     */
    private String resolveFrontendPath(String inputPath) {
        if (inputPath == null || inputPath.trim().isEmpty()) {
            inputPath = "/src/views";
        }
        
        // 如果是绝对路径，直接返回
        if (Paths.get(inputPath).isAbsolute()) {
            return inputPath;
        }
        
        // 尝试多种路径解析方式
        String[] possibleBasePaths = {
            // 尝试从当前工作目录的上级目录找 ljwx-admin
            "../ljwx-admin" + inputPath,
            // 尝试从项目根目录找 ljwx-admin
            "../../ljwx-admin" + inputPath,
            // 尝试从 release 目录找 ljwx-admin
            "../../../ljwx-admin" + inputPath,
            // 直接从当前目录找（如果ljwx-boot和ljwx-admin在同一目录）
            "../ljwx-admin" + inputPath,
            // 尝试绝对路径构建
            "/Users/brunogao/work/codes/93/release/ljwx-admin" + inputPath
        };
        
        for (String basePath : possibleBasePaths) {
            Path resolvedPath = Paths.get(basePath).normalize();
            if (Files.exists(resolvedPath)) {
                log.info("成功解析前端路径: {} -> {}", inputPath, resolvedPath.toAbsolutePath());
                return resolvedPath.toAbsolutePath().toString();
            }
        }
        
        // 如果所有尝试都失败，返回默认的绝对路径
        String defaultPath = "/Users/brunogao/work/codes/93/release/ljwx-admin" + inputPath;
        log.warn("无法自动解析前端路径，使用默认路径: {}", defaultPath);
        return defaultPath;
    }
}