# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (core, aws_lambda as lambda_, aws_s3 as s3, aws_eks as eks,
                     aws_iam as iam, aws_ec2 as ec2, aws_ssm as ssm)

import json


class ContainerInfraStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, k8sVersionTxt: str,
                 **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        # create new vpc
        vpc = ec2.Vpc(self, "VPC")

        # create eks
        self.eks = self.create_eks(vpc, k8sVersionTxt)

    def create_eks(self, vpc, k8sVersionTxt):

        # map input k8s version string to eks.KubernetesVersion object
        k8sVersion = self.getK8sVersion(k8sVersionTxt)

        # initialize bottlerocket arm64 AMI id from SSM parameter store
        bottleRkt_arm64Ami = ssm.StringParameter.value_for_string_parameter(
            self, "/aws/service/bottlerocket/aws-k8s-" + k8sVersionTxt +
            "/arm64/latest/image_id")

        # initialize bottlerocket x86 AMI id from SSM parameter store
        bottleRkt_x86Ami = ssm.StringParameter.value_for_string_parameter(
            self, "/aws/service/bottlerocket/aws-k8s-" + k8sVersionTxt +
            "/x86_64/latest/image_id")

        # create eks cluster
        cluster = eks.Cluster(self,
                              "EKS",
                              vpc=vpc,
                              version=k8sVersion,
                              default_capacity=0)

        # prepare userdata in TOML format
        clusterCertAuthorityData = cluster.cluster_certificate_authority_data
        clusterEndpoint = cluster.cluster_endpoint
        clusterName = cluster.cluster_name
        userdata = "settings.kubernetes.api-server = \"" + \
                    clusterEndpoint + \
                    "\"\nsettings.kubernetes.cluster-certificate = \"" + \
                    clusterCertAuthorityData + \
                    "\"\nsettings.kubernetes.cluster-name = \"" \
                    + clusterName + "\""
        core.CfnOutput(self, "EC2-Instance-UserData", value=userdata)

        # create a launch template for arm64
        launchTemplData = ec2.CfnLaunchTemplate.LaunchTemplateDataProperty(
            image_id=bottleRkt_arm64Ami,
            instance_type="c6g.medium",
            user_data=core.Fn.base64(userdata))

        launchTempl = ec2.CfnLaunchTemplate(
            self,
            id="bottle_arm64_lt",
            launch_template_data=launchTemplData,
            launch_template_name="bottlerocket-arm64-launchTempl")

        launchTemplSpec = eks.LaunchTemplateSpec(
            id=launchTempl.ref,
            version=launchTempl.attr_default_version_number)

        # add arm/graviton nodegroup
        ng = cluster.add_nodegroup_capacity(
            "bottle_arm64_ng",
            desired_size=1,
            nodegroup_name="bottlerocket_arm64_ng",
            launch_template_spec=launchTemplSpec)

        # add ssm access and secret access to eks node role
        ng.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSSMManagedInstanceCore"))
        ng.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "SecretsManagerReadWrite"))

        # Now repeat the same steps for x86
        # create a launch template for x86
        launchTemplData = ec2.CfnLaunchTemplate.LaunchTemplateDataProperty(
            image_id=bottleRkt_x86Ami,
            instance_type="c5.large",
            user_data=core.Fn.base64(userdata))
        launchTempl = ec2.CfnLaunchTemplate(
            self,
            id="bottle_x86_lt",
            launch_template_data=launchTemplData,
            launch_template_name="bottlerocket-x86-launchTempl")
        launchTemplSpec = eks.LaunchTemplateSpec(
            id=launchTempl.ref,
            version=launchTempl.attr_default_version_number)

        # add x86 nodegroup
        ng = cluster.add_nodegroup_capacity(
            "bottle_x86_ng",
            desired_size=1,
            nodegroup_name="bottlerocket_x86_ng",
            launch_template_spec=launchTemplSpec)

        # add ssm access and secret access to eks node role
        ng.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSSMManagedInstanceCore"))
        ng.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "SecretsManagerReadWrite"))

        return cluster

    @staticmethod
    def getK8sVersion(k8sVersionTxt):
        if (k8sVersionTxt == '1.19'):
            k8sVersion = eks.KubernetesVersion.V1_19
        elif (k8sVersionTxt == '1.18'):
            k8sVersion = eks.KubernetesVersion.V1_18
        elif (k8sVersionTxt == '1.17'):
            k8sVersion = eks.KubernetesVersion.V1_17
        elif (k8sVersionTxt == '1.16'):
            k8sVersion = eks.KubernetesVersion.V1_16
        elif (k8sVersionTxt == '1.15'):
            k8sVersion = eks.KubernetesVersion.V1_15
        else:
            print("Input argument for K8s version txt is not valid, exiting")
            exit(1)

        return k8sVersion
