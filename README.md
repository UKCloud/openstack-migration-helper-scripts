## UKCloud Network/Security group migration helper tool.

### Disclaimer
This script is provided as is with no gaurentee or warrenty, bugs or suggestions may be submited through github issues.
UKCloud accepts no liability for loss or damage through use of this scipt.

### Installation
Clone this repo into a directory.
Ensure your running python3. (We would recomend a virtual env)
Ensure you have python-openstacksdk installed.

### Using the script

To export a set of data from a project:
Source the rc file for the host project
Then run;
network_secgroup_mover.py -s "{SourceProjectID}" -r "{SourceRegionID}" -p "export"

eg.
source project1.rc
python network_secgroup_mover.py -s "ABCDEFG123" -r "RegionOne" -p export


Exporting the data will create three files in the /tmp/"region" directory   

"source project id"-networks.csv  
"source project id"-subnet.csv  
"source project id"-security.csv

eg.
/tmp/RegionOne/
ABCDEFG123-networks.csv
ABCDEFG123-subnet.csv
ABCDEFG123-security.csv


To import the configuration to a new project :  
Source the RC file for the new project ensuring it has access to the /tmp directory where the files were created  
Then run;
network_secgroup_mover.py -s "{SourceProjectID}" -r "{SourceRegionID}" -d "{DestinationProjectID}" -p "import"  

eg.
source destproject.rc
python network_secgroup_mover.py -s "{SourceProjectID}" -r "{SourceRegionID}" -d "{DestinationProjectID}" -p "import"

When the command is run the program will read from the source csv files using the original source project id and output accordingly to the new project.
