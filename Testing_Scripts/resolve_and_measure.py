#!/usr/bin/env python3
import sys, socket, time, csv, os

if len(sys.argv) != 3:
    print("Usage: python3 resolve_measure_summary.py <host_name> <queries_csv>")
    sys.exit(1)

host_name, queries_csv = sys.argv[1], sys.argv[2]
socket.setdefaulttimeout(5.0)

queries = []
with open(queries_csv, newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        if row and row[1]:  # row[1] = dns.qry.name
            try:
                frame_len = int(row[3])  # row[3] = frame.len
            except:
                frame_len = 100  # fallback if missing
            queries.append((row[1], frame_len))

total = len(queries)
successes, failures = 0, 0
latencies = []
total_bits = 0  

t_start = time.perf_counter()
for i, (domain, query_len) in enumerate(queries, 1):
    t0 = time.perf_counter()
    try:
        socket.getaddrinfo(domain, None)
        latency = (time.perf_counter() - t0) * 1000
        latencies.append(latency)
        successes += 1
        total_bits += query_len * 8  
    except:
        failures += 1
    if i % 50 == 0:
        print(f"{i}/{total} queries done...")

t_total = time.perf_counter() - t_start
avg_latency = sum(latencies) / len(latencies) if latencies else 0
throughput_bps = total_bits / t_total if t_total else 0

# Print summary
print(f"\n=== DNS Resolution Stats for {host_name} ===")
print(f"Total queries: {total}")
print(f"Successful resolutions: {successes}")
print(f"Failed resolutions: {failures}")
print(f"Average lookup latency: {avg_latency:.2f} ms")
print(f"Average throughput: {throughput_bps:.2f} bits/s")

# Write / append to CSV
csv_path = "/home/mininet/Assignment2/results_summary_partb.csv"
file_exists = os.path.exists(csv_path)

with open(csv_path, "a", newline="") as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(["Host", "Total Queries", "Success", "Failure", "Avg Latency (ms)", "Throughput (bps)"])
    writer.writerow([host_name, total, successes, failures, f"{avg_latency:.2f}", f"{throughput_bps:.2f}"])

print(f"\nAppended results to {csv_path}\n")

