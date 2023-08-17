#!/bin/bash

echo "Building backend container image..."
container=$(buildah from alpine)
buildah run $container -- apk update
buildah run $container -- apk add python3
buildah run $container -- apk add py3-pip
buildah run $container -- pip install --ignore-installed packaging
buildah run $container -- pip install wheel
buildah run $container -- pip install flask_limiter
buildah run $container -- pip install flask_restful
buildah run $container -- mkdir /objects
buildah copy $container objst.py /root
buildah config --cmd "" $container
buildah config --entrypoint "python3 /root/objst.py" $container
buildah commit $container backend-image
echo "Commited container to image 'backend-image'"
buildah rm $container
exit
