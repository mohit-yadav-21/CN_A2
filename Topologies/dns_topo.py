from mininet.topo import Topo
from mininet.link import TCLink

class CustomTopo(Topo):
    def build(self):
        H1 = self.addHost('H1', ip='10.0.0.1/24')
        H2 = self.addHost('H2', ip='10.0.0.2/24')
        H3 = self.addHost('H3', ip='10.0.0.3/24')
        H4 = self.addHost('H4', ip='10.0.0.4/24')
        DNSR = self.addHost('DNSR', ip='10.0.0.5/24')

        S1, S2, S3, S4 = [self.addSwitch(f'S{i}') for i in range(1,5)]

        self.addLink(H1, S1, bw=100, delay='2ms', cls=TCLink)
        self.addLink(H2, S2, bw=100, delay='2ms', cls=TCLink)
        self.addLink(H3, S3, bw=100, delay='2ms', cls=TCLink)
        self.addLink(H4, S4, bw=100, delay='2ms', cls=TCLink)

        self.addLink(S1, S2, bw=100, delay='5ms', cls=TCLink)
        self.addLink(S2, S3, bw=100, delay='8ms', cls=TCLink)
        self.addLink(S3, S4, bw=100, delay='10ms', cls=TCLink)
        self.addLink(DNSR, S2, bw=100, delay='1ms', cls=TCLink)

topos = { 'mytopo': (lambda: CustomTopo()) }
