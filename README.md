# Rostinho · Central de posts

Página com tudo para publicar no Instagram do Rostinho (@rostinhobaby): imagens e vídeos prontos, legendas, hashtags, texto alternativo, primeiro comentário e o calendário de lançamento (19/10 a 28/11/2026).

## O que tem aqui
- `index.html` — o sistema (abre direto no GitHub Pages). Abas **Plano**, **Posts** e **Pastas**; filtros Carrosséis, Posts únicos, Reels e Story
- `docs/SEQUENCIA-DE-POSTAGEM.md` — calendário final dos 28 itens, a lógica da ordem e as regras
- `docs/LEGENDAS-REELS-E-CARROSSEL.md` — legendas finais dos 8 Reels e do carrossel R9
- `docs/ROTEIROS-MOTION.md` — roteiros dos vídeos (cena a cena, com som)
- `img/full`, `img/web` — imagens 1080 px para publicar e prévias leves
- `video/full` (1080×1920, para publicar), `video/web` (540×960, prévia), `video/cover` (capas JPG)
- `zip/` — carrosséis em .zip
- `motion/` — código-fonte dos vídeos (ver `motion/README.md`)
- `src/` — dados e scripts do site

## Como editar
1. Legendas, hashtags, dia e hora: `src/posts.json` (campo `plan`). Texto do plano: `src/plan.json`.
2. `python3 src/build_assets.py` (imagens, vídeos e `data.json`) e depois `python3 src/build_html.py` (gera o `index.html`).
3. Novo Reel: coloque `rostinho-<id>.mp4` em `video/full` e `video/web` e a capa em `video/cover`, e crie o post com `"type": "reel"`.
