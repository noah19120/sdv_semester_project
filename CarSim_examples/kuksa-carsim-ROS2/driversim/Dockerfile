# /********************************************************************************
# * Copyright (c) 2023 Contributors to the Eclipse Foundation
# *
# * See the NOTICE file(s) distributed with this work for additional
# * information regarding copyright ownership.
# *
# * This program and the accompanying materials are made available under the
# * terms of the Apache License 2.0 which is available at
# * http://www.apache.org/licenses/LICENSE-2.0
# *
# * SPDX-License-Identifier: Apache-2.0
# ********************************************************************************/

# Changed base image from python:3.9-slim to ROS2 Humble Base
FROM --platform=$TARGETPLATFORM ros:humble-ros-base

ARG TARGETPLATFORM
ARG BUILDPLATFORM

RUN echo "-- Running on $BUILDPLATFORM, building for $TARGETPLATFORM"

# Added python3-pip to system requirements
RUN apt-get update -qqy && apt-get upgrade -qqy && apt-get install -qqy binutils g++ python3-pip

COPY . /

# Install requirements + kuksa-client for your bridge
RUN pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir kuksa-client

# Install sdv package in edit mode
RUN pip3 install --no-cache-dir -e .

# Removed PyInstaller and Staticx compression layers to preserve ROS2 bindings.
# Replaced FROM scratch with a simple working directory startup execution.
WORKDIR /app
COPY . /app

# Create a clean startup script to source ROS2 and run both components
RUN echo '#!/bin/bash\n\
source /opt/ros/humble/setup.bash\n\
python3 driver.py &\n\
python3 ros2_vss_bridge.py\n\
' > /app/run_all.sh && chmod +x /app/run_all.sh

ENTRYPOINT ["/app/run_all.sh"]