#FROM container.repository.cloudera.com/cloudera/flink:1.19.1-csaop1.1.2-b17
# To build this example without a Cloudera license, please switch to the Apache docker image:
FROM flink:1.19

COPY ./target/pyflink-kafka-1.19.2-csaop1.2.0-b27.jar /opt/flink/usrlib/pyflink-kafka.jar
USER root
#RUN yum install python3.9 -y

RUN apt-get update -y
#RUN apt-get install -y python3.11 python3.11-dev python3.11-distutils
RUN apt-get install -y python3 python3-dev python3-distutils
# Python3.11 doesn't work with Google cloudpickle module
RUN apt-get install -y python3-pip
#RUN ln -s /usr/bin/python3.11 /usr/bin/python
RUN ln -s /usr/bin/python3.10 /usr/bin/python
RUN rm -rf /var/lib/apt/lists/*
#RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

USER flink
#RUN /usr/bin/python -m pip install google google-api-python-client protobuf apache-flink
RUN /usr/bin/python3 -m pip install google google-api-python-client protobuf apache-flink
#RUN flink run --python /opt/flink/examples/python/datastream/word_count.py 
#RUN pyflink-shell.sh local /opt/flink/examples/python/datastream/word_count.py
