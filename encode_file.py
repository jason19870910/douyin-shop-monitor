import base64
with open(r'c:\Users\Administrator\Documents\trae_projects\douyin\src\backend\blueprints\creators.py', 'rb') as f:
    content = f.read()
encoded = base64.b64encode(content).decode()
with open(r'c:\Users\Administrator\Documents\trae_projects\douyin\creators_b64.txt', 'w') as f:
    f.write(encoded)
print("Done")