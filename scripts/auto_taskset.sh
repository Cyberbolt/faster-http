#!/bin/bash

# 简单版自动taskset脚本
# 用法: ./auto_taskset.sh "command"

if [ $# -eq 0 ]; then
    echo "用法: $0 \"command\""
    echo "示例: $0 \"echo Hello\""
    exit 1
fi

# 获取CPU核心数
cores=$(nproc)
echo "系统有 $cores 个CPU核心"

# 简单策略：避开核心0，轮询选择其他核心
if [ "$cores" -gt 1 ]; then
    # 随机选择1到cores-1之间的核心
    core=$((1 + RANDOM % (cores - 1)))
else
    core=0
fi

echo "选择CPU核心: $core"
echo "执行: taskset -c $core $1"

# 执行命令
taskset -c $core $1