
"""
Stats architecture:

 * streamer.StatsStreamer listens to circusd events and maintain a list of pids
 * collector.StatsCollector runs a pool of threads that compute stats for each
   pid in the list. Each stat is pushed in a queue
 * publisher.StatsPublisher continuously pushes those stats in a zmq PUB socket
 * client.StatsClient is a simple subscriber that can be used to intercept the
   stream of stats.
"""
import sys
import argparse
import logging

from circus.stats.streamer import StatsStreamer
from circus import logger
from circus import util


LOG_LEVELS = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG}

LOG_FMT = r"%(asctime)s [%(process)d] [%(levelname)s] %(message)s"
LOG_DATE_FMT = r"%Y-%m-%d %H:%M:%S"


def main():
    desc = 'Runs the stats aggregator for Circus'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--endpoint',
            help='The circusd ZeroMQ socket to connect to',
            default='tcp://127.0.0.1:5555')

    parser.add_argument('--pubsub',
            help='The circusd ZeroMQ pub/sub socket to connect to',
            default='tcp://127.0.0.1:5556')

    parser.add_argument('--statspoint',
            help='The ZeroMQ pub/sub socket to send data to',
            default='tcp://127.0.0.1:5557')

    parser.add_argument('--log-level', dest='loglevel', default='info',
            help="log level")

    parser.add_argument('--log-output', dest='logoutput', default='-',
            help="log output")

    args = parser.parse_args()

    # configure the logger
    loglevel = LOG_LEVELS.get(args.loglevel.lower(), logging.INFO)
    logger.setLevel(loglevel)
    if args.logoutput == "-":
        h = logging.StreamHandler()
    else:
        h = logging.FileHandler(args.logoutput)
        util.close_on_exec(h.stream.fileno())
    fmt = logging.Formatter(LOG_FMT, LOG_DATE_FMT)
    h.setFormatter(fmt)
    logger.addHandler(h)

    stats = StatsStreamer(args.endpoint, args.pubsub, args.statspoint)
    try:
        stats.start()
    finally:
        stats.stop()
        sys.exit(0)


if __name__ == '__main__':
    main()
