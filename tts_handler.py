import edge_tts
import os
import traceback
import tempfile
import json # NOVO: Para carregar o ficheiro JSON
import re
from pathlib import Path
from pydub import AudioSegment # NOVO: Para conversão de áudio
from dotenv import load_dotenv

from utils import LOG_ERROS_DETALHADO

load_dotenv()

# --- Carregamento de Configurações ---
PROXY = os.getenv("PROXY", None)

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

async def gerar_audio(texto: str, voz: str, formato_resposta: str, velocidade: float) -> str:
    """
    Gera o áudio usando edge-tts com suporte opcional a pausas customizadas [pause: Xs].
    Se o texto contiver [pause: 2s] ou [pause: 500ms], gera áudio com pausas inseridas.
    """
    # Verifica se a voz solicitada é um apelido da OpenAI e a converte
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
    
    i = 0
    while i < len(partes):
        parte_texto = partes[i].strip()
        
        # Se tem texto, gerar áudio para essa parte
        if parte_texto:
            try:
                temp_audio_path = await gerar_audio_normal(parte_texto, voz, taxa, 'mp3')
                audio_segment = AudioSegment.from_mp3(temp_audio_path)
                audio_final += audio_segment
                Path(temp_audio_path).unlink()  # Deletar arquivo temporário
            except Exception as e:
                if LOG_ERROS_DETALHADO:
                    print(f"Erro ao gerar segmento de áudio: {e}")
        
        # Se há informação de pausa (tempo + unidade), adicionar silêncio
        if i + 2 < len(partes):
            tempo = float(partes[i + 1])
            unidade = partes[i + 2].lower()
            
            # Converter para milissegundos
            pausa_ms = int(tempo if unidade == 'ms' else tempo * 1000)
            pausa_ms = min(pausa_ms, 10000)  # Máximo 10 segundos por pausa
            
            # Adicionar silêncio digital (24kHz = sample rate do Edge TTS)
            silencio = AudioSegment.silent(duration=pausa_ms, frame_rate=24000)
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
    Gera o áudio normalmente usando edge-tts (código original).
    """
    # Cria um ficheiro temporário para a saída inicial do edge-tts (sempre mp3)
    ficheiro_temp_mp3 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    caminho_temp_mp3 = ficheiro_temp_mp3.name
    ficheiro_temp_mp3.close()

    caminho_final_audio = None # Variável para guardar o caminho do ficheiro final

    try:
        # 1. Gera o áudio com edge-tts e salva como MP3
        comunicador = edge_tts.Communicate(texto, voz=voz, rate=taxa, proxy=PROXY)
        await comunicador.save(caminho_temp_mp3)

        # 2. Converte o áudio se o formato de resposta for diferente de mp3
        if formato.lower() != "mp3":
            # Cria um novo ficheiro temporário para o formato final
            ficheiro_temp_final = tempfile.NamedTemporaryFile(delete=False, suffix=f".{formato_resposta}")
            caminho_final_audio = ficheiro_temp_final.name
            ficheiro_temp_final.close()

            # Usa pydub para carregar o MP3 e exportar no formato desejado
            audio = AudioSegment.from_mp3(caminho_temp_mp3)
            audio.export(caminho_final_audio, format=formato.lower())
            
            # Remove o ficheiro mp3 intermediário
            Path(caminho_temp_mp3).unlink()
        else:
            # Se o formato for mp3, o ficheiro temporário já é o final
            caminho_final_audio = caminho_temp_mp3

    except Exception as e:
        # Se ocorrer um erro, remove os ficheiros temporários para não deixar lixo
        if caminho_temp_mp3 and Path(caminho_temp_mp3).exists():
            Path(caminho_temp_mp3).unlink(missing_ok=True)
        if caminho_final_audio and Path(caminho_final_audio).exists():
            Path(caminho_final_audio).unlink(missing_ok=True)
            
        if LOG_ERROS_DETALHADO:
            print(f"Erro detalhado em gerar_audio: {traceback.format_exc()}")
        raise RuntimeError(f"Falha ao gerar ou converter áudio: {e}")

    # Retorna o caminho do ficheiro de áudio final
    return caminho_final_audio