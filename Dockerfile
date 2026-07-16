# Imagem base
FROM python:3.12

# Diretorio de trabalho
WORKDIR /app

# Copia o arquivo de dependencias
COPY requirements.txt .

# Instala as dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante da aplicação
COPY . . 

# Instala o navegador Chromium do Playwright
RUN playwright install chromium

# Comando padrão
CMD ["python", "-m", "app/main.py"]