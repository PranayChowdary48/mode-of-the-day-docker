FROM python:3.12

# set a directory for the app
WORKDIR /app

# copy requirements to the container
COPY requirements.txt .
# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copy other required files to  the container
COPY app.py .
COPY templates/ templates/

# tell the port number the container should expose
EXPOSE 5000

# run the command
CMD ["python", "./app.py"]