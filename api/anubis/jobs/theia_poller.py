import os
import time

if 'SENTRY_DSN' in os.environ:
    del os.environ['SENTRY_DSN']

from kubernetes import config

from anubis.utils.data import with_context
from anubis.k8s.theia.update import update_all_theia_sessions


def main():
    config.load_incluster_config()
    poll_interval = int(os.environ.get("ANUBIS_POLLER_INTERVAL_SECONDS", "1"))

    while True:
        with_context(update_all_theia_sessions)()
        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
