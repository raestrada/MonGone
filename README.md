# MonGone - MongoDB Resource Optimization

![MonGone Logo](https://res.cloudinary.com/dyknhuvxt/image/upload/v1731607427/mongone_wnzxyl.png)

[![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://raestrada.github.io/mongone/)

## Overview
MonGone is an open-source CLI tool designed to optimize MongoDB Atlas environments by scaling down or removing unused resources and converting fixed resources into auto-scaling ones. MonGone aims to help you reduce costs and make your database management more efficient by eliminating unnecessary expenses.

Visit the [MonGone Home Page](https://raestrada.github.io/mongone/) for more information.

## Features
- **Effortless Installation**: Install MonGone with `pipx` and start optimizing immediately.
- **Zero to Optimal**: Automatically detect and manage unused MongoDB clusters and databases.
- **Generate and Execute Plans**: Create an optimization plan and execute it to enhance your MongoDB resource management.
- **Cost Analysis**: Identify costly resources and make informed optimization decisions.

## Installation
MonGone can be installed using `pipx` directly from the GitHub repository:

```sh
pipx install git+https://github.com/raestrada/MonGone.git@v0.1.0
```

## Usage
MonGone provides a straightforward CLI with several commands to help you optimize your MongoDB Atlas environment. Below are some of the key commands:

### 1. Initialize Configuration
To begin using MonGone, you need to initialize a configuration file with your MongoDB Atlas organization details.

```sh
mongone init --atlas-org-id YOUR_ATLAS_ORG_ID --report-period-days 30
```
- **`atlas-org-id`**: Your MongoDB Atlas organization ID.
- **`report-period-days`**: The number of days to consider resources as unused. Default is 30 days.

This command will create a configuration file named `mongone.yaml` with the provided information.

### 2. Generate Report
Once configured, you can generate a report of your MongoDB Atlas resources, identifying which clusters or databases are unused.

```sh
mongone generate-report --period 30
```
- **`period`**: Specifies the number of days to consider databases as unused (default is 30).

This command will generate a report in HTML format that shows the current state of all projects, clusters, and databases within your MongoDB Atlas organization.

### 3. Export Atlas API Keys
Ensure that you have your Atlas API keys available as environment variables to interact with MongoDB Atlas.

```sh
export ATLAS_PUBLIC_KEY=your_public_key
export ATLAS_PRIVATE_KEY=your_private_key
```
These keys are required for MonGone to authenticate with MongoDB Atlas and gather the necessary information.

## Contributing
MonGone is open-source, and contributions are welcome! You can contribute by:
- Reporting issues.
- Suggesting new features.
- Creating pull requests.

The project repository can be found here: [MonGone on GitHub](https://github.com/raestrada/MonGone).

## License
MonGone is licensed under the MIT License.

---
![MonGone Thumbnail](https://res.cloudinary.com/dyknhuvxt/image/upload/c_thumb,w_200,g_face/v1731607427/mongone_wnzxyl.png)

For detailed documentation, visit the [GitHub Page](https://raestrada.github.io/mongone/).
