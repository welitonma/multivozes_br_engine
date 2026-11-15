import fastapi
from fastapi import HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import traceback
import uvicorn

from config import DEFAULT_CONFIGS
from handle_text import preparar_texto_para_tts
from tts_handler import gerar_audio, DADOS_MODELOS
from utils import (obter_env_bool, TIPOS_MIME_AUDIO, 
                   LOG_ERROS_DETALHADO, EXIGIR_CHAVE_API, CHAVE_API)

# Configuração de segurança para Swagger UI
security = HTTPBearer(auto_error=False)

# --- Modelo de Request Body ---
class TTSRequest(BaseModel):
    """Modelo para requisição de geração de áudio"""
    input: str = Field(..., description="Texto a ser convertido em áudio", example="Olá, bem-vindo ao sistema!")
    model: str = Field(default="tts-1", description="Modelo de TTS", example="tts-1")
    voice: str | None = Field(default=None, description="Voz (apelido ou nome técnico)", example="pt-BR-ThalitaMultilingualNeural")
    response_format: str | None = Field(default=None, description="Formato do áudio", example="mp3")
    speed: float | None = Field(default=None, ge=0.25, le=2.0, description="Velocidade (0.25 a 2.0)", example=1.0)

# Inicializa a aplicação FastAPI e carrega as variáveis de ambiente.
app = fastapi.FastAPI()
load_dotenv()

# --- Carregamento de Configurações ---
_PORT_BRUTO = os.getenv('PORT', DEFAULT_CONFIGS.get("PORT"))
try:
    PORTA = int(_PORT_BRUTO)
except (TypeError, ValueError):
    raise RuntimeError(f"Configuração inválida: PORT='{_PORT_BRUTO}' (esperado inteiro de 1 a 65535)")
if not 1 <= PORTA <= 65535:
    raise RuntimeError(f"Configuração inválida: PORT='{_PORT_BRUTO}' (esperado inteiro de 1 a 65535)")
VOZ_PADRAO = os.getenv('DEFAULT_VOICE', DEFAULT_CONFIGS.get("DEFAULT_VOICE"))
FORMATO_RESPOSTA_PADRAO = os.getenv('DEFAULT_RESPONSE_FORMAT', DEFAULT_CONFIGS.get("DEFAULT_RESPONSE_FORMAT"))
if FORMATO_RESPOSTA_PADRAO not in TIPOS_MIME_AUDIO:
    raise RuntimeError(f"Configuração inválida: DEFAULT_RESPONSE_FORMAT='{FORMATO_RESPOSTA_PADRAO}' (esperado um de: {', '.join(sorted(TIPOS_MIME_AUDIO))})")
_VELOCIDADE_BRUTA = os.getenv('DEFAULT_SPEED', DEFAULT_CONFIGS.get("DEFAULT_SPEED"))
try:
    VELOCIDADE_PADRAO = float(_VELOCIDADE_BRUTA)
except (TypeError, ValueError):
    raise RuntimeError(f"Configuração inválida: DEFAULT_SPEED='{_VELOCIDADE_BRUTA}' (esperado número de 0.25 a 2.0)")
if not 0.25 <= VELOCIDADE_PADRAO <= 2.0:
    raise RuntimeError(f"Configuração inválida: DEFAULT_SPEED='{_VELOCIDADE_BRUTA}' (esperado número de 0.25 a 2.0)")
REMOVER_FILTRO = obter_env_bool('REMOVE_FILTER', DEFAULT_CONFIGS.get("REMOVE_FILTER"))


# --- Função de Segurança (Dependência) ---
async def verificar_chave_api(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    """
    Verifica se a chave de API fornecida no cabeçalho 'Authorization' é válida.
    Esta função é usada como uma dependência nas rotas protegidas.
    """
    if not EXIGIR_CHAVE_API:
        return
    
    if not CHAVE_API:
        raise HTTPException(
            status_code=500, 
            detail="Servidor não configurado para autenticação. A variável API_KEY não foi definida."
        )

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Chave de API ausente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != CHAVE_API:
        raise HTTPException(
            status_code=401, 
            detail="Chave de API inválida.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials


# --- Rota Principal de Geração de Áudio ---
@app.post("/v1/audio/speech", dependencies=[Depends(verificar_chave_api)])
async def text_to_speech(request_data: TTSRequest, background_tasks: BackgroundTasks):
    """
    Endpoint principal que recebe texto e retorna o áudio sintetizado.
    Compatível com a API da OpenAI.
    """
    try:
        texto = request_data.input
        if not texto:
            raise HTTPException(status_code=400, detail="O campo 'input' é obrigatório.")

        # Aplica o filtro de texto se não estiver desativado
        if not REMOVER_FILTRO:
            texto = preparar_texto_para_tts(texto)

        # Obtém os parâmetros da requisição ou usa os padrões
        voz = request_data.voice if request_data.voice else VOZ_PADRAO
        formato_resposta = request_data.response_format if request_data.response_format is not None else FORMATO_RESPOSTA_PADRAO
        velocidade = request_data.speed if request_data.speed is not None else VELOCIDADE_PADRAO
        tipo_mime = TIPOS_MIME_AUDIO.get(formato_resposta, "audio/mpeg")

        # Gera o áudio de forma assíncrona
        caminho_ficheiro_audio = await gerar_audio(texto, voz, formato_resposta, velocidade)
        
        # Agenda a exclusão do ficheiro temporário após o envio da resposta
        background_tasks.add_task(os.unlink, caminho_ficheiro_audio)
        
        return FileResponse(path=caminho_ficheiro_audio, media_type=tipo_mime, filename=f"speech.{formato_resposta}")

    except HTTPException:
        raise
    except Exception as e:
        if LOG_ERROS_DETALHADO:
            print(f"Erro inesperado: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {e}")


# --- Rota para Listar Modelos ---
@app.get("/v1/models")
def listar_modelos():
    """
    Endpoint para listar os modelos de TTS disponíveis (para compatibilidade com OpenAI).
    """
    return {"data": [{"id": m["id"], "object": "model"} for m in DADOS_MODELOS]}


# --- Bloco de Inicialização do Servidor ---
if __name__ == '__main__':
    print("=====================================================================")
    print("      🔊 Iniciando o Multivozes BR Engine 🇧🇷 (Modo Estável)")
    print("=====================================================================")
    print("🐍 Criado por: Samuel de Sousa Santos (samucatutoriais)")
    print("🔧 Baseado no projeto de: travisvn/openai-edge-tts")
    print("⚙️  Servidor: Uvicorn (FastAPI)")
    print(f"🌐 Servidor a correr em: http://0.0.0.0:{PORTA}")
    print(f"🔑 Exigir chave de API: {'Sim' if EXIGIR_CHAVE_API else 'Não'}")
    print("=====================================================================")
    
    uvicorn.run(app, host='0.0.0.0', port=PORTA)

