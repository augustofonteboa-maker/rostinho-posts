"""Gera img/, video/web-cover e src/data.json a partir de src/posts.json.

Imagens:  se o arquivo listado em "files" já existe no repositório (ex.: img/full/...), ele é reutilizado.
          Caso contrário, é lido de SRC (pasta CRIATIVOS original) e convertido.
Vídeos:   posts do tipo "reel" usam video/full/rostinho-<id>.mp4, video/web/... e video/cover/...jpg
          (gerados a partir de motion/ — ver motion/README.md). A capa vira o slide do cartão.
"""
import json, os, zipfile, unicodedata, re
from PIL import Image
SRC='/mnt/user-data/uploads/CRIATIVOS/'
d=json.load(open('src/posts.json'))
for p_ in ('img/full','img/web','zip','video/web','video/full','video/cover'): os.makedirs(p_,exist_ok=True)

def tint(im):
    return '#%02x%02x%02x'%im.crop((0,0,60,60)).resize((1,1),Image.BOX).getpixel((0,0))

def slide_from(im, base, full, bgpx=None):
    w=900; h=round(im.height*w/im.width)
    web=f'img/web/{base}.webp'
    im.resize((w,h),Image.LANCZOS).save(web,'WEBP',quality=82,method=6)
    return {'full':full,'web':web,'w':im.width,'h':im.height,'bg':tint(im),'bytes':os.path.getsize(full)}

out=[]
for p in d['posts']:
    slides=[]; p2={k:v for k,v in p.items() if k!='files'}
    if p['type']=='reel':
        vid=p['id']; stem=f'rostinho-{vid}'
        full=f'video/full/{stem}.mp4'; web=f'video/web/{stem}.mp4'; cover=f'video/cover/{stem}.jpg'
        for f in (full,web,cover): assert os.path.exists(f), f
        im=Image.open(cover).convert('RGB')
        s=slide_from(im, stem, cover)
        slides=[s]
        p2['video']={'full':full,'web':web,'cover':cover,'dur':p['video']['dur'],
                     'bytes':os.path.getsize(full),'w':1080,'h':1920}
    else:
        for i,f in enumerate(p['files'],1):
            base=f"rostinho-{p['id']}" + (f"-{i}" if len(p['files'])>1 else '')
            full=f'img/full/{base}.png'
            if f.startswith('img/') and os.path.exists(f):
                full=f; base=os.path.splitext(os.path.basename(f))[0]
            if os.path.exists(full):
                im=Image.open(full).convert('RGB')      # reutiliza o arquivo já publicado
            else:
                im=Image.open(SRC+f).convert('RGB'); im.save(full,optimize=True)
            slides.append(slide_from(im,base,full))
    p2['slides']=slides
    if p['type']!='reel' and len(slides)>1:
        z=f"zip/rostinho-{p['id']}.zip"
        with zipfile.ZipFile(z,'w',zipfile.ZIP_STORED) as zf:
            for s in slides: zf.write(s['full'],os.path.basename(s['full']))
        p2['zip']=z
    out.append(p2)
json.dump({'sections':d['sections'],'phases':d.get('phases',[]),'posts':out},open('src/data.json','w'),ensure_ascii=False,indent=1)
print('ok',len(out))
