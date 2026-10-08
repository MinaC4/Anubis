import os
import time

if 'SENTRY_DSN' in os.environ:
    del os.environ['SENTRY_DSN']

from kubernetes import config

from anubis.utils.data import with_context
from anubis.k8s.pipeline.reap import reap_pipeline_jobs


def main():
    config.load_incluster_config()
    poll_interval = int(os.environ.get("ANUBIS_POLLER_INTERVAL_SECONDS", "1"))

    while True:
        with_context(reap_pipeline_jobs)()
        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
