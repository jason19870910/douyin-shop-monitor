#!/usr/bin/env python3
"""
生成版本信息文件，供 Docker 构建时复制使用。
在宿主机运行（有 .git 目录），输出到 src/backend/data/ 目录。

注意：app 容器存在 ./data:/data bind mount，会遮蔽镜像内 /data/version_info.json，
因此部署流程（scripts/deploy.sh 或 CI deploy job）必须再以服务器 data 目录为
输出目录运行一次，刷新 bind mount 下的副本。

用法:
    python generate_version_info.py [输出目录]

省略输出目录时默认写到 src/backend/data/（构建上下文副本）；
传入 /opt/douyin-platform/data 可直接刷新服务器 bind mount 副本。
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_git(cmd: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def get_version_info(repo_root: Path) -> dict:
    # 版本号：优先取最新 tag，否则用 commit 短哈希
    tag = run_git(["git", "describe", "--tags", "--always", "--dirty"], repo_root)
    if not tag:
        tag = run_git(["git", "rev-parse", "--short", "HEAD"], repo_root) or "dev"
    
    # 完整 commit hash
    commit = run_git(["git", "rev-parse", "HEAD"], repo_root) or "unknown"
    
    # 构建时间（ISO 8601，UTC）
    built_at = datetime.utcnow().isoformat() + "Z"
    
    return {
        "version": tag,
        "commit": commit,
        "builtAt": built_at,
    }


def get_changes_info(repo_root: Path, limit: int = 20) -> list[dict]:
    """获取最近的 git log 作为变更记录"""
    # 格式：commit hash, subject, author, date (ISO), type (from conventional commits)
    log_format = '%h|%s|%an|%aI|%b'
    output = run_git(["git", "log", f"-{limit}", f"--pretty=format:{log_format}"], repo_root)
    
    changes = []
    if not output:
        return changes
    
    for line in output.split('\n'):
        if not line.strip():
            continue
        parts = line.split('|', 4)
        if len(parts) < 4:
            continue
        
        commit_hash, message, author, date_str = parts[0], parts[1], parts[2], parts[3]
        body = parts[4] if len(parts) > 4 else ""
        
        # 从 conventional commits 推断类型
        change_type = "chore"
        if message.startswith("feat"):
            change_type = "feat"
        elif message.startswith("fix"):
            change_type = "fix"
        elif message.startswith("docs"):
            change_type = "docs"
        elif message.startswith("refactor"):
            change_type = "refactor"
        elif message.startswith("test"):
            change_type = "test"
        elif message.startswith("chore"):
            change_type = "chore"
        
        changes.append({
            "id": commit_hash,
            "message": message,
            "author": author,
            "date": date_str,
            "type": change_type,
        })
    
    return changes


def main():
    # 项目根目录（包含 .git 的目录）
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent  # scripts/ 的父目录
    
    # 输出目录：命令行为服务器 data 目录；默认 src/backend/data/（构建上下文副本）
    if len(sys.argv) > 1:
        output_dir = Path(sys.argv[1]).resolve()
    else:
        output_dir = repo_root / "src" / "backend" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成 version_info.json
    version_info = get_version_info(repo_root)
    version_file = output_dir / "version_info.json"
    version_file.write_text(json.dumps(version_info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated: {version_file}")
    print(f"  Version: {version_info['version']}")
    print(f"  Commit:  {version_info['commit']}")
    print(f"  Built:   {version_info['builtAt']}")
    
    # 生成 changes_info.json
    changes = get_changes_info(repo_root)
    changes_file = output_dir / "changes_info.json"
    changes_file.write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated: {changes_file} ({len(changes)} changes)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())