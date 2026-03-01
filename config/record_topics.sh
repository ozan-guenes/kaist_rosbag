rosbag record \
/tf \
/tf_static \
/clock \
/diagnostics \
/rosout \
/navsat/fix \
/mavros/state \
/mavros/extended_state \
/mavros/statustext/recv \
/mavros/imu/data_raw \
/mavros/imu/data \
/mavros/local_position/pose \
/mavros/local_position/odom \
/mavros/local_position/velocity_local \
/mavros/setpoint_velocity/cmd_vel \
/mavros/vision_pose/pose \
/mavros/odometry/out \
/uav/camera/color/camera_info \
/uav/camera/color/image_raw/compressed \
/t265/camera/odom/sample \
/t265/vio_watchdog/state \
/t265/vio_watchdog/healthy \
/endo_cam/camera_info \
/endo_cam/image_raw/compressed \
/tag_detections \
/tag_detections_image/compressed \
/docking/command \
/docking/dock_estimate \
/docking/dock_measurement/front \
/docking/gates \
/docking/lock_command \
/docking/state \
/docking/target_pose \
/docking/uav_path \
/odometry/filtered \
-o ${MISSION_NAME}

# /docking/uav_path \ ----
# /docking/path_marker \
# /docking/state_marker \
# /docking/target_arrow \
# /docking/target_cube \
# /uav/arrow_marker \
# /uav/mesh_marker \

# /uav/camera/depth/camera_info \
# /uav/camera/depth/image_raw \