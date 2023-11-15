# docker_to_jupyter
transforms docker containers to jupyter notebooks for easier use by data scientists, QAs, and my manager
Creating documentation for your code involves explaining how to set up the environment, how to run the script, and what to expect as outputs. Here’s a template you can follow to document the usage of your code:

---

# Documentation for Dockerfile to Jupyter Notebook Script

## Overview
This script automates the process of generating a Jupyter notebook from a Dockerfile and associated Docker run configuration files. The notebook produced will contain code cells that replicate the Docker container setup and execution environment.

## Prerequisites
- Python 3.x
- Jupyter Notebook or JupyterLab installed
- Docker installed (if the script needs to interface with Docker directly)

## Setup
1. Clone the repository or download the script files to your local machine.
2. Ensure all prerequisite software is installed and operational.
3. Place your `Dockerfile` and any Docker run configuration files (`docker-run.txt`, `docker-run.sh`, or `Dockerfile.run.xml`) in the same directory as the script.

## Usage

### Step 1: Prepare Your Docker Files
Ensure your `Dockerfile` and Docker run configuration files are in the working directory. If your Docker setup relies on a `requirements.txt` file, make sure it is also present.

### Step 2: Run the Script
Execute the script in your terminal or command prompt:

```bash
dockerrun_to_jupyter.py
```

### Step 3: Output
The script will generate a Jupyter notebook named after the current working directory with all necessary setup commands translated into code cells. The notebook will be saved in the working directory.

### Step 4: Review the Notebook
Open the generated notebook in Jupyter Notebook or JupyterLab to review and execute the cells.

## Expected Outputs
- A Jupyter notebook with the necessary environment setup and execution steps extracted from the Dockerfile and Docker run files.
- Any output files that are found in the `output` directory will be included in the notebook.

## Error Handling
If the script encounters any issues, it will print error messages to the console. Common issues may include missing files, incorrect file formats, or permission issues.

## Customization
Users can modify the regular expressions at the beginning of the script to match different patterns within their Dockerfiles if the default patterns do not suit their needs.
