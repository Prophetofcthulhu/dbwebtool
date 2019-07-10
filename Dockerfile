FROM python:3.7.3

RUN echo "alias ll='ls -alG'" >> /root/.bashrc

COPY . dbwebtool
WORKDIR webdb
RUN pip install -r requirements.txt

EXPOSE 8886
CMD [ "python", "start_webdb.py" ]

