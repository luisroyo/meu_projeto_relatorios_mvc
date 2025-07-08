FROM python:3.10-slim

# Instala locale pt_BR.UTF-8
RUN apt-get update && apt-get install -y locales && \
    sed -i 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen pt_BR.UTF-8 && \
    update-locale LANG=pt_BR.UTF-8 && \
    apt-get clean

ENV LANG=pt_BR.UTF-8
ENV LC_ALL=pt_BR.UTF-8
ENV FLASK_APP=app:create_app()
ENV FLASK_ENV=production

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD flask db upgrade && flask seed-db && gunicorn --workers 3 --bind 0.0.0.0:$PORT app:create_app()
