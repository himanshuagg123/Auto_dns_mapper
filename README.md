aws sam cli

here in this we will learn how to step up aws sam and how to use sam to automate certian task

step 1 : to install aws sam cli in your system visit this site :- https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

step 2 : open your terminal and check if sam is intalled in your system by using command(sam --version) this commad will show does ypur sam installed or not

step 3 : run sam init – Initialize a New Serverless Application

this will start an interactive setup that guides you through the process of creating a new AWS SAM (Serverless Application Model) project. You’ll be prompted to choose:

A template source (e.g., AWS Quick Start Templates or custom location)

A runtime (e.g., Python, Node.js, Java, etc.)

A project name

Whether you want to use an example "Hello World" function or start from scratch

The package type (ZIP or Image)

Once completed, it creates a project structure including:

A sample Lambda function

template.yaml – the SAM template defining your infrastructure

Optional test events and unit test scaffolding

Build and deploy helper files

step 4 you will see a strucure like a my repository. now you have everything y





