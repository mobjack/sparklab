#!/usr/bin/env python

import os, sys
import ConfigParser
import argparse
import time

import googleapiclient.discovery
from six.moves import input



gcpzones = ['us-west1-a','us-west1-b','us-central1-b','us-central1-c','us-central1-f',
            'us-east1-c','us-east1-d','europe-west1-c','europe-west1-d','asia-east1-b',
            'asia-east1-c','asia-northeast1-b','asia-northeast1-c']

configfile = "labsetup.conf"

# [START list_instances]
def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items']
# [END list_instances]

# [START create_instance]
def create_instance(compute, project, zone, name, size):
    # Get the latest Centos 7 image.
    image_response = compute.images().getFromFamily(
        project='centos-cloud', family='centos-7').execute()
    source_disk_image = image_response['selfLink']

    # Configure the machine
    if size == 'medium': 
        machine_type = "zones/%s/machineTypes/n1-standard-1" % zone
    elif size == 'small':
        machine_type = "zones/%s/machineTypes/g1-small" % zone
    elif size == 'large':
        machine_type = "zones/%s/machineTypes/n1-highmem-2" % zone

    image_url = "http://storage.googleapis.com/gce-demo-input/photo.jpg"
    image_caption = "Ready for dessert?"

    config = {
        'name': name,
        'machineType': machine_type,

        # Specify the boot disk and the image to use as a source.
        'disks': [
            {
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': source_disk_image,
                }
            }
        ],

        # Specify a network interface with NAT to access the public
        # internet.
        'networkInterfaces': [{
            'network': 'global/networks/default'
            #'network': 'global/networks/default',
            #'accessConfigs': [
            #    {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
            #]
        }],

        # Allow the instance to access cloud storage and logging.
        'serviceAccounts': [{
            'email': 'default',
            'scopes': [
                'https://www.googleapis.com/auth/devstorage.read_write',
                'https://www.googleapis.com/auth/logging.write'
            ]
        }],

        # Metadata is readable from the instance and allows you to
        # pass configuration from deployment scripts to instances.
        'metadata': {
            'items': [
            {
                'key': 'url',
                'value': image_url
            }, {
                'key': 'text',
                'value': image_caption
            }]
        }
    }

    return compute.instances().insert(
        project=project,
        zone=zone,
        body=config).execute()
# [END create_instance]

# [START wait_for_operation]
def wait_for_operation(compute, project, zone, operation):
    print('Waiting for operation to finish...')
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            print("done.")
            if 'error' in result:
                raise Exception(result['error'])
            return result

        time.sleep(1)
# [END wait_for_operation]



def setupapi(project, zone, instance_name, instance_size, wait=False):
    compute = googleapiclient.discovery.build('compute', 'v1')

    print('Creating instance.')

    operation = create_instance(compute, project, zone, instance_name, instance_size)
    wait_for_operation(compute, project, zone, operation['name'])
    instances = list_instances(compute, project, zone)

    print('Instances in project %s and zone %s:' % (project, zone))
    for instance in instances:
        print(' - ' + instance['name'])

    print("""
Instance created.
It will take a minute or two for the instance to complete work.
Check this URL: http://storage.googleapis.com/{}/output.png
Once the image is uploaded press enter to delete the instance.
""")



def setupconfig():
    print ("""\nThis script is entended to spin up a cloud instance
of hadoop, spark and zeppelin on a google cloud instance. The setup is fast and automatic.""")

    askcontinue = raw_input('Do wish to continue? Y/n: ')
    while askcontinue != "Y":
        if askcontinue == "Y":
            pass
	elif askcontinue == "n":
            sys.exit("Exiting")
        else:
            askcontinue = raw_input('Do wish to continue? Y/n: ')

    print "\nGreat! Lets get some info.  A few questions:"
    print "What is your GCP username?  This user should be able to sudo."
    useris = raw_input("Username: ")

    print "\nWhat is your google instance ID?"
    print "You can find the id in GCP by clicking the project name like 'My First Project'"
    idis = raw_input("Google Project Id: ")

    print "\nWhat zone do you want these instances to exist:"
    print "See: https://cloud.google.com/compute/docs/regions-zones/regions-zones" 
    print "Options are:" 
    print gcpzones
    print ""
    zoneis = raw_input("Zone: ")

    print "\nThis script will spin up a single captain and several privates"
    #privatecnt = raw_input("How many private workers do we create? [1-20] ")

    privatetrk = False
    privatecnt = 0
    while privatetrk == False:
        try:
            privatecnt = int(raw_input("How many private workers to create? [1-20]: "))
            if 0 <= privatecnt <= 20:
                privatetrk = True
        except ValueError:
            print "Error: Numbers Only\n"
    privatesize = 'small'
    
    confsetup = ConfigParser.ConfigParser()
    twriter = open(configfile, 'w')

    confhead = 'labsetup'
    confsetup.add_section(confhead)
    confsetup.set(confhead, 'gcp_user', useris)
    confsetup.set(confhead, 'gcp_project_id', idis)
    confsetup.set(confhead, 'gcp_zone', zoneis)
    confsetup.set(confhead, 'private_number', privatecnt)
    confsetup.set(confhead, 'private_size', privatesize)
    confsetup.write(twriter)
    twriter.close()


def getconfig():
    # Read the config file
    confhead = 'labsetup'
    settings = ConfigParser.ConfigParser()
    settings.read(configfile)
    config = {}
    config['user'] =  settings.get(confhead,'gcp_user')
    config['projectid'] =  settings.get(confhead,'gcp_project_id')
    config['zone'] =  settings.get(confhead,'gcp_zone')
    config['private_num'] =  settings.get(confhead,'private_number')
    config['private_size'] =  settings.get(confhead,'private_size')

    return config

def main():
    
    if os.path.isfile(configfile): 
        apiconfig = getconfig()
    else:
        setupconfig()
        apiconfig = getconfig()

    # setup one captain
    setupapi(apiconfig['projectid'],apiconfig['zone'],'captain','medium')

    pstart = 1
    pend = int(apiconfig['private_num']) + 1
    while pstart != pend:
        print "Working on private %s" % pstart
        iname = 'private' + str(pstart) 
        setupapi(apiconfig['projectid'],apiconfig['zone'],iname,'small')
        pstart += 1

    compute = googleapiclient.discovery.build('compute', 'v1')
    current_inst = list_instances(compute,apiconfig['projectid'],apiconfig['zone'])
    print current_inst[0]
    sys.exit()
    print 'Waiting for instances to start'
    tstart = 1
    tstop = 100 
    while tstart != tstop:
        sys.stdout.write('\r')
        sys.stdout.write("[%-100s] %d%%" % ('='*tstart, 1*tstart))
        sys.stdout.flush()
        time.sleep(1)
        tstart += 1 
    print ""
    print "Configure Captain" 
    print "Configure Privates" 


if __name__ == '__main__':
    main()

