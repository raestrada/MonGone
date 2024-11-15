# MonGone - MongoDB Resource Optimization

![MonGone Logo](https://res.cloudinary.com/dyknhuvxt/image/upload/v1731607427/mongone_wnzxyl.png)

[![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://raestrada.github.io/mongone/)

## Overview
MonGone is an open-source CLI tool designed to streamline your MongoDB Atlas environment by automatically scaling down unused resources and converting fixed configurations into auto-scaling ones. Its focus is on reducing costs and improving the efficiency of your database management.

Visit the [MonGone Home Page](https://raestrada.github.io/mongone/) for more information.

## Key Features
- 🚒 **Effortless Installation**: Get MonGone up and running in seconds with `pipx`.
- 🚀 **Zero to Optimal**: Detect and manage unused MongoDB clusters and databases, scaling them to zero or removing them entirely.
- 📝 **Generate and Execute Plans**: Create an optimization plan and let MonGone execute it, making your database resource management simple and effective.
- 💸 **Cost Analysis**: Track and identify costly resources to make informed decisions, optimizing cloud database expenses.

## Quick Start
### Installation
Install MonGone directly from GitHub using `pipx`:

```sh
pipx install git+https://github.com/raestrada/MonGone.git@v0.3.0
```

### Usage
MonGone offers a clean, straightforward CLI to help you optimize your MongoDB Atlas environment. Here are some of the most important commands:

#### 1. Initialize Configuration
Start by initializing a configuration file with your MongoDB Atlas organization details:

```sh
mongone init --atlas-org-id YOUR_ATLAS_ORG_ID --report-period-days 30
```
- **`--atlas-org-id`**: Your MongoDB Atlas organization ID.
- **`--report-period-days`**: The number of days to consider resources as unused. Default is 30 days.

This will create a configuration file named `mongone.yaml` with the provided details.

#### 2. Generate a Resource Report
With the configuration set, generate a detailed report of your MongoDB Atlas resources to identify which clusters or databases are unused:

```sh
mongone generate-report --period 30
```
- **`--period`**: Specifies the number of days to consider databases as unused (default is 30).

The report is generated in HTML format, presenting the current state of all projects, clusters, and databases within your organization.

#### 3. Set Up MongoDB Atlas API Keys
Make sure you have your Atlas API keys available as environment variables to authenticate with MongoDB Atlas:

```sh
export ATLAS_PUBLIC_KEY=your_public_key
export ATLAS_PRIVATE_KEY=your_private_key
```
These keys are needed for MonGone to interact with MongoDB Atlas and collect necessary information.

#### 4. Generate Optimization Plans
MonGone allows you to generate optimization plans to efficiently manage your resources:

```sh
mongone generate-plan
```
This command creates a plan to scale down or remove unused clusters, providing you with an actionable summary of suggested optimizations.

To apply these plans automatically, use:

```sh
mongone execute-plan --force
```
The `--force` flag allows MonGone to proceed with the changes without further confirmation.

### Force Data Option
To override data checks and force an action, you can use the `--force-data` option with the generate-report or generate-plan commands:

```sh
mongone generate-report --period 30 --force-data
```
This forces the tool to regenerate all data, ignoring any cached information.

## Documentation
For detailed guidance and more examples, check out the [MonGone Documentation](https://raestrada.github.io/MonGone/docs.html).

## Screenshot
Below is a preview of the MonGone resource report:

![MongoDB Atlas Example](https://res.cloudinary.com/dyknhuvxt/image/upload/v1731674258/mongo-example_kzkqlh.png)

## Contributing
MonGone is open-source, and contributions are always welcome! Here’s how you can contribute:
- Report issues.
- Suggest new features.
- Create pull requests to improve the project.

Find the repository here: [MonGone on GitHub](https://github.com/raestrada/MonGone).

## License
MonGone is licensed under the MIT License.

---

For more information, visit our [GitHub Page](https://raestrada.github.io/mongone/).
