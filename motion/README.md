# Código-fonte dos motions (Reels R1–R8 e carrossel R9)

Cada vídeo é uma cena HTML/SVG com função pura `render(t)`, capturada quadro a quadro pelo Playwright e codificada com ffmpeg. O som é sintetizado em Python (um som diferente por vídeo).

- `r1-…html` a `r8-…html` — cenas dos Reels (R1–R5 de 30 s, R6–R8 de 15 s); `r9-carrossel.html` — carrossel 4:5
- `brand.js` — identidade (cores, fontes, logo, Zinho, helpers); `motion.js` — linha do tempo e easing
- `render.mjs` — captura de quadros com motion blur; `render_all.sh` — renderiza tudo
- `trilhas.py` — sintetizador das trilhas e efeitos (r1 a r8); `audio/cues_r*.json` — marcações de tempo dos sons
- `assets/`, `fonts/` — recortes do Zinho, imagens e fontes usadas

Para regenerar: `python3 trilhas.py` e depois `bash render_all.sh` (exige Node + Playwright, Python com numpy/scipy e ffmpeg). Os vídeos finais para publicar já estão em `../video/full`. Os arquivos .wav e os renders brutos não são versionados.
