FROM python:3.11-slim

# Metadados
LABEL maintainer="welitonma"
LABEL description="Multivozes BR Engine - TTS API compatível com OpenAI"

# Instalar dependências do sistema (FFmpeg é essencial para pydub;
# libgomp1 é exigida pelo onnxruntime do backend local Piper)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (para cache de layers)
COPY requirements.txt requirements-local.txt ./

# Instalar dependências Python (inclui o backend local Piper)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -r requirements-local.txt

# Baixar a voz padrão do Piper numa camada própria (cache):
# só refaz o download se requirements ou o script mudarem, antes do COPY . .
COPY scripts/baixar_voz_piper.py scripts/baixar_voz_piper.py
RUN python scripts/baixar_voz_piper.py pt_BR-faber-medium --dir /app/models

# Backend padrão continua o Edge; modelos Piper em /app/models.
# PIPER_THREADS não é definido aqui (o humano define no `docker run`;
# o padrão do código é usar todos os núcleos).
ENV TTS_BACKEND=edge PIPER_MODELS_DIR=/app/models

# Copiar todo o código da aplicação
COPY . .

# Criar diretório para arquivos temporários
RUN mkdir -p /tmp/tts_audio

# Expor a porta padrão
EXPOSE 5050

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5050/v1/models')" || exit 1

# Comando de inicialização
CMD ["python", "main.py"]
