echo "Stop and remove beanstalkd server container.."
docker stop beanstalkd_server
docker rm beanstalkd_server

echo "Stop dispatcher worker"
systemctl stop dispatcher-worker.service

echo "Stop scan worker"
systemctl stop scan-worker.service

echo "Stop notify worker"
systemctl stop  notify-worker.service
