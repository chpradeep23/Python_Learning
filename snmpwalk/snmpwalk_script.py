import subprocess #subprocess: Allows you to run shell commands like snmpwalk from Python.
import re #re: Python’s regular expression module, used to search and extract patterns from text.
import os

# SNMP settings
ip_file = "ip_list.txt" #The file containing IP addresses (one per line).
community = os.environ.get('SNMP_COMMUNITY')
oid = "1.3.6.1.2.1.1.1.0"  # System description

def load_ips(filename): #This defines a function named load_ips.It takes one parameter: filename, which should be the name (or path) of the file containing IP addresses
    with open(filename, "r") as f: #This opens the file in read mode ("r"). with is a context manager that ensures the file is properly closed after reading.f is the file object used to read the contents.
        return [line.strip() for line in f if line.strip()] #line.strip() removes whitespace and newline characters.

# return [line.strip() for line in f if line.strip()]
#This is a list comprehension that:
#Loops through each line in the file.
#line.strip() removes leading/trailing whitespace (including newline characters).
#if line.strip() ensures empty lines are skipped.
#The result is a list of cleaned IP addresses.


def extract_vendor_and_version(output):
    # Extract vendor: first word after STRING:
    vendor_match = re.search(r'STRING:\s*"?(\w+)', output)
    vendor = vendor_match.group(1) if vendor_match else "N/A"

##vendor_match = re.search(r'STRING:\s*"?(\w+)', output)
#STRING:	Matches the literal word STRING:
#\s*	Matches zero or more whitespace characters (spaces, tabs, etc.)
#"?	Matches an optional double quote (")
#(\w+)	Captures one or more word characters (letters, digits, underscore)

##vendor = vendor_match.group(1) if vendor_match else "N/A"
#If a match is found, group(1) returns the captured vendor name.
#If no match is found, it returns "N/A".
#This ensures your script doesn’t crash if the pattern isn’t found.


    # Extract version: look for version-like patterns
    version_match = re.search(r'(\d+\.\d+(\.\d+)?)', output)
    version = version_match.group(1) if version_match else "N/A"

#version_match = re.search(r'(\d+\.\d+(\.\d+)?)', output)
#\d+	Matches one or more digits
#\.	Matches a literal dot
#\d+	Matches one or more digits after the dot
#(\.\d+)?	Matches an optional second dot and digits (for versions like 1.2.3)
#(...)	Capturing group — returns the matched version string
 
    return vendor, version
#This returns both values as a tuple, which you can unpack like this: vendor, version = extract_vendor_and_version(output)
def run_snmpwalk(ip):
    try:
        result = subprocess.run(
            ["snmpwalk", "-v2c", "-c", community, ip, oid],
            capture_output=True,
            text=True,
            timeout=10
        )
        vendor, version = extract_vendor_and_version(result.stdout)
        print(f"{ip}\tVENDOR: {vendor}\tVERSION: {version}")
    except subprocess.TimeoutExpired:
        print(f"{ip}\tVENDOR: Timeout\tVERSION: Timeout")
    except Exception as e:
        print(f"{ip}\tVENDOR: Error\tVERSION: Error")

if __name__ == "__main__":
    ip_list = load_ips(ip_file)
    print("IP Address\tVENDOR\tVERSION")
    print("-" * 50)
    for ip in ip_list:
        run_snmpwalk(ip)