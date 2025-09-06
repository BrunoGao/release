#!/bin/bash
# 双仓库同步脚本 - 自动推送到GitHub和本地Gitea
# Created: 2025-01-14
# Description: 将代码同步到GitHub（主仓库）和本地Gitea服务器

set -e

echo "🔄 灵境万象系统 - 双仓库同步脚本"

# 配置信息
GITHUB_REMOTE="github"
GITEA_REMOTE="origin" 
MAIN_BRANCH="main"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印彩色信息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查Git状态
check_git_status() {
    print_info "检查Git仓库状态..."
    
    if [ ! -d ".git" ]; then
        print_error "当前目录不是Git仓库"
        exit 1
    fi
    
    # 检查是否有未提交的更改
    if [ -n "$(git status --porcelain)" ]; then
        print_warning "检测到未提交的更改:"
        git status --short
        echo ""
        
        # 检查是否包含构建结果文件
        local has_build_files=false
        if git status --porcelain | grep -E "build-info\.json|\.build\.log|build-history/|data\.sql" >/dev/null; then
            has_build_files=true
            print_info "🔍 发现构建结果文件需要提交"
        fi
        
        read -p "是否要先提交这些更改? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [ "$has_build_files" = true ]; then
                commit_build_changes
            else
                commit_changes
            fi
        else
            print_info "跳过未提交的更改，仅同步已提交的版本"
        fi
    fi
    
    # 获取当前分支
    CURRENT_BRANCH=$(git branch --show-current)
    print_info "当前分支: $CURRENT_BRANCH"
}

# 提交更改
commit_changes() {
    print_info "准备提交当前更改..."
    
    # 显示将要提交的文件
    echo "将要提交的文件:"
    git status --short
    echo ""
    
    # 询问提交信息
    read -p "请输入提交信息: " commit_message
    if [ -z "$commit_message" ]; then
        commit_message="chore: 自动同步提交 $(date +'%Y-%m-%d %H:%M:%S')"
    fi
    
    # 提交更改
    git add .
    git commit -m "$commit_message

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    print_success "更改已提交"
}

# 提交构建结果更改
commit_build_changes() {
    print_info "准备提交构建结果更改..."
    
    # 显示构建相关文件
    echo "构建相关文件:"
    git status --short | grep -E "build-info\.json|\.build\.log|build-history/|data\.sql" || echo "  (无构建文件变化)"
    echo ""
    echo "其他文件:"
    git status --short | grep -vE "build-info\.json|\.build\.log|build-history/|data\.sql" || echo "  (无其他文件变化)"
    echo ""
    
    # 获取构建版本信息（如果存在）
    local build_version="unknown"
    local git_commit="unknown"
    if [ -f ".build-info.json" ]; then
        if command -v jq >/dev/null 2>&1; then
            build_version=$(jq -r '.build.version // "unknown"' .build-info.json 2>/dev/null || echo "unknown")
            git_commit=$(jq -r '.git.commit.short // "unknown"' .build-info.json 2>/dev/null || echo "unknown")
        fi
    fi
    
    # 询问提交信息
    read -p "请输入提交信息 (留空使用默认): " commit_message
    if [ -z "$commit_message" ]; then
        commit_message="build: 同步构建结果 $build_version ($git_commit)"
    fi
    
    # 提交更改
    git add .
    local full_commit_message="$commit_message

📦 构建同步信息:
- 构建版本: $build_version
- 源代码提交: $git_commit  
- 同步时间: $(date +'%Y-%m-%d %H:%M:%S')

🎯 包含文件:
$(git status --short | sed 's/^/- /')

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    git commit -m "$full_commit_message"
    print_success "构建结果已提交"
}

# 检查远程仓库配置
check_remotes() {
    print_info "检查远程仓库配置..."
    
    # 检查GitHub远程仓库
    if ! git remote get-url $GITHUB_REMOTE >/dev/null 2>&1; then
        print_error "GitHub远程仓库 '$GITHUB_REMOTE' 未配置"
        print_info "请先运行: git remote add $GITHUB_REMOTE git@github.com:BrunoGao/release.git"
        exit 1
    fi
    
    # 检查Gitea远程仓库  
    if ! git remote get-url $GITEA_REMOTE >/dev/null 2>&1; then
        print_error "Gitea远程仓库 '$GITEA_REMOTE' 未配置"
        exit 1
    fi
    
    print_success "远程仓库配置正常"
    echo "📋 远程仓库列表:"
    git remote -v | grep -E "(github|origin)"
}

# 获取Git信息用于跟踪
get_sync_info() {
    GIT_COMMIT=$(git rev-parse HEAD)
    GIT_COMMIT_SHORT=$(git rev-parse --short HEAD)
    GIT_BRANCH=$(git branch --show-current)
    GIT_MESSAGE=$(git log -1 --pretty=format:"%s")
    SYNC_TIME=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    
    print_info "同步信息:"
    echo "   提交: $GIT_COMMIT_SHORT"
    echo "   分支: $GIT_BRANCH"  
    echo "   消息: $GIT_MESSAGE"
    echo "   时间: $SYNC_TIME"
}

