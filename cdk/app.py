#!/usr/bin/env python3
# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import os

from aws_cdk import core

from build_infra.build_infra_stack import BuildInfraStack
from container_infra.container_infra_stack import ContainerInfraStack

env = core.Environment(account=os.environ["CDK_DEPLOY_ACCOUNT"],
                       region=os.environ["CDK_DEPLOY_REGION"])

k8sVer = os.environ["KUBERNETES_VERSION"]
codeRepoName = os.environ["CODE_REPOSITORY_NAME"]
ecrRepoName = os.environ["ECR_REPOSITORY_NAME"]

app = core.App()

containerInfraStack = ContainerInfraStack(app,
                                          "container-infra-stack",
                                          k8sVersionTxt=k8sVer,
                                          env=env)

buildInfraStack = BuildInfraStack(app,
                                  "build-infra-stack",
                                  eks=containerInfraStack.eks,
                                  codeRepoName=codeRepoName,
                                  ecrRepoName=ecrRepoName,
                                  env=env)

app.synth()
