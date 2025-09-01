import 'package:flutter/material.dart';
import 'package:ljwx_health_new/design_system/design_system.dart';

/// 企业级搜索栏组件
/// 提供统一的搜索界面和功能
class EnterpriseSearchBar extends StatefulWidget {
  final String? hintText;
  final ValueChanged<String>? onChanged;
  final VoidCallback? onFilterPressed;
  final bool showFilter;
  final TextEditingController? controller;
  final bool enabled;
  final Widget? prefixIcon;
  final Widget? suffixIcon;

  const EnterpriseSearchBar({
    super.key,
    this.hintText,
    this.onChanged,
    this.onFilterPressed,
    this.showFilter = false,
    this.controller,
    this.enabled = true,
    this.prefixIcon,
    this.suffixIcon,
  });

  @override
  State<EnterpriseSearchBar> createState() => _EnterpriseSearchBarState();
}

class _EnterpriseSearchBarState extends State<EnterpriseSearchBar>
    with SingleTickerProviderStateMixin {
  late TextEditingController _controller;
  late AnimationController _animationController;
  late Animation<double> _scaleAnimation;
  bool _isActive = false;

  @override
  void initState() {
    super.initState();
    _controller = widget.controller ?? TextEditingController();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 200),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 1.02,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    if (widget.controller == null) {
      _controller.dispose();
    }
    _animationController.dispose();
    super.dispose();
  }

  void _onFocusChanged(bool hasFocus) {
    setState(() {
      _isActive = hasFocus;
    });
    if (hasFocus) {
      _animationController.forward();
    } else {
      _animationController.reverse();
    }
  }

  void _clearSearch() {
    _controller.clear();
    widget.onChanged?.call('');
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: AnimatedBuilder(
        animation: _scaleAnimation,
        builder: (context, child) {
          return Transform.scale(
            scale: _scaleAnimation.value,
            child: Container(
              decoration: BoxDecoration(
                color: isDark ? DSColors.cardDark : DSColors.cardLight,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: (isDark ? DSColors.shadowDark : DSColors.shadowLight)
                        .withOpacity(_isActive ? 0.3 : 0.1),
                    blurRadius: _isActive ? 12 : 6,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Row(
                children: [
                  // 搜索输入框
                  Expanded(
                    child: Focus(
                      onFocusChange: _onFocusChanged,
                      child: TextField(
                        controller: _controller,
                        enabled: widget.enabled,
                        onChanged: widget.onChanged,
                        style: DSTypography.bodyMedium.copyWith(
                          color: isDark 
                              ? DSColors.textPrimaryDark 
                              : DSColors.textPrimaryLight,
                        ),
                        decoration: InputDecoration(
                          hintText: widget.hintText ?? '搜索...',
                          hintStyle: DSTypography.bodyMedium.copyWith(
                            color: isDark 
                                ? DSColors.textTertiaryDark 
                                : DSColors.textTertiaryLight,
                          ),
                          prefixIcon: widget.prefixIcon ?? Icon(
                            Icons.search_rounded,
                            color: _isActive 
                                ? DSColors.primary500 
                                : (isDark 
                                    ? DSColors.textSecondaryDark 
                                    : DSColors.textSecondaryLight),
                            size: 20,
                          ),
                          suffixIcon: _controller.text.isNotEmpty
                              ? IconButton(
                                  icon: Icon(
                                    Icons.clear_rounded,
                                    color: isDark 
                                        ? DSColors.textSecondaryDark 
                                        : DSColors.textSecondaryLight,
                                    size: 20,
                                  ),
                                  onPressed: _clearSearch,
                                  padding: const EdgeInsets.all(8),
                                  constraints: const BoxConstraints(),
                                )
                              : widget.suffixIcon,
                          border: InputBorder.none,
                          enabledBorder: InputBorder.none,
                          focusedBorder: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 12,
                          ),
                        ),
                      ),
                    ),
                  ),
                  
                  // 筛选按钮（可选）
                  if (widget.showFilter && widget.onFilterPressed != null) ...[
                    Container(
                      height: 40,
                      width: 1,
                      color: isDark ? DSColors.borderDark : DSColors.borderLight,
                      margin: const EdgeInsets.symmetric(vertical: 8),
                    ),
                    IconButton(
                      icon: Icon(
                        Icons.tune_rounded,
                        color: _isActive 
                            ? DSColors.primary500 
                            : (isDark 
                                ? DSColors.textSecondaryDark 
                                : DSColors.textSecondaryLight),
                        size: 20,
                      ),
                      onPressed: widget.onFilterPressed,
                      padding: const EdgeInsets.all(12),
                      constraints: const BoxConstraints(),
                      tooltip: '筛选',
                    ),
                  ],
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

/// 搜索结果高亮组件
class SearchHighlight extends StatelessWidget {
  final String text;
  final String searchQuery;
  final TextStyle? style;
  final TextStyle? highlightStyle;

  const SearchHighlight({
    super.key,
    required this.text,
    required this.searchQuery,
    this.style,
    this.highlightStyle,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final defaultStyle = style ?? theme.textTheme.bodyMedium!;
    final defaultHighlightStyle = highlightStyle ?? 
        defaultStyle.copyWith(
          backgroundColor: DSColors.warning200,
          fontWeight: FontWeight.bold,
        );

    if (searchQuery.isEmpty) {
      return Text(text, style: defaultStyle);
    }

    final spans = <TextSpan>[];
    final String lowerText = text.toLowerCase();
    final String lowerQuery = searchQuery.toLowerCase();
    
    int start = 0;
    int index = lowerText.indexOf(lowerQuery);
    
    while (index != -1) {
      // 添加匹配前的文本
      if (index > start) {
        spans.add(TextSpan(
          text: text.substring(start, index),
          style: defaultStyle,
        ));
      }
      
      // 添加高亮的匹配文本
      spans.add(TextSpan(
        text: text.substring(index, index + searchQuery.length),
        style: defaultHighlightStyle,
      ));
      
      start = index + searchQuery.length;
      index = lowerText.indexOf(lowerQuery, start);
    }
    
    // 添加剩余文本
    if (start < text.length) {
      spans.add(TextSpan(
        text: text.substring(start),
        style: defaultStyle,
      ));
    }
    
    return RichText(
      text: TextSpan(children: spans),
    );
  }
}