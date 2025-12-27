FROM python:3.11-slim

# Metadados
LABEL maintainer="welitonma"
LABEL description="Multivozes BR Engine - TTS API compatível com OpenAI"

# Instalar dependências do sistema (FFmpeg é essencial para pydub)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (para cache de layers)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

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
