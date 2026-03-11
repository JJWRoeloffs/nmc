FROM ubuntu:24.04

WORKDIR /root/

RUN apt-get update -y && apt-get install -y vim wget tar python3

RUN wget https://nuxmv.fbk.eu/theme/download.php?file=nuXmv-2.0.0-linux64.tar.gz && tar -xzf download.php?file=nuXmv-2.0.0-linux64.tar.gz && mv nuXmv-2.0.0-Linux/bin/* /usr/local/bin && rm -rf download.php?file=nuXmv-2.0.0-linux64.tar.gz nuXmv-2.0.0-Linux

RUN wget https://github.com/diffblue/hw-cbmc/releases/download/ebmc-5.9/ebmc_5.9_amd64.deb && dpkg -i ebmc_5.9_amd64.deb && rm ebmc_5.9_amd64.deb

COPY ./nuXmv_IC3 /usr/local/bin/
RUN chmod +x /usr/local/bin/nuXmv_IC3

COPY ./run_experiment.py ./
