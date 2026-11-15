import os
import traceback
import tempfile
import json # NOVO: Para carregar o ficheiro JSON
import re
from pathlib import Path
from pydub import AudioSegment # NOVO: Para conversão de áudio
from dotenv import load_dotenv

from utils import LOG_ERROS_DETALHADO

from tts_backends.edge import BackendEdge

load_dotenv()

_BACKEND_EDGE = BackendEdge()

# --- Carregamento de Configurações ---

# --- Mapeamento e Dados de Vozes ---

# ALTERADO: Carrega o mapeamento de vozes de um ficheiro JSON externo
def carregar_mapeamento_vozes():
    """Carrega o mapeamento de vozes do ficheiro voices.json."""
    caminho_ficheiro = Path(__file__).parent / "voices.json"
    if not caminho_ficheiro.exists():
        # Retorna um mapeamento padrão caso o ficheiro não exista, para evitar erros
        print("AVISO: Ficheiro 'voices.json' não encontrado. A usar mapeamento padrão.")
        return {
            'alloy': 'pt-BR-FranciscaNeural',
            'echo': 'pt-BR-AntonioNeural',
        }
    with open(caminho_ficheiro, 'r', encoding='utf-8') as f:
        return json.load(f)

MAPEAMENTO_VOZES = carregar_mapeamento_vozes()

# Dados dos modelos para compatibilidade com a API OpenAI
DADOS_MODELOS = [
    {"id": "tts-1", "name": "Text-to-speech v1"},
    {"id": "tts-1-hd", "name": "Text-to-speech v1 HD"},
]

def velocidade_para_taxa(velocidade: float) -> str:
    """Converte um multiplicador de velocidade (ex: 1.5) para o formato de taxa do edge-tts (ex: '+50%')."""
    if not 0.25 <= velocidade <= 2.0:
        raise ValueError("A velocidade deve estar entre 0.25 e 2.0.")
    percentagem = int((velocidade - 1) * 100)
    return f"+{percentagem}%" if percentagem >= 0 else f"{percentagem}%"

def obter_backend_nome() -> str:
    """Backend pedido em TTS_BACKEND (edge padrão); inválido levanta RuntimeError."""
    bruto = os.getenv("TTS_BACKEND", "edge")
    nome = bruto.strip().lower()
    if nome not in ("edge", "piper"):
        raise RuntimeError(
            f"Configuração inválida: TTS_BACKEND='{bruto}' (esperado edge ou piper)"
        )
    return nome


async def gerar_audio(texto: str, voz: str, formato_resposta: str, velocidade: float) -> str:
    """
    Gera o áudio usando edge-tts com suporte opcional a pausas customizadas [pause: Xs].
    Se o texto contiver [pause: 2s] ou [pause: 500ms], gera áudio com pausas inseridas.
    """
    # Verifica se a voz solicitada é um apelido da OpenAI e a converte
    if obter_backend_nome() == "piper":
        return await gerar_audio_piper(texto, voz, formato_resposta, velocidade)
    voz_edge_tts = MAPEAMENTO_VOZES.get(voz, voz)
    taxa = velocidade_para_taxa(velocidade)

    # Detectar se há pausas customizadas no texto
    if '[pause:' in texto.lower():
        return await gerar_audio_com_pausas(texto, voz_edge_tts, taxa, formato_resposta)
    else:
        return await gerar_audio_normal(texto, voz_edge_tts, taxa, formato_resposta)

async def gerar_audio_com_pausas(texto: str, voz: str, taxa: str, formato: str) -> str:
    """
    Gera áudio com pausas customizadas inseridas digitalmente.
    Exemplo: "Olá [pause: 2s] Mundo [pause: 500ms] Fim"
    """
    # Parse do texto: divide em partes de texto e pausas
    # Regex captura: [pause: 2s] ou [pause: 1000ms]
    partes = re.split(r'\[pause:\s*(\d+(?:\.\d+)?)(s|ms)\]', texto, flags=re.IGNORECASE)
    
    audio_final = AudioSegment.empty()
    taxa_silencio = 24000  # sample rate do áudio gerado (Edge: 24 kHz)
    
    i = 0
    while i < len(partes):
        parte_texto = partes[i].strip()
        
        # Se tem texto, gerar áudio para essa parte
        if parte_texto:
            try:
                temp_audio_path = await gerar_audio_normal(parte_texto, voz, taxa, 'mp3')
                audio_segment = AudioSegment.from_mp3(temp_audio_path)
                taxa_silencio = audio_segment.frame_rate
                audio_final += audio_segment
                Path(temp_audio_path).unlink()  # Deletar arquivo temporário
            except Exception as e:
                if LOG_ERROS_DETALHADO:
                    print(f"Erro ao gerar segmento de áudio: {e}")
                # Não devolver áudio parcial: propaga o erro para a API responder 5xx
                raise RuntimeError(f"Falha ao gerar segmento de áudio: {e}") from e
        
        # Se há informação de pausa (tempo + unidade), adicionar silêncio
        if i + 2 < len(partes):
            tempo = float(partes[i + 1])
            unidade = partes[i + 2].lower()
            
            # Converter para milissegundos
            pausa_ms = int(tempo if unidade == 'ms' else tempo * 1000)
            pausa_ms = min(pausa_ms, 10000)  # Máximo 10 segundos por pausa
            
            # Silêncio na taxa de amostragem do áudio gerado
            silencio = AudioSegment.silent(duration=pausa_ms, frame_rate=taxa_silencio)
            audio_final += silencio
            
            i += 2  # Pular os grupos capturados (tempo e unidade)
        
        i += 1
    
    # Salvar arquivo final no formato solicitado
    ficheiro_final = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{formato}')
    caminho_final = ficheiro_final.name
    ficheiro_final.close()
    
    try:
        audio_final.export(caminho_final, format=formato.lower())
    except Exception as e:
        if Path(caminho_final).exists():
            Path(caminho_final).unlink(missing_ok=True)
        if LOG_ERROS_DETALHADO:
            print(f"Erro ao exportar áudio final: {traceback.format_exc()}")
        raise RuntimeError(f"Falha ao exportar áudio com pausas: {e}")
    
    return caminho_final

