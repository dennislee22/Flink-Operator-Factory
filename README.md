# Flink Operator: Real-Time Stream Processing on K8s

<img src="/images/flinkfactory.gif" width="700" height="636"/>

Apache Flink provides a robust platform for building scalable, real-time stream processing applications. Whether you're building real-time analytics, data pipeline, monitoring systems, or complex event-driven applications, Flink ensures that developers can run real-time data transformation logic while taking advantage of Flink’s powerful features like event-time processing, windowing, and fault tolerance. Running the Flink Operator on K8s is an ideal combination, leveraging Kubernetes's scalability and self-healing capabilities. Flink requires Java because it's built on the JVM which provides the necessary libraries for Flink. Therefore building an immutable Docker image to run Flink application on K8s can be challenging. This challenge can be addressed by setting up a `Flink Factory` to build Flink libraries into an immutable Docker image, while creating a PyFlink application using an editable ConfigMap in Kubernetes. Using a ConfigMap to store the PyFlink script allows for seamless code modification without the need to rebuild the Docker image repeatedly.

# My Flink Factory environment:
**CSA Operator Version:** `1.19.2-csaop1.2.0`, based on [OSS Flink Kubernetes Operator v1.9](https://nightlies.apache.org/flink/flink-kubernetes-operator-docs-release-1.9/) and [Flink v1.19](https://nightlies.apache.org/flink/flink-docs-master/release-notes/flink-1.19/)


# Deploy CSA (Cloudera Streaming Analytics) operator
1. In the CNCF-compatible Kubernetes cluster (version 1.23 or later), create a new namespace.
```
# kubectl create ns csa-ssb
namespace/csa-ssb created
```

2. Create a secret object in the same namespace to store your Cloudera credentials.
```
# kubectl create secret docker-registry cfm-credential --docker-server container.repository.cloudera.com \
--docker-username xxx --docker-password yyy --namespace csa-ssb
secret/cfm-credential created
```

3. Log into Cloudera registry.
 ```
# helm registry login container.repository.cloudera.com
Username: xxx
Password: yyy
Login Succeeded
```

4. Ensure that no `csa-operator` Helm chart was previously installed.
```
helm list -A | grep csa-operator
```

5. Deploy the `csa-operator` Helm chart. Administrator has the option to set additional settings during deployment. For instance, the following installation is deployed with 'csa-ssb-config.yml' file in which the Flink cluster uses the external postgresql database rather than embedded database. In addition, the user database is derived from an external LDAP server. Other helm options can be obtained [here](https://docs.cloudera.com/csa-operator/1.2/reference/topics/csa-op-reference.html). 
```
# kubectl create secret generic ssb-ldap -n csa-ssb \
  --from-literal=SSB_LDAP_URL="ldap://10.129.82.87:389" \
  --from-literal=SSB_LDAP_BASE_DN=dc=cldr,dc=example \
  --from-literal=SSB_LDAP_USERNAME=uid=admin,cn=users,cn=accounts,dc=cldr,dc=example \
  --from-literal=SSB_LDAP_PASSWORD=zxczxc \
  --from-literal=SSB_LDAP_USER_DN_PATTERNS=uid={0} \
  --from-literal=SSB_LDAP_USER_SEARCH_BASE=cn=users,cn=accounts,dc=cldr,dc=example \
  --from-literal=SSB_LDAP_USER_SEARCH_FILTER= \
  --from-literal=SSB_LDAP_GROUP_SEARCH_BASE=cn=groups,cn=accounts,dc=cldr,dc=example
```

```
# helm install csa-operator --namespace csa-ssb --set 'flink-kubernetes-operator.imagePullSecrets[0].name=cfm-credential' \
--set 'ssb.sse.image.imagePullSecrets[0].name=cfm-credential' --set 'ssb.sqlRunner.image.imagePullSecrets[0].name=cfm-credential' \
--set-file flink-kubernetes-operator.clouderaLicense.fileContent=/license.txt \
oci://container.repository.cloudera.com/cloudera-helm/csa-operator/csa-operator --version 1.2.0-b27 -f ./csa-ssb-config.yml

Pulled: container.repository.cloudera.com/cloudera-helm/csa-operator/csa-operator:1.2.0-b27
Digest: sha256:06771c433e481b93c8cf2f92fac2a2a8abd6a0076b575ec97ff0b8970aabf332
NAME: csa-operator
LAST DEPLOYED: Sat Mar  8 07:31:41 2025
NAMESPACE: csa-ssb
STATUS: deployed
REVISION: 1
TEST SUITE: None  
```

6. Upon successful deployment, ensure all pods and its associated containers are up and `Running`.
```
# kubectl -n csa-ssb get secret
NAME                                 TYPE                             DATA   AGE
cfm-credential                       kubernetes.io/dockerconfigjson   1      76m
csa-op-license                       Opaque                           1      7m48s
flink-operator-webhook-secret        Opaque                           1      7m48s
sh.helm.release.v1.csa-operator.v1   helm.sh/release.v1               1      7m48s
ssb-fernet-key                       Opaque                           1      7m48s
ssb-ldap                             Opaque                           11     88s
ssb-postgresql-auth                  Opaque                           8      7m48s
ssb-ssb-users-secret                 Opaque                           1      7m48s
webhook-server-cert                  kubernetes.io/tls                5      15m

# kubectl -n csa-ssb get all
NAME                                            READY   STATUS    RESTARTS       AGE
pod/flink-kubernetes-operator-79d98b567-6n82v   2/2     Running   2 (5d3h ago)   6d4h
pod/ssb-sse-865457bc46-9wt6m                    1/1     Running   1 (5d3h ago)   6d4h

NAME                                     TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)             AGE
service/flink-operator-webhook-service   ClusterIP   10.43.199.16    <none>        443/TCP             6d4h
service/ssb-sse                          ClusterIP   10.43.2.207     <none>        18121/TCP           6d4h

NAME                                        READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/flink-kubernetes-operator   1/1     1            1           6d4h
deployment.apps/ssb-sse                     1/1     1            1           6d4h

NAME                                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/flink-kubernetes-operator-79d98b567   1         1         1       6d4h
replicaset.apps/ssb-sse-865457bc46                    1         1         1       6d4h
```

**Note:** A total of 35 tables created at the external Postgres database. 
```
postgres=# \c ssb
You are now connected to database "ssb" as user "postgres".
ssb=# SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
 count 
-------
    35
(1 row)
```

# Build JAR containing connectors and dependencies

1. Now that your Flink cluster is ready to run the application. Next step is build the Flink docker image with the necessary Flink dependencies to run the application. Ensure that `git` and `maven` tools are already deployed in your client system before proceeding with the following steps.
```
# git clone https://github.com/dennislee22/Flink-SSB-Operator
# cd flink-build
# mvn clean package
[INFO] Scanning for projects...
[INFO] ------------------------------------------------------------------------
[INFO] Reactor Build Order:
[INFO] 
[INFO] Flink Build                                                        [pom]
[INFO] Flink Master :: Pyflink Kafka                                      [jar]
[INFO] 
[INFO] -------------------< com.cloudera.flink:flink-build >-------------------
[INFO] Building Flink Build 1.19.2-csaop1.2.0-b27                         [1/2]
[INFO]   from pom.xml
[INFO] --------------------------------[ pom ]---------------------------------
[INFO] 
[INFO] --- clean:3.2.0:clean (default-clean) @ flink-build ---
[INFO] 
[INFO] ------------------< com.cloudera.flink:pyflink-kafka >------------------
[INFO] Building Flink Master :: Pyflink Kafka 1.19.2-csaop1.2.0-b27       [2/2]
[INFO]   from pyflink-kafka/pom.xml
[INFO] --------------------------------[ jar ]---------------------------------
Downloading from cloudera: https://repository.cloudera.com/artifactory/cloudera-repos/org/apache/flink/flink-clients/1.19.2-csaop1.2.0/flink-clients-1.19.2-csaop1.2.0.pom
Downloaded from cloudera: https://repository.cloudera.com/artifactory/cloudera-repos/org/apache/flink/flink-clients/1.19.2-csaop1.2.0/flink-clients-1.19.2-csaop1.2.0.pom (9.3 kB at 16 kB/s)
......
......
Downloaded from cloudera: https://repository.cloudera.com/artifactory/cloudera-repos/org/apache/flink/flink-shaded-zookeeper-3/3.8.1-1.19.2-csaop1.2.0/flink-shaded-zookeeper-3-3.8.1-1.19.2-csaop1.2.0.jar (12 MB at 2.7 MB/s)
[INFO] 
[INFO] --- clean:3.2.0:clean (default-clean) @ pyflink-kafka ---
[INFO] Deleting /root/flink-build/pyflink-kafka/target
[INFO] 
[INFO] --- resources:3.3.1:resources (default-resources) @ pyflink-kafka ---
[INFO] skip non existing resourceDirectory /root/flink-build/pyflink-kafka/src/main/resources
[INFO] 
[INFO] --- compiler:3.13.0:compile (default-compile) @ pyflink-kafka ---
[INFO] No sources to compile
[INFO] 
[INFO] --- resources:3.3.1:testResources (default-testResources) @ pyflink-kafka ---
[INFO] skip non existing resourceDirectory /root/flink-build/pyflink-kafka/src/test/resources
[INFO] 
[INFO] --- compiler:3.13.0:testCompile (default-testCompile) @ pyflink-kafka ---
[INFO] No sources to compile
[INFO] 
[INFO] --- surefire:3.2.2:test (default-test) @ pyflink-kafka ---
[INFO] No tests to run.
[INFO] 
[INFO] --- jar:3.4.1:jar (default-jar) @ pyflink-kafka ---
[WARNING] JAR will be empty - no content was marked for inclusion!
[INFO] Building jar: /root/flink-build/pyflink-kafka/target/pyflink-kafka-1.19.2-csaop1.2.0-b27.jar
......
......
[INFO] Replacing original artifact with shaded artifact.
[INFO] Replacing /root/flink-build/pyflink-kafka/target/pyflink-kafka-1.19.2-csaop1.2.0-b27.jar with /root/flink-build/pyflink-kafka/target/pyflink-kafka-1.19.2-csaop1.2.0-b27-shaded.jar
[INFO] ------------------------------------------------------------------------
[INFO] Reactor Summary for Flink Build 1.19.2-csaop1.2.0-b27:
[INFO] 
[INFO] Flink Build ........................................ SUCCESS [  0.223 s]
[INFO] Flink Master :: Pyflink Kafka ...................... SUCCESS [ 20.538 s]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  20.900 s
[INFO] Finished at: 2025-03-09T06:11:38Z
[INFO] ------------------------------------------------------------------------
```

2. Verify that dependencies such as flink-connector-datagen have already been built into the JAR file.
```
# jar tf pyflink-kafka/target/pyflink-kafka-1.19.2-csaop1.2.0-b27.jar | grep datagen
org/apache/flink/connector/datagen/
org/apache/flink/connector/datagen/functions/
org/apache/flink/connector/datagen/functions/FromElementsGeneratorFunction.class
org/apache/flink/connector/datagen/source/
org/apache/flink/connector/datagen/source/GeneratorFunction.class
org/apache/flink/connector/datagen/source/DataGeneratorSource.class
org/apache/flink/connector/datagen/source/GeneratorSourceReaderFactory.class
org/apache/flink/connector/datagen/source/GeneratingIteratorSourceReader.class
```

# Build Docker image with Flink runtime
1. Log into the docker registry in the local environment. I built a docker registry and the URL is `nexus.dlee1.cldr.example:9999`.
```
# podman login nexus.dlee1.cldr.example:9999
Username: admin
Password: 
Login Succeeded!
```
2. Build the `pyflink-kafka` docker image. Tag the image. Push the image into the above docker registry.
```
# docker build -t pyflink-kafka .
STEP 1/10: FROM flink:1.19
STEP 2/10: COPY ./target/pyflink-kafka-1.19.2-csaop1.2.0-b27.jar /opt/flink/usrlib/pyflink-kafka.jar
....
....
Successfully tagged localhost/pyflink-kafka:latest

# podman image tag pyflink-kafka nexus.dlee1.cldr.example:9999/pvcds/pyflink-kafka:dlee-1.0
# podman image ls
REPOSITORY                                         TAG         IMAGE ID      CREATED             SIZE
localhost/pyflink-kafka                            latest      dfe6e1a98b37  About a minute ago  2.49 GB
nexus.dlee1.cldr.example:9999/pvcds/pyflink-kafka  dlee-1.0    dfe6e1a98b37  About a minute ago  2.49 GB
docker.io/library/flink                            1.19        7fb8e45bc851  3 weeks ago         801 MB

# podman push nexus.dlee1.cldr.example:9999/pvcds/pyflink-kafka:dlee-1.0
Getting image source signatures
Copying blob d2e07a5d820e done
....
....
Writing manifest to image destination
Storing signatures
```

# Build PyFlink script in the ConfigMap

Note: This PyFlink script reads messages from a Kafka source topic, processes the data by calculating the length of each message, and writes the results to a new Kafka destination topic.
1. Deploy the PyFlink script in the ConfigMap by applying the `pyflink-cm-kafka-sink-kafka.yaml` file.
```
# kubectl -n csa-ssb apply -f pyflink-cm-kafka-sink-kafka.yaml 
configmap/pyflink-kafka-sink-script created
```
2. The producer of the Kafka source topic is expected to be running, producing the messages as shown in the following example.
<img width="501" alt="image" src="https://github.com/user-attachments/assets/d6b8c48c-a1a6-4a51-ad98-ff53e42b983b" />


# Create Flink deployment

1. Deploy the Flink application by applying the `pyflink-job-kafka-sink-kafka.yaml` file.
```
# kubectl -n csa-ssb apply -f pyflink-job-kafka-sink-kafka.yaml
flinkdeployment.flink.apache.org/pyflink-kafka-sink-kafka created
```

2. Upon successful deployment, ensure all pods (Flink application and TaskManager) and its associated container(s) are up and `Running`.
```
# kubectl -n csa-ssb get pods
NAME                                        READY   STATUS    RESTARTS       AGE
flink-kubernetes-operator-79d98b567-6n82v   2/2     Running   2 (5d3h ago)   6d4h
pyflink-kafka-sink-kafka-84d456d8db-ftrlz   1/1     Running   0              3d
pyflink-kafka-sink-kafka-taskmanager-1-1    1/1     Running   0              3d
ssb-sse-865457bc46-9wt6m                    1/1     Running   1 (5d3h ago)   6d4h
```

# Expose Flink REST 

1. Expose the Flink REST service to the external network by deploying the `ingress-flink-kafkasink.yaml` file.
```
```
# kubectl -n csa-ssb get svc
NAME                             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)             AGE
flink-operator-webhook-service   ClusterIP   10.43.199.16    <none>        443/TCP             7d
pyflink-kafka-sink-kafka         ClusterIP   None            <none>        6123/TCP,6124/TCP   3d21h
pyflink-kafka-sink-kafka-rest    ClusterIP   10.43.128.194   <none>        8081/TCP            3d21h
ssb-sse                          ClusterIP   10.43.2.207     <none>        18121/TCP           7d

# kubectl -n csa-operator apply -f ingress-flink-kafkasink.yaml 
ingress.networking.k8s.io/ingress-flink-kafka-sink created

# kubectl -n csa-ssb get ingress
NAME                       CLASS    HOSTS                                        ADDRESS         PORTS   AGE
ingress-flink-kafka-sink   <none>   pyflink-kafka-sink.apps.dlee1.cldr.example   10.129.83.133   80      4d
```

2. You may now browse the Flink dashboard via `http://pyflink-kafka-sink.apps.dlee1.cldr.example`. The dashboard depicts that the Flink application is running.
<img width="1427" alt="image" src="https://github.com/user-attachments/assets/773e5326-0987-4f12-b719-19fcef86b0f1" />

# Verify the result of running the PyFlink script
1. Run JupyterLab to consume the messages from the Kafka destination topic. This shows that the PyFlink script is running successfully, processing the data by calculating the length of each message in real time!
<img width="524" alt="image" src="https://github.com/user-attachments/assets/ab41d3d0-f0bb-4110-8381-e7ac9cea25aa" />


