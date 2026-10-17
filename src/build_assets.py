import json, os, zipfile, unicodedata, re
from PIL import Image
SRC='/mnt/user-data/uploads/CRIATIVOS/'
d=json.load(open('src/posts.json'))
os.makedirs('img/full',exist_ok=True); os.makedirs('img/web',exist_ok=True); os.makedirs('zip',exist_ok=True)
def slug(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+','-',s).strip('-')
out=[]
for p in d['posts']:
    slides=[]
    for i,f in enumerate(p['files'],1):
        im=Image.open(SRC+f).convert('RGB')
        base=f"rostinho-{p['id']}" + (f"-{i}" if len(p['files'])>1 else '')
        full=f'img/full/{base}.png'
        if not os.path.exists(full): im.save(full,optimize=True)
        w=900; h=round(im.height*w/im.width)
        web=f'img/web/{base}.webp'
        im.resize((w,h),Image.LANCZOS).save(web,'WEBP',quality=82,method=6)
        tint='#%02x%02x%02x'%im.resize((1,1),Image.BOX).getpixel((0,0))
        corner='#%02x%02x%02x'%im.crop((0,0,60,60)).resize((1,1),Image.BOX).getpixel((0,0))
        slides.append({'full':full,'web':web,'w':im.width,'h':im.height,'bg':corner,'bytes':os.path.getsize(full)})
    p2={k:v for k,v in p.items() if k!='files'}; p2['slides']=slides
    if len(slides)>1:
        z=f"zip/rostinho-{p['id']}.zip"
        with zipfile.ZipFile(z,'w',zipfile.ZIP_STORED) as zf:
            for s in slides: zf.write(s['full'],os.path.basename(s['full']))
        p2['zip']=z
    out.append(p2)
json.dump({'sections':d['sections'],'phases':d.get('phases',[]),'posts':out},open('src/data.json','w'),ensure_ascii=False,indent=1)
print('ok',len(out))
