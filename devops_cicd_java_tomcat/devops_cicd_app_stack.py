from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_autoscaling as autoscaling,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as cp_actions,
)
from constructs import Construct

class AppStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Load parameters from parameters.yaml
        with open('parameters.yaml') as file:
            params = yaml.safe_load(file)
        
        env_params = params

        # VPC
        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id="vpc-xxxxxxx")  # Replace with your VPC ID

        # Security Group
        security_group = ec2.SecurityGroup(self, "SG", vpc=vpc)
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(8080))  # Tomcat default port

        # EC2 Instance
        ami = ec2.MachineImage.latest_amazon_linux()
        instance_role = iam.Role.from_role_arn(self, "InstanceRole", "arn:aws:iam::123456789012:role/your-role")  # Replace with your IAM role

        # Auto Scaling Group
        asg = autoscaling.AutoScalingGroup(self, "ASG",
            vpc=vpc,
            instance_type=ec2.InstanceType(env_params['instance_type']),
            machine_image=ami,
            min_capacity=env_params['min_size'],
            max_capacity=env_params['max_size'],
            role=instance_role,
            security_group=security_group
        )

        # Load Balancer
        lb = elbv2.ApplicationLoadBalancer(self, "LB", vpc=vpc, internet_facing=True)
        listener = lb.add_listener("Listener", port=80)
        listener.add_targets("Target", port=8080, targets=[asg])