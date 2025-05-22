# 🛰️ AutoDNS EC2 → Route 53 Mapper

This project automatically maps EC2 instance public IPs to Route 53 DNS A records based on lifecycle state changes (running, stopped, terminated). It is built using AWS Lambda, CloudWatch Events, and SAM CLI.

---

## 📘 Overview

Whenever an EC2 instance starts, stops, or terminates:

- The Lambda function fetches the instance's `dns` tag.
- It updates the appropriate A record in Route 53:
  - **Running** → Maps to the instance's public IP.
  - **Stopped** → Maps to `127.0.0.1`.
  - **Terminated** → Deletes the record.

---

## 🧠 How It Works

1. EC2 triggers a **CloudWatch Event** on state changes.
2. The event invokes a **Lambda function**.
3. Lambda fetches:
   - The public IP.
   - The `dns` tag value.
4. It updates the appropriate A record in **Route 53**.

---

## 🛠️ AWS Services Used

| Service        | Purpose                                |
|----------------|----------------------------------------|
| **Lambda**     | Runs the automation logic              |
| **EC2**        | Source of lifecycle events             |
| **Route 53**   | Hosts DNS records                      |
| **CloudWatch** | Detects EC2 state changes              |
| **IAM**        | Manages permissions for the Lambda     |

---

## 🚀 Deployment Guide (Using AWS SAM CLI)

Follow these steps to deploy the project using AWS SAM CLI.

---

### ✅ Step 1: Install AWS SAM CLI

Install the SAM CLI using the official guide for your OS:  
👉 https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

---

### ✅ Step 2: Initialize the SAM Project

Open your terminal and run:

```bash
sam init
Select these options when prompted:

Template: "Hello World Example"

Runtime: Python 3.12

Package type: Zip

Project name: auto-dns-mapper

✅ Step 3: Replace template.yaml Content
Navigate into the generated project folder, then open and replace the contents of template.yaml with the following:

AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Description: Auto-maps EC2 public IP to Route 53 DNS using CloudWatch Events and Lambda.

Globals:
  Function:
    Timeout: 10

Resources:
  AutoDNSMapping:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: auto_dns_mapping/
      Handler: app.lambda_handler
      Runtime: python3.12
      Architectures: [x86_64]
      Environment:
        Variables:
          DOMAIN_NAME: "yourdomain.com"
          ROUTE53_ZONE_ID: "YOUR_HOSTED_ZONE_ID"
          AWS_PRIMARY_REGION: "us-east-1"
      Policies:
        - Statement:
            - Effect: Allow
              Action: ec2:DescribeInstances
              Resource: "*"
            - Effect: Allow
              Action:
                - route53:ChangeResourceRecordSets
                - route53:ListResourceRecordSets
              Resource: arn:aws:route53:::hostedzone/YOUR_HOSTED_ZONE_ID
      Events:
        CWEvent:
          Type: CloudWatchEvent
          Properties:
            Pattern:
              source: ["aws.ec2"]
              detail-type: ["EC2 Instance State-change Notification"]
              detail:
                state: ["running", "stopped", "terminated"]
🔁 Replace:

yourdomain.com → your actual domain (e.g. himanshuprojects.duckdns.org)

YOUR_HOSTED_ZONE_ID → your Route 53 hosted zone ID

us-east-1 → your AWS region

✅ Step 4: Add Lambda Function Code in app.py

✅ Step 5: Build and Deploy
🧱 sam build
This command compiles your Lambda function, installs dependencies (if any), and prepares everything for deployment.

sam build
It scans your template.yaml, packages the function code from auto_dns_mapping/, and places everything inside a .aws-sam folder.

☁️ sam deploy --guided
This command deploys your stack to AWS with helpful prompts the first time.

sam deploy --guided
You’ll be prompted to provide:

Stack name: e.g., auto-dns

AWS region: e.g., us-east-1

Confirm changes before deployment: Y

Allow SAM to create IAM roles: Y

Save these settings for future deploys: Y

The CLI will upload your packaged Lambda function to an S3 bucket, create the necessary roles, events, and permissions, and deploy your full stack to AWS.

Afterward, you can use:

sam deploy

🔐 IAM Permissions Required
SAM will auto-generate the permissions, but here’s what your Lambda function specifically needs:

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "ec2:DescribeInstances",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "route53:ChangeResourceRecordSets",
        "route53:ListResourceRecordSets"
      ],
      "Resource": "arn:aws:route53:::hostedzone/YOUR_HOSTED_ZONE_ID"
    }
  ]
}


✅ Expected Behavior
EC2 State	DNS Result
running	autodns-myinstance.yourdomain.com → public IP
stopped	autodns-myinstance.yourdomain.com → 127.0.0.1
terminated	Record deleted from Route 53

🙏 Thank You
Thanks for checking out this project!
If it helps you, feel free to ⭐ the repo or suggest improvements.
Happy automating with AWS!



