from dns_topo import CustomTopo
import networkx as nx
import matplotlib.pyplot as plt

t = CustomTopo()
G = nx.Graph()

for node in t.hosts() + t.switches():
    G.add_node(node)

for src, dst in t.links():
    params = t.linkInfo(src, dst)
    bw = params.get('bw', '')
    delay = params.get('delay', '')
    label = f"{bw}Mbps, {delay}" if bw or delay else ''
    G.add_edge(src, dst, label=label)

pos = nx.spring_layout(G, seed=42)
plt.figure(figsize=(8,6))
nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=2000, font_size=10, font_weight='bold')
edge_labels = nx.get_edge_attributes(G, 'label')
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

plt.title("Mininet Custom Topology (with link parameters)")
plt.tight_layout()
plt.show()

