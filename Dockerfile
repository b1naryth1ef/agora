FROM python:3.7

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV ENV docker

RUN mkdir /opt/agora

ADD requirements.txt /opt/agora/
RUN pip install -r /opt/agora/requirements.txt

ADD . /opt/agora/
WORKDIR /opt/agora

