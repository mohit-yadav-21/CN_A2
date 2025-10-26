#!/usr/bin/env python3
import socket
import time
import sys
from dnslib import DNSRecord

ROOT_SERVERS = [
    "198.41.0.4",
    "199.9.14.201",
    "192.33.4.12",
]


def iterative_resolve(query_data):
    query = DNSRecord.parse(query_data)
    qname = str(query.q.qname)
    log = []
    start_time = time.time()
    current_servers = ROOT_SERVERS
    response = None
    step = 0

    while True:
        step += 1
        got_response = False
        data = None
        server_used = None
        recv_time = send_time = None

        for server in current_servers:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)  
            send_time = time.time()
            try:
                sock.sendto(query_data, (server, 53))
                data, _ = sock.recvfrom(2048)
                recv_time = time.time()
                got_response = True
                server_used = server
                sock.close()
                break  
            except socket.timeout:
                log.append({
                    "step": step,
                    "mode": "Iterative",
                    "stage": "Timeout",
                    "server": server,
                    "rtt": None,
                    "response": ["No response (timeout)"]
                })
                sock.close()
                continue  

        if not got_response:
            break

        rtt = (recv_time - send_time) * 1000
        resp = DNSRecord.parse(data)


        if step == 1:
            stage = "Root"
        elif len(resp.auth) > 0 and not resp.rr:
            stage = "TLD"
        else:
            stage = "Authoritative"

        response_summary = []
        records = resp.rr or resp.auth or []
        if records:
            for rr in records:
                response_summary.append(f"{rr.rname} -> {rr.rtype} -> {rr.rdata}")
        else:
            response_summary.append("Referral or empty response")

        log.append({
            "step": step,
            "mode": "Iterative",
            "stage": stage,
            "server": server_used,
            "rtt": round(rtt, 2),
            "response": response_summary
        })

        if resp.rr:
            response = data
            break

        ns_ips = []
        for rr in resp.ar:
            if rr.rtype == 1:
                ns_ips.append(str(rr.rdata))

        if not ns_ips:
            ns_names = [str(rr.rdata) for rr in resp.auth if rr.rtype == 2]
            if not ns_names:
                break

            ns_ips = []
            for ns in ns_names:
                sub_q = DNSRecord.question(ns)
                sub_resp, sub_log, _, _ = iterative_resolve(bytes(sub_q.pack()))
                log.extend(sub_log)  
                if sub_resp:
                    sub_parsed = DNSRecord.parse(sub_resp)
                    for rr in sub_parsed.rr:
                        if rr.rtype == 1:
                            ns_ips.append(str(rr.rdata))

        if not ns_ips:
            break

        current_servers = ns_ips

    total_time = (time.time() - start_time) * 1000
    return response, log, round(total_time, 2), qname


def main():
    log_file = sys.argv[1] if len(sys.argv) > 1 else "resolver_log.txt"
    with open(log_file, "a") as f:
        def log_print(*args, **kwargs):
            print(*args, **kwargs)
            print(*args, **kwargs, file=f)
            f.flush()

        header = f"\n===== New Run at {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n"
        f.write(header)
        print(header.strip())

        log_print("DNS Listener running on DNSR (port 53) ...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("10.0.0.5", 53))  # DNSR IP

        while True:
            data, addr = sock.recvfrom(512)
            recv_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            response, log, total, qname = iterative_resolve(data)

            log_print(f"\n[{recv_time}] Query from {addr[0]} for {qname}")
            for step_info in log:
                log_print(f"  Step {step_info['step']} | Mode: {step_info['mode']} | "
                          f"Stage: {step_info['stage']} | Server: {step_info['server']} | "
                          f"RTT: {step_info['rtt']} ms")
                log_print("    Response:")
                for line in step_info['response']:
                    log_print(f"      {line}")
                log_print()

            log_print(f"  Total resolution time: {total} ms")

            if response:
                sock.sendto(response, addr)
            else:
                log_print("  Resolution failed.\n")


if __name__ == "__main__":
    main()
