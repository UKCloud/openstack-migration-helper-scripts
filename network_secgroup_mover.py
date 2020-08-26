#!/usr/bin/env python3

import os
import csv
import argparse
import openstack
import json
import time
import fileinput
from getpass import getpass


def validate_export(export_sec_grp, file_location, src_networks, src_subnet):
    """
    Initialise the storage location
    """
    
    if not os.path.exists(file_location):
        os.makedirs(file_location)
    if os.path.exists(export_sec_grp):
        sec_grp=open(export_sec_grp, "w")
        sec_grp.close()
    if os.path.exists(src_networks):
        sec_grp=open(src_networks, "w")
        sec_grp.close()
    if os.path.exists(src_subnet):
        sec_grp=open(src_subnet, "w")
        sec_grp.close()

def validate_project(project, conn):
    """
    Check the argument project exists and print out
    """

    projects = conn.identity.projects()
    for prj in projects:
        if project == prj.id:
            print ('Project ', project, ' exists continuing to collect data')
        else:
            exit

def export_security_groups(project, conn, src_sec_grp):
    """
    Collect list of Security Groups for a project
    once the list is collected extract the rules, if a rule has a remote group id replace
    the remote group id with the name of the associated rule, this will then be used to perform
    the reverse lookup when being imported to the new region. 
    """
    sec_grp_csv=open(src_sec_grp, "w")

    secgroup = conn.list_security_groups()

    for grp in secgroup:
        if project == grp.project_id:
            print(grp.name, grp.description, grp.id)
            groups = [ "group,%s,%s,%s \n" % (grp.name, grp.description, grp.id)]
            sec_grp_csv.writelines(groups)


    for grp in secgroup:
        if project == grp.project_id:
            print(grp.name, grp.description, grp.id)
            for i in range(len(grp.security_group_rules)):
                if grp.security_group_rules[i]['remote_group_id'] != None:
                    for remote_grp in secgroup:
                        if grp.security_group_rules[i]['remote_group_id'] == remote_grp.id:
                            grp.security_group_rules[i]['remote_group_id'] = remote_grp.name
                            rules = ["rules,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" %(grp.name,grp.security_group_rules[i]['direction'],grp.security_group_rules[i]['protocol'], grp.security_group_rules[i]['description'],
                                grp.security_group_rules[i]['port_range_max'], grp.security_group_rules[i]['port_range_min'], grp.security_group_rules[i]['ethertype'], 
                                grp.security_group_rules[i]['remote_group_id'], grp.security_group_rules[i]['remote_ip_prefix'])]
                            sec_grp_csv.writelines(rules)

                else:
                    print(grp.name,grp.security_group_rules[i])
                    rules = ["rules,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" %(grp.name,grp.security_group_rules[i]['direction'],grp.security_group_rules[i]['protocol'], grp.security_group_rules[i]['description'],
                            grp.security_group_rules[i]['port_range_max'], grp.security_group_rules[i]['port_range_min'], grp.security_group_rules[i]['ethertype'], 
                            grp.security_group_rules[i]['remote_group_id'], grp.security_group_rules[i]['remote_ip_prefix'])]
                    sec_grp_csv.writelines(rules)

def import_security_groups(project, conn, src_sec_grp):
    """
                create_rules=conn.create_security_group_rule(row[1],
                port_range_min=row[6],
                port_range_max=row[5],
                protocol=row[3],
                remote_ip_prefix=row[9],
                remote_group_id=row[8],
                direction=row[2],
                ethertype=row[7],
                project_id=project)
    """
    
    listsecgroup = conn.list_security_groups()
    
    for grp in listsecgroup:
        if (project == grp.project_id and grp.name == 'default'):
            default_id = grp.id
        elif project == grp.project_id:
            print(grp.id, grp.name)
  
    with open(src_sec_grp, newline='') as sec_grp_csv:
        reader=csv.reader(sec_grp_csv)
        for row in reader:
            for i, item in enumerate(row):
                if item == 'None':
                    row[i]=None
            if (row[0]=='group' and row[1]!='default'):    
                print ("group process")
                grp_create=conn.create_security_group(row[1], row[2], project_id=project)
                print("new security group id ", grp_create.id)
                getrules=conn.get_security_group_by_id(grp_create.id)
                print(getrules)
                for x in range(len(getrules.security_group_rules)):
                    print("removing automatically created rules to prevent duplication", getrules.security_group_rules[x]['id'])
                    remove_rules=conn.delete_security_group_rule(getrules.security_group_rules[x]['id'])
            elif (row[0]=='group' and row[1]=='default'):
                getdefrules=conn.get_security_group_by_id(default_id)
                print(getdefrules)
                for r in range(len(getdefrules.security_group_rules)):
                    print("removing automatically created DEFAULT rules to prevent duplication", getdefrules.security_group_rules[r]['id'])
                    remove_rules=conn.delete_security_group_rule(getdefrules.security_group_rules[r]['id'])

