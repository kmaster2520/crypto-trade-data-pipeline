import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
)
from constructs import Construct


class EndpointsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc_id = self.node.try_get_context("vpc_id")
        subnet_id = self.node.try_get_context("subnet_id")

        if not vpc_id:
            raise ValueError("Context variable 'vpc_id' is required. Pass with --context vpc_id=<id>")
        if not subnet_id:
            raise ValueError("Context variable 'subnet_id' is required. Pass with --context subnet_id=<id>")

        vpc = ec2.Vpc.from_lookup(self, "Vpc", vpc_id=vpc_id)
        subnet = ec2.Subnet.from_subnet_id(self, "Subnet", subnet_id)

        kinesis_endpoint_sg = ec2.SecurityGroup(
            self,
            "KinesisEndpointSecurityGroup",
            vpc=vpc,
            security_group_name="kinesis-endpoint-sg",
            description="Enable Access from EC2 instances",
        )
        kinesis_endpoint_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            "Allow https access from anywhere",
        )
        kinesis_endpoint_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow http access from anywhere",
        )

        ec2.CfnInstanceConnectEndpoint(
            self,
            "InstanceConnectEndpoint",
            subnet_id=subnet_id,
            preserve_client_ip=True,
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "KinesisStreamsVPCEndpoint",
            vpc=vpc,
            service=ec2.InterfaceVpcEndpointAwsService.KINESIS_STREAMS,
            subnets=ec2.SubnetSelection(subnets=[subnet]),
            security_groups=[kinesis_endpoint_sg],
            private_dns_enabled=True,
        )

        cdk.CfnOutput(self, "KinesisEndpointSGId", value=kinesis_endpoint_sg.security_group_id)
