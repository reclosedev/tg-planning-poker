FROM python:3.6-alpine

COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

COPY ppbot /ppbot

WORKDIR /
CMD PYTHONPATH=. python ppbot/bot.py
