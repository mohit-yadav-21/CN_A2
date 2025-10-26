import re
import sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def parse_log(filename):
    results = []
    domain = None
    steps = 0
    total_time = None
    success = None
    rtts = []
    order_counter = 0

    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    for raw in lines:
        line = raw.strip()

        if "Query from" in line and " for " in line:
            if domain is not None:
                results.append({
                    "domain": domain,
                    "steps": steps,
                    "total_time": total_time,
                    "success": success,
                    "rtts": rtts,
                    "order": order_counter
                })
                order_counter += 1

            m = re.search(r'for\s+([^\s]+)', line)
            domain = m.group(1).rstrip('.') if m else "UNKNOWN"
            steps = 0
            total_time = None
            success = True
            rtts = []

        elif "RTT:" in line:
            m = re.search(r"RTT:\s*([\d\.]+)\s*ms", line)
            if m:
                rtts.append(float(m.group(1)))
                steps += 1

        elif "Total resolution time:" in line:
            m = re.search(r"Total resolution time:\s*([\d\.]+)\s*ms", line)
            if m:
                total_time = float(m.group(1))

        elif "Resolution failed" in line:
            success = False

    if domain is not None:
        results.append({
            "domain": domain,
            "steps": steps,
            "total_time": total_time,
            "success": success,
            "rtts": rtts,
            "order": order_counter
        })

    df = pd.DataFrame(results)
    df = df.dropna(subset=["total_time"]).reset_index(drop=True)
    return df


def select_first_10(df):
    """
    Keep the first 10 unique domains that appear in the log.
    If a later entry for one of these domains is successful, replace the earlier one.
    """
    selected = {}
    domain_order = []

    for _, row in df.iterrows():
        domain = row["domain"]

        if domain not in selected:
            if len(selected) < 10:
                selected[domain] = row.to_dict()
                domain_order.append(domain)
        else:
            if not selected[domain]["success"] and row["success"]:
                selected[domain] = row.to_dict()

        if len(selected) == 10 and all(d in selected for d in domain_order):
            break

    ordered = [selected[d] for d in domain_order if d in selected]
    return pd.DataFrame(ordered)


def plot_results(df10):
    if df10.empty:
        print("No data to plot.")
        return

    print("\nSummary of selected queries (first 10 unique domains):\n")
    print(df10[["domain", "steps", "total_time", "success"]].to_string(index=False))

    plt.figure(figsize=(11,6))
    x = np.arange(len(df10))
    bottoms = np.zeros(len(df10))

    for i in range(df10["steps"].max()):
        heights = [rtts[i] if len(rtts) > i else 0 for rtts in df10["rtts"]]
        plt.bar(x, heights, bottom=bottoms, label=f"Step {i+1}")
        bottoms += np.array(heights)

    plt.xticks(x, df10["domain"], rotation=45, ha="right")
    plt.title("Resolution Latency Breakdown (first 10 unique domains)")
    plt.xlabel("Domain")
    plt.ylabel("Time (ms)")
    plt.legend(title="Step")
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(11,5))
    plt.bar(df10["domain"], df10["steps"], color="skyblue")
    plt.xticks(rotation=45, ha="right")
    plt.title("DNS Servers Visited (first 10 unique domains)")
    plt.xlabel("Domain")
    plt.ylabel("Servers Visited")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyse_PCAP1.py <resolver_log.txt>")
        sys.exit(1)

    logfile = sys.argv[1]
    df = parse_log(logfile)

    if df.empty:
        print("No valid query data found in log.")
        sys.exit(0)

    df10 = select_first_10(df)
    plot_results(df10)
