#!/bin/bash

for file in media/js/*.coffee
do 
   echo "Compiling ${file}"
   cat ${file} | coffee -cbs | yuicompressor --type js > ${file/.coffee/.js}
done
