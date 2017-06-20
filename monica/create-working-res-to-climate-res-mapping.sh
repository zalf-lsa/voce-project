#!/bin/bash

#for row in {1..5001..25}
for row in {1..1000..5}
do
	#((row2=row+25))
	((row2=row+4))
	#echo "$row - $row2"
	python create-working-res-to-climate-res-mapping-json.py user=cluster2 start-row=$row end-row=$row2 & 
done