from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import time
import os
from pprint import pprint


# Define device parameters

USERNAME = os.environ.get('SSH_USER')
PASSWORD = os.environ.get('SSH_PASSWORD')
device_list = []
device_parameters = {
    "device_type": "cisco_ios",
#   "device_type": "arista_eos",    #Use this if you are connecting to Arista_EOS.
#    "host": "10.155.76.10",  # Replace with your device's IP address if you want to run for device locally rather than from a file.
    "username": USERNAME,  # Replace with your SSH username
    "password": PASSWORD,  # Replace with your SSH password
    "secret": PASSWORD,  # Replace with your enable password if required
#    "port": 22, # Replace with your port that you use for SSH
}


# --- Read IP addresses from the file and build the list of dictionaries ---
try:
    with open("ip_list2.txt", "r") as file:
        for ip in file:
            # Strip whitespace (like newlines) from the IP address
            ip = ip.strip()

            # Create a dictionary for the current device
            device_info = device_parameters.copy()  # Use .copy() to avoid overwriting
            device_info["host"] = ip

            # Add the new device dictionary to our list
            device_list.append(device_info)
except FileNotFoundError:
    print("Error: ip_list2.txt not found.")
    exit()

# --- Loop through the device list and connect ---
def device_info(device):
#for device in device_list:
    try:
        print(f"Connecting to {device['host']}...")
        with ConnectHandler(**device) as net_connect:
            commands = ['no snmp-server community ******** view NO_BAD_SNMP RO',
                        'snmp-server view NO_BAD_SNMP iso included',
                        'snmp-server view NO_BAD_SNMP snmpUsmMIB excluded',
                        'snmp-server view NO_BAD_SNMP snmpVacmMIB excluded',
                        'snmp-server view NO_BAD_SNMP snmpCommunityMIB excluded',
#                        'snmp-server view NO_BAD_SNMP internet.6.3.15 excluded',
#                        'snmp-server view NO_BAD_SNMP internet.6.3.16 excluded',
#                        'snmp-server view NO_BAD_SNMP internet.6.3.18 excluded',
                        'snmp-server view NO_BAD_SNMP cafSessionMethodsInfoEntry.2.1.111 excluded',
                        'snmp-server community tenney-dog view NO_BAD_SNMP RO']
            result = net_connect.send_config_set(commands)
            print(f"Config result for {device['host']}:\n{result}")
            output = net_connect.send_command("show run | include snmp")
            return f"Host: {device['host']}\n{output}"
    except NetmikoTimeoutException:
        output = 'Connection timed out'
    except NetmikoAuthenticationException:
        output = 'Authentication failed'
        print(f"Output from {device['host']}:\n{output}\n")
    except Exception as e:
        print(f"Could not connect to {device['host']}: {e}\n")

# Run the tasks in parallel
start_time = time.time()
with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(device_info, device_list)

for result in results:
    print("-" * 20)
    print(result)

end_time = time.time()
print(f"\nExecution Time: {end_time - start_time:.2f} seconds")