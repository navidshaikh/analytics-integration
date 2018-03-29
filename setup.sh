echo "Run beanstalkd server container.."
docker run -d --name beanstalkd_server -p 11300:11300 beanstalkd:rhel7

echo "Start dispatcher worker"
cp scripts/dispatcher-worker.service /etc/systemd/system/dispatcher-worker.service
systemctl daemon-reload
systemctl restart dispatcher-worker.service
systemctl status dispatcher-worker.service

echo "Start scan worker"
cp scripts/scan-worker.service /etc/systemd/system/scan-worker.service
systemctl daemon-reload
systemctl restart scan-worker.service
systemctl status scan-worker.service

echo "Start scan worker"
cp scripts/notify-worker.service /etc/systemd/system/notify-worker.service
systemctl daemon-reload
systemctl restart notify-worker.service
systemctl status notify-worker.service
