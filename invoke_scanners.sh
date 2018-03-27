set u+x

# invoke analytics-integration scanner
echo "Running analytics-integration scanner"
IMAGE_NAME=che-starter:rhel7 SERVER=http://f8a-gemini-server-aagshah-greenfield-test.dev.rdu2c.fabric8.io atomic scan --verbose --scanner=analytics-integration che-starter:rhel7

# invoke scanner-rpm-verify
echo "Running rpm-verify scanner.."
atomic scan --scanner=rpm-verify  --verbose che-starter:rhel7

# invoke misc-package-update-scanner
echo "Running misc-package-updates scanner for pip-updates.."
IMAGE_NAME=che-starter:rhel7 atomic scan --verbose --scanner=misc-package-updates  che-starter:rhel7

# invoke container-capabilities-scanner
echo "Running container-capabilities scanner.."
IMAGE_NAME=che-starter:rhel7 atomic scan --verbose --scanner=container-capabilities-scanner  che-starter:rhel7

##  invoke pipeline-scanner

# first mount the image under test on /mnt
echo "Running pipeline-scanner.."
atomic mount -o rw che-starter:rhel7 /mnt
# now run the scanner
atomic scan --verbose --scanner=pipeline-scanner  --rootfs=/mnt che-starter:rhel7
umount /mnt
