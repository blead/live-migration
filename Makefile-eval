infra:
	cd ${INFRA_DIR} && terraform apply
	terraform output ansible_inventory > hosts
	cd -

infra-refresh:
	cd ${INFRA_DIR} && terraform refresh
	terraform output ansible_inventory > hosts
	cd -

vpn: 
	ansible-playbook -i ${HOST_FILE} ipsec-vpn/playbook.yaml

host:
	ansible-playbook -i ${HOST_FILE} -e source=${SOURCE_IP} -e target=${DEST_IP} migration-host/playbook.yaml

container:
	time ansible-playbook -i ${HOST_FILE} -e source=${SOURCE_IP} oci-container/playbook.yaml

reset:
	time ansible-playbook -i ${HOST_FILE} -e source=${SOURCE_IP} reset-environment/playbook.yaml

migrate:
	time ansible-playbook -v -i ${HOST_FILE} -e source=${SOURCE_IP} -e target=${DEST_IP} process-migration/playbook.yaml

migrate-pre-copy:
	time ansible-playbook -v -i ${HOST_FILE} -e source=${SOURCE_IP} -e target=${DEST_IP} -e precopy=true process-migration/playbook.yaml

migrate-pre-copy-dedup:
	time ansible-playbook -v -i ${HOST_FILE} -e source=${SOURCE_IP} -e target=${DEST_IP} -e precopy=true -e autodedup=true process-migration/playbook.yaml -e number=${NUMBER}

migrate-page-server:
	time ansible-playbook -v -i ${HOST_FILE} -e source=${SOURCE_IP} -e target=${DEST_IP} -e pageserver=true process-migration/playbook.yaml

migrate-pc-ps:
	time ansible-playbook -v -i ${HOST_FILE} -e source=${SOURCE_IP} -e target=${DEST_IP} -e precopy=true -e pageserver=true -e autodedup=true process-migration/playbook.yaml -e number=${NUMBER} -e experiment='precopy-pageserver-haproxy' -e workload=400

migrate-pageserver-dedup:
	time ansible-playbook -v -i ${HOST_FILE} -e source=${SOURCE_IP} -e target=${DEST_IP} -e pageserver=true -e autodedup=true process-migration/playbook.yaml -e number=${NUMBER}

migrate-eval:
	time ansible-playbook -v -i ${HOST_FILE} -e source=${SOURCE_IP} -e target=${DEST_IP} -e precopy=true -e pageserver=true -e autodedup=true process-migration/playbook.yaml -e number=${NUMBER} -e experiment='demo' -e workload=0

clean: reset container
