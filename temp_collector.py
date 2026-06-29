import subprocess
import json

result = subprocess.run(['sensors', '-j'], capture_output=True, text=True)
data = json.loads(result.stdout)

proxmox_temperatures = {
    'cpu_package': data['coretemp-isa-0000']['Package id 0']['temp1_input'],
    'nvme0': data['nvme-pci-0100']['Composite']['temp1_input'],
    'nvme1': data['nvme-pci-0200']['Composite']['temp1_input'],
    'network': data['r8169_0_8200:00-mdio-0']['temp1']['temp1_input'],
}

print(json.dumps(proxmox_temperatures))