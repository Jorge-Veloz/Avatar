# Base: Python 3.10 slim
FROM python:3.10-slim

# Rutas persistentes (un solo prefijo)
ENV APP_HOME=/home/Avatar \
    APP_STORAGE=/home/Avatar/storage \
    XDG_CACHE_HOME=/home/Avatar/storage/.cache \
    HF_HOME=/home/Avatar/storage/.cache/huggingface \
    PYTORCH_HUB=/home/Avatar/storage/.cache/torch/hub \
    CTRANSLATE2_CACHE_DIR=/home/Avatar/storage/.cache/ctranslate2 \
    TTS_HOME=/home/Avatar/storage/.local/share/tts \
    PM2_HOME=/home/Avatar/storage/.pm2

# Instala utilidades, pm2 y servidor SSH; limpia caché de apt
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    sudo \
    pip \
    nano \
    curl \
    npm \
    git \
    openssh-server \
    nodejs npm \
 && npm install -g pm2 \
 # Configura SSH
 && mkdir -p /var/run/sshd \
 && echo 'root:root' | chpasswd \
 && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
 && sed -i 's/#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config \
 && rm -rf /var/lib/apt/lists/*

 # Copiamos el proyecto (código queda baked en la imagen)
WORKDIR ${APP_HOME}
COPY requirements.txt ./
COPY . .

# Creamos storage y permisos (el volumen montará aquí)
RUN mkdir -p ${PM2_HOME} && chmod -R 777 ${PM2_HOME}

RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Expón puertos SSH (22) y el puerto de tu app (ajusta si es necesario)
EXPOSE 22 3005

CMD service ssh start && pm2-runtime start ecosystem.config.js
