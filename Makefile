SOURCE_IP=13.250.58.159
DEST_IP=35.247.160.215
HOST_FILE=infrastructure/aws-gcp/hosts

host:
	ansible-playbook -i ${HOST_FILE} -e source=${SOURCE_IP} -e target=${DEST_IP} migration-host/playbook.yaml
container:
	time ansible-playbook -i ${HOST_FILE} -e source=$(SOURCE_IP) oci-container/playbook.yaml

reset:
	time ansible-playbook -i ${HOST_FILE} reset-environment/playbook.yaml

migrate:
	time ansible-playbook -i ${HOST_FILE} -e source=$(SOURCE_IP) -e target=${DEST_IP} process-migration/playbook.yaml


all: reset container
