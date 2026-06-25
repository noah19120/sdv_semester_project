## Step 1 setup the env and the Databroker

```bash
conda activate kuksa-carsim
```

Start Kuksa Databroker : 

```bash
docker run -it --rm --name kuksa-val-databroker -p 55555:55555 ghcr.io/eclipse/kuksa.val/databroker:latest
```

## Step 2 Setup the dockers

### ROS2 Bridge + Driversim
```bash
cd ~/Desktop/sdv_project/kuksa-carsim/driversim
docker build --no-cache -t my-ros2-driversim .
```

### Carsim
```bash
cd ~/Desktop/sdv_project/kuksa-carsim/carsim
docker build --no-cache -t leda-carsim -f Dockerfile .
```
## Step 3 : Run the processes

### Run the DriverSim + Bridge
```bash
docker run -it --rm --net=host my-ros2-driversim
```

### Run Carsim
```bash
docker run -it --rm --net=host leda-carsim
```

## Step4 :Run the CLI and subscribe to the APIs

### Kuksa CLI : 
```bash
docker run -it --rm --net=host ghcr.io/eclipse-kuksa/kuksa-databroker-cli:main --server 127.0.0.1:55555
```
### Subscriptions : 
#### Steering wheel angle : stream
```bash
subscribe Vehicle.Chassis.SteeringWheel.Angle
```
### Stearing wheel angle : single moment
```bash
get Vehicle.Chassis.SteeringWheel.Angle
```

#### Pedal position : stream
```bash
subscribe Vehicle.Chassis.Accelerator.PedalPosition
```
### Pedal position : single moment
```bash
get Vehicle.Chassis.Accelerator.PedalPosition
```
#### Speed : stream
```bash
subscribe Vehicle.Speed
```
### Pedal position : single moment
```bash
get Vehicle.Speed
```

### TO discover all the APIs : 
```bash
metadata Vehicle.*
```


### ROS Topics : 

check the id of driversim
```bash
docker ps
```
open a consol in the docker : 
```bash
docker exec -it 33ae6fbb8c7f bash
```

run ROS2 setup script : 
```bash
source /opt/ros/humble/setup.bash
```

list the topics : 
```bash
ros2 topic list
```

echo the output of the choosen one
```bash
ros2 topic echo /vehicle/...
```