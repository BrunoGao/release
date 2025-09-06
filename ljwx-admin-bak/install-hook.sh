#!/bin/bash
# Created Time:    2025-04-19 13:39:02
# Modified Time:   2025-04-19 13:39:14
#set -e # 这告诉bash一但有任何一个语句返回非真的值，则退出bash。
#!/bin/bash

echo "🔧 安装 Gitea Hook 到当前仓库..."

HOOK_SRC="$HOME/.git-templates/hooks/post-commit"
HOOK_DST="$(git rev-parse --show-toplevel)/.git/hooks/post-commit"

if [ ! -f "$HOOK_SRC" ]; then
  echo "❌ 源 hook 文件不存在：$HOOK_SRC"
  exit 1
fi

cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"

echo "✅ 安装完成: $HOOK_DST"
