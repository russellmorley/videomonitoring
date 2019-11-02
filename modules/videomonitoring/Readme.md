# Simple IoT Edge video monitoring for Raspberry PI

A simple USB video camera frame processor for video monitoring from a Raspberry PI with USB camera.
Includes:

- Runtime Docker container.
- Support for Azure IoT Edge deployment an bi-directional messaging.
- Cross compilation of Arm32v7 builds on AMD64/x86-64 processors. 

## Build
### Build for AMD64

```
docker build --rm -f "modules/videomonitoring/Dockerfile.amd64" -t videomonitoring-amd64 modules/videomonitoring
docker run --rm -it -p 8080:8080 --name videomonitoring --device=/dev/video0:/dev/video0 videomonitoring-amd64
```

### Build for ARM32v7 (raspberry pi 3B) on AMD64 processors

To build on AMD64 processor and move to Raspberry PI:

```
docker build --rm -f "modules/videomonitoring/Dockerfile.arm32v7" -t videomonitoring-arm32v7 modules/videomonitoring
docker save videomonitoring-arm32v7 | bzip2 | ssh pi@ADDRESS 'bunzip2 | docker load'
```

## Run
### Run on Raspberry PI:

```
docker run --rm -it -p 8080:8080 --name videomonitoring --device=/dev/video0:/dev/video0 videomonitoring-arm32v7
```

### To access running shell on Raspberry PI:

```
docker exec -it videomonitoring bash
```

