FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /root

RUN apt-get update -y && apt-get install -y python3 python3-pip python3-venv git software-properties-common wget vim pkg-config libgmp-dev build-essential m4

RUN wget https://github.com/diffblue/hw-cbmc/releases/download/ebmc-5.6/ebmc_5.6_amd64.deb && dpkg -i ebmc_5.6_amd64.deb && rm ebmc_5.6_amd64.deb

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN /opt/venv/bin/python3 -m pip install colorama numpy matplotlib cmake meson ninja cython


RUN wget https://gmplib.org/download/gmp/gmp-6.3.0.tar.xz && tar -xf gmp-6.3.0.tar.xz
RUN cd gmp-6.3.0 && ./configure --enable-cxx && make && make check && make install
RUN rm -r ./gmp-6.3.0

# For some reason, installing libgmp-dev as done earlier before doing the manual install fixes a compiler error here,
# Even though we manually installed gmp in a directory with higher priority, and the package is never linked with.
RUN wget https://ftp.gnu.org/gnu/mpfr/mpfr-4.2.1.tar.xz && tar -xf mpfr-4.2.1.tar.xz
RUN cd mpfr-4.2.1 && ./configure && make && make install
RUN rm -r ./mpfr-4.2.1

RUN apt-get update -y && apt-get install -y build-essential pkg-config ninja-build libgtest-dev
RUN /opt/venv/bin/python3 -m pip install cmake meson ninja cython
RUN git clone https://github.com/bitwuzla/bitwuzla && cd bitwuzla && git checkout 1177124ddc7e6ea9ce7eaf464da199d141146f04 && /opt/venv/bin/python3 ./configure.py debug && cd build && /opt/venv/bin/meson test
RUN /opt/venv/bin/python3 -m pip install ./bitwuzla

COPY ./gurobi.lic ./
RUN apt-get update -y && apt-get install -y z3 cvc5
RUN /opt/venv/bin/python3 -m pip install setuptools gurobipy
RUN /opt/venv/bin/python3 -m pip install pysmt --pre && pysmt-install --confirm-agreement --msat
RUN pysmt-install --confirm-agreement --z3 --cvc5

COPY ./requirements.txt ./
RUN /opt/venv/bin/python3 -m pip install -r ./requirements.txt

COPY ./ ./
RUN /opt/venv/bin/python3 -m pip install .
