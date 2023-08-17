#!/bin/bash

echo "Building load balancer container image"
container=$(buildah from alpine)
buildah run $container -- apk update
buildah run $container -- apk add haproxy
buildah copy $container haproxy.cfg /root
buildah config --cmd "" $container
buildah config --entrypoint "haproxy -f /root/haproxy.cfg -n 128; sleep infinity" $container
buildah commit $container balancer-image
echo "Commited container to image 'balancer-image'"
buildah rm $container
exit
