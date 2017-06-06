Image Compare Demo App
===================


How to build and run
-------------

1. Get latest version of docker and docker-compose (https://docs.docker.com/compose/install/)
2. Have Python3 installed.  Should be accessible with the shell command python3
3. Either ensure port 8000 is open or change the port number to whatever is best for you by modifying the following line in docker-compose.yml:
`command: python3 manage.py runserver 0.0.0.0:8000`
4.  In a terminal:
`cd image_compare`
`docker-compose up`
5. Navigate to http://your-server:8000/
6. Any problems/concerns please create an issue on the project page (https://github.com/dchrostowski/image_compare/issues) or email dan@danchrostowski.com
