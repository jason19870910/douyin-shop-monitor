p = '/tmp/original_fetcher.py'
lines = open(p, encoding='utf-8').read().splitlines(keepends=True)
out = []
i = 0
n = len(lines)
fixed1 = False
fixed2 = False

while i < n:
    line = lines[i]

    # 修复 1：token 降级读取
    if "token = _read_secret('token', '__TOKEN')" in line and not fixed1:
        out.append("    token = _read_secret('token', '__TOKEN') or _read_secret('token', 'TOKEN')\n")
        fixed1 = True
        i += 1
        continue

    # 修复 2：在 _request 失败检查之后插入业务错误码检测
    if ("# _request 失败时返回 {'data': {}, 'error': ...}，需检查" in line and not fixed2):
        # 复制当前这三行（注释、if、raise）
        out.append(line)
        i += 1
        out.append(lines[i])  # if isinstance...
        i += 1
        out.append(lines[i])  # raise ...
        i += 1
        # 插入业务错误码检测块
        out.append('\n')
        out.append("    # 检测 FXG API 业务错误码（HTTP 200 但返回业务错误，如 code: 10008 登录失效）\n")
        out.append("    if isinstance(result, dict):\n")
        out.append("        api_code = result.get('code')\n")
        out.append("        if api_code is not None and str(api_code) not in ('0', '200', 'success'):\n")
        out.append("            raise requests.RequestException(f\"External API error: code={api_code}, msg={result.get('msg', '')}\")\n")
        out.append('\n')
        fixed2 = True
        continue

    out.append(line)
    i += 1

assert fixed1, 'fix1 not applied'
assert fixed2, 'fix2 not applied'
open(p, 'w', encoding='utf-8').writelines(out)
print('patched both fixes (line-based)')
