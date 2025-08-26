FROM python:3.8-slim

# Installer tkinter, locales et outils nécessaires
RUN apt-get update && apt-get install -y \
    python3-tk \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Configurer locale fr_CH.UTF-8
RUN sed -i '/fr_CH.UTF-8/s/^# //g' /etc/locale.gen && locale-gen fr_CH.UTF-8

ENV LANG=fr_CH.UTF-8
ENV LANGUAGE=fr_CH:fr
ENV LC_ALL=fr_CH.UTF-8

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["python", "app.py"]
