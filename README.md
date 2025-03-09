# Flink + SQL Stream Operator: Real-Time Stream Processing

<img width="811" alt="image" src="https://github.com/user-attachments/assets/f8c0b546-0faf-4bd3-af50-9f4c2571e425" />

Apache Flink, coupled with SQL Stream Builder (SSB), provides a robust platform for building scalable, real-time stream processing applications. Whether you're building real-time analytics, monitoring systems, or complex event-driven applications, Flink's support for SQL-based stream processing ensures that developers can quickly express complex logic while taking advantage of Flink’s powerful features like event-time processing, windowing, and fault tolerance. By abstracting the complexity of stream processing behind familiar SQL syntax, SSB democratizes real-time data analytics, enabling teams to deliver actionable insights faster and more efficiently.
In this article, I will explain the procedures to deploy for CSA (Cloudera Streaming Analytics) operator on a Kubernetes cluster, harnessing cloud-native benefits such as declarative deployments and scalability.

**CSA Operator Version:** `1.19.2-csaop1.2.0`, which is based on [OSS Flink Kubernetes Operator v1.9](https://nightlies.apache.org/flink/flink-kubernetes-operator-docs-release-1.9/) and [Flink v1.19](https://nightlies.apache.org/flink/flink-docs-master/release-notes/flink-1.19/)
OSS Flink Version: 


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

# kubectl -n csa-ssb get pods
NAME                                        READY   STATUS    RESTARTS   AGE
flink-kubernetes-operator-79d98b567-6n82v   2/2     Running   0          7m52s
ssb-sse-865457bc46-9wt6m                    1/1     Running   0          79s

NAME                                            READY   STATUS    RESTARTS   AGE
pod/flink-kubernetes-operator-79d98b567-6n82v   2/2     Running   0          8m48s
pod/ssb-sse-865457bc46-9wt6m                    1/1     Running   0          2m15s

NAME                                     TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)     AGE
service/flink-operator-webhook-service   ClusterIP   10.43.199.16   <none>        443/TCP     8m48s
service/ssb-sse                          ClusterIP   10.43.2.207    <none>        18121/TCP   8m48s

NAME                                        READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/flink-kubernetes-operator   1/1     1            1           8m48s
deployment.apps/ssb-sse                     1/1     1            1           8m48s

NAME                                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/flink-kubernetes-operator-79d98b567   1         1         1       8m48s
replicaset.apps/ssb-sse-865457bc46                    1         1         1       8m48s
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

7. Now that your Flink cluster is ready to run the application. Next step is build the Flink docker image with the necessary Flink dependencies to run the application. Ensure that `git` and `maven` tools are already deployed in your client system before proceeding with the following steps.
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

8. Verify that dependencies such as flink-connector-datagen have already been built into the JAR file.
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

9. Log into the docker registry in the local environment. I built a docker registry and the URL is `nexus.dlee1.cldr.example:9999`.
```
# podman login nexus.dlee1.cldr.example:9999
Username: admin
Password: 
Login Succeeded!
```

10. Build the `pyflink-kafka` docker image. Tag the image. Push the image into the above docker registry.
```
# docker build -t pyflink-kafka .
STEP 1/10: FROM flink:1.19
STEP 2/10: COPY ./target/pyflink-kafka-1.19.2-csaop1.2.0-b27.jar /opt/flink/usrlib/pyflink-kafka.jar
....
....
Successfully tagged localhost/pyflink-kafka:latest

# podman image tag pyflink-kafka nexus.dlee1.cldr.example:9999/pvcds/pyflink-kafka:19.2-csaop1.2.0-b27
# docker image ls
Emulate Docker CLI using podman. Create /etc/containers/nodocker to quiet msg.
REPOSITORY                                         TAG                  IMAGE ID      CREATED        SIZE
localhost/pyflink-kafka                            latest               babcd0aece38  2 minutes ago  2.38 GB
nexus.dlee1.cldr.example:9999/pvcds/pyflink-kafka  19.2-csaop1.2.0-b27  babcd0aece38  2 minutes ago  2.38 GB
docker.io/library/flink                            1.19                 7fb8e45bc851  3 weeks ago    801 MB

# podman push nexus.dlee1.cldr.example:9999/pvcds/pyflink-kafka:19.2-csaop1.2.0-b27
Getting image source signatures
Copying blob d2e07a5d820e done
....
....
Writing manifest to image destination
Storing signatures
```

11. Deploy the Flink application by applying the `pyflink-job-helloworld.yaml` file.
```
# kubectl -n csa-ssb apply -f pyflink-job-helloworld.yaml
flinkdeployment.flink.apache.org/pyflink-helloworld created
```

