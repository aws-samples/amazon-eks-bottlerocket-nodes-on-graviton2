#!/bin/bash
if [[ $# -eq 2 ]]; then
    export CDK_DEPLOY_ACCOUNT=$1
    export CDK_DEPLOY_REGION=$2
    export CODE_REPOSITORY_NAME=hello-bottlerocket-multi-cpu-arch
    export ECR_REPOSITORY_NAME=hello-bottlerocket-multi-cpu-arch
    # initialize the Kubernetes version for the EKS cluster and for AMI version
    export KUBERNETES_VERSION=1.19
    source .env/bin/activate

    # Delete the kubernetes resources first
    kubectl delete -f ../app/kubernetes.yaml

    # Delete the ECR repo since undoing the cdk stack will not get rid of this repo
    aws ecr delete-repository --repository-name $ECR_REPOSITORY_NAME --region $CDK_DEPLOY_REGION --force
    # Destroy the cdk stacks we created
    cdk destroy build-infra-stack container-infra-stack

    exit $?
else
    echo 1>&2 "Provide AWS account and region as two input args."
    exit 1
fi
