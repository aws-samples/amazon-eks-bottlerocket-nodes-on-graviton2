# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (core, aws_codebuild as codebuild, aws_codecommit as
                     codecommit, aws_codepipeline as codepipeline,
                     aws_codepipeline_actions as codepipeline_actions,
                     aws_lambda as lambda_, aws_s3 as s3, aws_iam as iam,
                     aws_ecr as ecr)


class BuildInfraStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, eks, codeRepoName: str,
                 ecrRepoName: str, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        self.eks = eks

        # create ECR
        ecr_repo = ecr.Repository(self, "ECRRep", repository_name=ecrRepoName)

        # create code repo
        code = codecommit.Repository(self,
                                     "CodeRep",
                                     repository_name=codeRepoName)
        core.CfnOutput(self,
                       "CodeCommitOutput_repository-url",
                       value=code.repository_clone_url_http)

        # create code builds
        arm_build = codebuild.PipelineProject(
            self,
            "ARMBuild",
            build_spec=codebuild.BuildSpec.from_source_filename(
                "cdk/build_infra/arm_buildspec.yml"),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_ARM,
                privileged=True),
            environment_variables=self.get_build_env_vars(ecr_repo))
        self.add_role_access_to_build(arm_build)

        amd_build = codebuild.PipelineProject(
            self,
            "AMDBuild",
            build_spec=codebuild.BuildSpec.from_source_filename(
                "cdk/build_infra/amd_buildspec.yml"),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                privileged=True),
            environment_variables=self.get_build_env_vars(ecr_repo))
        self.add_role_access_to_build(amd_build)

        post_build = codebuild.PipelineProject(
            self,
            "PostBuild",
            build_spec=codebuild.BuildSpec.from_source_filename(
                "cdk/build_infra/post_buildspec.yml"),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                privileged=True),
            environment_variables=self.get_build_env_vars(ecr_repo))
        self.add_role_access_to_build(post_build)

        # create pipeline
        source_output = codepipeline.Artifact()
        arm_build_output = codepipeline.Artifact("ARMBuildOutput")
        amd_build_output = codepipeline.Artifact("AMDBuildOutput")
        post_build_output = codepipeline.Artifact("PostBuildOutput")

        codepipeline.Pipeline(
            self,
            "Pipeline",
            stages=[
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[
                        codepipeline_actions.CodeCommitSourceAction(
                            action_name="CodeCommit_Source",
                            repository=code,
                            output=source_output)
                    ]),
                codepipeline.StageProps(
                    stage_name="Build",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="ARM_Build",
                            project=arm_build,
                            input=source_output,
                            outputs=[arm_build_output]),
                        codepipeline_actions.CodeBuildAction(
                            action_name="AMD_Build",
                            project=amd_build,
                            input=source_output,
                            outputs=[amd_build_output]),
                    ]),
                codepipeline.StageProps(
                    stage_name="PostBuild",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="Post_Build",
                            project=post_build,
                            input=source_output,
                            outputs=[post_build_output])
                    ]),
            ])

    def add_role_access_to_build(self, build):
        build.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonEC2ContainerRegistryFullAccess"))
        build.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSSMReadOnlyAccess"))
        build.add_to_role_policy(
            iam.PolicyStatement(
                actions=["kms:Decrypt", "kms:GenerateDataKey*"],
                resources=["*"]))
        build.add_to_role_policy(
            iam.PolicyStatement(actions=[
                "eks:DescribeNodegroup", "eks:DescribeFargateProfile",
                "eks:DescribeUpdate", "eks:DescribeCluster"
            ],
                                resources=["*"]))
        build.add_to_role_policy(
            iam.PolicyStatement(actions=["sts:AssumeRole"],
                                resources=[self.eks.kubectl_role.role_arn]))

    def get_build_env_vars(self, ecr_repo):
        return {
            "REPOSITORY_URI":
            codebuild.BuildEnvironmentVariable(value=ecr_repo.repository_uri),
            "DOCKERHUB_USERNAME":
            codebuild.BuildEnvironmentVariable(
                value="/hello-bottlerocket/dockerhub/username",
                type=codebuild.BuildEnvironmentVariableType.PARAMETER_STORE),
            "DOCKERHUB_PASSWORD":
            codebuild.BuildEnvironmentVariable(
                value="/hello-bottlerocket/dockerhub/password",
                type=codebuild.BuildEnvironmentVariableType.PARAMETER_STORE),
            "EKS_NAME":
            codebuild.BuildEnvironmentVariable(value=self.eks.cluster_name),
            "EKS_ROLE":
            codebuild.BuildEnvironmentVariable(
                value=self.eks.kubectl_role.role_arn),
        }
