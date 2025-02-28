# Use a minimal Python Alpine image as the base
FROM python:3.13-alpine3.21

# Set the working directory
WORKDIR /app

# Copy the entire repository into the container
COPY . ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the bot
CMD ["python", "./main/bot.py"]