#!/usr/bin/env python3
import os

from aws_cdk import App

from devops_cicd_java_tomcat.devops_cicd_java_tomcat_stack import DevopsCicdJavaTomcatStack


app = App()
DevopsCicdJavaTomcatStack(app, "DevopsCicdJavaTomcatStack", env={"account": os.getenv('CDK_DEFAULT_ACCOUNT'), "region": os.getenv('CDK_DEFAULT_REGION')})

app.synth()
