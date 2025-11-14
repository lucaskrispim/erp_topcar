# Base image
FROM python:3.10-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV APP_HOME /app

# Define o diretório de trabalho
WORKDIR $APP_HOME

# Copia e instala as dependências
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copia o código da aplicação
COPY . $APP_HOME

EXPOSE 8000

# Comando padrão para rodar a aplicação
CMD ["/bin/bash", "-c", "python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]