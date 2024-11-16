import aws_cdk as core
import aws_cdk.assertions as assertions

from devops_cicd_java_tomcat.devops_cicd_java_tomcat_stack import DevopsCicdJavaTomcatStack

# example tests. To run these tests, uncomment this file along with the example
# resource in devops_cicd_java_tomcat/devops_cicd_java_tomcat_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = DevopsCicdJavaTomcatStack(app, "devops-cicd-java-tomcat")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
