# To build this example without a Cloudera license, please switch to the Apache docker image:
#FROM container.repository.cloudera.com/cloudera/flink:1.19.1-csaop1.1.2-b17
FROM flink:1.19

COPY ./target/pyflink-kafka-1.19.1-csaop1.1.2.jar /opt/flink/usrlib/pyflink-kafka.jar
USER root
#RUN yum install python3.9 -y

RUN apt-get update -y && \
apt-get install -y python3 python3-pip python3-dev && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python

USER flink
RUN /usr/bin/python3 -m pip install kafka-python grpcio apache-flink cython
