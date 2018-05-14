# registry to poll repos for weekly scanning
# REGISTRY="10.70.49.190:5000"
REGISTRY="registry.devshift.net"
# whether registry is secured? set True/False
SECURE_REGISTRY=True
# empty list means all repos are target namespaces
TARGET_NAMESPACES=[]
ANALYTICS_SERVER=""
NOTIFY_EMAILS=["nshaikh@redhat.com"]

#===============email-configs===================
# possible types ["ok", "problem"]
ALERTS=["problem"]
