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


def consolidate_all(df):
    """
    For all domains in the log:
    - Keep the last successful entry if available.
    - Otherwise keep the latest entry (even if failed).
    """
    latest = {}
    for _, row in df.iterrows():
        domain = row["domain"]
        if domain not in latest:
            latest[domain] = row.to_dict()
        else:
            if row["success"] or not latest[domain]["success"]:
                latest[domain] = row.to_dict()
    return pd.DataFrame(latest.values()).sort_values("order").reset_index(drop=True)


def plot_results(df_all):
    if df_all.empty:
        print("No data to plot.")
        return

    print("\nSummary of all unique domain queries:\n")
    print(df_all[["domain", "steps", "total_time", "success"]].to_string(index=False))

    plt.figure(figsize=(12,6))
    x = np.arange(len(df_all))
    bottoms = np.zeros(len(df_all))

    for i in range(df_all["steps"].max()):
        heights = [rtts[i] if len(rtts) > i else 0 for rtts in df_all["rtts"]]
        plt.bar(x, heights, bottom=bottoms, label=f"Step {i+1}")
        bottoms += np.array(heights)

    plt.xticks(x, df_all["domain"], rotation=45, ha="right")
    plt.title("Resolution Latency Breakdown (all unique domains)")
    plt.xlabel("Domain")
    plt.ylabel("Time (ms)")
    plt.legend(title="Step", fontsize=8)
    plt.tight_layout()
    plt.show()

    # Plot 2: Servers visited
    plt.figure(figsize=(12,5))
    plt.bar(df_all["domain"], df_all["steps"], color="skyblue")
    plt.xticks(rotation=45, ha="right")
    plt.title("DNS Servers Visited (all unique domains)")
    plt.xlabel("Domain")
    plt.ylabel("Servers Visited")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyse_PCAP1_all.py <resolver_log.txt>")
        sys.exit(1)

    logfile = sys.argv[1]
    df = parse_log(logfile)

    if df.empty:
        print("No valid query data found in log.")
        sys.exit(0)

    df_all = consolidate_all(df)
    plot_results(df_all)
