# Remote Access Comparison: HTTP API Bridge vs Direct ROS2 Subscription

AI assistance note: the raw commands, screenshots, and observations were written by Wenbo Yan in `compare_raw_test_notes.md`. This report is a cleaned-up English version based on those raw notes, with wording and structure polished with help from OpenAI Codex.

Date: 2026-06-03  
Raw notes: `compare_raw_test_notes.md`  
Truck API address used in the test: `http://100.102.142.126:8000`  
ROS2 client image: `ros:humble-ros-base-jammy`

## 1. Purpose

The purpose of this test was to compare two possible ways to access the SAVD truck services from outside the truck:

1. **HTTP API bridge**

   ```text
   remote client
     -> HTTP request
     -> savd_api on the truck
     -> ROS2 topics, services, and actions inside the truck
   ```

2. **Direct ROS2 subscription**

   ```text
   remote ROS2 client
     -> ROS2/DDS discovery
     -> direct subscription to truck ROS2 topics
   ```

This comparison is useful for deciding whether future SDV services should access the truck through the existing on-board API bridge, or whether they should subscribe directly to ROS2 topics.

Only read-only tests were used. No vehicle control command was sent.

## 2. HTTP API Bridge Test From Laptop

The first test was done from the laptop using the truck Tailscale address:

```text
http://100.102.142.126:8000
```

The tested API endpoints were:

```text
GET /modes/get_current_mode
GET /vehicle/parameters
GET /diagnostics
```

The API returned the current mode, vehicle parameters, and diagnostics. This means that the HTTP bridge can be used remotely to access selected truck information.

Screenshots from the raw test:

![HTTP bridge test 1](image.png)

![HTTP bridge test 2](image-1.png)

Observed result:

```text
HTTP access worked from the laptop through Tailscale.
The laptop did not need ROS2 installed.
The client only needed the truck IP address and API port.
```

## 3. ROS2 Environment Check

Before testing direct ROS2 access, the running truck containers were checked for ROS-related environment variables:

```bash
for c in $(docker ps --format '{{.Names}}' | grep '^savd_docker'); do
  echo "===== $c ====="
  docker exec "$c" sh -lc 'printenv | grep -E "ROS_DOMAIN_ID|ROS_LOCALHOST_ONLY|RMW_IMPLEMENTATION|CYCLONEDDS|FASTRTPS" || true'
done
```

The important observation was:

```text
Most ROS2 containers set ROS_LOCALHOST_ONLY=0.
No ROS_DOMAIN_ID was explicitly found in the inspected container environments.
```

Because no explicit domain ID was found, the client tests used the ROS2 default:

```text
ROS_DOMAIN_ID=0
```

This is an important detail because ROS2 discovery is not global. A ROS2 client does not connect to a fixed server like HTTP. It discovers nodes through DDS, and discovery depends on domain ID, network reachability, Docker networking, VPN behavior, and DDS configuration.

## 4. Direct ROS2 Test From Mac Docker

A ROS2 Humble client container was started on the Mac laptop:

```bash
docker run --rm -it \
  -e ROS_DOMAIN_ID=0 \
  -e ROS_LOCALHOST_ONLY=0 \
  ros:humble-ros-base-jammy bash
```

Inside the container:

```bash
source /opt/ros/humble/setup.bash
ros2 daemon stop
ros2 topic list -t --no-daemon
```

The result only showed the local ROS2 topics:

```text
/parameter_events [rcl_interfaces/msg/ParameterEvent]
/rosout [rcl_interfaces/msg/Log]
```

Screenshot:

![Mac Docker ROS2 test](image-4.png)

Interpretation:

```text
The Mac Docker ROS2 client did not discover the truck ROS2 graph.
This does not mean ROS2 is broken.
It means this Docker/Tailscale/macOS network setup was not suitable for direct ROS2/DDS discovery in this test.
```

This is different from HTTP. HTTP only needs normal IP connectivity to the API server. Direct ROS2 discovery needs a compatible DDS network environment.

## 5. HTTP Test From Inside The Same ROS2 Container

To check whether the ROS2 container had basic network access to the truck, HTTP was tested from inside the same Mac ROS2 container:

