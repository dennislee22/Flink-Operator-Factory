# Flink + SQL Stream Operator: Real-Time Stream Processing

<img width="811" alt="image" src="https://github.com/user-attachments/assets/f8c0b546-0faf-4bd3-af50-9f4c2571e425" />

Apache Flink, coupled with SQL Stream Builder (SSB), provides a robust platform for building scalable, real-time stream processing applications. Whether you're building real-time analytics, monitoring systems, or complex event-driven applications, Flink's support for SQL-based stream processing ensures that developers can quickly express complex logic while taking advantage of Flink’s powerful features like event-time processing, windowing, and fault tolerance. By abstracting the complexity of stream processing behind familiar SQL syntax, SSB democratizes real-time data analytics, enabling teams to deliver actionable insights faster and more efficiently.
In this article, I will explain the installation procedures for CSA (Cloudera Streaming Analytics) operator on a Kubernetes cluster, harnessing cloud-native benefits such as self-healing, declarative deployments, and scalability.

1. In the existing Kubernetes cluster (version 1.23 or later), create a new namespace.
```
# kubectl create ns csa-operator
namespace/csa-operator created
```

2. Create a secret object in the same namespace to store your Cloudera credentials.
```
# kubectl create secret docker-registry cfm-credential --docker-server container.repository.cloudera.com --docker-username xxx --docker-password yyy --namespace csa-operator
secret/cfm-credential created
```

3. Log into Cloudera registry.
 ```
# helm registry login container.repository.cloudera.com
Username: xxx
Password: yyy
Login Succeeded
```

