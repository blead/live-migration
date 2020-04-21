[host]
${hosts}
[host:vars]
ansible_ssh_extra_args='-o StrictHostKeyChecking=no'
ansible_ssh_private_key_file=${private_key_file}
ansible_ssh_user=${ssh_user}

[vpn]
${vpns}
[vpn:vars]
ansible_ssh_extra_args='-o StrictHostKeyChecking=no'
ansible_ssh_private_key_file=${private_key_file}
ansible_ssh_user=${ssh_user}
