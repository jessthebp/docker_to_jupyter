import os
import re
import nbformat.v4 as nb
import nbformat as nbf
import xml.etree.ElementTree as ET
import json

FROM_REGEX = re.compile(r'^FROM (.+)', re.MULTILINE)
RUN_REGEX = re.compile(r'^RUN (.+)', re.MULTILINE)
ENTRYPOINT_REGEX = re.compile(r'^ENTRYPOINT (.+)', re.MULTILINE)

def extract_dockerfile_info(dockerfile, from_regex=FROM_REGEX, run_regex=RUN_REGEX, entrypoint_regex=ENTRYPOINT_REGEX):
    """Extracts information from a Dockerfile"""
    try:
        # Extract the FROM instruction
        from_image = from_regex.search(dockerfile).group(1)
    except AttributeError:
        from_image = None

    # Extract any other relevant instructions
    commands = list(run_regex.findall(dockerfile))

    # Extract any libraries specified in requirements.txt
    if os.path.exists('requirements.txt'):
        print('requirements.txt exists')
        with open('requirements.txt') as f:
            requirements = f.read().strip()
        if requirements:
            # for requirement in the requirements file, add a pip install command split by new line
            #for requirement in requirements.split('\n'):
            #    commands.append(f'!pip install {requirement}')
            commands.append(f'!pip install -r requirements.txt')
            # if boto3 is in the requirements file, add a command to install awscli
            if 'boto3' in requirements:
                commands.append(f'!python -m pip install boto3 ')
            if 'pandas_gbq' in requirements:
                commands.append(f'!python -m pip install pandas_gbq ')

            #commands.append(f'pip install {requirements}')

    entrypoint = entrypoint_regex.search(dockerfile)
    if entrypoint:
        entrypoint = entrypoint.group(1).strip('[]').split(',')
        entrypoint = [arg.strip().strip('"\'') for arg in entrypoint]
        # If the first entrypoint argument is "python", assume the second argument is the script to run
        if entrypoint[0] == 'python' and len(entrypoint) > 1:
            entrypoint_script = entrypoint[1]
        else:
            entrypoint_script = None
    else:
        entrypoint_script = None

    return from_image, commands, entrypoint_script

import xml.etree.ElementTree as ET
import os

def extract_docker_run_info(docker_run):
    """Extracts information from a Docker run file"""
    # Determine the file type (e.g. txt or xml)
    file_extension = os.path.splitext(docker_run)[1]

    # Extract the docker run command and any options or arguments
    if file_extension == '.xml':
        # Parse the XML file
        root = ET.parse(docker_run).getroot()
        command = root.find(".//option[@name='command']").attrib['value']

        # Extract environment variables from the DockerEnvVarImpl elements
        env_vars = {}
        env_var_elements = root.findall(".//DockerEnvVarImpl")
        for env_var_element in env_var_elements:
            name = env_var_element.find(".//option[@name='name']").attrib['value']
            value = env_var_element.find(".//option[@name='value']").attrib['value']
            env_vars[name] = value

        # Write environment variables to an environment file
        with open('docker_env', 'w') as f:
            for name, value in env_vars.items():
                f.write(f'{name}={value}\n')

        # Extract arguments from the DockerEntryPointImpl elements
        args = []
        entry_point_elements = root.findall(".//DockerEntryPointImpl")
        for entry_point_element in entry_point_elements:
            arg = entry_point_element.find(".//option[@name='arg']").attrib['value']
            args.append(arg)

        # Write arguments to a JSON file
        with open('arguments.json', 'w') as f:
            json.dump(args, f)

        # Add the environment file and arguments file to the docker run command
        command += f' --env-file docker_env -v $(pwd)/arguments.json:/usr/src/app/arguments.json'
        command += f' python entrypoint.py /usr/src/app/arguments.json'
        # we gotta point the "output" folder somewhere- we just point it to the current directory
        # it's a jupyter notebook so we'll just create a folder called output
        command += f' -v $(pwd)/output:/usr/src/app/output'


    else:
        with open(docker_run) as f:
            docker_run = f.read()
        command = docker_run.strip()

    return command, args

