FROM ubuntu:24.04

WORKDIR /root/

RUN apt-get update -y && apt-get install -y vim wget python3

RUN wget https://github.com/diffblue/hw-cbmc/releases/download/ebmc-5.6/ebmc_5.6_amd64.deb && dpkg -i ebmc_5.6_amd64.deb && rm ebmc_5.6_amd64.deb

COPY ./run_experiment.py ./
