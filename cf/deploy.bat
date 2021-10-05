cls
aws cloudformation package --template-file selenium.yaml        --output-template-file  selenium-deploy.yaml --s3-bucket innovalab-working-bucket --profile sre
aws cloudformation deploy  --template-file selenium-deploy.yaml --stack-name            StackSet-ST    --capabilities CAPABILITY_IAM --profile sre