```bash
python3 - <<'PY'
import urllib.request
print(
    urllib.request.urlopen(
        "http://100.102.142.126:8000/modes/get_current_mode",
        timeout=5,
    ).read().decode()
)
PY
```

Observed output:

```json
{"data":{"data":"IDLE"},"success":{"data":true,"message":""}}
```

Screenshot:

![HTTP from ROS2 container](image-3.png)

Interpretation:

```text
The container could reach the truck over normal IP/HTTP.
Therefore, the direct ROS2 failure was not caused by complete network disconnection.
The more likely issue was ROS2/DDS discovery in the Mac Docker and Tailscale environment.
```

This is one of the main differences between the two approaches. HTTP worked in an environment where direct ROS2 discovery did not.

## 6. Truck-Local ROS2 Baseline

The next test was done directly on the truck over SSH. A ROS2 client container was started on the truck, and the topic list was checked.

The raw notes record the ROS2 client container command and the ROS2 commands used inside it:

```bash
source /opt/ros/humble/setup.bash
ros2 daemon stop
ros2 topic list -t --no-daemon
```

The truck-local test discovered real SAVD ROS2 topics, for example:

```text
/commands/motor/brake [std_msgs/msg/Float64]
/commands/motor/current [std_msgs/msg/Float64]
/commands/motor/duty_cycle [std_msgs/msg/Float64]
/commands/motor/position [std_msgs/msg/Float64]
/commands/motor/speed [std_msgs/msg/Float64]
/commands/servo/position [std_msgs/msg/Float64]
/savd_sysmode/mode [std_msgs/msg/String]
/savd_wpo/current_pose [geometry_msgs/msg/PoseStamped]
/savd_wpo/curvature [std_msgs/msg/Float32]
/savd_wpo/drive_cmds [geometry_msgs/msg/TwistStamped]
/savd_wpo/path [nav_msgs/msg/Path]
/sensors/core [vesc_msgs/msg/VescStateStamped]
/sensors/imu [vesc_msgs/msg/VescImuStamped]
/sensors/imu/raw [sensor_msgs/msg/Imu]
```

Screenshot:

![Truck-local ROS2 test](image-6.png)

Interpretation:

```text
The ROS2 client image and ROS2 commands were valid.
When the client ran in a truck-local network environment, it could discover real truck ROS2 topics.
This is a useful baseline, but it is not a true remote test because the client was running on the truck itself.
```

This result shows that the failure from the Mac laptop was not caused by a wrong ROS2 command or a completely invalid client image. The difference is the network environment.

## 7. Same-LAN Linux ROS2 Test

A further test was done on a separate Linux machine connected to the same local network as the truck.

The ROS2 client was started with:

```bash
docker run --rm -it \
  -e ROS_DOMAIN_ID=0 \
  -e ROS_LOCALHOST_ONLY=0 \
  ros:humble-ros-base-jammy bash
```

Inside the container:

```bash
source /opt/ros/humble/setup.bash
ros2 daemon stop
ros2 topic list -t --no-daemon
```

This test discovered many truck ROS2 topics, including:

```text
/ackermann_cmd [ackermann_msgs/msg/AckermannDriveStamped]
/diagnostics [diagnostic_msgs/msg/DiagnosticArray]
/diagnostics_agg [diagnostic_msgs/msg/DiagnosticArray]
/gpsfix [gps_msgs/msg/GPSFix]
/odom [nav_msgs/msg/Odometry]
/savd_manop/drive_cmds [geometry_msgs/msg/TwistStamped]
/savd_manop/joy_cmds [sensor_msgs/msg/Joy]
/savd_micro_ros/cmd [savd_interfaces/msg/SAVDCommand]
/savd_micro_ros/state [savd_interfaces/msg/SAVDState]
/savd_syscontrol/drive_cmds [geometry_msgs/msg/TwistStamped]
/savd_sysmode/mode [std_msgs/msg/String]
/savd_vehicle/battery_state [sensor_msgs/msg/BatteryState]
/savd_vehicle/odom [nav_msgs/msg/Odometry]
/savd_vehicle/parameters [savd_interfaces/msg/Parameters]
/savd_wpo/current_pose [geometry_msgs/msg/PoseStamped]
/savd_wpo/curvature [std_msgs/msg/Float32]
/savd_wpo/drive_cmds [geometry_msgs/msg/TwistStamped]
```

