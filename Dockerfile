# Usa una imagen ligera de Python 3.12
FROM python:3.12-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos del proyecto
COPY . /app

# Instala las dependencias del bot
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto (por si en el futuro necesitas usarlo)
EXPOSE 8080

# Comando para ejecutar el bot
CMD ["python", "main.py"]
