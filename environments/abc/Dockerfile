FROM ubuntu:18.04 AS provebuilder
WORKDIR /root/
RUN apt-get update -y && apt-get install -y cmake ninja-build g++ python-dev python-setuptools python-pip git zlib1g-dev
RUN git clone --recursive https://github.com/sterin/super-prove-build --depth=1 && cd super-prove-build && mkdir build && cd build && cmake -DCMAKE_BUILD_TYPE=Release -G Ninja .. && ninja && ninja package

FROM ubuntu:20.04 AS aigerbuilder
WORKDIR /root/
RUN apt-get update -y && apt-get install -y git build-essential
RUN git clone https://github.com/zimmski/aiger.git --depth=1 && cd aiger && ./configure && make

FROM ubuntu:20.04
WORKDIR /root/
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && apt-get install -y tar wget vim python3 python2 python2.7-dev libxml2 libedit-dev
RUN ln -s /usr/lib/x86_64-linux-gnu/libedit.so.2 /usr/lib/x86_64-linux-gnu/libedit.so.0
COPY --from=provebuilder /root/super-prove-build/build/super_prove-hwmcc20-2-Ubuntu_18.04-Release.tar.gz ./
RUN tar -xzf super_prove-hwmcc20-2-Ubuntu_18.04-Release.tar.gz && rm super_prove-hwmcc20-2-Ubuntu_18.04-Release.tar.gz
COPY --from=aigerbuilder /root/aiger/smvtoaig /usr/local/bin/smvtoaig
RUN wget https://nusmv.fbk.eu/distrib/NuSMV-2.6.0-linux64.tar.gz && tar -xzf NuSMV-2.6.0-linux64.tar.gz && mv /root/NuSMV-2.6.0-Linux/bin/* /usr/local/bin/ && rm -rf NuSMV-2.7.1-linux64.tar.xz NuSMV-2.7.1-linux64
RUN wget https://github.com/diffblue/hw-cbmc/releases/download/ebmc-5.6/ebmc_5.6_amd64.deb && dpkg -i ebmc_5.6_amd64.deb && rm ebmc_5.6_amd64.deb

COPY ./run_experiment.py ./
