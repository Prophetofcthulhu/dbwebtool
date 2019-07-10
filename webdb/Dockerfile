FROM python3.7:latest

COPY . /webdb

WORKDIR /webdb
RUN pip install --no-cache-dir -r requirements.txt && mkdir -p logs

CMD [ "python", "webdb_start.py" ]

EXPOSE 8886