def import_security_group_rules(project, conn, src_sec_grp):
    """
                create_rules=conn.create_security_group_rule(row[1],
                port_range_min=row[6],
                port_range_max=row[5],
                protocol=row[3],
                remote_ip_prefix=row[9],
                remote_group_id=row[8],
                direction=row[2],
                ethertype=row[7],
                project_id=project)
    """
    listsecgroup = conn.list_security_groups()
    
    for grp in listsecgroup:
        if (project == grp.project_id and grp.name == 'default'):
            default_id = grp.id
    
    with open(src_sec_grp, newline='') as sec_grp_csv:
        reader=csv.reader(sec_grp_csv)
        for row in reader:
            for i, item in enumerate(row):
                if item == 'None':
                    row[i]=None
            if (row[0]=='rules' and row[8]==None and row[1]!='default'):
                print ("no remote group")
                create_rules=conn.create_security_group_rule(row[1],
                port_range_min=row[6],
                port_range_max=row[5],
                protocol=row[3],
                remote_ip_prefix=row[9],
                remote_group_id=row[8],
                direction=row[2],
                ethertype=row[7],
                project_id=project)
            elif(row[0]=='rules' and row[8]==None and row[1]=='default'):
                row[1] = default_id
                create_rules=conn.create_security_group_rule(row[1],
                port_range_min=row[6],
                port_range_max=row[5],
                protocol=row[3],
                remote_ip_prefix=row[9],
                remote_group_id=row[8],
                direction=row[2],
                ethertype=row[7],
                project_id=project)
                print("remote group required ")
            elif(row[0]=='rules' and row[8]!=None):
                for grp in listsecgroup:
                    if (project == grp.project_id and grp.name == row[8]):
                        row[8] = grp.id
                    if (row[8] == 'default'):
                        row[1] = default_id
                        row[8] = default_id

                create_rules=conn.create_security_group_rule(row[1],
                port_range_min=row[6],
                port_range_max=row[5],
                protocol=row[3],
                remote_ip_prefix=row[9],
                remote_group_id=row[8],
                direction=row[2],
                ethertype=row[7],
                project_id=project)
                print("remote group")        

def export_networks(project, conn, src_networks, src_subnet):
    networks_csv=open(src_networks, "w")
    subnet_csv=open(src_subnet, "w")
    
    listnetworks = conn.list_networks()

    for net in listnetworks:
        if project == net.project_id:
            print(net.name, net.subnets)
            networks = ["%s,%s\n" %(net.name, net.description)]
            networks_csv.writelines(networks)
            for i in net.subnets:
                getsubnets = conn.get_subnet(i)
                print (getsubnets.name,
                    getsubnets.description, 
                    getsubnets.enable_dhcp,
                    getsubnets.network_id,
                    getsubnets.dns_nameservers,
                    getsubnets.gateway_ip,
                    getsubnets.allocation_pools,
                    getsubnets.host_routes,
                    getsubnets.cidr)
                getsubnets.network_id = net.name
                subnets = ["%s|%s|%s|%s|%s|%s|%s|%s|%s\n" %(getsubnets.name,
                    getsubnets.description, 
                    getsubnets.enable_dhcp,
                    getsubnets.network_id,
                    getsubnets.dns_nameservers,
                    getsubnets.gateway_ip,
                    getsubnets.allocation_pools,
                    getsubnets.host_routes,
                    getsubnets.cidr)]
                subnet_csv.writelines(subnets)

def import_networks(project, conn, src_networks):
    
    with open(src_networks, newline='') as src_networks_csv:
        reader=csv.reader(src_networks_csv)
        for row in reader:
            for i, item in enumerate(row):
                if item == 'None':
                    row[i]=None
            createNetwork=conn.create_network(row[0], project_id=project)
            print("Network created\n" % createNetwork)

