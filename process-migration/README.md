# Live Migration: Process Migration

This performs the live migration. Source and target hosts need to be supplied to Ansible via variables (`-e` option).

## Inventory

Inventory file can be copied from the output of [Infrastructure](../infrastructure) section:

```sh
cp ../infrastructure/aws-gcp/hosts ./hosts
```

Otherwise, manually create a new file. See [`hosts.example`](hosts.example) for an example.

## Provision

Before provisioning, set up the SSH agent. For example, if the private key is `~/.ssh/id_rsa.pem`:

```sh
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa.pem
```

From the inventory, pick the source and target hosts.

Start provisioning:

```sh
ansible-playbook -i hosts -e source=8.9.10.11 -e target=104.215.155.205 playbook.yaml
```

## Enabling pre-copy

Add `-e precopy=true` to the command, for example, to enable both pre-copy:

```sh
ansible-playbook -i hosts -e source=8.9.10.11 -e target=104.215.155.205 -e precopy=true -e postcopy=true playbook.yaml
```
