FROM alpine:latest

RUN apk add --update --no-cache --virtual .build-deps  \
    git

RUN apk add --update --no-cache \
    fontconfig \
    py3-pillow \
    py3-future \
    py3-jinja2 \
    py3-bottle \
    python3 \
    ttf-dejavu \
    py3-pip \
    poppler-utils

RUN ln -s /usr/bin/python3 /usr/bin/python
RUN git clone --depth=1 https://github.com/tbnobody/brother_ql_web.git

WORKDIR /brother_ql_web

RUN rm -r .git
RUN python3 -m venv .venv
RUN source .venv/bin/activate
RUN pip3 install -r requirements.txt
RUN apk del .build-deps

EXPOSE 8013

CMD [ "./run.py", "--model", "QL-580N", "tcp://192.168.5.169" ]