def import_subnets(project, conn, src_subnet):
    """
    subnets = ["%s|%s|%s|%s|%s|%s|%s|%s|%s\n" %(getsubnets.name, row[0]
        getsubnets.description, row[1]
        getsubnets.enable_dhcp, row[2] 
        getsubnets.network_id, row[3]
        getsubnets.dns_nameservers, row[4]
        getsubnets.gateway_ip, row[5]
        getsubnets.allocation_pools, row[6]
        getsubnets.host_routes, row[7]
        getsubnets.cidr row[8])]
        create_subnet(network_name_or_id, 
        cidr=None, 
        ip_version=4, 
        enable_dhcp=False, 
        subnet_name=None, 
        tenant_id=None, 
        allocation_pools=None, 
        gateway_ip=None, 
        disable_gateway_ip=False, 
        dns_nameservers=None, 
        host_routes=None, 
        ipv6_ra_mode=None, 
        ipv6_address_mode=None, 
        prefixlen=None, 
        use_default_subnetpool=False, 
        **kwargs)
    """
    listnetworks = conn.list_networks()


    with open(src_subnet, newline='') as src_subnet_csv:
        reader=csv.reader(src_subnet_csv, delimiter='|')
        for row in reader:
            for i, item in enumerate(row):
                if item == 'None':
                    row[i]=None
                if item == '[]':
                    row[i]=None
                if "'" in item:
                    row[i]=json.loads(row[i].replace("'", '"'))
            for net in listnetworks:
                if (project == net.project_id and net.name == row[3] and row[7] != None):
                    row[3] = net.id
                    print(row[7])
                    create_subnets = conn.create_subnet(row[3],
                        cidr=row[8],
                        enable_dhcp=row[2],
                        subnet_name=row[0],
                        tenant_id=project,
                        allocation_pools=row[6],
                        dns_nameservers=row[4],
                        gateway_ip=row[5],
                        host_routes=row[7])
                    print(create_subnets)
                if (project == net.project_id and net.name == row[3] and row[7] == None):
                    row[3] = net.id
                    print(row[7])
                    create_subnets = conn.create_subnet(row[3],
                        cidr=row[8],
                        enable_dhcp=row[2],
                        subnet_name=row[0],
                        tenant_id=project,
                        allocation_pools=row[6],
                        dns_nameservers=row[4],
                        gateway_ip=row[5])
                    print(create_subnets)





def main():
    parser = argparse.ArgumentParser(
        description="\
\n==================================================================================================================================\
\nDumps Security Groups, Rules, Networks and subnets for a given project, and provides a method of importing them to a blank project.\
\n==================================================================================================================================\
\n**********************************WARNING******************************************************************************\
\nThis script is provided as is with no gaurentee or warrenty, bugs or suggestions may be submited through github issues.\
\nUKCloud accepts no liability for loss or damage through use of this scipt.\
\n***********************************************************************************************************************\
\nIf you are a UKCloud Customer requiring assistance with this script, please raise a support ticket via the portal.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-s",
                        "--source",
                        help="Source Customer Project ID",
                        required=True)
    parser.add_argument("-r",
                        "--region",
                        help="Customer Project source region",
                        required=True)
    parser.add_argument("-d",
                        "--destination",
                        help="Destination Customer Project ID ",
                        required=False)
    parser.add_argument("-p",
                        "--process",
                        help="import or export",
                        required=True)

    args = parser.parse_args()
    source=args.source
    region=args.region
    destination=args.destination
    process=args.process
    
    conn = openstack.connect(cloud='envvars')

    sec_grp_file=source + '-security.csv'
    file_location='/tmp/' + region + '/'
    src_sec_grp=file_location + sec_grp_file
    network_file=source + '-networks.csv'
    src_networks=file_location + network_file
    subnet_file=source + '-subnet.csv'
    src_subnet=file_location + subnet_file


    if process == 'export':
        project = source
        validate_export(src_sec_grp, file_location, src_networks, src_subnet)
        validate_project(project, conn)
        export_security_groups(project, conn, src_sec_grp)
        export_networks(project, conn, src_networks, src_subnet)
    else:
        project = destination
        validate_project(project, conn)
        import_security_groups(project, conn, src_sec_grp)
        import_security_group_rules(project, conn, src_sec_grp)
        import_networks(project, conn, src_networks)
        import_subnets(project, conn, src_subnet)




    ##validate_project(project, conn)
    ##parse_security_groups(project, conn, export_sec_grp)

if __name__ == "__main__":
    main()
