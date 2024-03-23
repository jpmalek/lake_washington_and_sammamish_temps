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

# Technologies and Tools Overview
- **Operating Systems**: OSX, Linux Ubuntu
- **Integrated Development Environment (IDE)**: VS Code, Jupyter Notebooks
- **Package Management**: Anaconda, Apt, Pip 
- **Revision Control and Related Tools**: Git, GitHub, Github Actions, Github Pages, Github Issues
- **Coding Languages**: Python, bash 
- **Noteable Python Libraries**: Selenium, Pandas, Boto
- **Unit tests and Test Coverage**: PyTest
- **Markup Languages**: Markdown, JSON, YAML
- **Cloud Services via Amazon Web Services (AWS)**: IAM, EC2, S3, CloudFront, ECS, ECR, Fargate, Route 53, CloudWatch, EventBridge, Certificate Manager, Secrets Manager
- **Containerization**: Docker
- **Domain Registrar**: Namecheap

# Techologies and Tools Detail
## Operating Systems
Unix/Linux operating systems have long been a favorite of mine due to their flexibility, robustness, and the control offered to the user. My go-to distribution is Ubuntu (previously Debian), which has great package management built in. It's an open-source system, which means it's continually being improved by a community of dedicated developers. This openness also allows for a level of customization and control that's hard to match. You can tweak and tune your system to fit your exact needs, whether you're setting up a server, a desktop workstation, or a tiny embedded system. The vast array of distributions available, each with their own strengths, allows you to choose a system that's tailored to your specific requirements.

One of the most powerful aspects of Linux that I absolutely love is its command-line interface and the suite of tools that come with it. These tools, often referred to as the "Unix philosophy," are designed to do one thing and do it well. They can be combined in countless ways to perform complex tasks. For example, the grep command can be used to search for a specific string in a file or stream of input. The ls command lists the contents of a directory. You can pipe the output of ls into grep to search for a specific file in a directory. The command would look like this: 
    
    ls | grep myfile.txt. 

This will list all files in the current directory and then search that list for "myfile.txt". To get a bit cheeky, this will create a file named "me", fill "me" with beer, and move me to hawaii:

    touch me && echo "beer" > me && mkdir -p hawaii && mv me hawaii/

This ability to chain reliable, well-documented, modular commands together allows for a level of power and flexibility that's hard to match in other operating systems.

After using Windows for many years and then switching many more years ago, I also have a deep appreciation for the macOS operating system. Being Unix-based, it combines the power and flexibility of Unix with the sleek and intuitive user interface that Apple is known for. This means I can leverage powerful command-line tools and scripts, similar to a Linux environment, while also enjoying a smooth, user-friendly desktop experience. The seamless integration between software and hardware in a Mac system also contributes to a stable and efficient operating environment. In terms of security, macOS has a strong track record. It's built on a Unix-based foundation which is known for its robust security features. Furthermore, Apple has implemented several security measures such as Gatekeeper, which blocks untrusted applications, and XProtect, an automatic malware detection tool. Additionally, the fact that macOS is less targeted by malware compared to other operating systems adds an extra layer of security.

I'm a big proponent of doing development work in the environment that matches where the code will end up running. So, if I'm working on server code, I'll typically be working on my Mac, but remoting into a cloud server or container that's running Ubuntu. No point in wrestling with package install challenges on my Mac when the target environment is Ubuntu!  

*nix OS provided for the wonderful low price of: free!

## IDE and Jupyter Notebooks
While I've been a long-time Vim user and advocate (and Emacs long ago), over the years Visual Studio Code (VS Code) has become my go-to IDE for several reasons. As a long-time Vim user, I appreciate the efficiency and control that Vim offers. However, VS Code brings together the best of both worlds. It provides a modern, feature-rich interface while also offering a Vim emulation mode. This means I can leverage my Vim keybindings and workflows within a more robust development environment. But I don't need to anymore, really. 

VS Code's IntelliSense feature is a game-changer. It offers smart completions based on variable types, function definitions, and imported modules. This feature alone has saved me countless hours of time. The built-in Git support is another major plus. Being able to stage and commit changes, create new branches, and view diffs right from the editor with a modern-day UI is incredibly convenient.

The extensibility of VS Code is another reason why I love it. There's a vast marketplace of extensions that can add new languages, themes, debuggers, and more to the editor. From BASH intellisense to Docker and everything else, quick and easy...it's a game-changer. It's easy to customize VS Code to fit my exact needs. And despite all these features, VS Code remains fast and responsive, which is a testament to its well-designed architecture.

As for Jupyter notebooks, they have transformed the way I work with Python, especially for data analysis and visualization tasks. The ability to interleave code, outputs, and explanatory text in a single document is incredibly powerful. I can experiment with code, see the results, and make adjustments in a very efficient and interactive way. This is a stark contrast to the traditional edit-run-debug cycle that can be time-consuming and disruptive.

Jupyter notebooks also make it easy to share my work with others. The notebooks are self-contained and can be rendered in a web browser, making them accessible to anyone, regardless of their development environment. This has made Jupyter notebooks an essential tool for collaborative projects and for presenting my work in a clear and understandable way. I've started adding one by default to every repo I work in. 

All for the wonderful low price of: free.

## Environment and Package Management
It's critical to leverage the best available "tools that manage your tools" and your working environment reliably and efficiently. 

