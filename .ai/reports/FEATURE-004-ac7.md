# FEATURE-004 — AC7 (medida manual em CPU)

Executado pelo orquestrador, a pedido e com autorização do humano (download só da voz pt-BR `pt_BR-faber-medium`, 63 MB).
Ambiente: piper-tts 1.8.0, onnxruntime CPU, `CUDA_VISIBLE_DEVICES=""`, texto de 339 caracteres (~18,8 s de áudio), voz `alloy` -> `pt_BR-faber-medium`, formato wav.

| Cenário | Chamada fria (RTF) | Chamadas mornas (RTF) | Pico de memória | Rodadas |
|---|---|---|---|---|
| (a) sem limite | 0,053–0,059 (1,00–1,10 s) | 0,028–0,036 (0,53–0,69 s) | 382–462 MB | 3 |
| (b) `taskset -c 0,1` (threads irmãos do núcleo 0) + `PIPER_THREADS=2` | 0,078–0,079 (1,46–1,49 s) | 0,057–0,059 (1,07–1,12 s) | 383–463 MB | 3 |

Pior caso medido: RTF 0,079 (cenário b, chamada fria). Meta da spec (< 0,5): **atendida com folga (~6x)**.
Ressalva: a máquina de teste é mais rápida que uma VPS típica e sem vizinhos; os números da VPS real devem ser medidos lá.
Licenças: piper-tts 1.8.0 = GPL-3.0-or-later; licença da voz `faber` a conferir no cartão do modelo (não baixado).
