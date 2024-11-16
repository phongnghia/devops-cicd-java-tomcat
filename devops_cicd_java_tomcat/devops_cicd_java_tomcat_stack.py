from ast import arg
from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_autoscaling as autoscaling,
    aws_elasticloadbalancingv2 as elbv2,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codebuild as codebuild,
    aws_iam as iam
)
import yaml

class DevopsCicdJavaTomcatStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # CodePipeline
        source_output = codepipeline.Artifact()
        build_output = codepipeline.Artifact()

        pipeline = codepipeline.Pipeline(self, "Pipeline")

        # Source Stage
        pipeline.add_stage(
            stage_name="Source",
            actions=[
                codepipeline_actions.GitHubSourceAction(
                    action_name="GitHub_SourceCode",
                    owner="phongnghia",
                    repo="devops-cicd-java-tomcat",
                    branch="main",
                    oauth_token=core.SecretValue.secrets_manager("github-token"),
                    output=source_output,
                )
            ]
        )

        # Build Stage
        build_project = codebuild.PipelineProject(self, "Build",
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml")
        )

        pipeline.add_stage(
            stage_name="Build",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="Build",
                    project=build_project,
                    input=source_output,
                    outputs=[build_output]
                )
            ]
        )

        # Deploy Stage
        pipeline.add_stage(
            stage_name="Deploy",
            actions=[
                codepipeline_actions.EcsDeployAction(
                    action_name="Deploy",
                    service=arg,
                    input=build_output,
                )
            ]
        )