# 推送到GitHub（主仓库）
push_to_github() {
    print_info "推送到GitHub主仓库..."
    
    # 先获取最新代码避免冲突
    if git ls-remote --exit-code --heads $GITHUB_REMOTE $CURRENT_BRANCH >/dev/null 2>&1; then
        print_info "从GitHub拉取最新代码..."
        git fetch $GITHUB_REMOTE $CURRENT_BRANCH
        
        # 检查是否需要合并
        BEHIND=$(git rev-list --count HEAD..$GITHUB_REMOTE/$CURRENT_BRANCH 2>/dev/null || echo "0")
        if [ "$BEHIND" -gt 0 ]; then
            print_warning "本地分支落后GitHub $BEHIND 个提交"
            print_info "尝试自动合并..."
            git merge $GITHUB_REMOTE/$CURRENT_BRANCH --no-edit
        fi
    fi
    
    # 推送到GitHub
    print_info "推送到GitHub: $CURRENT_BRANCH"
    if git push $GITHUB_REMOTE $CURRENT_BRANCH; then
        print_success "GitHub推送成功"
        GITHUB_SUCCESS=true
    else
        print_error "GitHub推送失败"
        GITHUB_SUCCESS=false
    fi
}

# 推送到Gitea（备用仓库）
push_to_gitea() {
    print_info "推送到Gitea备用仓库..."
    
    # 推送到Gitea
    print_info "推送到Gitea: $CURRENT_BRANCH"
    if git push $GITEA_REMOTE $CURRENT_BRANCH; then
        print_success "Gitea推送成功"
        GITEA_SUCCESS=true
    else
        print_error "Gitea推送失败"
        GITEA_SUCCESS=false
    fi
}

# 推送标签
push_tags() {
    print_info "同步Git标签..."
    
    # 检查是否有标签
    if git tag -l | wc -l | grep -q "0"; then
        print_info "没有标签需要推送"
        return
    fi
    
    # 推送标签到GitHub
    if [ "$GITHUB_SUCCESS" = true ]; then
        print_info "推送标签到GitHub..."
        git push $GITHUB_REMOTE --tags
    fi
    
    # 推送标签到Gitea
    if [ "$GITEA_SUCCESS" = true ]; then
        print_info "推送标签到Gitea..."
        git push $GITEA_REMOTE --tags
    fi
}

# 记录同步日志
log_sync() {
    local sync_log=".sync.log"
    local status="SUCCESS"
    
    if [ "$GITHUB_SUCCESS" != true ] || [ "$GITEA_SUCCESS" != true ]; then
        status="PARTIAL"
    fi
    
    if [ "$GITHUB_SUCCESS" != true ] && [ "$GITEA_SUCCESS" != true ]; then
        status="FAILED"
    fi
    
    echo "[$SYNC_TIME] $status: $GIT_COMMIT_SHORT ($GIT_BRANCH) -> GitHub:$GITHUB_SUCCESS, Gitea:$GITEA_SUCCESS - $GIT_MESSAGE" >> "$sync_log"
}

# 生成同步报告
generate_sync_report() {
    echo ""
    echo "📊 同步结果报告:"
    echo "   时间: $SYNC_TIME"
    echo "   提交: $GIT_COMMIT_SHORT ($GIT_BRANCH)"
    echo "   消息: $GIT_MESSAGE"
    
    # 显示构建信息（如果存在）
    if [ -f ".build-info.json" ]; then
        local build_version="unknown"
        if command -v jq >/dev/null 2>&1; then
            build_version=$(jq -r '.build.version // "unknown"' .build-info.json 2>/dev/null || echo "unknown")
        fi
        echo "   构建版本: $build_version"
        echo "   📦 包含构建结果文件"
    fi
    
    echo ""
    echo "📤 推送结果:"
    if [ "$GITHUB_SUCCESS" = true ]; then
        print_success "   GitHub: 推送成功 ✅"
        echo "   GitHub URL: https://github.com/BrunoGao/release/commit/$GIT_COMMIT"
    else
        print_error "   GitHub: 推送失败 ❌"
    fi
    
    if [ "$GITEA_SUCCESS" = true ]; then
        print_success "   Gitea: 推送成功 ✅"
        echo "   Gitea URL: http://192.168.1.83:33000/bruno/release/commit/$GIT_COMMIT"
    else
        print_error "   Gitea: 推送失败 ❌"
    fi
    
    echo ""
    echo "📋 跟踪文件:"
    if [ -f ".build-info.json" ]; then
        echo "   构建信息: .build-info.json"
    fi
    if [ -f ".build.log" ]; then
        echo "   构建日志: .build.log"
    fi
    if [ -f ".sync.log" ]; then
        echo "   同步日志: .sync.log"
    fi
    if [ -d "build-history" ]; then
        echo "   构建历史: build-history/"
    fi
}

# 主函数
main() {
    case "${1:-sync}" in
        "sync")
            check_git_status
            check_remotes
            get_sync_info
            
            echo ""
            print_info "开始双仓库同步..."
            
            # 推送到两个仓库
            push_to_github
            push_to_gitea
            
            # 推送标签
            push_tags
            
            # 记录和报告
            log_sync
            generate_sync_report
            ;;
        "status")
            check_git_status
            check_remotes
            get_sync_info
            ;;
        "github")
            check_git_status
            check_remotes
            get_sync_info
            push_to_github
            log_sync
            generate_sync_report
            ;;
        "gitea")
            check_git_status
            check_remotes  
            get_sync_info
            push_to_gitea
            log_sync
            generate_sync_report
            ;;
        "help"|"-h"|"--help")
            echo "使用方法:"
            echo "   $0 [sync]     # 同步到两个仓库(默认)"
            echo "   $0 github     # 仅推送到GitHub"
            echo "   $0 gitea      # 仅推送到Gitea"
            echo "   $0 status     # 检查状态"
            echo "   $0 help       # 显示帮助"
            echo ""
            echo "远程仓库:"
            echo "   GitHub: git@github.com:BrunoGao/release.git"
            echo "   Gitea:  http://192.168.1.83:33000/bruno/release.git"
            ;;
        *)
            print_error "未知命令: $1"
            echo "使用 '$0 help' 查看帮助"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"