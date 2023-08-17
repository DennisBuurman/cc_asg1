#!/bin/python3

from podman import PodmanClient
import subprocess
from subprocess import Popen
import time
import pandas as pd
from collections import deque
import numpy as np

class Controller:
    # Set up 
    def __init__(self):
        self.client = PodmanClient(base_url="unix:///run/podman/podman.sock")
        self.active_backends = []  # list of tuples containing active container info (name, ip, port)
        self.container_count = 0  # keeps track of issued and deleted backend container instances
        self.remove_queue = {}  # dict of async container rm processes to avoid race conditions
        
        # Scaling parameters
        self.upscale_threshold = 8
        self.downscale_threshold = 4
        
        # Create and start the load balancer
        self.balancer = self.create_balancer_container()
        self.balancer_ip = self.balancer.inspect()['NetworkSettings']['Networks']['podman']['IPAddress']
        
        # Check existing containers and update accordingly
        self.update_active_containers()
        self.container_count = len(self.active_backends)
        if self.container_count < 1:
            self.create_backend_container()
        
        # Update config to make sure it is correct
        self.update_active_containers()
        self.update_balancer_config()
    
    # Prunes images + stops and prunes containers
    def clean(self, images=True, containers=True):
        if images:
            try:
                self.client.images.prune()
            except:
                print("Pruning images failed")
        
        if containers:
            try:
                for c in self.client.containers.list():
                    c.stop()
                self.client.containers.prune()
            except:
                print("Stopping and pruning containers failed")
    
    # Recreates images
    def update_images(self):
        subprocess.call(['sh', './create_balancer_image.sh'])
        subprocess.call(['sh', './create_backend_image.sh'])
    
    # Creates backend (webapp) container
    def create_backend_container(self):
        try:
            image = self.client.images.get('backend-image')
        except:
            subprocess.call(['sh', './create_backend_image.sh'])
        print('Scale up')
        command = 'podman run --rm -d -v /srv/objects:/objects backend-image'
        p = Popen(command, shell=True)
        self.container_count += 1
    
    # Removes backend container
    def remove_backend_container(self):
        if self.container_count > 1:
            for container in self.active_backends[1:]:
                if container[0] not in self.remove_queue:
                    print('Scale down')
                    command = 'podman rm -f {}'.format(container[0])
                    p = Popen(command, shell=True)
                    self.remove_queue[container[0]] = p
                    break
    
    # Polls if queued remove container processes are done
    def poll_removes(self):
        for key in list(self.remove_queue.keys()):
            if self.remove_queue[key].poll() is not None:
                self.container_count -= 1
                del self.remove_queue[key]
    
    # Creates load balancer container; should be only one
    def create_balancer_container(self):
        exists = False
        for c in self.client.containers.list():
            c.image.tags[0] == 'localhost/balancer-image:latest'
            container = c
            exists = True
            print("Using existing balancer")
            break;
        
        if not exists:
            try:
                image = self.client.images.get('balancer-image')
            except:
                subprocess.call(['sh', './create_balancer_image.sh'])
                image = self.client.images.get('balancer-image')
            container = self.client.containers.create(image)
            container.start()
        return container
    
    def update_active_containers(self):
        self.active_backends = [
            (c.name,
             c.inspect()['NetworkSettings']['Networks']['podman']['IPAddress'], 
             5000)
             for c in self.client.containers.list()
             if c.image.tags[0] != 'localhost/balancer-image:latest'
        ]
    
    # Updates HAProxy
    def update_balancer_config(self):
        config = ""
        with open('haproxy.cfg', 'r') as f:
            for line in f.readlines():
                config += line
                if line == 'backend app\n':
                    break
        
        config += '    balance' + 8*' ' + 'roundrobin\n'
        for c in self.active_backends:
            config +=  '    server ' + str(c[0]) + ' ' + str(c[1]) + ':' + str(c[2]) + ' check\n'

        with open('haproxy.cfg', 'w') as f:
            f.write(config)
        
        # Send config to balancer and soft-reset HAProxy process
        command = ['podman', 'cp', 'haproxy.cfg', '{}:/root/haproxy.cfg'.format(self.balancer.name)]
        subprocess.call(command)
        pid = subprocess.check_output('podman exec {} cat /var/run/haproxy.pid'.format(self.balancer.name), shell=True, encoding='utf-8').strip(' \n\t')
        command = 'podman exec {} haproxy -f root/haproxy.cfg -p /var/run/haproxy.pid -sf {}'.format(self.balancer.name, pid)
        subprocess.run(command, shell=True)
    
    # Starts the scaling controller
    def start(self):
        print('Load balancer IP:', self.balancer.name, self.balancer.inspect()['NetworkSettings']['Networks']['podman']['IPAddress'])
        old_active_backends = self.active_backends.copy()
        
        rps_buffer = deque(maxlen=10)
        while (True):
            for _ in range(5):
                df = pd.read_csv('http://{}:9999/stats;csv'.format(self.balancer_ip))
                backend_rps = df.iloc[-1]['rate']
                rps_buffer.append(backend_rps)
                time.sleep(0.1)
            
            self.poll_removes()
            backends = len(self.active_backends) 
            mean_rpc = np.average(rps_buffer)/backends if backends else 0
            print('Mean_rps: {}, c: {}, a: {}'.format(mean_rpc, self.container_count, backends))
            
            # Scaling
            if mean_rpc > self.upscale_threshold:
                self.create_backend_container()  # Scale up
            elif mean_rpc < self.downscale_threshold:
                self.remove_backend_container()  # Scale down
            
            # Check if config needs to be updated
            self.update_active_containers()
            if old_active_backends != self.active_backends:
                self.update_balancer_config()
                old_active_backends = self.active_backends.copy()


def main():
    print("Setting up system")
    controller = Controller()
    print("Starting scaling controller")
    controller.start()
    

if __name__ == '__main__':
    main()