# get the ouput: we know the output will be in a /output folder so we can just get the files in that folder
# we need to deal with the case where there are multiple files in the output folder

def get_output():
    """Gets the output from the output folder if the output folder exists"""
    if not os.path.exists('output'):
        return None

    else:
        output_files = os.listdir('output')
        output = {}
        for output_file in output_files:
            with open(os.path.join('output', output_file)) as f:
                output[output_file] = f.read()
    return output


def generate_notebook(from_image, commands, command, dockerfile, entrypoint_script, args):
    """Generates a Jupyter notebook"""
    nb_cells = []

    # Run any commands specified in the docker run file
    if command:
        # Take in user input/arguments based on the Dockerfile's entrypoint

       # if entrypoint_args:
        #    nb_cells.extend([nb.new_code_cell(source=f'{arg} = input("Enter {arg}: ")') for arg in entrypoint_args])

        nb_cells.extend([nb.new_code_cell(source=cmd) for cmd in commands])

        # Load Python modules based on the Dockerfile's COPY/ADD instructions
        #copy_add_args = re.findall(r'COPY|ADD\s+(.+)\s+(.+)', dockerfile)
        #if copy_add_args:
        #    nb_cells.extend([nb.new_code_cell(source=f'import sys\nsys.path.append("{dest}")') for src, dest in copy_add_args if src.endswith('.py')])

        # Run the entrypoint script
        if entrypoint_script:
            # nb_cells.append(nb.new_code_cell(source=command))
            entrypoint_args = command
            # If the entrypoint script takes arguments, pass them in
            if entrypoint_args:
                # If the entrypoint script takes a single argument, pass in the list of arguments
                nb_cells.append(nb.new_code_cell(source=f'!python {entrypoint_script} {entrypoint_args}'))
            else:
                nb_cells.append(nb.new_code_cell(source=f'!python {entrypoint_script}'))

    # Run any commands specified in the Dockerfile
    else:
        nb_cells.extend([nb.new_code_cell(source=cmd) for cmd in commands])

    # Display any output from the container
    output = get_output()
    if output:
        nb_cells.append(nb.new_markdown_cell(source='## Output'))
        for output_file, output in output.items():
            nb_cells.append(nb.new_markdown_cell(source=f'### {output_file}'))
            nb_cells.append(nb.new_code_cell(source=output))

    # Create the notebook
    nb_notebook = nb.new_notebook(cells=nb_cells)
    return nb_notebook


# Step 1: Parse the Dockerfile
with open('Dockerfile') as f:
    dockerfile = f.read()
    from_image, commands, entrypoint_script = extract_dockerfile_info(dockerfile)


# Step 2: Parse the Docker run file (if it exists)

command = None
if os.path.exists('docker-run.txt'):
    print('docker-run.txt exists')
    docker_run = 'docker-run.txt'
    command, env_var_elements = extract_docker_run_info(docker_run)

if os.path.exists('docker-run.sh'):
    print('docker-run.sh exists')
    docker_run = 'docker-run.sh'
    command, env_var_elements = extract_docker_run_info(docker_run)

if os.path.exists(r'runConfigurations\Dockerfile.run.xml'):
    print('Dockerfile.run.xml exists')
    docker_run = r'runConfigurations\Dockerfile.run.xml'
    command, env_var_elements = extract_docker_run_info(docker_run)



# Step 5: Generate the Jupyter notebook
nb_notebook = generate_notebook(from_image, commands, command, dockerfile, entrypoint_script, env_var_elements)

# notebook name from current directory
notebook_name = os.path.basename(os.getcwd())
notebook_name = notebook_name.replace(' ', '-').lower()
notebook_name = notebook_name.replace('_', '-')
notebook_name = notebook_name + '.ipynb'

# Step 6: Save or return the Jupyter notebook
nbf.write(nb_notebook, notebook_name, version=nbf.NO_CONVERT)
