from mininet.net import Mininet
from mininet.node import Node
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.nodelib import NAT

class CustomTopo(Topo):
    def build(self):
        H1 = self.addHost('H1', ip='10.0.0.1/24')
        H2 = self.addHost('H2', ip='10.0.0.2/24')
        H3 = self.addHost('H3', ip='10.0.0.3/24')
        H4 = self.addHost('H4', ip='10.0.0.4/24')
        DNSR = self.addHost('DNSR', ip='10.0.0.5/24')

        S1, S2, S3, S4 = [self.addSwitch(f'S{i}') for i in range(1,5)]

        host_params = dict(bw=100, delay='2ms')
        self.addLink(H1, S1, cls=TCLink, **host_params)
        self.addLink(H2, S2, cls=TCLink, **host_params)
        self.addLink(H3, S3, cls=TCLink, **host_params)
        self.addLink(H4, S4, cls=TCLink, **host_params)

        self.addLink(S1, S2, cls=TCLink, bw=100, delay='5ms')
        self.addLink(S2, S3, cls=TCLink, bw=100, delay='8ms')
        self.addLink(S3, S4, cls=TCLink, bw=100, delay='10ms')

        # DNS server link
        self.addLink(DNSR, S2, cls=TCLink, bw=100, delay='1ms')

def topo():
	return CustomTopo()

topos = {'lin4': topo}

def run():
    topo = CustomTopo()
    net = Mininet(topo=topo, link=TCLink)

    info('*** Adding NAT for DNS forwarding\n')
    nat = net.addNAT(name='nat', connectTo='S2')
    nat.configDefault()

    nat.cmd('iptables -t nat -A PREROUTING -p udp --dport 53 -j DNAT --to-destination 10.0.0.6:53')
    nat.cmd('iptables -t nat -A PREROUTING -p tcp --dport 53 -j DNAT --to-destination 10.0.0.6:53')
    nat.cmd('iptables -A FORWARD -p udp -d 10.0.0.6 --dport 53 -j ACCEPT')
    nat.cmd('iptables -A FORWARD -p tcp -d 10.0.0.6 --dport 53 -j ACCEPT')

    net.start()

    info('*** Network configured. Ready for testing.\n')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
