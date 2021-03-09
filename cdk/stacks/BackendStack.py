from aws_cdk import (
    core,
	aws_lambda as _lambda
)

class BackendStack(core.Stack):

	def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
		super().__init__(scope, construct_id, **kwargs)

		my_lambda = _lambda.Function(
			self, 'HelloLambda',
			runtime = _lambda.Runtime.PYTHON_3_7,
			code = _lambda.Code.asset('../backend/src'),
			handler = 'hello.handler'
		)
