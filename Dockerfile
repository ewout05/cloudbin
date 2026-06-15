# Gebruik een lichte Python base image
FROM python:3.9-slim

# Stel de werkmap in
WORKDIR /app

# Kopieer de afhankelijkhedenlijst
COPY requirements.txt .

# Update pip en installeer afhankelijkheden
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Kopieer de volledige app directory naar de container
COPY . .

# Stel de standaard poort in waarop Flask draait
EXPOSE 8080

# Stel het startcommando in met Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
