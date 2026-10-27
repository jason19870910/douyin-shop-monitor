s = open('/tmp/original_fetcher.py', encoding='utf-8').read()
print('has fix1:', "token = _read_secret('token', '__TOKEN') or _read_secret('token', 'TOKEN')" in s)
print('has fix2:', '业务错误码' in s)
print('line endings CRLF:', '\r\n' in s)
