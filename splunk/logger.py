import sys
import logging
logging.basicConfig(level=logging.CRITICAL)

import hpfeeds
from processors import *

import traceback

HOST = 'localhost'
PORT = 10000
CHANNELS = [
    'amun.events',
    'dionaea.connections',
    'dionaea.capture',
    'glastopf.events',
    'beeswarm.hive',
    'kippo.sessions',
    'conpot.events',
    'snort.alerts'
    'wordpot.events',
    'shockpot.events',
    'p0f.events',
    'suricata.events',
]
IDENT = ''
SECRET = ''

if len(sys.argv) > 1:
    print >>sys.stderr, "Parsing config file: %s"%sys.argv[1]
    import json
    config = json.load(file(sys.argv[1]))
    HOST        = config["HOST"]
    PORT        = config["PORT"]
    # hpfeeds protocol has trouble with unicode, hence the utf-8 encoding here
    CHANNELS    = [c.encode("utf-8") for c in config["CHANNELS"]]
    IDENT       = config["IDENT"].encode("utf-8")
    SECRET      = config["SECRET"].encode("utf-8")
else:
    print >>sys.stderr, "Warning: no config found, using default values for hpfeeds server"

PROCESSORS = {
    'amun.events': [amun_events],
    'glastopf.events': [glastopf_event,],
    'dionaea.capture': [dionaea_capture,],
    'dionaea.connections': [dionaea_connections,],
    'beeswarm.hive': [beeswarm_hive,],
    'kippo.sessions': [kippo_sessions,],
    'conpot.events': [conpot_events,],
    'snort.alerts': [snort_alerts,],
    'wordpot.events': [wordpot_event,],
    'shockpot.events': [shockpot_event,],
    'p0f.events': [p0f_events,],
    'suricata.events': [suricata_events,],
}

def main():    
    try:
        hpc = hpfeeds.new(HOST, PORT, IDENT, SECRET)
    except hpfeeds.FeedException, e:
        print >>sys.stderr, 'feed exception:', e
        return 1

    print >>sys.stderr, 'connected to', hpc.brokername

    def on_message(identifier, channel, payload):
        procs = PROCESSORS.get(channel, [])
        for processor in procs:
            try:
                message = processor(identifier, payload)
            except Exception, e:
                print >> sys.stderr, "invalid message %s" % payload
                traceback.print_exc(file=sys.stdout)
                continue
            if message: 
                # TODO: log message to CIM format
                print message
                pass


    def on_error(payload):
        print >>sys.stderr, ' -> errormessage from server: {0}'.format(payload)
        hpc.stop()

    hpc.subscribe(CHANNELS)
    try:
        hpc.run(on_message, on_error)
    except hpfeeds.FeedException, e:
        print >>sys.stderr, 'feed exception:', e
    except KeyboardInterrupt:
        pass
    except:
        traceback.print_exc()
    finally:
        hpc.close()
    return 0

if __name__ == '__main__':
    try: sys.exit(main())
    except KeyboardInterrupt:sys.exit(0)
