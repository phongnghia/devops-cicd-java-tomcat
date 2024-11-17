from aws_cdk import (
    SecretValue,
    Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_elasticloadbalancingv2_targets as targets,
    aws_codebuild as codebuild,
    aws_iam as iam,
)
import yaml
import os
from constructs import Construct


class DevopsCicdJavaTomcatStack(Stack):

    def __init__(self, scope: Construct, id: str, environment: str = None, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        env_params = self._load_parameters(environment)

        # Initialize Pipeline
        source_output = codepipeline.Artifact()
        build_output = codepipeline.Artifact()
        pipeline = codepipeline.Pipeline(self, "Pipeline")

        # Source Stage
        self._add_source_stage(pipeline, source_output)

        # Build Stage
        self._add_build_stage(pipeline, source_output, build_output)

        # Test Stage
        self._add_test_stage(pipeline, source_output, env_params)

        # # Deploy Stage
        self._add_deploy_stage(pipeline)

    def _load_parameters(self, environment: str) -> dict:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parameters_path = os.path.join(current_dir, "parameters.yaml")

        try:
            with open(parameters_path, 'r') as file:
                params = yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError("The 'parameters.yaml' file is missing.")

        if not environment or environment not in params:
            environment = "default"

        if environment not in params:
            raise KeyError(f"Environment '{environment}' is not defined in parameters.yaml.")

        return params[environment]

    def _add_source_stage(self, pipeline: codepipeline.Pipeline, source_output: codepipeline.Artifact) -> None:
        pipeline.add_stage(
            stage_name="Source",
            actions=[
                codepipeline_actions.GitHubSourceAction(
                    action_name="GitHub_SourceCode",
                    owner="phongnghia",
                    repo="devops-cicd-java-tomcat",
                    branch="main",
                    oauth_token=SecretValue.secrets_manager('github-token'),
                    output=source_output,
                )
            ]
        )

    def _add_build_stage(self, pipeline: codepipeline.Pipeline, source_output: codepipeline.Artifact, build_output: codepipeline.Artifact) -> None:
        build_project = codebuild.PipelineProject(
            self,
            "Build",
            build_spec=codebuild.BuildSpec.from_source_filename("java_tomcat_application/buildspec.yml"),
        )

        pipeline.add_stage(
            stage_name="Build",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="Build",
                    project=build_project,
                    input=source_output,
                    outputs=[build_output],
                )
            ]
        )

    def _add_test_stage(self, pipeline: codepipeline.Pipeline, source_output: codepipeline.Artifact, env_params: dict) -> None:
        vpc = ec2.Vpc.from_lookup(self, "Test-VPC", vpc_id="vpc-02fa5b99649483e11")
        security_group = ec2.SecurityGroup(self, "TestSecurityGroup", vpc=vpc)
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(8080), "Allow Tomcat traffic")

        subnets = ec2.SubnetSelection(
            subnets=[
                ec2.Subnet.from_subnet_attributes(
                    self,
                    "SubnetIP32",
                    subnet_id="subnet-0c9e7687ebf7b8141",
                    availability_zone="ap-southeast-1b",
                )
            ]
        )

        instance = ec2.Instance(
            self,
            "TestInstance",
            instance_type=ec2.InstanceType(env_params.get('instance_type', 't2.micro')),
            machine_image=ec2.MachineImage.latest_amazon_linux(),
            vpc=vpc,
            vpc_subnets=subnets,
            role=iam.Role(
                self,
                "InstanceRole",
                assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            ),
            security_group=security_group,
        )

        # Load Balancer
        lb = elbv2.ApplicationLoadBalancer(self, "LB", vpc=vpc, internet_facing=True)
        listener = lb.add_listener("Listener", port=80)
        listener.add_targets("Target", port=8080, targets=[targets.InstanceTarget(instance)])

        instance.add_user_data(
            """
            #!/bin/bash
            echo "Installing Java 17"
            sudo apt update -y
            sudo apt install openjdk-17-jdk -y
            # echo "Installing Tomcat 9.0.86"
            # wget https://archive.apache.org/dist/tomcat/tomcat-9/v9.0.86/bin/apache-tomcat-9.0.86.tar.gz
            # tar -xvzf apache-tomcat-9.0.86.tar.gz
            # mv apache-tomcat-9.0.86 /opt/tomcat
            # echo "Tomcat installed to /opt/tomcat"
            # groupadd tomcat
            # useradd -r -s /bin/false -g tomcat tomcat
            # chown -R tomcat:tomcat /opt/tomcat
            # cp deploy/tomcat.service /etc/systemd/system/tomcat.service
            # aws s3 cp s3://devopscicdjavatomcatstack-pipelineartifactsbucket2-ops076t0rsuk/${CODEBUILD_ARTIFACT_NAME} /usr/share/tomcat/webapps/ROOT.war
            # systemctl daemon-reload
            # systemctl enable tomcat
            # systemctl start tomcat
            """
        )

        # Test Project
        test_project = codebuild.PipelineProject(
            self,
            "TestProject",
            build_spec=codebuild.BuildSpec.from_source_filename("tests/buildspec.yml")
            # build_spec=codebuild.BuildSpec.from_object({
            #     "version": "0.2",
            #     "phases": {
            #         "build": {
            #             "commands": [
            #                 "cd java_tomcat_application",
            #                 "mvn clean package",
            #                 "echo Installing Java 17",
            #                 "sudo apt update -y",
            #                 "sudo apt install openjdk-17-jdk -y",
            #                 "echo Installing Tomcat 9.0.86",
            #                 "wget https://archive.apache.org/dist/tomcat/tomcat-9/v9.0.86/bin/apache-tomcat-9.0.86.tar.gz",
            #                 "tar -xvzf apache-tomcat-9.0.86.tar.gz",
            #                 "mv apache-tomcat-9.0.86 /opt/tomcat",
            #                 "echo Tomcat installed to /opt/tomcat",
            #                 "groupadd tomcat",
            #                 "useradd -r -s /bin/false -g tomcat tomcat",
            #                 "chown -R tomcat:tomcat /opt/tomcat",
            #                 "cp ../deploy/tomcat.service /etc/systemd/system/tomcat.service",
            #                 "cp target/*.war /usr/share/tomcat/webapps/java_tomcat_application.war",
            #                 "systemctl daemon-reload",
            #                 "systemctl enable tomcat",
            #                 "systemctl start tomcat",
            #                 "echo Installing dependencies",
            #                 "curl -O https://bootstrap.pypa.io/get-pip.py",
            #                 "python3 get-pip.py",
            #                 "pip install requests",
            #                 "echo Running API tests",
            #                 "python ../tests/test_api.py"
            #             ]
            #         }
            #     },
            #     "artifacts": {
            #         "files": ["**/*"]
            #     }
            # }),
        )

        pipeline.add_stage(
            stage_name="Test",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="Test",
                    project=test_project,
                    input=source_output,
                )
            ]
        )

    def _add_deploy_stage(self, pipeline: codepipeline.Pipeline) -> None:
        pipeline.add_stage(
            stage_name="Deploy",
            actions=[
                codepipeline_actions.ManualApprovalAction(action_name="ManualApproval"),
            ]
        )
