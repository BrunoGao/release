#!/bin/bash
# 日志查看工具

show_help() {
    echo "日志查看工具"
    echo "用法: $0 [服务名] [选项]"
    echo ""
    echo "服务名:"
    echo "  gitea      查看Gitea日志"
    echo "  jenkins    查看Jenkins日志"
    echo "  registry   查看Registry日志"
    echo "  all        查看所有服务日志"
    echo ""
    echo "选项:"
    echo "  -f, --follow    实时跟随日志"
    echo "  -n NUM         显示最近NUM行日志"
    echo ""
    echo "示例:"
    echo "  $0 jenkins -f      # 实时查看Jenkins日志"
    echo "  $0 all -n 100      # 查看所有服务最近100行日志"
}

case "${1:-help}" in
    "gitea")
        docker logs jenkins-simple "${@:2}"
        ;;
    "jenkins")
        docker logs jenkins-simple "${@:2}"
        ;;
    "registry")
        docker logs registry "${@:2}"
        ;;
    "all")
        echo "=== Gitea日志 ==="
        docker logs gitea "${@:2}" | tail -20
        echo ""
        echo "=== Jenkins日志 ==="
        docker logs jenkins-simple "${@:2}" | tail -20
        echo ""
        echo "=== Registry日志 ==="
        docker logs registry "${@:2}" | tail -20
        ;;
    "help"|*)
        show_help
        ;;
esac