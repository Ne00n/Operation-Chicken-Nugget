FROM python:3.12-alpine

COPY . .

RUN pip3 install requests ovh

CMD ["python", "nugget.py"]