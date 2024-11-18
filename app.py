#!/usr/bin/env python3
import os

from aws_cdk import App

from devops_cicd_java_tomcat.devops_cicd_java_tomcat_stack import DevopsCicdJavaTomcatStack


app = App()
# Dev
DevopsCicdJavaTomcatStack(app, "DevopsCicdJavaTomcatStack-Dev", environment="dev", env={"account": os.getenv('CDK_DEFAULT_ACCOUNT'), "region": os.getenv('CDK_DEFAULT_REGION')})
# Test
DevopsCicdJavaTomcatStack(app, "DevopsCicdJavaTomcatStack-Test", environment="test", env={"account": os.getenv('CDK_DEFAULT_ACCOUNT'), "region": os.getenv('CDK_DEFAULT_REGION')})
# Production
DevopsCicdJavaTomcatStack(app, "DevopsCicdJavaTomcatStack-Prod", environment="prod", env={"account": os.getenv('CDK_DEFAULT_ACCOUNT'), "region": os.getenv('CDK_DEFAULT_REGION')})

app.synth()
