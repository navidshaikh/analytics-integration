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

#===================OSIO access token config================
# place where refresh token needs to be sourced
REFRESH_TOKEN_FILE = "/opt/scanning/refresh_token.txt"

# place where the access token will be exported via this
# script
ACCESS_TOKEN_FILE = ("/opt/scanning/atomic_scanners/"
                     "scanner-analytics-integration/osio_token.txt")

ANALYTICS_SCANNER_CONTEXT = \
    "/opt/scanning/atomic_scanners/scanner-analytics-integration/"
