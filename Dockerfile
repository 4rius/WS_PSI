FROM python:3.9-alpine
LABEL authors="santi"

ENV FLASK_APP=flaskr
ENV FLASK_ENV=development

WORKDIR /app

COPY requirements.txt requirements.txt
RUN apk add build-base python3-dev linux-headers net-tools wireless-tools gmp-dev mpfr-dev mpc1-dev
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]
