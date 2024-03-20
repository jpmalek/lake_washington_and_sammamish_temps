# Overview
    This open-source project produces a service that gathers historical record-high/record-low and real-time lake water temperatures for Lake Washington and Lake Sammamish from King County Washington data sources.

    Current Lake Washington and Lake Sammamish water temperatures are published in JSON format here: https://swimming.withelvis.com/WA/lake_temps.json

    Record all-time, and by-month high and low Lake Washington and Lake Sammamish water temperatures are published in JSON format here: https://swimming.withelvis.com/WA/lake_wa_highs_and_lows.json
<!-- 
# Intro 
    why lk wa temps
    why swimming.withelvis.com
    NOTE: https://green2.kingcounty.gov/lake-buoy/GenerateMapData.aspx is called from https://green2.kingcounty.gov/lake-buoy/default.aspx
    NOTE: real-time data is updated by King County at approx 12AM, 8AM and 4PM 
    why open-source

TODO:
Setup and Dependencies
    IDE - why VS code
    cloud environment
        why aws
        how-to setup and get started
            security first
            IAM and root access
            create a new AWS admin user with only the necessary permissions, test their credentials work with the script AWS reqs
            delete any root keys
    cloud build environment
        why not local, examples, brew and other package managers
        anaconda
    git, github, github actions, issues, pages
    Python. why
        built with python 3.11.5
    naming the project - use underscores for python!
    python package setup steps:
        pip install pipreqs; run pipreqs . in project directory to generate a requirements.txt file. pip freeze > requirements.txt outputs all installed packages.
    unit testing
        coveragepre-commit hook: vim .git/hooks/pre-commit; chmod +x .git/hooks/pre-commit; 
        action to get coverage reports;
        action bug: coverage.py creating .gitignore with *, and "permissions" content:writevs
        NOTE: coverage on github pages here: https://jpmalek.github.io/lake_washington_and_sammamish_temps/ 
        Python doesn't allow hyphens in module names because it interprets them as minus signs. This is why you're getting an error when you try to import lake-washington-and-sammamish-temps.app. So don't name projects with hyphens.  Python package names should be all lowercase and use underscores instead of hyphens. This is because Python doesn't allow hyphens in module names, as they're interpreted as minus signs.
    docker
        run source ./export_aws_credentials_to_env.sh to export AWS credentials to environment variables locally.
        docker init (creates .dockerignore,compose.yaml,Dockerfile,README.Docker.md)
        update compose.yaml with environment variables
        docker compose up --build
        install chromedriver in docker
    ecs
        why ecs, fargate
        DONE: put their credentials in secrets manager for use by ECS
        DONE: update ecs policy to grant access to secrets manager
        DONE: test script in ecs
        DONE: create and test docker file on ec2 instance
        DONE: short-form ECS steps:
            ref: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/getting-started-fargate.html
            create repository : aws ecr create-repository --repository-name lake-washington-and-sammamish-temps --region us-west-2
            auth with default registry: aws ecr get-login-password --region us-west-2 | sudo docker login --username AWS --password-stdin 139626508613.dkr.ecr.us-west-2.amazonaws.com
            tag image: sudo docker tag lake-washington-and-sammamish-temps:latest 139626508613.dkr.ecr.us-west-2.amazonaws.com/lake-washington-and-sammamish-temps:latest
            push image to default registry: sudo docker push 139626508613.dkr.ecr.us-west-2.amazonaws.com/lake-washington-and-sammamish-temps:latest
            ~1.5G
            create all_cloudwatch_policy and attach to role https://us-east-1.console.aws.amazon.com/iam/home#/policies/details/arn%3Aaws%3Aiam%3A%3A139626508613%3Apolicy%2Fall_cloud_watch?section=entities_attached 
Files Overview
VS Code and Copilot: commit messages - copilot star
AWS ECS vs Github Actions
>
