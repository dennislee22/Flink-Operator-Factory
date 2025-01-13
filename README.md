# Flink-Operator

```
# oc create ns csa-operator
namespace/csa-operator created

# kubectl create secret docker-registry cfm-credential --docker-server container.repository.cloudera.com --docker-username xxx --docker-password yyy --namespace csa-operator
secret/cfm-credential created

# helm registry login container.repository.cloudera.com
Username: cde1c910-c09e-4f44-a966-0718bffb6106
Password: 
Login Succeeded

# helm install csa-operator --namespace csa-operator --set 'flink-kubernetes-operator.imagePullSecrets[0].name=cfm-credential' --set 'ssb.sse.image.imagePullSecrets[0].name=cfm-credential' --set 'ssb.sqlRunner.image.imagePullSecrets[0].name=cfm-credential' --set-file flink-kubernetes-operator.clouderaLicense.fileContent=/cloudera_license.txt oci://container.repository.cloudera.com/cloudera-helm/csa-operator/csa-operator --version 1.1.2-b17  
Pulled: container.repository.cloudera.com/cloudera-helm/csa-operator/csa-operator:1.1.2-b17
Digest: sha256:df29576c99a6a98ac69f46ca0bd9f09e02eeb3a408c99076be0030784a7d84da
NAME: csa-operator
LAST DEPLOYED: Mon Jan 13 01:13:23 2025
NAMESPACE: csa-operator
STATUS: deployed
REVISION: 1
TEST SUITE: None
```