Anaconda is a powerful tool for Python and R data science and machine learning. It's an open-source distribution that simplifies package management and deployment. Anaconda comes with a suite of over a thousand data science packages, and a package manager called Conda. Conda makes it easy to install both Python and non-Python packages, manage environments, and ensure all packages work together without conflicts. Anaconda also includes Jupyter Notebook, an environment for interactive computing, which is widely used in data analysis and scientific research.

Apt, or Advanced Package Tool, is the default package manager for Ubuntu and other Debian-based Linux distributions. It handles the installation and removal of software on your system. Apt simplifies the process of managing software on Unix-like computer systems by automating the retrieval, configuration, and installation of software packages. It also resolves and handles dependencies automatically. This means that if you want to install a software package that relies on other packages to function, Apt will identify these dependencies and install all necessary packages.

Pip, which stands for "Pip Installs Packages", is the standard package manager for Python. It allows you to install and manage additional libraries and dependencies that are not distributed as part of the standard Python library. Pip provides a simple way to install packages from the Python Package Index (PyPI) and other package directories. It also supports virtual environments, which is a key feature for Python developers as it allows them to create isolated Python environments for different projects, ensuring dependencies are kept separate and organized.

## Revision Control and Related Tools
For revision control, I was a long-time svn user, but years ago switched myself and my teams to Git.

Git is a distributed version control system that has become the de facto standard for source code management in the software industry. It allows multiple developers to work on the same codebase without stepping on each other's toes. Git tracks changes to files over time, so you can always see who made what changes and when. This makes it easier to track down bugs and understand the evolution of a project. Git also supports branching and merging, which allows developers to experiment with new features or fixes without affecting the main codebase.

GitHub is a web-based hosting service for Git repositories. It provides a user-friendly interface for managing and viewing Git repositories, along with a host of other features that facilitate collaborative development. With GitHub, you can easily share your code with others, contribute to open-source projects, and review code changes. GitHub also integrates with many other tools, making it a central hub for many development workflows.

GitHub Actions is a CI/CD (Continuous Integration/Continuous Deployment) tool that allows you to automate your software workflows directly within your GitHub repository. With GitHub Actions, you can build, test, and deploy your code right from GitHub. You can also assign tasks and workflows based on certain events, such as pushing code to a branch or creating a pull request. This level of automation can greatly increase productivity and ensure consistent quality of code.

GitHub Pages is a static site hosting service that takes HTML, CSS, and JavaScript files straight from a repository on GitHub, optionally runs the files through a build process, and publishes a website. It's a great way to host project pages, documentation, or a personal blog. One of the key benefits of GitHub Pages is its tight integration with GitHub, which means you can manage your website content with the same Git workflows you use for your code.

This project uses Github Actions to push code unit test coverage results to Github Pages whenever code is pushed to the main branch. 

GitHub Issues is a robust tracking system that allows you to track bugs, enhancements, or other requests related to your project. It's more than just a bug tracker - it's also a great way to manage your development tasks and workflows. You can assign issues to specific team members, label them for easy searching, and reference them directly in your code commits. This makes GitHub Issues a central part of your project management toolkit. It's great, but frankly it doesn't yet quite compare to other project management tools like Asana or the toolset provided by Atlassian (Jira, etc), albiet at much higher costs.

## Coding Languages
I've coded in many languages over the years, starting with C, HTML and Javascript. 

I absolutely love Python. 

Python has long been my language of choice for a variety of reasons. First and foremost, Python's syntax is clean and easy to understand, which makes it a great language for beginners. But don't let its simplicity fool you - Python is a powerful and versatile language that's used in everything from web development to data science to machine learning. Python's philosophy is "There should be one-- and preferably only one --obvious way to do it", which leads to more readable and maintainable code.

Python also has a rich ecosystem of libraries and frameworks. Whether you're working with data (Pandas, NumPy), building a web app (Django, Flask), or delving into machine learning (scikit-learn, TensorFlow), there's likely a Python library that can make your job easier. Python's extensive standard library, often described as "batteries included," means that often you don't even need to install anything to start building.

The Zen of Python, a collection of 19 "guiding principles", really encapsulates why I love Python. If you run this command in a Python interpreter: 
    
    import this

You'll get:

    The Zen of Python, by Tim Peters

    Beautiful is better than ugly.
    Explicit is better than implicit.
    Simple is better than complex.
    Complex is better than complicated.
    Flat is better than nested.
    Sparse is better than dense.
    Readability counts.
    Special cases aren't special enough to break the rules.
    Although practicality beats purity.
    Errors should never pass silently.
    Unless explicitly silenced.
    In the face of ambiguity, refuse the temptation to guess.
    There should be one-- and preferably only one --obvious way to do it.
    Although that way may not be obvious at first unless you're Dutch.
    Now is better than never.
    Although never is often better than *right* now.
    If the implementation is hard to explain, it's a bad idea.
    If the implementation is easy to explain, it may be a good idea.
    Namespaces are one honking great idea -- let's do more of those!

 It's a great reminder of what makes Python special, and a guide to writing good Python code.

 As for BASH, I've already talked about why I love it so much: solid, simple commands that can be chained together reliably to produce powerful outcomes. 

<!-- 
TODO:
sub: [WMA ETO Jira] (WDS-639) lake water temperatures API
Stephen Huddleston - Enterprise Application Support
USGS ETO Infrastructure and Services Branch

how-to setup and get started
    IDE - why VS code; Jupyter Notebooks
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
VS Code and Copilot: commit messages - copilot star; copilot configuration 
AWS ECS vs Github Actions
>
