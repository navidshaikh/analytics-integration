ANALYTICS_SERVER = ""

# ===============alert-configs===================
#  possible types ["ok", "problem"]
# if specified only "problem" like ["problem"],
# only containers with problems will be reported
# if specified both like ["ok", "problem"],
# every container scanned will be reported
ALERTS = ["ok", "problem"]

# enter path to configured git repo with write and push access
# alerts will be added in this repo and pushed upon scan completion
GITREPO = ""
GITBRANCH = "master"
