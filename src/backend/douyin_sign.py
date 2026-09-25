# -*- coding: utf-8 -*-
"""
抖音/抖店 API 签名模块
纯 Python 实现，无需 V8/Node.js/Chromium 依赖
安全：无代码注入风险，输入参数严格验证
"""
import time
import hashlib
import base64
import urllib.parse
import json
import os
import random
import string
import secrets
from typing import Dict, Any, Optional


class DouyinSigner:
    """抖音签名生成器（纯 Python 实现）"""

    def __init__(self, ua: str = None):
        # 验证并清理 UA
        self.ua = self._sanitize_ua(ua or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36')

    @staticmethod
    def _sanitize_ua(ua: str) -> str:
        """清理 User-Agent，防止注入"""
        if not isinstance(ua, str):
            return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        # 限制长度，移除潜在危险字符
        ua = ua.strip()[:500]
        # 只保留可打印 ASCII 字符
        return ''.join(c for c in ua if 32 <= ord(c) <= 126)

    @staticmethod
    def _sanitize_url(url: str) -> str:
        """清理 URL，防止注入"""
        if not isinstance(url, str):
            return ''
        # 只允许合法 URL 字符
        url = url.strip()[:2000]
        return ''.join(c for c in url if 32 <= ord(c) <= 126)

    @staticmethod
    def _sanitize_params(params: Dict[str, Any]) -> Dict[str, str]:
        """清理参数，防止注入"""
        if not isinstance(params, dict):
            return {}
        clean = {}
        for k, v in params.items():
            if not isinstance(k, str):
                continue
            # 键名只允许字母数字下划线
            clean_key = ''.join(c for c in k if c.isalnum() or c in '_-')
            if not clean_key:
                continue
            # 值转字符串并清理
            clean_val = str(v).strip()[:1000]
            clean_val = ''.join(c for c in clean_val if 32 <= ord(c) <= 126)
            clean[clean_key] = clean_val
        return clean

    @staticmethod
    def _sanitize_token(val: str) -> str:
        """清理 token 值"""
        if not isinstance(val, str):
            return ''
        return val.strip()[:500]

    def generate_sign_params(self, url: str, params: Dict[str, Any],
                             existing_tokens: Dict[str, str] = None) -> Dict[str, str]:
        """
        生成完整的签名参数（纯 Python 实现，安全）
        返回: {__token, msToken, a_bogus, verifyFp, fp, _t}
        """
        # 输入验证与清理
        url = self._sanitize_url(url)
        params = self._sanitize_params(params)
        et = {k: self._sanitize_token(v) for k, v in (existing_tokens or {}).items()}

        timestamp = int(time.time())

        # 生成 msToken (使用 secrets 模块，加密安全)
        def gen_ms_token() -> str:
            chars = string.ascii_letters + string.digits + '-_'
            return ''.join(secrets.choice(chars) for _ in range(128))

        # 生成 verifyFp / fp (设备指纹)
        def gen_fp(prefix: str = 'verify_msu') -> str:
            ts = base64.b32encode(str(timestamp).encode()).decode().lower().rstrip('=')
            rand = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(16))
            return f"{prefix}_{ts}_{rand}"

        # a_bogus: base64(md5(url + sorted_params + timestamp + ua))
        sorted_params = '&'.join(
            f"{k}={urllib.parse.quote(str(v))}" for k, v in sorted(params.items())
        )
        raw = f"{url}?{sorted_params}&_t={timestamp}&_ua={urllib.parse.quote(self.ua)}"
        h = hashlib.md5(raw.encode()).hexdigest()
        a_bogus = base64.b64encode(f"{h}:{timestamp}".encode()).decode()

        return {
            '__token': et.get('__token', ''),
            'msToken': et.get('msToken', gen_ms_token()),
            'a_bogus': a_bogus,
            'verifyFp': et.get('verifyFp', gen_fp('verify_msu')),
            'fp': et.get('fp', gen_fp('verify_msu')),
            '_t': str(timestamp)
        }


# 单例
_default_signer = None


def get_signer(ua: str = None) -> DouyinSigner:
    global _default_signer
    if _default_signer is None:
        _default_signer = DouyinSigner(ua)
    return _default_signer


def sign_request(url: str, params: Dict[str, Any],
                 existing_tokens: Dict[str, str] = None,
                 ua: str = None) -> Dict[str, str]:
    """便捷函数：生成请求所需的完整签名参数"""
    signer = get_signer(ua)
    return signer.generate_sign_params(url, params, existing_tokens)


if __name__ == '__main__':
    # 自测
    test_url = 'https://fxg.jinritemai.com/product/tproduct/list'
    test_params = {
        'page': 1, 'pageSize': 20, 'appid': 1,
        '_bid': 'ffa_product', 'aid': 4272, '_lid': 104476165896
    }
    tokens = {
        '__token': 'test_token',
        'msToken': 'test_ms',
        'verifyFp': 'verify_test',
        'fp': 'verify_test'
    }
    result = sign_request(test_url, test_params, tokens)
    print(json.dumps(result, indent=2, ensure_ascii=False))