Screenshot:

![Same-LAN Linux ROS2 test](ded9f5642a66cdcc764f74ca31344609.jpg)

Interpretation:

```text
Direct ROS2 discovery worked much better from a Linux machine on the same LAN than from Mac Docker over Tailscale.
This suggests that direct ROS2 access is possible in a suitable local network environment.
However, it is more sensitive to network and Docker setup than the HTTP API bridge.
```

For future reproduction, the exact Docker network mode used on the LAN Linux machine should also be recorded, because ROS2/DDS discovery can behave differently with Docker bridge networking and host networking.

## 8. Comparison

| Topic | HTTP API bridge | Direct ROS2 subscription |
| --- | --- | --- |
| Client requirement | Any HTTP client can be used. | Client needs ROS2 installed or a ROS2 container. |
| Addressing model | Client calls a known IP and port. | Client depends on DDS discovery. |
| Network behavior | Worked over Tailscale in this test. | Failed from Mac Docker/Tailscale, but worked in truck-local and same-LAN Linux tests. |
| Message definitions | Client receives JSON from the API. | Client may need ROS2 message packages, especially for custom messages such as `savd_interfaces`. |
| Scope | Only exposes endpoints implemented by `savd_api`. | Can potentially access many ROS2 topics directly if discovery and message types work. |
| Control and safety | Easier to filter and expose only selected services. | More direct access to the ROS2 graph, so it needs careful network and access control. |
| Best use | Remote access, SDV wrapper, simple client integration. | Local ROS2 development, debugging, or controlled lab networks. |

## 9. SDV Wrapper and Common API Idea

My current understanding is that the HTTP bridge can be used as a wrapper layer for the SDV side. This does not replace ROS2. ROS2 can still run inside the truck and use its own discovery mechanism between ROS2 nodes.

The wrapper layer would hide some ROS2 details from remote clients:

```text
ROS2 topics, services, and actions inside the truck
  -> wrapper layer / HTTP API / SDV service layer
  -> common API for remote clients
```

With this wrapper layer, different ROS2 modules could be exposed in a similar way. For example, instead of asking the remote client to know every ROS2 topic name, message type, QoS setting, or DDS network detail, the SDV layer could provide common operations such as:

```text
GET /services
GET /services/{id}/info
POST /services/{id}/subscribe
PATCH /subscriptions/{id}
DELETE /subscriptions/{id}
GET /subscriptions/{id}/latest
```

In this model, ROS2 discovery and SDV discovery are not exactly the same thing:

- ROS2 discovery is internal to the truck ROS2 graph. It discovers ROS2 nodes, topics, services, and actions.
- SDV discovery would be an external service catalog. It would tell a remote client which selected vehicle services are available and how to access them through a common API.

For example, if a new ROS2 module is added to the truck, the wrapper could discover it or be configured to expose it. Then the SDV side could update its service list through a `get_info` or `GET /services` endpoint. Remote clients would then subscribe, update, unsubscribe, or read the latest value through the common API instead of directly handling ROS2 details.

This could make remote access easier and more stable, especially outside a simple local network. It would also allow only selected safe services to be exposed, instead of exposing the whole ROS2 graph directly.

## 10. Conclusion

The tests show that the HTTP API bridge is currently the easier and more robust method for remote access. It worked from the laptop over Tailscale and even worked from inside the ROS2 client container on the laptop.

Direct ROS2 subscription is more native and exposes more of the vehicle ROS2 graph, but it depends strongly on the network environment. In this test, direct ROS2 discovery did not work from Mac Docker over Tailscale, but it did work in a truck-local environment and on a Linux machine in the same LAN.

For the next SDV step, a practical approach would be:

```text
Use the HTTP API bridge first to wrap a small number of selected vehicle services.
Keep direct ROS2 subscription as a second experiment for controlled local-network or lab-network scenarios.
```

This matches the project goal of advertising or wrapping selected SAVD services without replacing the existing truck software.

The main limitation of this test is that it only compares basic reachability and ROS2 topic discovery. A next step would be to select one or two safe read-only ROS2 services or topics and test how an SDV wrapper could advertise them through HTTP or another service layer.
