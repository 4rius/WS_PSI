FROM python:3.11-alpine
LABEL authors="Santiago Arias"

ENV FLASK_APP=flaskr
ENV FLASK_ENV=production

WORKDIR /app

COPY requirements.txt requirements.txt
COPY dockerstart.sh start.sh
COPY Crypto/py-fhe /app/Crypto/py-fhe
RUN apk add build-base python3-dev libffi-dev linux-headers net-tools wireless-tools gmp-dev mpfr-dev mpc1-dev
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install /app/Crypto/py-fhe \
    && pip install waitress

COPY . .

EXPOSE 5000
CMD ["./start.sh"]
