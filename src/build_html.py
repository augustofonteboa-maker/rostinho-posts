import json
d=json.load(open('src/data.json'))
d['plan']=json.load(open('src/plan.json'))
d=json.dumps(d,ensure_ascii=False).replace('</','<\\/')
t=open('src/template.html').read().replace('__DATA__',d)
open('index.html','w').write(t); print(len(t))
