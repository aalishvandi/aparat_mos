# Use Debian 11 (Bullseye) as the base image
FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive

# Update package list and install packages
RUN apt update && apt install python3-pip python3-venv python3-dev -y

# Install additional packages
RUN apt install wget git iputils-ping lsof gnupg ca-certificates -y 

# Install ffmpeg
RUN apt install ffmpeg -y

# Install build-essential
RUN apt install build-essential -y

# Install ffmpeg requirements
RUN apt install libavdevice-dev libavformat-dev libavfilter-dev libavcodec-dev libswresample-dev libswscale-dev libavutil-dev build-essential pkg-config firefox openjdk-11-jre-headless snap snapd -y

# WORKDIR /tmp

# # Clone and build ffmpeg-debug-qp
# RUN git clone https://github.com/slhck/ffmpeg-debug-qp.git \
#   && cd ffmpeg-debug-qp \
#   && make \
#   && cp ffmpeg_debug_qp /usr/bin/ffmpeg_debug_qp \
#   && chmod +x /usr/bin/ffmpeg_debug_qp

WORKDIR /usr/src/app

COPY . .

# Clone and build ffmpeg-debug-qp
RUN cd ffmpeg-debug-qp-master && make && cp ffmpeg_debug_qp /usr/bin/ffmpeg_debug_qp 
RUN chmod +x /usr/bin/ffmpeg_debug_qp

# install firefox and depencencies
# RUN install -d -m 0755 /etc/apt/keyrings \
# && wget -q https://packages.mozilla.org/apt/repo-signing-key.gpg -O- | tee /etc/apt/keyrings/packages.mozilla.org.asc > /dev/null \
# && gpg -n -q --import --import-options import-show /etc/apt/keyrings/packages.mozilla.org.asc | awk '/pub/{getline; gsub(/^ +| +$/,""); if($0 == "35BAA0B33E9EB396F59CA838C0BA5CE6DC6315A3") print "\nThe key fingerprint matches ("$0").\n"; else print "\nVerification failed: the fingerprint ("$0") does not match the expected one.\n"}' \
# && echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main" | tee -a /etc/apt/sources.list.d/mozilla.list > /dev/null \
# && echo ' \
# Package: * \
# Pin: origin packages.mozilla.org \
# Pin-Priority: 1000 \
# ' | tee /etc/apt/preferences.d/mozilla \
# && apt-get update && apt-get install firefox 
# RUN dpkg -i --force-depends debs/firefox_124.deb && apt-get update && apt-get install -f -y
# RUN dpkg -i debs/firefox_124.deb
# RUN apt-get install -f -y

# install java
# RUN apt-get update && DEBIAN_FRONTEND=noninteractive && apt install ca-certificates-java -y
# RUN apt install openjdk-11-jre-headless -y
# RUN dpkg -i debs/libjpeg62-turbo_2.1.5-2_amd64.deb
# RUN apt install ca-certificates-java -y
# RUN dpkg -i debs/openjdk-11-jre-headless_11.0.21+9-1_amd64.deb
# RUN apt install libgl1 libgif7 libx11-6 libxext6 libxi6 libxrender1 libxtst6  -y
# RUN dpkg -i debs/openjdk-11-jre_11.0.21+9-1_amd64.deb


# RUN source .venv/bin/activate
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install libs/itu-p1203-master/

# create logs folder for run program succussfully
RUN mkdir logs/ts_files logs/mp4_files

# ENTRYPOINT ["/bin/bash", "-c", "source .venv/bin/activate && python3 ./start_selenium.py --file ./aparat_urls_test.txt"]
ENTRYPOINT python3 ./firefox_selenium.py --file ./aparat_urls.txt
