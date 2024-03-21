# Overview
This open-source project produces a service that gathers historical record-high/record-low and real-time lake water temperatures for Lake Washington and Lake Sammamish from King County Washington data sources.

Current Lake Washington and Lake Sammamish water temperatures are published in JSON format <a href="https://swimming.withelvis.com/WA/lake_temps.json" target="_blank">here</a>.

Record all-time, and by-month high and low Lake Washington and Lake Sammamish water temperatures are published in JSON format <a href="https://swimming.withelvis.com/WA/lake_wa_highs_and_lows.json" target="_blank">here</a>.

# Intro 
When spring hits in Washington state, we start thinking about jumping in the lakes here in Seattle! Year over year, I've often considered dropping a network-enabled water temperature gauge into the lake and creating an IOT project to monitor and publish lake water temperature data. Finally in 2024 I decided to dig in on this project. 

My first step was to do some research on what has already been done on this front. 

My findings were very interesting; I half-expected there to be an API(s) that surfaced lake water temperature data worldwide, or at least nationwide. After looking around quite a bit, and getting some help via email (thank you!) from Ronald Henderson and others at the USGS, it turns out that there apparently isn't a good source of this kind of data, outside of the county level. Interesting, given current climate concerns with regard to surface water temperatures! 

This left me focused on the information provided on the King County website <a href="https://kingcounty.gov/en/dept/dnrp/nature-recreation/environment-ecology-conservation/science-services" target="_blank">here</a>. I found it a bit cumbersome to find what I was looking for (which was a good thing, in terms of substantiating my project), so I reached out and got some help from 
Curtis DeGasperi, Water Quality Engineer at King County Department of Natural Resources and Parks. They first pointed me to data sources <a href="https://data.kingcounty.gov/Environment-Waste-Management/Water-Quality/vwmt-pvjw/about_data" target="_blank">here</a>, but I was looking for more of a real-time data feed, so I followed up with more questions. 

Per Curtis' response, I learned that the data sources for the pages <a href="https://green2.kingcounty.gov/lakes/" target="_blank">here</a> are updated only twice monthly (Mar-Nov) and monthly (Dec-Feb), and it takes ~45 days after each sampling event for the data generated via field and lab analysis to post to the web. 

However, I was pointed to the Lake buoy data pages <a href="https://green2.kingcounty.gov/lake-buoy/default.aspx" target="_blank">here</a>, learning that real-time lake temperatures could be found by scrolling-over the buoy locations. Cool! 

After reading about the buoy specifications <a href="https://kingcounty.gov/services/environment/water-and-land/lakes/lake-buoy-data/BuoyInfo.aspx" target="_blank">here</a>, researching their costs online, and reviewing the very well done maintenance and quality assurance plan <a href="https://green2.kingcounty.gov/ScienceLibrary/Document.aspx?ArticleID=532" target="_blank">here</a> I came to the happy conclusion that researching, finding, buying and dropping my own sensor into the lake would not be the best next step; I decided to proceed with leveraging the data King County rigorously collects, and received permission to do so, noting their disclaimer <a href="https://kingcounty.gov/services/environment/water-and-land/lakes/lake-buoy-data/provisional.aspx" target="_blank">here</a>.

With all of this research, I landed on a plan to publish lake water temperature data that could be consumed in JSON format by any web-enabled application I might decide to build in the future. I'd get what I primarily wanted, a real-time temperature data JSON file. As a cool added outcome, I'd process all historical temperature data (since 1983) to determine what the all-time recorded high and low temperatures are, and the by-month highs and lows, regardless of year.

You may have noticed that my service posts data to swimming.withelvis.com. In one of my previous startups, I had a saying "with Elvis", e.g. "Next we're going to build a new client app! With Elvis." The idea being that Elvis is a cool legend, and doing anything "with Elvis" would make it that much more fun and better. I got so wrapped up in the idea that I purchased the domain name "withelvis.com", which had been sitting for years, unused. I got a kick out of the "swimming.withelvis.com" idea, and so it is.

Over many years in the startup world, I'd never published my own personal open-source project, and felt this was the perfect candidate and time to do it. So it is! 

Ultimately I hope this fun little project serves to help others in some way. Cheers! 

# Technologies and Tools 
## Operating Systems: OSX, Linux Ubuntu
## Integrated Development Environment (IDE): VS Code
## Package Management: Anaconda, Apt, Pip 
## Revision Control and Related Tools: Git, GitHub, Github Actions, Github Pages, Issues
## Coding Language: Python 
## Noteable Python Libraries: Selenium, Pandas, Boto
## Unit tests and Test Coverage: PyTest
## Markup Languages: Markdown, JSON, YAML
## Cloud Services via Amazon Web Services (AWS): IAM, EC2, S3, CloudFront, ECS, ECR, Fargate, Route 53, CloudWatch, EventBridge, Certificate Manager, Secrets Manager
## Containerization: Docker
## Domain Registrar: Namecheap

<!-- 
TODO:


sub: [WMA ETO Jira] (WDS-639) lake water temperatures API
Stephen Huddleston - Enterprise Application Support
USGS ETO Infrastructure and Services Branch

Setup and Dependencies
    IDE - why VS code
    domain hosting
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
    NOTE: https://green2.kingcounty.gov/lake-buoy/GenerateMapData.aspx is called from https://green2.kingcounty.gov/lake-buoy/default.aspx
    NOTE: real-time data is updated by King County at approx 12AM, 8AM and 4PM 
VS Code and Copilot: commit messages - copilot star
AWS ECS vs Github Actions
>
