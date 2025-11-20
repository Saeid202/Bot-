# HOW TO RUN DOCKER (WIP)

1. BUILD
    - docker build -f docker/api_stub/Dockerfile -t api_stub:latest .

2. RUN (map port 3000)
    - docker run --rm -p 3000:3000 --name api_stub api_stub:latest (currently not working)