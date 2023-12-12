FROM python:3.9-alpine
LABEL authors="santi"

ENV FLASK_APP=flaskr
ENV FLASK_ENV=development

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]