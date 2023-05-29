# Use a Python base image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask application code into the container
COPY app app
COPY migrations migrations
COPY flask_app.py config.py .flaskenv gunicorn.conf.py boot.sh ./

# Expose the port that the Flask application listens on
EXPOSE 5000

# Run migrations
RUN flask db upgrade

# Set the command to run the Flask application
CMD ["bash", "boot.sh"]
