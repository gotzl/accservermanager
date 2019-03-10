Small web project to manage Assetto Corsa Competizione servers, build on Django.
Allows to manage multiple configs and multiple server instances. Works in Linux and in Windows, dunno about OSX.


## Quick start
```bash
git clone https://github.com/gotzl/accservermanager.git
cd accservermanager/
# Configure the things in accservermanager/local_settings.py, ie the path to your ACC server files
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
``` 

Now you should be able to access the service at localhost:8000.
After login, you can add more users with djangos admin pages (...:8000/admin).

Currently, the web-app consists of two sub-apps
* cfgs: Basically creates an autogenerated view from ACCs event.json, navigating through the object. Allows to create and edit multiple configurations, they are stored in the folder 'local_settings.CONFIGS'.
* instances: Start a new ACC server instance or stop/delete running instances. Each instance uses a copy of the ACC 'server' directory, which is placed in the folder 'local_settings.INSTANCES'.



## Dependencies
```bash
pip3 install -r requirements.txt # --user
```
Windows users might want to follow the official Django install instructions.


## Deployment
Follow the quick start instructions to deploy the app, should be good enough for our purposes...

Alternatively, I've created a Dockerfile which uses wine to run the ACC server. No modifications to the local_settings.py are necessary in this case.

```bash
# Create the image
docker build -t accservermanager .
# Create a volume (if you didn't already create one)
docker volume create accservermanager-data
# fire up a container
docker run -d --name accservermanager \
            -e SECRET_KEY=RANDOM_SEQUENCE \
            -v accservermanager-data:/data 
            -v PATH_TO_ACC/server:/server 
            -p 8000:8000 -p 9231:9231/udp -p 9232:9232/tcp 
            accservermanager
# initiate the app and create a manager user (only neccessary at the very first start)
docker exec -i -t accservermanager python3 manage.py migrate
docker exec -i -t accservermanager python3 manage.py createsuperuser
```

If you want to allow connections to the server from anywhere, use `-e ALLOWED_HOSTS='["*"]'`. This should only be used behind a proxy!


## Persistence
All relevant data will be placed insided the 'local_settings.DATA_DIR' folder. In case of docker the folder is persisted outside of the container using a docker volume.
This means you can delete and rebuild your container without needing to restore your settings manually.


## Compose example
```bash
version: '2'

services:
 acc:
  image: gotzl/accservermanager
  volumes:
   - /acc/server:/server
   - accservermanager-data:/data
  environment:
#   - ALLOWED_HOSTS=["*"]
   - SECRET_KEY=
  ports:
   - 9232:9232/tcp
   - 9231:9231/udp
   - 8000:8000

volumes:
  accservermanager-data:
```