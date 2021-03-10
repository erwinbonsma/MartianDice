from aws_cdk import (
    core,
	aws_lambda as _lambda,
	aws_elasticache as cache,
	aws_ec2 as ec2
)

def CacheHelper(scope: core.Construct, vpc: ec2.Vpc, lambda_security_group: ec2.SecurityGroup):
	cache_security_group = ec2.SecurityGroup(
		scope, 'security-group-cache',
		description = "Security Group for ElastiCache",
		vpc = vpc
	)

	# cache_security_group.add_ingress_rule(
	# 	lambda_security_group, ec2.Port.tcp(11211), 'Memcached ingress 11211'
	# )
	cache_security_group.add_ingress_rule(
		Peer.any_ipv4(), ec2.Port.tcp(11211), 'Memcached ingress 11211'
	)

	subnet_group = cache.CfnSubnetGroup(
		scope, 'vpc-subnet-group',
		description = 'ElastiCache subnetgroup',
		subnet_ids = [subnet.subnet_id for subnet in vpc.isolated_subnets]
	)

	cache_cluster = cache.CfnCacheCluster(
		scope, 'cache-cluster',
		cache_node_type = 'cache.t3.micro',
		engine = 'memcached',
		num_cache_nodes = 1,
		cache_subnet_group_name = subnet_group.ref,
		vpc_security_group_ids = [
			cache_security_group.security_group_id
		]
	)

	return cache_cluster

class BackendStack(core.Stack):

	def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
		super().__init__(scope, construct_id, **kwargs)

		vpc = ec2.Vpc(
			self, 'cache-vpc',
			subnet_configuration = [ec2.SubnetConfiguration(
				name = 'isolated',
				subnet_type = ec2.SubnetType.ISOLATED
			)]
		)

		lambda_security_group = ec2.SecurityGroup(
			self, 'security-group-lambda',
			description = "Security Group for Lambda service(s)",
			vpc = vpc
		)

		cache_cluster = CacheHelper(self, vpc, lambda_security_group)

		my_lambda = _lambda.Function(
			self, 'HelloLambda',
			runtime = _lambda.Runtime.PYTHON_3_7,
			code = _lambda.Code.asset('../backend/src'),
			handler = 'hello.handler',
			environment = {
				"CACHE_CLUSTER": f"{cache_cluster.attr_configuration_endpoint_address}:{cache_cluster.attr_configuration_endpoint_port}"
			},
			vpc = vpc,
			vpc_subnets = ec2.SubnetSelection(subnet_type = ec2.SubnetType.ISOLATED),
			# security_groups = [lambda_security_group]
		)
