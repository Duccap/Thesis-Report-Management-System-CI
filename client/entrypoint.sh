#!/bin/sh

STATIC_DIR=/usr/share/nginx/html

for file in $STATIC_DIR/static/js/*.js
do
    echo "Processing $file ..."

    sed -i "s|__REACT_APP_SERVICE_LIST__|${REACT_APP_SERVICE_LIST}|g" $file
    sed -i "s|__REACT_APP_BACKEND_HOST__|${REACT_APP_BACKEND_HOST}|g" $file
done

nginx -g 'daemon off;'