12. Upon successful deployment, ensure all pods (Flink application and TaskManager) and its associated container(s) are up and `Running`.
```
# kubectl -n csa-ssb get pods
NAME                                        READY   STATUS    RESTARTS      AGE
flink-kubernetes-operator-79d98b567-6n82v   2/2     Running   2 (44m ago)   25h
pyflink-helloworld-8d7468b76-ckgtr          1/1     Running   0             84s
pyflink-helloworld-taskmanager-1-1          1/1     Running   0             53s
ssb-sse-865457bc46-9wt6m                    1/1     Running   1 (44m ago)   25h
```

13. Verify that the Flink job has completed successfully by checking the Flink application pod log.
```
# oc -n csa-ssb logs pyflink-helloworld-8d7468b76-ckgtr  
Defaulted container "flink-main-container" out of: flink-main-container, create-scripts-directory (init), k8tz (init)
/opt/flink/bin/config-parser-utils.sh: line 45: /opt/flink/conf/flink-conf.yaml: Read-only file system
Starting kubernetes-application as a console application on host pyflink-helloworld-8d7468b76-ckgtr.
2025-03-09 08:43:49,561 INFO  org.apache.flink.runtime.entrypoint.ClusterEntrypoint        [] - --------------------------------------------------------------------------------
2025-03-09 08:43:49,565 INFO  org.apache.flink.runtime.entrypoint.ClusterEntrypoint        [] -  Preconfiguration: 
....
....
2025-03-09 08:44:22,366 INFO  org.apache.flink.runtime.resourcemanager.slotmanager.DefaultSlotStatusSyncer [] - Freeing slot b8a2b8fc9c054fbe2fe7a23b13bed31a.
2025-03-09 08:44:23,597 INFO  org.apache.flink.client.deployment.application.ApplicationDispatcherBootstrap [] - Application completed SUCCESSFULLY
```

14. Upon successful deployment, ensure all pods and its associated container(s) are up and `Running`.
```
# kubectl get pods -n csa-operator 
NAME                                        READY   STATUS    RESTARTS      AGE
flink-kubernetes-operator-f67b98774-rvhsb   2/2     Running   2 (24m ago)   161m
flink-kubernetes-tutorial-557c46fdc-hbb9d   1/1     Running   0             15m
flink-kubernetes-tutorial-taskmanager-1-1   1/1     Running   0             14m
ssb-postgresql-844bbb6c5b-9hprs             1/1     Running   0             161m
ssb-sse-58cf4cf8c6-r8xqf                    1/1     Running   1 (24m ago)   161m
```

15. Note that `pyflink-helloworld` and `pyflink-helloworld-rest` services have been created automatically.
```
# kubectl -n csa-ssb get svc
NAME                             TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)             AGE
flink-operator-webhook-service   ClusterIP   10.43.199.16   <none>        443/TCP             25h
pyflink-helloworld               ClusterIP   None           <none>        6123/TCP,6124/TCP   5m6s
pyflink-helloworld-rest          ClusterIP   10.43.247.39   <none>        8081/TCP            5m6s
ssb-sse                          ClusterIP   10.43.2.207    <none>        18121/TCP           25h
```

16. Expose the Flink REST service to the external network by deploying the `ingress-flink.yml` file.
```
# kubectl -n csa-operator apply -f ingress-flink-helloworld.yaml
ingress.networking.k8s.io/ingress-flink created

# kubectl -n csa-ssb get ingress
NAME                       CLASS    HOSTS                             ADDRESS   PORTS   AGE
ingress-flink-helloworld   <none>   myflink.apps.dlee1.cldr.example             80      12s
```

17. You may now browse the Flink dashboard as follows.
<img width="1421" alt="image" src="https://github.com/user-attachments/assets/0ab02dd2-b81e-4522-8780-83ce809c3387" />

18. Expose the SSB UI service to the external network by deploying the `ingress-ssb.yml` file.
```
# kubectl -n csa-operator apply -f ingress-ssb.yml
ingress.networking.k8s.io/ingress-ssb created

# kubectl -n csa-operator get ingress ingress-ssb 
NAME          CLASS    HOSTS                           ADDRESS         PORTS   AGE
ingress-ssb   <none>   myssb.apps.dlee1.cldr.example   10.129.83.133   80      62s
```

19. Browse SSB dashboard at `http://myssb.apps.dlee1.cldr.example` and login as admin user.
<img width="1419" alt="image" src="https://github.com/user-attachments/assets/7ce5c9dd-564a-4083-9259-b6c6fbd6602b" />






```
# kubectl create secret generic ssb-sampling-kafka -n csa-ssb \
--from-literal=SSB_SAMPLING_BOOTSTRAP_SERVERS=my-cluster-kafka-brokers.dlee-kafkanodepool.svc.cluster.local:9092 \
--from-literal=SSB_SAMPLING_SECURITY_PROTOCOL=PLAINTEXT
```



```

```
