
# python current version
FROM python:3.12.13
# working directory
WORKDIR /app

# copy all the files
COPY . . 

RUN pip install --no-cache-dir --prefer-binary -r requirements.txt


# run the backend file
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

