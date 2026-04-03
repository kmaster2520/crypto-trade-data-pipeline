import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_autoscaling as autoscaling,
    aws_logs as logs,
)
from constructs import Construct

KINESIS_STREAM_ARN = "arn:aws:kinesis:us-east-1:391262527903:stream/raw-trade-data"


class EcsWebsocketStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc_id = self.node.try_get_context("vpc_id")
        subnet_id = self.node.try_get_context("subnet_id")
        ecr_image_uri = self.node.try_get_context("ecr_image_uri")
        product_id = self.node.try_get_context("product_id") or "BTC-USD"
        instance_type = self.node.try_get_context("instance_type") or "t4g.micro"

        if not subnet_id:
            raise ValueError("Context variable 'subnet_id' is required.")
        if not ecr_image_uri:
            raise ValueError("Context variable 'ecr_image_uri' is required.")

        vpc = ec2.Vpc.from_lookup(self, "Vpc", vpc_id=vpc_id)

        # --- IAM: task role (container → Kinesis) ---
        task_role = iam.Role(
            self,
            "EcsTaskRole",
            role_name="btc-websocket-ecs-task-role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            inline_policies={
                "KinesisWrite": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            sid="AllowWriteToKinesisStream",
                            effect=iam.Effect.ALLOW,
                            actions=["kinesis:PutRecord", "kinesis:PutRecords"],
                            resources=[KINESIS_STREAM_ARN],
                        )
                    ]
                )
            },
        )

        # --- IAM: execution role (ECS agent → ECR + CloudWatch) ---
        execution_role = iam.Role(
            self,
            "EcsTaskExecutionRole",
            role_name="btc-websocket-ecs-execution-role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
        )

        # --- IAM: EC2 instance role (host → ECS agent + SSM) ---
        instance_role = iam.Role(
            self,
            "Ec2InstanceRole",
            role_name="btc-websocket-ecs-instance-role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2ContainerServiceforEC2Role"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                ),
            ],
        )

        # --- VPC: EC2 security group ---
        instance_sg = ec2.SecurityGroup(
            self,
            "InstanceSecurityGroup",
            vpc=vpc,
            security_group_name="coinbase-websocket-ec2-sg",
            description="Enable SSH and HTTPS access via port 22 and 443",
        )
        instance_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(22),
            "Allow SSH access from anywhere",
        )
        instance_sg.add_egress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            "Enable outward HTTPS traffic",
        )
        instance_sg.add_egress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Enable outward HTTP traffic",
        )
        cdk.Tags.of(instance_sg).add("Application", "CoinbaseDataFlow")

        # --- ECS Cluster ---
        cluster = ecs.Cluster(
            self,
            "EcsCluster",
            cluster_name="coinbase-websocket-cluster",
        )
        cdk.Tags.of(cluster).add("Application", "CoinbaseDataFlow")

        # --- CloudWatch Log Group ---
        log_group = logs.LogGroup(
            self,
            "LogGroup",
            log_group_name="/ecs/coinbase-websocket",
            retention=logs.RetentionDays.TWO_WEEKS,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )

        # --- Launch Template (Graviton ECS-optimized AMI) ---
        launch_template = ec2.LaunchTemplate(
            self,
            "LaunchTemplate",
            launch_template_name="coinbase-websocket-ecs-lt",
            machine_image=ec2.MachineImage.from_ssm_parameter(
                "/aws/service/ecs/optimized-ami/amazon-linux-2023/arm64/recommended/image_id"
            ),
            instance_type=ec2.InstanceType(instance_type),
            role=instance_role,
            security_group=instance_sg,
            user_data=ec2.UserData.custom(
                f"#!/bin/bash\necho ECS_CLUSTER={cluster.cluster_name} >> /etc/ecs/ecs.config"
            ),
        )
        cdk.Tags.of(launch_template).add("Name", "coinbase-websocket-ecs-instance")
        cdk.Tags.of(launch_template).add("Application", "CoinbaseDataFlow")

        # --- ASG: always exactly one container instance ---
        autoscaling.CfnAutoScalingGroup(
            self,
            "AutoScalingGroup",
            auto_scaling_group_name="coinbase-websocket-ecs-asg",
            min_size="0",
            max_size="1",
            desired_capacity="1",
            vpc_zone_identifier=[subnet_id],
            launch_template=autoscaling.CfnAutoScalingGroup.LaunchTemplateSpecificationProperty(
                launch_template_id=launch_template.launch_template_id,
                version=launch_template.latest_version_number,
            ),
            tags=[
                autoscaling.CfnAutoScalingGroup.TagPropertyProperty(
                    key="Application",
                    value="CoinbaseDataFlow",
                    propagate_at_launch=True,
                )
            ],
        )

        # --- ECS Task Definition ---
        task_def = ecs.Ec2TaskDefinition(
            self,
            "TaskDefinition",
            family="coinbase-websocket",
            network_mode=ecs.NetworkMode.BRIDGE,
            task_role=task_role,
            execution_role=execution_role,
        )

        task_def.add_container(
            "websocket-consumer",
            image=ecs.ContainerImage.from_registry(ecr_image_uri),
            command=[product_id],
            memory_limit_mib=256,
            memory_reservation_mib=128,
            essential=True,
            environment={"AWS_REGION": self.region},
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="websocket",
                log_group=log_group,
            ),
        )

        # --- ECS Service: keep exactly one task running ---
        service = ecs.CfnService(
            self,
            "EcsService",
            service_name="coinbase-websocket-service",
            cluster=cluster.cluster_arn,
            task_definition=task_def.task_definition_arn,
            desired_count=1,
            launch_type="EC2",
            deployment_configuration=ecs.CfnService.DeploymentConfigurationProperty(
                minimum_healthy_percent=0,
                maximum_percent=100,
            ),
            tags=[cdk.CfnTag(key="Application", value="CoinbaseDataFlow")],
        )

        # --- Outputs ---
        cdk.CfnOutput(self, "ClusterName", value=cluster.cluster_name)
        cdk.CfnOutput(self, "ServiceArn", value=service.attr_service_arn)
        cdk.CfnOutput(self, "TaskDefinitionArn", value=task_def.task_definition_arn)
        cdk.CfnOutput(self, "InstanceSecurityGroupId", value=instance_sg.security_group_id)
        cdk.CfnOutput(self, "LogGroupName", value=log_group.log_group_name)
