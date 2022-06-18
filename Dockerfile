FROM python:3
COPY requirements.txt ./ 
COPY src/ src/
RUN pip install --no-cache-dir -r requirements.txt
CMD [ "python", "./src/game.py" ]