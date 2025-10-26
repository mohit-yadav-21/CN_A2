#!/usr/bin/env python3
import sys, csv, socket, time

if len(sys.argv) != 2:
    print("Usage: python3 send_first_10.py <queries_csv>")
    sys.exit(1)

queries_csv = sys.argv[1]
domains = []

with open(queries_csv, newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        if row and row[1] and row[1] not in domains:
            domains.append(row[1])
        if len(domains) >= 10:
            break

print(f"Sending {len(domains)} queries...\n")

for i, domain in enumerate(domains, 1):
    try:
        socket.setdefaulttimeout(1)
        t0 = time.perf_counter()
        socket.getaddrinfo(domain, None)
        latency = (time.perf_counter() - t0) * 1000
        print(f"[{i}/10] {domain} resolved in {latency:.2f} ms")
    except Exception as e:
        print(f"[{i}/10] {domain} failed")

print("Done.\n")
