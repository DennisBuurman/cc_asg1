#!/bin/python3
from locust import HttpUser, task, between
import random

'''
Request examples:
    GET: 
        requests.get("<IP>:<port>/")
        requests.get("<IP>:<port>/objs/<obj_id>")
        requests.get("<IP>:<port>/objs/<obj_id>/checksum")
    
    PUT:
        requests.put("<IP>:<port>/objs/<obj_id>", data={"content": <string: content>})
    
    DELETE:
        requests.delete("<IP>:<port>/")
        requests.delete("<IP>:<port>/objs/<obj_id>")
'''

class Test(HttpUser):
    wait_time = between(0.1, 1.9)

    @task(5)
    def put_random(self):
        #self.client.get("10.88.0.36:5000")
        obj_id = str(int(random.uniform(0,1)*100))
        self.client.put("/objs/{}".format(obj_id), data={"content": "mega fahgot"})
    
    @task(2)
    def get_all(self):
        self.client.get("/")
    
    @task(0)
    def get_random(self):
        obj_id = str(int(random.uniform(0,1)*100))
        self.client.get("/objs/{}".format(obj_id))
    
    @task(0)
    def delete_random(self):
        obj_id = str(int(random.uniform(0,1)*100))
        self.client.delete("/objs/{}".format(obj_id))
    
    @task(0)
    def delete_all(self):
        self.client.delete("/")
