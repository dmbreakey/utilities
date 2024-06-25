#! /usr/bin/python3
import argparse
import json
import math
import re
import subprocess

class Ping:
    _target:str = None
    _count:int = None
    _interval:float = None
    ping_binary:str = "/bin/ping"
    _parse_split:str = None
    _parse_response:object = None
    _parse_packets:object = None
    _parse_rtt:object = None
    _type:str = None
    _packet_loss:float = None
    _packets_transmitted:int = None
    _packets_received:int = None
    _time:int = None
    _rtt_min:float = None
    _rtt_avg:float = None
    _rtt_max:float = None
    _rtt_mdev:float = None


    def __init__(self, target:str, count:int = 20, interval:float = None, binary:str = None):
        self._target = target
        self._count = count
        self._interval = interval
        if binary:
            self.ping_binary = binary
        self.capture()

    def capture(self):
        if self._interval:
            command = f"{self.ping_binary} -n -i {self._interval} -c {self._count} -W 1 {self._target}"
        else:
            command = f"{self.ping_binary} -n -A -c {self._count} -w 2 {self._target}"
        ping = subprocess.getoutput(command)
        self._identify(ping)
        (raw, summary) = ping.split(self._parse_split)
        raw = raw.split('\n')
        summary = summary.split('\n')
        if self._type == "linux":
            self._evaluate_linux(raw, summary)
        elif self._type == "busybox":
            self._evaluate_busybox(raw, summary)
    
    def _evaluate_linux(self, raw:list, summary:list):
        try:
            match = self._parse_packets.match(summary[0])
        except:
            match = False
        if match:
            self._packets_transmitted = int(match.groups()[0])
            self._packets_received = int(match.groups()[1])
            self._packet_loss = float(match.groups()[2])
            self._time = int(match.groups()[3])

        try:
            match = self._parse_rtt.match(summary[1])
        except:
            match = False
        if match:
            self._rtt_min = float(match.groups()[0])
            self._rtt_avg = float(match.groups()[1])
            self._rtt_max = float(match.groups()[2])
            self._rtt_mdev = float(match.groups()[3])

    def _evaluate_busybox(self, raw:list, summary:list):
        try:
            match = self._parse_packets.match(summary[0])
        except:
            match = False
        if match:
            self._packets_transmitted = int(match.groups()[0])
            self._packets_received = int(match.groups()[1])
            self._packet_loss = float(match.groups()[2])
            self._time = None
        
        try:
            match = self._parse_rtt.match(summary[1])
        except:
            match = False
        if match:
            self._rtt_min = float(match.groups()[0])
            self._rtt_avg = float(match.groups()[1])
            self._rtt_max = float(match.groups()[2])

        # Evaluate raw data, to calculate mdev for RTT
        times = []
        for row in raw:
            try:
                match = self._parse_response.match(row)
            except:
                match = False
            if match:
                times.append(float(match.groups()[4]))
        if len(times) > 0:
            mean_rtt = sum(times) / len(times)
            squared_derivations = [(time - mean_rtt)**2 for time in times]

            self._rtt_mdev = round((sum(squared_derivations) / len(squared_derivations))**0.5, 3)
        else:
            self._rtt_mdev = None

    def _identify(self, input:object):
        if "\nrtt min/avg/max/mdev = " in input:
            self._type = "linux"
        elif "\nround-trip min/avg/max = " in input:
            self._type = "busybox"
        
        if self._type == "linux":
            self._re_setup_linux()
        elif self._type == "busybox":
            self._re_setup_busybox()

    def _re_setup_linux(self):
        self._parse_split = f"\n\n--- {self._target} ping statistics ---\n"
        self._parse_response = re.compile(r'^(\d+?) bytes from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}): icmp_seq=(\d+?) ttl=(\d+?) time=([0-9\.]+?) ms$')
        self._parse_packets = re.compile(r'^(\d+?) packets transmitted, (\d+?) received, ([0-9\.]+?)% packet loss, time (\d+?)ms$')
        self._parse_rtt = re.compile(r'^rtt min/avg/max/mdev = ([0-9\.]+?)/([0-9\.]+?)/([0-9\.]+?)/([0-9\.]+?) ms$')

    def _re_setup_busybox(self):
        self._parse_split = f"\n\n--- {self._target} ping statistics ---\n"
        self._parse_response = re.compile(r'^(\d+?) bytes from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}): seq=(\d+?) ttl=(\d+?) time=([0-9\.]+?) ms$')
        self._parse_packets = re.compile(r'^(\d+?) packets transmitted, (\d+?) packets received, ([0-9\.]+?)% packet loss$')
        self._parse_rtt = re.compile(r'^round-trip min/avg/max = ([0-9\.]+?)/([0-9\.]+?)/([0-9\.]+?) ms$')

    @property
    def rtt_min(self):
        return self._rtt_min
    
    @property
    def rtt_avg(self):
        return self._rtt_avg
    
    @property
    def rtt_max(self):
        return self._rtt_max
    
    @property
    def rtt_mdev(self):
        return self._rtt_mdev
    
    @property
    def packets_transmitted(self):
        return self._packets_transmitted
    
    @property
    def packets_received(self):
        return self._packets_received
    
    @property
    def packet_loss(self):
        return self._packet_loss
    
    @property
    def time(self):
        return self._time

    @property
    def ping_type(self):
        return self._type

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform a ping test and report on results")
    parser.add_argument("target", help="The IP address or hostname to ping")
    parser.add_argument("-c", "--count", type=int, default=50, help="Number of ping packets to send")
    parser.add_argument("-i", "--interval", type=float, default=0.2, help="Inter-packet interval, in seconds")
    parser.add_argument("-b", "--path", type=str, default="/bin/ping", help="Path to the ping binary")
    args = parser.parse_args()

    test = Ping(target=args.target, count=args.count, interval=args.interval, binary=args.path)

#    output = {'parameters': { 'target': args.target, 'count': args.count, 'interval': args.interval, 'binary': args.path},
#        'result': {'packets': { 'sent': test.packets_transmitted, 'received': test.packets_received, 'loss_percent': test.packet_loss},
#            'rtt': { 'minimum': test.rtt_min, 'average': test.rtt_avg, 'maximum': test.rtt_max, 'mdev': test.rtt_mdev},
#            'type': test.ping_type }}

    output = { 'target': args.target, 'count': args.count, 'interval': args.interval, 'binary': args.path,
        'packets_sent': test.packets_transmitted, 'packets_received': test.packets_received, 'packet_loss': test.packet_loss,
        'rtt_minimum': test.rtt_min, 'rtt_average': test.rtt_avg, 'rtt_maximum': test.rtt_max, 'rtt_mdev': test.rtt_mdev,
        'type': test.ping_type }

    print(json.dumps(output))
