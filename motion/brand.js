/* brand.js — identidade Rostinho para as cenas (tokens + peças reutilizáveis) */
(function (G) {
  const M = G.M, E = M.ease; G.G = G;
  const C = G.C = {
    ink: '#2B1922', inkSoft: '#5B4650', coral: '#D86F5D', coralDeep: '#B8523F', paper: '#FBF7F4',
    blush: '#F3E4DE', sky: '#DFE7F0', lav: '#E3DDF0', butter: '#F1E5CB', cream: '#F2EBE2', line: '#EADBD4',
    night: '#150F11', wine: '#2B1922', peach: '#F6D9CF', mint: '#DCEBE1'
  };
  const u = G.u = x => x * M.S;
  G.W = M.W; G.H = M.H;

  // posição absoluta em px
  G.box = (el, x, y, w, h) => { el.style.left = x + 'px'; el.style.top = y + 'px'; if (w != null) el.style.width = w + 'px'; if (h != null) el.style.height = h + 'px'; return el; };

  // camada de fundo viva: cor + 2 manchas desfocadas que derivam
  G.bgLayer = (parent, color, { glow = '#ffffff', glow2 = null, alpha = 0.55 } = {}) => {
    const L = M.el('div', { class: 'layer', style: { background: color } }, parent);
    const b1 = M.el('div', { class: 'abs blob', style: { width: u(900) + 'px', height: u(900) + 'px', borderRadius: '50%', background: `radial-gradient(circle, ${M.rgba(glow, alpha)} 0%, ${M.rgba(glow, 0)} 70%)` } }, L);
    const b2 = M.el('div', { class: 'abs blob', style: { width: u(1100) + 'px', height: u(1100) + 'px', borderRadius: '50%', background: `radial-gradient(circle, ${M.rgba(glow2 || glow, alpha * 0.7)} 0%, ${M.rgba(glow2 || glow, 0)} 70%)` } }, L);
    const dark = M.lum(color) < 0.2, step = u(72);
    const dots = M.el('div', { class: 'abs', style: { left: -step + 'px', top: -step + 'px', width: (M.W + 2 * step) + 'px', height: (M.H + 2 * step) + 'px', backgroundImage: `radial-gradient(circle, ${dark ? 'rgba(255,255,255,.10)' : 'rgba(43,25,34,.07)'} ${u(4)}px, transparent ${u(5)}px)`, backgroundSize: step + 'px ' + step + 'px' } }, L);
    L.upd = t => {
      M.css(dots, { transform: { x: (t * u(26)) % step, y: (t * u(18)) % step } });
      const d1 = M.drift(t, u(120), 0.12, 3), d2 = M.drift(t, u(140), 0.1, 8);
      M.css(b1, { transform: { x: -u(250) + d1.x, y: u(150) + d1.y } });
      M.css(b2, { transform: { x: M.W - u(600) + d2.x, y: M.H - u(900) + d2.y } });
    };
    return L;
  };

  // texto
  G.txt = (parent, cls, html, st = {}) => M.el('div', { class: 'abs ' + cls, style: st }, parent, html);
  G.title = (parent, html, x, y, size, color = C.ink, w = M.W - x - u(120)) =>
    G.txt(parent, 'disp', html, { left: x + 'px', top: y + 'px', width: w + 'px', fontSize: size + 'px', color });

  // anima linhas que sobem de dentro da máscara
  G.riseLines = (S, t, t0, { each = 0.09, dur = 0.75, out = null, outDur = 0.4, dist = 1.15 } = {}) => {
    S.lines.forEach((ln, i) => {
      const h = ln.offsetHeight || 100;
      const q = E.outExpo(M.seg(t, t0 + i * each, t0 + dur + i * each));
      const o = out == null ? 0 : E.inCubic(M.seg(t, out + i * 0.05, out + outDur + i * 0.05));
      M.css(ln.in, { transform: { y: (1 - q) * h * dist - o * h * 1.25 } });
    });
  };
  // palavras que sobem
  G.riseWords = (S, t, t0, { each = 0.07, dur = 0.7, out = null, outDur = 0.35 } = {}) => {
    S.words.forEach((w, i) => {
      const h = w.offsetHeight || 100;
      const q = E.outExpo(M.seg(t, t0 + i * each, t0 + dur + i * each));
      const o = out == null ? 0 : E.inCubic(M.seg(t, out + i * 0.03, out + outDur + i * 0.03));
      M.css(w.in, { transform: { y: (1 - q) * h * 1.2 - o * h * 1.3 } });
    });
  };

  // bloco de linhas pré-quebradas, cada uma numa máscara. spec: [[texto, 'disp'|'ser'|'body', tamanho, cor, extraGap]]
  G.lines = (parent, x, y, spec, { align = 'left', w = M.W } = {}) => {
    let yy = y; const out = [];
    spec.forEach(([text, cls, size, color, gap = 0]) => {
      const lh = cls === 'ser' ? 1.02 : cls === 'body' ? 1.25 : 0.98;
      const wrap = M.el('div', { class: 'abs', style: { left: (align === 'center' ? 0 : x) + 'px', top: yy + 'px', width: (align === 'center' ? M.W : w) + 'px', overflow: 'hidden', paddingBottom: (size * 0.16) + 'px', textAlign: align } }, parent);
      const inn = M.el('div', { class: cls, style: { fontSize: size + 'px', color, lineHeight: lh, whiteSpace: 'nowrap', transformOrigin: align === 'center' ? '50% 100%' : '0% 100%' } }, wrap, text);
      out.push({ wrap, in: inn, h: size * lh * 1.2, size });
      yy += size * lh + gap;
    });
    out.bottom = yy; return out;
  };
  G.riseL = (arr, t, t0, { each = 0.1, dur = 0.8, out = null, outDur = 0.4, bounce = 1.5 } = {}) => {
    arr.forEach((l, i) => {
      const p = M.seg(t, t0 + i * each, t0 + dur * 0.85 + i * each), q = E.outBack(p, bounce);
      const o = out == null ? 0 : E.inCubic(M.seg(t, out + i * 0.05, out + outDur + i * 0.05));
      const mv = Math.min(1, (1 - Math.min(1, q)) * 1.4 + o);         // quanto a linha ainda está em movimento
      const dir = (i % 2 ? 1 : -1);
      M.css(l.in, { transform: { y: (1 - q) * l.h - o * l.h * 1.1, sy: 1 + 0.16 * mv, sx: 1 - 0.035 * mv, r: dir * 2.2 * (1 - Math.min(1, p)) } });
    });
  };

  // imagem posicionada (centro ancorado)
  G.img = (parent, src, w, st = {}) => {
    const d = M.el('div', { class: 'abs', style: Object.assign({ width: w + 'px', transformOrigin: '50% 100%' }, st) }, parent);
    const i = M.el('img', { src, style: { width: '100%', display: 'block' } }, d);
    d.im = i; return d;
  };
  // coloca um elemento com centro (cx, base) e transform extra
  G.T = 0; G.lives = [];
  G.place = (el, cx, by, tf = {}) => {
    const w = el.offsetWidth, h = el.offsetHeight, T = G.T, ph = cx * 0.013;
    if (tf.idle !== false) tf = Object.assign({}, tf, { r: (tf.r || 0) + 1.3 * Math.sin(T * 2.6 + ph), sy: (tf.sy || 1) * (1 + 0.016 * Math.sin(T * 3.4 + ph)), sx: (tf.sx || 1) * (1 - 0.01 * Math.sin(T * 3.4 + ph)) });
    M.css(el, { left: (cx - w / 2) + 'px', top: (by - h) + 'px', transform: tf });
  };

  // pílula / adesivo
  G.pill = (parent, text, { bg = C.ink, color = C.paper, size = u(34), pad = [0.42, 0.95], weight = 700, radius = 999, cls = 'disp2' } = {}) =>
    M.el('div', { class: 'abs ' + cls, style: { background: bg, color, fontSize: size + 'px', padding: `${pad[0]}em ${pad[1]}em`, borderRadius: radius + 'px', whiteSpace: 'nowrap', fontWeight: weight, letterSpacing: '-0.01em', lineHeight: 1 } }, parent, text);

  // coração vetorial
  G.HEART = 'M50 88 C20 66 4 50 4 30 C4 15 16 4 30 4 C40 4 47 10 50 17 C53 10 60 4 70 4 C84 4 96 15 96 30 C96 50 80 66 50 88 Z';
  G.heart = (parent, size, color = C.coral) => {
    const s = M.el('svg', { width: size, height: size, viewBox: '0 0 100 92', style: { position: 'absolute', overflow: 'visible' } }, parent);
    const p = M.el('path', { d: G.HEART, fill: color }, s);
    s.p = p; return s;
  };

  // LOGO: letras separadas + carinha (tamanho nativo 762x130)
  const LG = { face: [665, 0, 97, 130], letters: [[0, 93], [91, 93], [184, 85], [268, 109], [378, 56], [437, 111], [549, 109]] };
  G.logo = (parent, width, variant = 'dark') => {
    const k = width / 762, root = M.el('div', { class: 'abs', style: { width: width + 'px', height: (130 * k) + 'px' } }, parent);
    const letters = LG.letters.map(([x, w], i) => {
      const d = M.el('img', { src: `assets/letter-${variant}-${i}.png`, class: 'abs', style: { left: (x * k) + 'px', top: (2 * k) + 'px', width: (w * k) + 'px', height: (128 * k) + 'px', transformOrigin: '50% 100%' } }, root);
      d.x0 = x * k; d.w0 = w * k; return d;
    });
    const face = M.el('img', { src: `assets/logo-face-${variant}.png`, class: 'abs', style: { left: (665 * k) + 'px', top: 0, width: (97 * k) + 'px', height: (130 * k) + 'px', transformOrigin: '50% 62%' } }, root);
    root.k = k; root.letters = letters; root.face = face; root.h = 130 * k; root.w = width;
    return root;
  };
  // entrada padrão da logo: letras caem com quique em cascata, a carinha rola e encaixa
  G.logoIn = (L, t, t0, { roll = true, each = 0.06 } = {}) => {
    L.letters.forEach((d, i) => {
      const a = t0 + i * each, s = M.springAt(t, a, 'bouncy'), p = M.clamp(s, 0, 1.3);
      const land = M.pulse(t, a + 0.22, 0.12);
      M.css(d, { opacity: t >= a ? 1 : 0, transform: { y: (1 - p) * -u(260), sy: 1 - 0.18 * land, sx: 1 + 0.12 * land } });
    });
    const fa = t0 + L.letters.length * each + 0.05;
    const fp = E.outBack(M.seg(t, fa, fa + 0.7), 1.6);
    const rot = roll ? (1 - E.outCubic(M.seg(t, fa, fa + 0.8))) * 360 : 0;
    M.css(L.face, { opacity: t >= fa ? 1 : 0, transform: { x: (1 - fp) * u(420), r: rot, s: 0.4 + 0.6 * Math.min(1, fp) + 0.06 * Math.sin(Math.PI * M.seg(t, fa + 0.55, fa + 0.95)) } });
    return fa + 0.6; // momento do encaixe
  };
  G.logoT = (L, each = 0.06) => L.letters.length * each + 0.05 + 0.6;

  // estrelinhas / brilhos (4 pontas)
  G.SPARK = 'M50 0 C54 34 66 46 100 50 C66 54 54 66 50 100 C46 66 34 54 0 50 C34 46 46 34 50 0 Z';
  G.sparks = (parent, n, color, seed = 3) => {
    const s = M.el('svg', { width: M.W, height: M.H }, parent), r = M.rng(seed), arr = [];
    for (let i = 0; i < n; i++) { const g = M.el('g', {}, s); M.el('path', { d: G.SPARK, fill: color }, g); g.a = r() * Math.PI * 2; g.d = 0.6 + r() * 0.6; g.s = 0.25 + r() * 0.35; g.dl = r() * 0.25; arr.push(g); }
    s.arr = arr;
    s.upd = (t, t0, cx, cy, R) => arr.forEach(g => {
      const p = M.seg(t, t0 + g.dl, t0 + g.dl + 0.9), q = E.outExpo(p), sc = Math.sin(Math.PI * p) * g.s * u(1);
      const x = cx + Math.cos(g.a) * R * g.d * (0.4 + 0.8 * q), y = cy + Math.sin(g.a) * R * g.d * (0.4 + 0.8 * q);
      g.setAttribute('transform', `translate(${x - 50 * sc} ${y - 50 * sc}) scale(${sc})`);
      g.style.opacity = p > 0 && p < 1 ? 1 : 0;
    });
    return s;
  };


  // formas que flutuam por trás do conteúdo (corações, brilhos, bolinhas, anéis)
  G.life = (parent, { n = 14, seed = 11, colors = [C.coral, C.lav, C.butter, C.peach], alpha = 0.6, size = [38, 104], speed = [60, 135], kinds = ['heart', 'spark', 'dot', 'ring'] } = {}) => {
    const svg = M.el('svg', { width: M.W, height: M.H, style: { pointerEvents: 'none' } }, parent), r = M.rng(seed), arr = [];
    for (let i = 0; i < n; i++) {
      const g = M.el('g', {}, svg), kind = kinds[Math.floor(r() * kinds.length)], col = colors[Math.floor(r() * colors.length)], sz = u(size[0] + r() * (size[1] - size[0]));
      if (kind === 'heart') M.el('path', { d: G.HEART, fill: col, transform: `translate(${-50} ${-46})` }, g);
      else if (kind === 'spark') M.el('path', { d: G.SPARK, fill: col, transform: 'translate(-50 -50)' }, g);
      else if (kind === 'ring') M.el('circle', { r: 40, fill: 'none', stroke: col, 'stroke-width': 9 }, g);
      else M.el('circle', { r: 34, fill: col }, g);
      arr.push({ g, x0: r() * M.W, sz, ph: r(), sp: u(speed[0] + r() * (speed[1] - speed[0])), sw: u(26 + r() * 50), sf: 0.4 + r() * 0.8, rot: (r() - 0.5) * 90, kind });
    }
    svg.upd = t => arr.forEach(a => {
      const span = M.H + 2 * a.sz, y = M.H + a.sz - (((t * a.sp + a.ph * span) % span + span) % span);
      const x = a.x0 + a.sw * Math.sin(t * a.sf + a.ph * 6.28), edge = Math.min(1, Math.min(y + a.sz, M.H + a.sz - y) / (a.sz * 2));
      const sc = (a.sz / 100) * (1 + 0.12 * Math.sin(t * 2.2 + a.ph * 9)) * Math.max(0, edge);
      a.g.setAttribute('transform', `translate(${x} ${y}) rotate(${a.rot * Math.sin(t * a.sf + a.ph * 3)}) scale(${a.kind === 'heart' ? sc * 1.05 : sc * (a.kind === 'spark' ? 1 : 1.35)})`);
      a.g.style.opacity = alpha * Math.max(0, edge);
    });
    G.lives.push(svg); return svg;
  };

  // câmera: respira e inclina de leve o quadro inteiro
  G.cam = (t, { zoom = 0.03, roll = 0.35, period = 8 } = {}) => {
    const st = document.getElementById('stage'); if (!st) return;
    st.style.transformOrigin = '50% 50%';
    const z = 1 + zoom * (0.5 - 0.5 * Math.cos(2 * Math.PI * t / period)) + 0.006 * Math.sin(t * 1.7);
    st.style.transform = `rotate(${roll * Math.sin(t * 0.55)}deg) scale(${z})`;
  };
  const _boot = M.boot;
  M.boot = (render, o) => _boot(t => { G.T = t; const r = render(t); G.lives.forEach(l => l.upd(t)); if (!G.noCam) G.cam(t); return r; }, o);

  // estilos comuns
  const css = document.createElement('style');
  css.textContent = `
  html,body{margin:0;background:#000;overflow:hidden}
  #stage{position:relative;width:var(--W);height:var(--H);overflow:hidden;background:${C.paper}}
  .layer{position:absolute;inset:0;overflow:hidden}
  .abs{position:absolute}
  .disp{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;letter-spacing:-0.035em;line-height:.95;font-kerning:normal}
  .disp2{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;letter-spacing:-0.01em}
  .body{font-family:'Bricolage Grotesque',sans-serif;font-weight:500;letter-spacing:-0.005em;line-height:1.25}
  .ser{font-family:'Instrument Serif',serif;font-style:italic;font-weight:400;letter-spacing:-0.015em;line-height:.98}
  .lab{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
  .em{font-family:'Instrument Serif',serif;font-style:italic;font-weight:400;color:${C.coral};letter-spacing:-0.01em}
  svg{position:absolute;left:0;top:0;overflow:visible}
  img{user-select:none}`;
  document.head.appendChild(css);
})(window);
