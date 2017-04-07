#!/bin/sh

# Setup a general

# Setup SSH keys Note we are using generals key
# Ansible needs to ssh to itself. Odd but necessary.
echo "Setting up SSH keys, hit returns for all default values or customize as you see fit"
/usr/bin/ssh-keygen -t rsa
/bin/cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys

# Start setting up the general
echo ""
echo -e "\e[0;"36"mYou will need to correct your labhosts file with the general info first"
echo "Edit labhosts with the correct IP/hostname and user"
echo "Then run your playbook on the general with:"
echo ""
echo -e "\e[0;"33"m ansible-playbook site.yml -i labhosts -l lab-general \033[0m"
echo ""
cd sparklab
exit
