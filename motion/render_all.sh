#!/bin/bash
cd /home/claude/rostinho-motion
mkdir -p saida
N=(r1-0307:Rostinho_R1_0307:1 r2-como-funciona:Rostinho_R2_ComoFunciona:2 r3-vida-inteira:Rostinho_R3_VidaInteira:3 r4-prazer-zinho:Rostinho_R4_PrazerZinho:4 r5-toda-familia:Rostinho_R5_TodaFamilia:5 r6-mito-verdade:Rostinho_R6_MitoOuVerdade:6 r7-puxou-a-quem:Rostinho_R7_PuxouAQuem:7 r8-pov-familia:Rostinho_R8_POV_Familia:8)
W=${WORKERS:-2}
for item in "${N[@]}"; do
  IFS=: read f name i <<< "$item"
  echo "=== $f $(date +%T)"
  node render.mjs $f.html --name $name --sizes 1080x1920 --audio audio/trilha_r$i.wav --outdir saida --workers $W 2>&1 | grep -vE '^\s*[0-9]+%|quadro' | tail -4
done
echo "=== carrossel $(date +%T)"
node render.mjs r9-carrossel.html --stills 1.4,3.4,5.4,7.4,9.4,11.4 --sizes 1080x1350 --outdir saida/carrossel 2>&1 | tail -2
echo "=== FIM $(date +%T)"
