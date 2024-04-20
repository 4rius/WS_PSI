FROM python:3.9-alpine
LABEL authors="santi"

ENV FLASK_APP=flaskr
ENV FLASK_ENV=production

WORKDIR /app

COPY requirements.txt requirements.txt
COPY dockerstart.sh start.sh
RUN apk add build-base python3-dev libffi-dev linux-headers net-tools wireless-tools gmp-dev mpfr-dev mpc1-dev
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install waitress

COPY . .

EXPOSE 5000
CMD ["./start.sh"]