4. Deploy the CSA Operator as follows. Other helm options can be obtained [here](https://docs.cloudera.com/csa-operator/1.1/reference/topics/csa-op-reference.html). 
```
# helm install csa-operator --namespace csa-operator --set 'flink-kubernetes-operator.imagePullSecrets[0].name=cfm-credential' --set 'ssb.sse.image.imagePullSecrets[0].name=cfm-credential' --set 'ssb.sqlRunner.image.imagePullSecrets[0].name=cfm-credential' --set-file flink-kubernetes-operator.clouderaLicense.fileContent=/license.txt  oci://container.repository.cloudera.com/cloudera-helm/csa-operator/csa-operator --version 1.1.2-b17 -f ./tochange.yml  
```

5. Upon successful deployment, ensure all pods and its associated containers are up and `Running`.
```
# kubectl get pods -n csa-operator
NAME                                        READY   STATUS    RESTARTS   AGE
flink-kubernetes-operator-f67b98774-rvhsb   2/2     Running   0          2m31s
ssb-postgresql-844bbb6c5b-9hprs             1/1     Running   0          2m31s
ssb-sse-58cf4cf8c6-r8xqf                    1/1     Running   0          2m31s

# kubectl -n csa-operator get pvc
NAME                STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
ssb-postgresql-db   Bound    pvc-5a36ee80-c7d6-4ca4-9025-2ddc6cc6a1e4   100Mi      RWO            longhorn       2m42s

# kubectl -n csa-operator get all
NAME                                            READY   STATUS    RESTARTS   AGE
pod/flink-kubernetes-operator-f67b98774-rvhsb   2/2     Running   0          3m29s
pod/ssb-postgresql-844bbb6c5b-9hprs             1/1     Running   0          3m29s
pod/ssb-sse-58cf4cf8c6-r8xqf                    1/1     Running   0          3m29s

NAME                                     TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)     AGE
service/flink-operator-webhook-service   ClusterIP   10.43.44.57     <none>        443/TCP     3m29s
service/ssb-postgresql                   ClusterIP   10.43.72.57     <none>        5432/TCP    3m29s
service/ssb-sse                          ClusterIP   10.43.152.255   <none>        18121/TCP   3m29s

NAME                                        READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/flink-kubernetes-operator   1/1     1            1           3m29s
deployment.apps/ssb-postgresql              1/1     1            1           3m29s
deployment.apps/ssb-sse                     1/1     1            1           3m29s

NAME                                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/flink-kubernetes-operator-f67b98774   1         1         1       3m29s
replicaset.apps/ssb-postgresql-844bbb6c5b             1         1         1       3m29s
replicaset.apps/ssb-sse-58cf4cf8c6                    1         1         1       3m29s
```

6. Next, deploy the Flink application. This step involves building a docker image, push it to the external docker registry with certified CA. Also, ensure that `git` and `maven` tools are already deployed in your client system before proceeding with the following steps.
```
# git clone https://github.com/cloudera/flink-tutorials.git -b CSA-OPERATOR-1.0.0
# cd flink-tutorials/flink-kubernetes-tutorial
# mvn clean package
# docker build -t flink-kubernetes-tutorial .
STEP 1/2: FROM flink:1.18
✔ docker.io/library/flink:1.18

# podman image ls
REPOSITORY                           TAG         IMAGE ID      CREATED        SIZE
localhost/flink-kubernetes-tutorial  latest      71d28938a00b  3 minutes ago  804 MB
docker.io/library/flink              1.18        b9caebf65539  7 months ago   802 MB

# podman login nexus.dlee1.cldr.example:9999
Username: admin
Password: 
Login Succeeded!

# podman image tag flink-kubernetes-tutorial nexus.dlee1.cldr.example:9999/pvcds/flink-kubernetes-tutorial:latest

# podman image ls
REPOSITORY                                                     TAG         IMAGE ID      CREATED        SIZE
localhost/flink-kubernetes-tutorial                            latest      71d28938a00b  6 minutes ago  804 MB
nexus.dlee1.cldr.example:9999/pvcds/flink-kubernetes-tutorial  latest      71d28938a00b  6 minutes ago  804 MB
docker.io/library/flink                                        1.18        b9caebf65539  7 months ago   802 MB

# podman push nexus.dlee1.cldr.example:9999/pvcds/flink-kubernetes-tutorial
Getting image source signatures

Copying blob 91afbf47d141 done  
Copying config 71d28938a0 done  
Writing manifest to image destination
Storing signatures
```

7. Deploy the Flink application by applying the `flink-deployment.yml` file.

8. Upon successful deployment, ensure all pods and its associated container(s) are up and `Running`.
```
# kubectl get pods -n csa-operator 
NAME                                        READY   STATUS    RESTARTS      AGE
flink-kubernetes-operator-f67b98774-rvhsb   2/2     Running   2 (24m ago)   161m
flink-kubernetes-tutorial-557c46fdc-hbb9d   1/1     Running   0             15m
flink-kubernetes-tutorial-taskmanager-1-1   1/1     Running   0             14m
ssb-postgresql-844bbb6c5b-9hprs             1/1     Running   0             161m
ssb-sse-58cf4cf8c6-r8xqf                    1/1     Running   1 (24m ago)   161m
```

9. Check out the services exposed inside the namespace.
```
# kubectl -n csa-operator get svc
NAME                             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)             AGE
flink-kubernetes-tutorial        ClusterIP   None            <none>        6123/TCP,6124/TCP   16m
flink-kubernetes-tutorial-rest   ClusterIP   10.43.111.1     <none>        8081/TCP            16m
flink-operator-webhook-service   ClusterIP   10.43.44.57     <none>        443/TCP             162m
ssb-postgresql                   ClusterIP   10.43.72.57     <none>        5432/TCP            162m
ssb-sse                          ClusterIP   10.43.152.255   <none>        18121/TCP           162m
```

10. Expose the Flink REST service to the external network by deploying the `ingress-flink.yml` file.
```
# kubectl -n csa-operator apply -f ingress-flink.yml 
ingress.networking.k8s.io/ingress-flink created

# kubectl -n csa-operator get ingress
NAME            CLASS    HOSTS                             ADDRESS         PORTS   AGE
ingress-flink   <none>   myflink.apps.dlee1.cldr.example   10.129.83.133   80      3m46s
```

11. You may now browse the Flink dashboard as follows.
<img width="1421" alt="image" src="https://github.com/user-attachments/assets/0ab02dd2-b81e-4522-8780-83ce809c3387" />

12. Expose the SSB UI service to the external network by deploying the `ingress-ssb.yml` file.
```
# kubectl -n csa-operator apply -f ingress-ssb.yml
ingress.networking.k8s.io/ingress-ssb created

# kubectl -n csa-operator get ingress ingress-ssb 
NAME          CLASS    HOSTS                           ADDRESS         PORTS   AGE
ingress-ssb   <none>   myssb.apps.dlee1.cldr.example   10.129.83.133   80      62s
```

13. Browse SSB dashboard at `http://myssb.apps.dlee1.cldr.example` and login as admin user.
<img width="1419" alt="image" src="https://github.com/user-attachments/assets/7ce5c9dd-564a-4083-9259-b6c6fbd6602b" />




```
# mvn clean package
[INFO] Scanning for projects...
[INFO] ------------------------------------------------------------------------
[INFO] Reactor Build Order:
[INFO] 
[INFO] Flink Tutorials                                                    [pom]
[INFO] Flink Master :: Pyflink Kafka                                      [jar]
[INFO] 
[INFO] ------------------< com.cloudera.flink:flink-master >-------------------
[INFO] Building Flink Tutorials 1.19.1-csaop1.1.2                         [1/2]
[INFO] --------------------------------[ pom ]---------------------------------
[INFO] 
[INFO] --- maven-clean-plugin:2.5:clean (default-clean) @ flink-master ---
[INFO] 
[INFO] ------------------< com.cloudera.flink:pyflink-kafka >------------------
[INFO] Building Flink Master :: Pyflink Kafka 1.19.1-csaop1.1.2           [2/2]
[INFO] --------------------------------[ jar ]---------------------------------
[INFO] 
[INFO] --- maven-clean-plugin:2.5:clean (default-clean) @ pyflink-kafka ---
[INFO] Deleting /root/flink-master/pyflink-kafka/target
...
...
...
[INFO] Replacing original artifact with shaded artifact.
[INFO] Replacing /root/flink-master/pyflink-kafka/target/pyflink-kafka-1.19.1-csaop1.1.2.jar with /root/flink-master/pyflink-kafka/target/pyflink-kafka-1.19.1-csaop1.1.2-shaded.jar
[INFO] ------------------------------------------------------------------------
[INFO] Reactor Summary:
[INFO] 
[INFO] Flink Tutorials 1.19.1-csaop1.1.2 .................. SUCCESS [  0.119 s]
[INFO] Flink Master :: Pyflink Kafka 1.19.1-csaop1.1.2 .... SUCCESS [  7.710 s]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
[INFO] Total time: 7.929 s
[INFO] Finished at: 2025-01-28T09:23:58Z
[INFO] ------------------------------------------------------------------------
```


```
# podman build -t pyflink-oss-kafka .
# podman image tag pyflink-oss-kafka nexus.dlee1.cldr.example:9999/pvcds/pyflink-oss-kafka:latest
# podman push nexus.dlee1.cldr.example:9999/pvcds/pyflink-oss-kafka
# curl -u admin:admin  https://admin:admin@nexus.dlee1.cldr.example:9999/v2/pvcds/pyflink-oss-kafka/tags/list | jq
{
  "name": "pvcds/pyflink-oss-kafka",
  "tags": [
    "latest"
  ]
}
```

```

```
