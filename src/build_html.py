import json
d=open('src/data.json').read()
d=json.dumps(json.loads(d),ensure_ascii=False).replace('</','<\\/')
t=open('src/template.html').read().replace('__DATA__',d)
open('index.html','w').write(t); print(len(t))
