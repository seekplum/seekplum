# -*- coding: utf-8 -*-

import time

from datetime import datetime

from scapy.arch import *  # noqa: F403
from scapy.layers.inet import IP, UDP
from scapy.packet import Raw, Packet
from scapy.sendrecv import sniff
from scapy.utils import hexdump


def packet_callback(packet: Packet) -> None:
    try:
        raw = packet[Raw]
        content = hexdump(raw, dump=True)
        if "02 00 48" not in content:
            return

        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("+" * 40)
        print("[*] Your IP: %s" % packet[IP].src)
        print("[*] Your Port: %s" % packet[UDP].sport)

        print("-" * 40)

        print("[*] Woof IP: %s" % packet[IP].dst)
        print("[*] Woof Port: %s" % packet[UDP].dport)
        print("+" * 40)

        # print(packet.show())
    except IndexError:
        pass
    except Exception as e:
        print("Unknown Error:", e)
    time.sleep(1)


if __name__ == "__main__":
    # 开启嗅探
    sniff(prn=packet_callback, store=False)
