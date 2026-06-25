# SAVD Vehicle Container Documentation

AI assistance note: the investigation, command outputs, and technical observations were produced from the vehicle inspection work. The documentation wording and structure were organized and polished with help from OpenAI Codex.

This repository documents the Docker/ROS2 container composition of the SAVD small vehicle test platform.

The documentation is based on a read-only live inspection of the vehicle at `172.21.16.162` on 2026-06-02. No remote files were modified, no containers were restarted, and no recovery scripts were executed during the inspection.

## Documents

- [Default English onboarding guide: SAVD Vehicle Container, Source, and Development Guide](SAVD_onboarding_and_test_guide.md)
- [English container reference snapshot](docs/SAVD_container_composition_en.md)
- [Remote access comparison: HTTP API bridge vs direct ROS2 subscription](docs/tests/compare.md)
- [Raw test notes for the remote access comparison](docs/tests/compare_raw_test_notes.md)

Chinese supporting documents are kept separately under `docs/zh/`:

- [中文辅助版：SAVD 小车容器、源码与开发指南](docs/zh/SAVD_onboarding_and_test_guide_zh.md)
- [中文容器组成参考快照](docs/zh/SAVD_container_composition_zh.md)
- [Original Chinese analysis baseline](docs/zh/SAVD_container_analysis.md)

## Scope

The default onboarding guide is organized by runtime flow first, then by container source reference. It is meant to let a new developer understand how GUI requests, ROS2 modes, command arbitration, vehicle abstraction, VESC, ESP32, cameras, GPS, diagnostics, and Foxglove fit together before reading individual container code.

The main documents explain:

- Current Docker Compose stack and container inventory.
- Runtime relationships between containers.
- Runtime image, command, mount, and status of each main service.
- Source-code paths inside each container.
- ROS2 nodes, topics, services, and actions owned by each container.
- GUI-to-API-to-ROS2 control flow.
- VESC, ESP32/micro-ROS, camera, GPS, diagnostics, and Foxglove chains.
- Current live issues observed during inspection.

## Safety and Credentials

This repository must not contain SSH passwords, tokens, private keys, or other credentials.

Some API endpoints and GUI controls can command the physical vehicle. Read the warning sections in the documentation before using control APIs or running recovery scripts.

## Current Key Findings

- The active stack is `savd_docker` with 18 services defined; 17 containers are running and `savd_jetson_stats` is exited.
- Core control containers are `savd_sysmode`, `savd_syscontrol`, `savd_manop`, `savd_wpo`, and `savd_vehicle`.
- Hardware interface containers are `vesc_driver`, `vesc_ackermann`, and `savd_micro_ros_agent`.
- The current camera chain is `savd_zed_gstreamer` to `savd_mediamtx`; the dual-camera override runs both ZED streams at 15 FPS and 8 Mbps.
- The U-Blox container mounts the local SAVD launch file over `ublox_gps_node-launch.py`; in that launch file the real GPS node is commented out, so the container only publishes static TF unless the launch is changed.
- `savd_jetson_stats` exits because `/run/jtop.sock` cannot be mounted as expected.
- `savd_teleop` can report healthy while it is only waiting for the Logitech F710 joystick process; check `/dev/input/js0` or logs to confirm the joystick is actually present.
