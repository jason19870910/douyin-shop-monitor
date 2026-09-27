#!/usr/bin/env python3
"""
Markdown 链接检查脚本
检查文档内部链接和外部链接的有效性
"""

import os
import re
import sys
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import List, Tuple, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

class LinkChecker:
    def __init__(self, docs_root: Path, timeout: int = 10, max_workers: int = 10):
        self.docs_root = docs_root
        self.timeout = timeout
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'DocLinkChecker/1.0'})
        
        # 缓存外部链接检查结果
        self.external_cache: dict = {}
        
    def find_markdown_files(self) -> List[Path]:
        """查找所有 Markdown 文件"""
        md_files = list(self.docs_root.rglob('*.md'))
        exclude_patterns = ['archive', 'templates', '.vitepress', 'node_modules']
        return [
            f for f in md_files
            if not any(p in str(f) for p in exclude_patterns)
        ]
    
    def extract_links(self, content: str, base_path: Path) -> List[Tuple[str, str, int]]:
        """提取 Markdown 中的所有链接
        返回: [(链接文本, 链接目标, 行号), ...]
        """
        links = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 匹配 [text](url) 格式
            for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line):
                text = match.group(1)
                url = match.group(2).strip()
                # 跳过图片链接
                if line[match.start()-1:match.start()] == '!':
                    continue
                links.append((text, url, line_num))
            
            # 匹配裸 URL
            for match in re.finditer(r'(?<!\]\()https?://[^\s\)]+', line):
                url = match.group(0).rstrip('.,;)')
                links.append((url, url, line_num))
        
        return links
    
    def resolve_internal_link(self, link: str, source_file: Path) -> Path:
        """解析内部链接为绝对路径"""
        # 移除锚点
        link_path = link.split('#')[0]
        
        if not link_path:
            # 只有锚点，指向当前文件
            return source_file
        
        if link_path.startswith('/'):
            # 绝对路径（相对于 docs 根目录）
            return self.docs_root / link_path.lstrip('/')
        else:
            # 相对路径
            return (source_file.parent / link_path).resolve()
    
    def check_internal_link(self, link: str, source_file: Path) -> Tuple[bool, str]:
        """检查内部链接"""
        try:
            target_path = self.resolve_internal_link(link, source_file)
            
            # 检查文件是否存在
            if not target_path.exists():
                return False, f"文件不存在: {target_path.relative_to(self.docs_root)}"
            
            # 如果有锚点，检查锚点是否存在
            if '#' in link:
                anchor = link.split('#')[1]
                content = target_path.read_text(encoding='utf-8')
                # 简单检查：查找对应的标题
                anchor_pattern = rf'^#+\s+{re.escape(anchor.replace("-", " "))}'
                if not re.search(anchor_pattern, content, re.MULTILINE | re.IGNORECASE):
                    # 尝试匹配中文标题
                    return False, f"锚点不存在: #{anchor}"
            
            return True, "OK"
        except Exception as e:
            return False, f"解析错误: {e}"
    
    def check_external_link(self, url: str) -> Tuple[bool, str]:
        """检查外部链接"""
        if url in self.external_cache:
            return self.external_cache[url]
        
        try:
            # HEAD 请求更轻量
            resp = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            if resp.status_code < 400:
                result = (True, f"HTTP {resp.status_code}")
            else:
                # 尝试 GET 请求
                resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                if resp.status_code < 400:
                    result = (True, f"HTTP {resp.status_code} (GET)")
                else:
                    result = (False, f"HTTP {resp.status_code}")
        except requests.exceptions.Timeout:
            result = (False, "连接超时")
        except requests.exceptions.ConnectionError:
            result = (False, "连接失败")
        except requests.exceptions.TooManyRedirects:
            result = (False, "重定向过多")
        except Exception as e:
            result = (False, f"错误: {type(e).__name__}")
        
        self.external_cache[url] = result
        return result
    
    def check_file(self, filepath: Path) -> List[dict]:
        """检查单个文件的所有链接"""
        try:
            content = filepath.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return [{'file': str(filepath), 'error': '编码错误'}]
        
        links = self.extract_links(content, filepath)
        results = []
        
        for text, url, line_num in links:
            is_external = url.startswith('http://') or url.startswith('https://')
            is_mailto = url.startswith('mailto:')
            is_anchor_only = url.startswith('#')
            
            if is_mailto:
                continue  # 跳过邮件链接
            
            if is_external:
                valid, msg = self.check_external_link(url)
                link_type = 'external'
            else:
                valid, msg = self.check_internal_link(url, filepath)
                link_type = 'internal'
            
            if not valid:
                results.append({
                    'file': str(filepath.relative_to(self.docs_root)),
                    'line': line_num,
                    'text': text,
                    'url': url,
                    'type': link_type,
                    'error': msg
                })
        
        return results
    
    def run(self) -> List[dict]:
        """运行完整检查"""
        md_files = self.find_markdown_files()
        print(f"检查 {len(md_files)} 个文件的链接...")
        
        all_errors = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.check_file, f): f 
                for f in md_files
            }
            
            for future in as_completed(future_to_file):
                errors = future.result()
                all_errors.extend(errors)
        
        return all_errors

def main():
    docs_root = Path(__file__).parent.parent
    checker = LinkChecker(docs_root)
    errors = checker.run()
    
    if errors:
        print(f"\n❌ 发现 {len(errors)} 个无效链接:\n")
        # 按文件分组显示
        by_file = {}
        for err in errors:
            fname = err['file']
            if fname not in by_file:
                by_file[fname] = []
            by_file[fname].append(err)
        
        for fname, file_errors in sorted(by_file.items()):
            print(f"📄 {fname}")
            for err in file_errors:
                print(f"  第 {err['line']} 行: [{err['text']}]({err['url']})")
                print(f"    类型: {err['type']}, 错误: {err['error']}")
            print()
        sys.exit(1)
    else:
        print("\n✅ 所有链接检查通过")
        sys.exit(0)

if __name__ == '__main__':
    main()
EOF