set u+x

# invoke analytics-integration scanner
IMAGE_NAME=che-starter:rhel7 SERVER=http://f8a-gemini-server-aagshah-greenfield-test.dev.rdu2c.fabric8.io atomic scan --verbose  --scanner=analytics-integration che-starter:rhel7

# invoke scanner-rpm-verify
atomic scan --scanner=rpm-verify --verbose che-starter:rhel7

# invoke misc-package-update-scanner
IMAGE_NAME=che-starter:rhel7 atomic scan --scanner=misc-package-updates --verbose che-starter:rhel7

# invoke container-capabilities-scanner
IMAGE_NAME=che-starter:rhel7 atomic scan --scanner=container-capabilities-scanner --verbose che-starter:rhel7

##  invoke pipeline-scanner

# first mount the image under test on /mnt
atomic mount -o rw che-starter:rhel7 /mnt
# now run the scanner
atomic scan --scanner=pipeline-scanner --verbose --rootfs=/mnt che-starter:rhel7
