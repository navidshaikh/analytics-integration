echo "Run beanstalkd server container.."
docker run -d --name beanstalkd_server -p 11300:11300 beanstalkd

echo "Start dispatcher worker"
cp scripts/dispatcher-worker.service /etc/systemd/dispatcher-worker.service
systemctl restart dispatcher-worker.service

echo "Start scan worker"
cp scripts/scan-worker.service /etc/systemd/scan-worker.service
systemctl restart scan-worker.service
