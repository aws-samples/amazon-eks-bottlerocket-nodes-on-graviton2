#!/usr/bin/env bash
if [[ $# -eq 2 ]]; then
    source .env/bin/activate
    pip install -r requirements.txt
    export CDK_DEPLOY_ACCOUNT=$1
    export CDK_DEPLOY_REGION=$2
    export CODE_REPOSITORY_NAME=hello-bottlerocket-multi-cpu-arch
    export ECR_REPOSITORY_NAME=hello-bottlerocket-multi-cpu-arch
    # initialize the Kubernetes version for the EKS cluster and for AMI version
    export KUBERNETES_VERSION=1.19
    cdk bootstrap aws://$1/$2
    cdk deploy build-infra-stack
    exit $?
else
	echo 1>&2 "Provide AWS account and region as two input args."
    exit 1
fi
