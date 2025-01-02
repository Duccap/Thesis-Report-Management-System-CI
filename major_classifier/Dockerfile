FROM python:3.9-slim-bullseye
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 list  # Debugging step to verify installed packages
COPY . .
CMD ["python3", "main.py"]
