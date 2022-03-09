FROM jlesage/firefox:v1.18.0

# replace novnc files to hide navbar
COPY ./node_container_files/bootstrap.custom.css /opt/novnc/css/bootstrap.custom.css
COPY ./node_container_files/index.vnc /opt/novnc/index.vnc

# make firefox run in kiosk mode with specified url
COPY ./node_container_files/startapp.sh /startapp.sh