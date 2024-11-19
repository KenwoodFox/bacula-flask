#!/bin/bash

mkdir -p /etc/bacula

sed -i 's/name/'"$NAME"'/g' bconsole.conf
sed -i 's/dirPort/'"$DIRPORT"'/g' bconsole.conf
sed -i 's/addRess/'"$ADDRESS"'/g' bconsole.conf
sed -i 's/password/'"$PASSWORD"'/g' bconsole.conf

cat bconsole.conf

cp bconsole.conf /etc/bacula
