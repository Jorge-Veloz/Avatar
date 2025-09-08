# Base: Python 3.10 slim
FROM python:3.10-slim

# Rutas persistentes
ENV APP_HOME=/home/asistente-energetico \
    APP_STORAGE=/home/asistente-energetico/storage \
    XDG_CACHE_HOME=/home/asistente-energetico/storage/.cache \
    HF_HOME=/home/asistente-energetico/storage/.cache/huggingface \
    PYTORCH_HUB=/home/asistente-energetico/storage/.cache/torch/hub \
    CTRANSLATE2_CACHE_DIR=/home/asistente-energetico/storage/.cache/ctranslate2 \
    TTS_HOME=/home/asistente-energetico/storage/.local/share/tts \
    PM2_HOME=/home/asistente-energetico/storage/.pm2

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    nano \
    curl \
    git \
    openssh-server \
    nodejs npm \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Configura pip
RUN python3 -m ensurepip --upgrade \
 && python3 -m pip install --upgrade pip setuptools wheel \
 && npm install -g pm2 \
 && mkdir -p /var/run/sshd \
 && echo 'root:root' | chpasswd \
 && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
 && sed -i 's/#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Copia el proyecto
WORKDIR ${APP_HOME}
COPY requirements.txt ./
COPY . .

# Crea storage y permisos
RUN mkdir -p ${APP_STORAGE} ${PM2_HOME} \
 && chmod -R 777 ${APP_STORAGE} ${PM2_HOME}

# Instala dependencias Python
RUN python3 -m pip install --no-cache-dir -r requirements.txt

EXPOSE 22 3005

CMD service ssh start && pm2-runtime start ecosystem.config.js
