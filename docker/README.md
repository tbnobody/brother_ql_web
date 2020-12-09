## Running via docker

First build the docker image and name it `brother_ql_web`, which only needs doing once.

1. `cd docker`
1. `docker build -t brother_ql_web .`
    
    > _don't miss the dot at the end!_

To run the image:

1. `docker run -it --rm -p 127.0.0.1:8013:8013 brother_ql_web ./run.py --model <MODEL> <FILE>`
    
    > replacing <MODEL> with your printers model, and <FILE> with your printers connection  file/network e.g. `tcp://192.168.5.169` or `file:///dev/usb/lp0`
1. Open http://localhost:8013/ in your web browser