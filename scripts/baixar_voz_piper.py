#!/usr/bin/env python3
"""Baixa uma voz Piper (.onnx + .onnx.json) para PIPER_MODELS_DIR.

Uso manual (nunca chamado em runtime nem nos testes):

    python scripts/baixar_voz_piper.py pt_BR-faber-medium
    PIPER_MODELS_DIR=./modelos python scripts/baixar_voz_piper.py pt_BR-faber-medium
"""

import argparse
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Baixa voz Piper (.onnx + .onnx.json)."
    )
    parser.add_argument("voz", help="Id da voz, ex: pt_BR-faber-medium")
    parser.add_argument(
        "--dir",
        default=os.getenv("PIPER_MODELS_DIR", "./models"),
        help="Destino (padrão: PIPER_MODELS_DIR ou ./models)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Baixa de novo mesmo se existir"
    )
    args = parser.parse_args()

    try:
        from piper.download_voices import download_voice
    except ImportError:
        print(
            "ERRO: pacote 'piper-tts' não instalado. "
            "Rode: pip install -r requirements-local.txt"
        )
        return 1

    destino = Path(args.dir)
    destino.mkdir(parents=True, exist_ok=True)
    try:
        download_voice(args.voz, destino, force_redownload=args.force)
    except ValueError as e:
        print(f"ERRO: {e} (exemplo válido: pt_BR-faber-medium)")
        return 1
    print(f"OK: voz '{args.voz}' em '{destino}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
