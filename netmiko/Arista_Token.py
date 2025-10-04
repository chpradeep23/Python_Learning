from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time
import os
from pprint import pprint


# Define device parameters

USERNAME = os.environ.get('SSH_USER')
PASSWORD = os.environ.get('SSH_PASSWORD')
device_parameters = {
#    "device_type": "cisco_ios",
    "device_type": "arista_eos",    #Use this if you are connecting to Arista_EOS.
#    "host": "10.155.76.10",  # Replace with your device's IP address if you want to run for device locally rather than from a file.
    "username": USERNAME,  # Replace with your SSH username
    "password": PASSWORD,  # Replace with your SSH password
    "secret": PASSWORD,  # Replace with your enable password if required
#    "port": 22, # Replace with your port that you use for SSH
}


# --- Read IP addresses from the file and build the list of dictionaries ---
device_list = []
try:
    with open("ip_list.txt", "r") as file:
        for ip in file:
            ip = ip.strip() # Strip whitespace (like newlines) from the IP address
            device_info = device_parameters.copy() # Creates a copy of a dictionary called device_parameters # Use .copy() to avoid overwriting
            device_info["host"] = ip #Sets the "host" key in the copied dictionary to the current IP address
            device_list.append(device_info) #Adds the modified dictionary to a list called device_list
except FileNotFoundError:
    print("Error: ip_list.txt not found.")
    exit()

# --- Loop through the device list and connect ---
def connect_and_run(device):
    result = {"host": ip, "output": {}, "status": "success"}   #for device in device_list:
    try:
        print(f"Connecting to {ip}...")
        connection = ConnectHandler(**device)

#Why send_command_timing?
#send_command() waits for a prompt and may timeout if the command expects user input.
#send_command_timing() doesn’t wait for a prompt, making it ideal for interactive commands like copy terminal: which expect input followed by Ctrl+D.

        # 1️⃣ Send 'copy terminal: file:/tmp/token' --> # Send the command using timing (for interactive commands)
        output = connection.send_command_timing("copy terminal: file:/tmp/token")
        time.sleep(1)

        # 2️⃣ Paste the token (multiline string)
        token_data = """******"""
        output += connection.send_command_timing(token_data)

        # 3️⃣ Send Ctrl+D (EOF) --> # Simulate Ctrl+D by sending the ASCII EOF character
        output += connection.send_command_timing("\x04", strip_prompt=False, strip_command=False) # Ctrl+D is ASCII 0x04
        result["output"]["copy_token"] = output

        connection.disconnect()
        print(f"[{ip}] Done.")
    except NetmikoTimeoutException:
        result["status"] = "timeout"
        result["error"] = "Connection timed out"
    except NetmikoAuthenticationException:
        result["status"] = "auth_failed"
        result["error"] = "Authentication failed" 
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    return result

# Run all devices in parallel
start_time = datetime.now()
results = []

max_threads = 5  # Adjust based on your system and network
with ThreadPoolExecutor(max_workers=max_threads) as executor:
    futures = [executor.submit(connect_and_run, device) for device in device_list]
    for future in as_completed(futures):
        results.append(future.result())

# ──────────────────────────────
# Print summary
print("\n=== Summary ===")
for r in results:
    print(f"\n✅ Device: {r['host']} - Status: {r['status']}")
    if r["status"] == "success":
        for cmd, output in r["output"].items():
            print(f"\n--- {cmd} ---\n{output}")
    else:
        print(f"❌ Error: {r.get('error', 'Unknown error')}")

print(f"\nCompleted in {datetime.now() - start_time}")