async def gerar_audio_normal(texto: str, voz: str, taxa: str, formato: str) -> str:
    """
    Gera o áudio normalmente via backend Edge (chamada em tts_backends/edge.py).
    """
    return await _BACKEND_EDGE.gerar(texto, voz, taxa, formato)


async def gerar_audio_piper(texto: str, voz: str, formato: str, velocidade: float) -> str:
    """Roteia a síntese para o backend Piper local (offline, CPU)."""
    # Import preguiçoso: `piper` nunca entra em sys.modules sem TTS_BACKEND=piper.
    from tts_backends.piper import BackendPiper

    # Valida a faixa 0.25-2.0 igual ao Edge (mesma mensagem de erro).
    velocidade_para_taxa(velocidade)
    backend = BackendPiper()
    voz_piper = backend.resolver_voz(voz)
    if "[pause:" in texto.lower():
        return await gerar_audio_com_pausas_piper(texto, voz_piper, velocidade, formato, backend)
    return await gerar_audio_normal_piper(texto, voz_piper, velocidade, formato, backend)


async def gerar_audio_normal_piper(
    texto: str, voz: str, velocidade: float, formato: str, backend=None
) -> str:
    """Sintetiza via Piper (WAV) e converte para o formato pedido."""
    if backend is None:
        from tts_backends.piper import BackendPiper

        backend = BackendPiper()
    caminho_wav = await backend.sintetizar_wav(texto, voz, velocidade)
    if formato.lower() == "wav":
        return caminho_wav
    caminho_final = None
    try:
        ficheiro_temp_final = tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{formato}"
        )
        caminho_final = ficheiro_temp_final.name
        ficheiro_temp_final.close()
        audio = AudioSegment.from_wav(caminho_wav)
        audio.export(caminho_final, format=formato.lower())
        Path(caminho_wav).unlink()
    except Exception as e:
        if Path(caminho_wav).exists():
            Path(caminho_wav).unlink(missing_ok=True)
        if caminho_final and Path(caminho_final).exists():
            Path(caminho_final).unlink(missing_ok=True)
        if LOG_ERROS_DETALHADO:
            print(f"Erro detalhado em gerar_audio_normal_piper: {traceback.format_exc()}")
        raise RuntimeError(f"Falha ao gerar ou converter áudio: {e}")
    return caminho_final


async def gerar_audio_com_pausas_piper(
    texto: str, voz: str, velocidade: float, formato: str, backend=None
) -> str:
    """Pausas [pause: Xs] com segmentos sintetizados pelo Piper."""
    if backend is None:
        from tts_backends.piper import BackendPiper

        backend = BackendPiper()
    partes = re.split(r"\[pause:\s*(\d+(?:\.\d+)?)(s|ms)\]", texto, flags=re.IGNORECASE)

    audio_final = AudioSegment.empty()
    taxa_silencio = 24000  # sample rate do áudio gerado (Piper: o da voz)

    i = 0
    while i < len(partes):
        parte_texto = partes[i].strip()

        if parte_texto:
            try:
                temp_audio_path = await gerar_audio_normal_piper(
                    parte_texto, voz, velocidade, "wav", backend
                )
                audio_segment = AudioSegment.from_wav(temp_audio_path)
                taxa_silencio = audio_segment.frame_rate
                audio_final += audio_segment
                Path(temp_audio_path).unlink()
            except Exception as e:
                if LOG_ERROS_DETALHADO:
                    print(f"Erro ao gerar segmento de áudio: {e}")
                raise RuntimeError(f"Falha ao gerar segmento de áudio: {e}") from e

        if i + 2 < len(partes):
            tempo = float(partes[i + 1])
            unidade = partes[i + 2].lower()

            pausa_ms = int(tempo if unidade == "ms" else tempo * 1000)
            pausa_ms = min(pausa_ms, 10000)

            silencio = AudioSegment.silent(duration=pausa_ms, frame_rate=taxa_silencio)
            audio_final += silencio

            i += 2

        i += 1

    ficheiro_final = tempfile.NamedTemporaryFile(delete=False, suffix=f".{formato}")
    caminho_final = ficheiro_final.name
    ficheiro_final.close()

    try:
        audio_final.export(caminho_final, format=formato.lower())
    except Exception as e:
        if Path(caminho_final).exists():
            Path(caminho_final).unlink(missing_ok=True)
        if LOG_ERROS_DETALHADO:
            print(f"Erro ao exportar áudio final: {traceback.format_exc()}")
        raise RuntimeError(f"Falha ao exportar áudio com pausas: {e}")

    return caminho_final
