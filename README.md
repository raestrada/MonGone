# MonGone - MongoDB Resource Optimization

![MonGone Logo](https://res.cloudinary.com/dyknhuvxt/image/upload/v1731607427/mongone_wnzxyl.png)

[![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://raestrada.github.io/mongone/)

## Overview
MonGone is an open-source CLI tool designed to streamline your MongoDB Atlas environment by automatically scaling down unused resources and converting fixed configurations into auto-scaling ones. Its focus is on reducing costs and improving the efficiency of your database management.

Visit the [MonGone Home Page](https://raestrada.github.io/mongone/) for more information.

## 🚨 Warning: Please Read Carefully
MonGone is currently in an experimental phase. The report generation features are safe to use, but **please exercise caution** with optimization actions, especially those involving **deletion** or resource scaling. Make sure you understand the tool thoroughly and verify your MongoDB setup carefully before executing any optimization commands.

## Key Features
- 🚒 **Effortless Installation**: Get MonGone up and running in seconds with `pipx`.
- 🚀 **Zero to Optimal**: Detect and manage unused MongoDB clusters and databases, scaling them to zero or removing them entirely.
- 📝 **Generate and Execute Plans**: Create an optimization plan and let MonGone execute it, making your database resource management simple and effective.
- 💸 **Cost Analysis**: Track and identify costly resources to make informed decisions, optimizing cloud database expenses.

## Quick Start
### Installation
Install MonGone directly from GitHub using `pipx`:

```sh
pipx install git+https://github.com/raestrada/MonGone.git@v0.4.2
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
- **`--force`**: Forcefully generates a report using the latest available data, overriding existing cached information.
- **`--test`**: Uses test data instead of fetching live data from MongoDB Atlas, useful for development and testing purposes.

The report is generated in HTML format, presenting the current state of all projects, clusters, and databases within your organization.

#### 3. Set Up MongoDB Atlas API Keys
Make sure you have your Atlas API keys available as environment variables to authenticate with MongoDB Atlas:

```sh
export ATLAS_PUBLIC_KEY=your_public_key
export ATLAS_PRIVATE_KEY=your_private_key
```
These keys are needed for MonGone to interact with MongoDB Atlas and collect necessary information.

#### 4. Generate Optimization Plans
MonGone allows you to generate optimization plans to efficiently manage your resources. The plans are generated automatically when you generate a report.

#### 5. Execute the Optimization Plan
Once an optimization plan is generated, you can execute it using the following command:

```sh
mongone execute
```
This command will execute the actions defined in the optimization plan, such as scaling down unused resources or enabling auto-scaling for clusters. The process is straightforward and automated, allowing you to quickly optimize your MongoDB environment with minimal manual intervention.

![Execute Optimization Plan Example](https://res.cloudinary.com/dyknhuvxt/image/upload/v1731724625/mongone-execute_xbdq6l.png)

The screenshot above shows an example of executing an optimization plan, highlighting the actions taken by MonGone to improve resource utilization and reduce costs.

### Force Data Option
To override data checks and force an action, you can use the `--force` option with the `generate-report` command:

```sh
mongone generate-report --period 30 --force
```
This forces the tool to regenerate all data, ignoring any cached information.

To use test data, add the `--test` option:

```sh
mongone generate-report --period 30 --test
```
This is helpful for development and testing purposes without making changes to actual MongoDB instances.

## Documentation
For detailed guidance and more examples, check out the [MonGone Documentation](https://raestrada.github.io/MonGone/docs.html).

## Screenshot
Below is a preview of the MonGone resource report:

![MongoDB Atlas Example](https://res.cloudinary.com/dyknhuvxt/image/upload/v1731785050/mongone-docs_wpuy8w.png)

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
