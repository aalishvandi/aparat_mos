
# Mos Estimation

This project use itu-p1203-master library for estimate mos of aparat videos in december of 2023.

## Create docker image
Run below command in project directory
```
docker build -t mos_estimate .
```

## Run docker image
After create docker image you can run docker image by below command
```
docker run mos_estimate
```

## Specify apart_urls file
This project use a file as input that contains aparat urls in each line.
when you run an image and a container started, you can copy your file to its container and start container for estimate mos of videos.
```
docker cp aparat_urls_file.txt container_id:/usr/src/app/
```

Then start container stopped
```
docker start container_id
```
after program ended, output results will save in output.csv file in directory. you can see results by copy the output file to your local by below command
```
docker cp container_id:/usr/src/app/output.csv /path/on/local/system
```

