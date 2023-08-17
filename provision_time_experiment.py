#!/bin/python3
from start_service import Controller
import time
import subprocess
import numpy as np

#system = Controller()

'''
***********************************
Single container provision time over 50 run(s): 0.965050745010376
***********************************

***********************************
Single container provision time over 10 run(s): 0.7193159580230712
***********************************

***********************************
Single container provision time over 1 run(s): 0.4904205799102783
***********************************
'''


def single_provisioning_time(runs=1):
    print("***********************************")
    command = 'podman run --rm -d -v /srv/objects:/objects backend-image'
    times = []
    for _ in range(runs):
        start = time.time()
        
        # Provision a container
        subprocess.call(command, shell=True)
        
        end = time.time()
        times.append(end - start)
    print("Single container provision time over {} run(s): {}".format(runs, np.average(times)))
    print("***********************************")

if __name__ == "__main__":
    single_provisioning_time()
    
    # Clean up container instances
    # TODO
