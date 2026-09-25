import pathlib, re
p = pathlib.Path('/opt/douyin-platform/config/.env')
txt = p.read_text()
txt = re.sub(r'^FXG_LOG_ID=.*', 'FXG_LOG_ID=104476165896', txt, flags=re.M)
p.write_text(txt)
