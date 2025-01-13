# Flink + SQL Stream Operator: Real-Time Stream Processing

<img width="594" alt="image" src="https://github.com/user-attachments/assets/93a9f8b7-5be8-46bc-a354-2608eabcd04e" />

Apache Flink, coupled with SQL Stream Builder (SSB), provides a robust platform for building scalable, real-time stream processing applications. Whether you're building real-time analytics, monitoring systems, or complex event-driven applications, Flink's support for SQL-based stream processing ensures that developers can quickly express complex logic while taking advantage of Flink’s powerful features like event-time processing, windowing, and fault tolerance. By abstracting the complexity of stream processing behind familiar SQL syntax, SQL Stream Builder democratizes real-time data analytics, enabling teams to deliver actionable insights faster and more efficiently.
In this article, I will explain the installation procedures for Apache Flink and the SSB operator on a Kubernetes cluster, harnessing cloud-native benefits such as self-healing, declarative deployments, and scalability.

1. In the existing Kubernetes cluster, create a new namespace.
```
# oc create ns csa-operator
namespace/csa-operator created
```

2. 
```
# kubectl create secret docker-registry cfm-credential --docker-server container.repository.cloudera.com --docker-username xxx --docker-password yyy --namespace csa-operator
secret/cfm-credential created

# helm registry login container.repository.cloudera.com
Username: xxx
Password: yyy
Login Succeeded

# helm install csa-operator --namespace csa-operator --set 'flink-kubernetes-operator.imagePullSecrets[0].name=cfm-credential' --set 'ssb.sse.image.imagePullSecrets[0].name=cfm-credential' --set 'ssb.sqlRunner.image.imagePullSecrets[0].name=cfm-credential' --set-file flink-kubernetes-operator.clouderaLicense.fileContent=/cloudera_license.txt oci://container.repository.cloudera.com/cloudera-helm/csa-operator/csa-operator --version 1.1.2-b17  
Pulled: container.repository.cloudera.com/cloudera-helm/csa-operator/csa-operator:1.1.2-b17
Digest: sha256:df29576c99a6a98ac69f46ca0bd9f09e02eeb3a408c99076be0030784a7d8asd
NAME: csa-operator
LAST DEPLOYED: Mon Jan 13 01:13:23 2025
NAMESPACE: csa-operator
STATUS: deployed
REVISION: 1
TEST SUITE: None
```

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

- Ensure `git` and `maven` tools are already deployed in your client system before proceeding with the following steps.
```
# git clone https://github.com/cloudera/flink-tutorials.git -b CSA-OPERATOR-1.0.0
# cd flink-tutorials/flink-kubernetes-tutorial
# mvn clean package
# docker build -t flink-kubernetes-tutorial .
STEP 1/2: FROM flink:1.18
✔ docker.io/library/flink:1.18

# docker image ls
Emulate Docker CLI using podman. Create /etc/containers/nodocker to quiet msg.
REPOSITORY                           TAG         IMAGE ID      CREATED        SIZE
localhost/flink-kubernetes-tutorial  latest      71d28938a00b  3 minutes ago  804 MB
docker.io/library/flink              1.18        b9caebf65539  7 months ago   802 MB

# podman login nexus.dlee1.cldr.example:9999
Username: admin
Password: 
Login Succeeded!

# podman image tag flink-kubernetes-tutorial nexus.dlee1.cldr.example:9999/pvcds/flink-kubernetes-tutorial:latest

# docker image ls
Emulate Docker CLI using podman. Create /etc/containers/nodocker to quiet msg.
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

```
# kubectl get pods -n csa-operator 
NAME                                        READY   STATUS    RESTARTS      AGE
flink-kubernetes-operator-f67b98774-rvhsb   2/2     Running   2 (24m ago)   161m
flink-kubernetes-tutorial-557c46fdc-hbb9d   1/1     Running   0             15m
flink-kubernetes-tutorial-taskmanager-1-1   1/1     Running   0             14m
ssb-postgresql-844bbb6c5b-9hprs             1/1     Running   0             161m
ssb-sse-58cf4cf8c6-r8xqf                    1/1     Running   1 (24m ago)   161m

# kubectl -n csa-operator get svc
NAME                             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)             AGE
flink-kubernetes-tutorial        ClusterIP   None            <none>        6123/TCP,6124/TCP   16m
flink-kubernetes-tutorial-rest   ClusterIP   10.43.111.1     <none>        8081/TCP            16m
flink-operator-webhook-service   ClusterIP   10.43.44.57     <none>        443/TCP             162m
ssb-postgresql                   ClusterIP   10.43.72.57     <none>        5432/TCP            162m
ssb-sse                          ClusterIP   10.43.152.255   <none>        18121/TCP           162m
```

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-flink
  namespace: csa-operator
spec:
  rules:
  - host: myflink.apps.dlee1.cldr.example
    http:
      paths:
      - backend:
          service:
            name: flink-kubernetes-tutorial-rest
            port:
              number: 8081
        path: /
        pathType: Prefix
```

```
# kubectl -n csa-operator apply -f ingress-flink.yml 
ingress.networking.k8s.io/ingress-flink created

# kubectl -n csa-operator get ingress
NAME            CLASS    HOSTS                             ADDRESS         PORTS   AGE
ingress-flink   <none>   myflink.apps.dlee1.cldr.example   10.129.83.133   80      3m46s
```

<img width="1421" alt="image" src="https://github.com/user-attachments/assets/0ab02dd2-b81e-4522-8780-83ce809c3387" />

```
# kubectl -n csa-operator apply -f ingress-ssb.yml
ingress.networking.k8s.io/ingress-ssb created

# kubectl -n csa-operator get ingress ingress-ssb 
NAME          CLASS    HOSTS                           ADDRESS         PORTS   AGE
ingress-ssb   <none>   myssb.apps.dlee1.cldr.example   10.129.83.133   80      62s
```

- Browse `http://myssb.apps.dlee1.cldr.example ` and login as admin user.
<img width="1419" alt="image" src="https://github.com/user-attachments/assets/7ce5c9dd-564a-4083-9259-b6c6fbd6602b" />




