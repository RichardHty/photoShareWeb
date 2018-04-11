# Sharing! 

###### online photo share system by Tianyou Huang and Sha Lai.

How to deploy python & flask web app on AWS EC2(terminal way):
- Set up an instance on AWS EC2
- download private key on console

- ``` chmod 600 <path to your private key> ``` 

- login in the instance with the private key
  ```
  ssh -i <path to your private key> userName@domain
  ```
  if username is unknown, type "root" as user name. Or after logged in, use "whoami" for ubuntu/linux/mac os
- download .zip file from s3, or use
  ```
  scp -i <path to your private key>  <path to file need to upload> userName@domain:<path to store>
  ```
  to upload .zip file
  
Install the apache webserver and mod_wsgi
```
$ sudo apt-get update
$ sudo apt-get install apache2
$ sudo apt-get install libapache2-mod-wsgi
```

install mysql server/flask/flask-login/flask-mysql
We'll create a directory in our home directory to work in, and link to it from the site-root defined in apache's configuration (/var/www/html by defualt, see /etc/apache2/sites-enabled/000-default.conf for the current value).
```
$ mkdir ~/flaskapp
$ sudo ln -sT ~/flaskapp /var/www/html/flaskapp
```
Create a .wsgi file to load the app.
Put the following content in a file named flaskapp.wsgi:
```
import sys
sys.path.insert(0, '/var/www/html/flaskapp')

from flaskapp import app as application
```
Enable mod_wsgi.
The apache server displays html pages by default but to serve dynamic content from a Flask app we'll have to make a few changes. In the apache configuration file located at /etc/apache2/sites-enabled/000-default.conf, add the following block just after the DocumentRoot /var/www/html line:
```
WSGIDaemonProcess flaskapp threads=5
WSGIScriptAlias / /var/www/html/flaskapp/flaskapp.wsgi

<Directory flaskapp>
    WSGIProcessGroup flaskapp
    WSGIApplicationGroup %{GLOBAL}
    Order deny,allow
    Allow from all
</Directory>
  ```
- sudo apachectl restart

- chmod 777 <absolute path to folder need to be public>
  
- cat /var/log/apache2/error.log

- export FLASK_APP=app.py
- flask run --host=0.0.0.0 --port=80



## deployed on:
http://18.218.143.71/


