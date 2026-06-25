from driver_base import DriverBase
import math
import random

import rclpy
from rclpy.node import Node
from std_msgs.msg import UInt8, Int16


class Driver(DriverBase):
    def __init__(self, simulation_speed=2.0):  # time scale of sim in seconds
        super().__init__(simulation_speed)
        self._simulation_time = 0
        self._good_driving_cycles = 0
        self._good_driving_time = 75 * self.simulation_speed  # seconds

        self._bad_driving_cycles = 0
        self._bad_driving_time = 75 * self.simulation_speed  # seconds

        self._is_good = True

        self._brake = 0
        self._accelerator = 0
        self._steer_angle = 0

    def recalculate_time(self):
        t = (
            self._simulation_time
            - self._good_driving_cycles * self._good_driving_time
            - self._bad_driving_cycles * self._bad_driving_time
        )  # proof needed!

        return t

    def calculate_good_driver(self):
        """
        Accelerate with a gaussian, peaking at max_accel_t and
        decelerate with a gaussian, peaking at max_decel_t (rescaled to sim
        speed)
        for 0 < t <  turn_time turn slowly between 0 and 20 degrees
        for turn_time < t < 4*turn_time turn back between 20 and 0 degrees
        """

        # rescale gaussians based on simulation speed
        sigma_acc = 20 * self.simulation_speed
        sigma_decel = 20 * self.simulation_speed
        max_accel_t = 30 * self.simulation_speed
        max_decel_t = 80 * self.simulation_speed
        turn_time = 50 * self.simulation_speed
        turn_angle_max = 20
        angle_step = 0.5

        t = self.recalculate_time()

        if t > self._good_driving_time:
            self._is_good = False
            self._good_driving_cycles += 1
            return

        control = math.exp(-(((t - max_accel_t) / sigma_acc) ** 2)) - math.exp(
            -(((t - max_decel_t) / sigma_decel) ** 2)
        )

        if control > 0:
            self._accelerator = control
            self._brake = 0
        else:
            self._accelerator = 0
            self._brake = -control

        if 0 < t < 2 * turn_time:
            new_angle = self._steer_angle + angle_step
            self._steer_angle = min(new_angle, turn_angle_max)
        elif turn_time < t < 4 * turn_time:
            new_angle = self._steer_angle - angle_step
            self._steer_angle = max(new_angle, 0)
        else:
            self._steer_angle = 0

    def calculate_bad_driver(self):
        """
        Presses the accelerator to the max for 1/4 of the bad driving time
        brake for 1/4 to 2/4, accelerator from 2/4 to 3/4, and brake again
        from 3/4 to 4/4
        Randomly steer between -5 and 5 degrees
        """
        t = self.recalculate_time()

        if t > self._bad_driving_time:
            self._is_good = True
            self._bad_driving_cycles += 1
            return

        if 0 <= t < 0.25 * self._bad_driving_time:
            self._accelerator = 1
            self._brake = 0
            self._steer_angle = random.randint(-5, 5)

        elif 0.25 * self._bad_driving_time <= t < 0.5 * self._bad_driving_time:
            self._accelerator = 0
            self._brake = 1
            self._steer_angle = random.randint(-5, 5)

        elif 0.50 * self._bad_driving_time <= t < 0.75 * self._bad_driving_time:
            self._accelerator = 1
            self._brake = 0
            self._steer_angle = random.randint(-5, 5)

        elif 0.50 * self._bad_driving_time <= t < self._bad_driving_time:
            self._accelerator = 0
            self._brake = 1
            self._steer_angle = random.randint(-5, 5)

    @property
    def accelerator_pos(self) -> int:
        return int(self._accelerator * 100)

    @property
    def brake_pos(self) -> int:
        return int(self._brake * 100)

    @property
    def steering_angle(self) -> int:
        return int(self._steer_angle)

    @property
    def simulation_time(self) -> float:
        return self._simulation_time

    def _update_driver_state(self):
        self._simulation_time += self.simulation_speed

        if self._is_good:
            self.calculate_good_driver()
        else:
            self.calculate_bad_driver()


class DriverSimNode(Node):
    def __init__(self):
        super().__init__('ros2_driversim')
        
        # Instantiate your exact Driver class
        self.driver = Driver(simulation_speed=2.0)
        
        # ROS2 Publishers matching the VSS bridge expectations
        self.pub_accel = self.create_publisher(UInt8, '/vehicle/chassis/accelerator', 10)
        self.pub_brake = self.create_publisher(UInt8, '/vehicle/chassis/brake', 10)
        self.pub_steer = self.create_publisher(Int16, '/vehicle/chassis/steering', 10)
        
        # Replace the while loop with a ROS2 timer (e.g., 0.1s interval = 10Hz)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info("ROS2 DriverSim Node has been started.")

    def timer_callback(self):
        # Fetch the calculated states using the base class method
        a, b, s = self.driver.get_controls()
        
        accel_msg = UInt8()
        accel_msg.data = a
        
        brake_msg = UInt8()
        brake_msg.data = b
        
        steer_msg = Int16()
        steer_msg.data = s
        
        # Publish to ROS2 topics
        self.pub_accel.publish(accel_msg)
        self.pub_brake.publish(brake_msg)
        self.pub_steer.publish(steer_msg)
        
        # Replicate the original print statement as a ROS2 log
        self.get_logger().debug(f"Time: {self.driver.simulation_time:.1f} | Accel: {a} | Brake: {b} | Steer: {s}")


def main(args=None):
    rclpy.init(args=args)
    node = DriverSimNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
