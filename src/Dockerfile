FROM python:3.6

RUN mkdir /opt/app
WORKDIR /opt/app
ADD requirements.txt ./

RUN pip3 install -r requirements.txt

ADD . .

CMD ["python3", "./manage.py", "runserver", "0.0.0.0:8000"]