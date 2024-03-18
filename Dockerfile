# Run as needed:
# sudo docker build -t lake-washington-and-sammamish-temps . | tee build.log 
# sudo docker run -it --name lake_wa_container lake-washington-and-sammamish-temps:latest


# If for some reason AWS credentials are needed at build time, the following works. But it bakes credentials into the image, which is not recommended.so don't do it! 
# sudo docker build --build-arg AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY --build-arg AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -t lake-washington-and-sammamish-temps . | tee build.log
# ARG AWS_SECRET_ACCESS_KEY
# ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
# ARG AWS_ACCESS_KEY_ID
# ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}

# Use an official Ubuntu runtime as a parent image
FROM ubuntu:latest

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Install Python, pip, SSH client, and other dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    vim \
    git \
    wget \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libu2f-udev \
    libvulkan1 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# install Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && apt install ./google-chrome-stable_current_amd64.deb

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Set the working directory in the container
WORKDIR /usr/src/app

# pull down the code and install the requirements
RUN git clone https://github.com/jpmalek/lake-washington-and-sammamish-temps.git 

WORKDIR /usr/src/app/lake-washington-and-sammamish-temps
RUN pip3 install --no-cache-dir -r requirements.txt 
CMD ["sh", "-c", "git pull && python3 app.py"]  
    