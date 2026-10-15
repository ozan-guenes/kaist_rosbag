# kaist_rosbag

Records the docking experiment topics in `config/record_topics.sh`.
The existing `real_mission.yaml` command still works unchanged.

| Mode | Start | Stop |
| --- | --- | --- |
| `armed` (default) | `/mavros/state`: disarmed -> armed, or first message armed | Disarm or recorder-node shutdown |
| `manual` | `/kaist_rosbag/start` service | `/kaist_rosbag/stop` or recorder-node shutdown |

```bash
export MISSION_NAME=docking_exp
# Automatic flight recording; creates the folder if necessary.
roslaunch kaist_rosbag kaist_rosbag.launch record_folder:=/path/to/bags

# Bench checks, preflight and post-lock recording without arming.
roslaunch kaist_rosbag kaist_rosbag.launch mode:=manual record_folder:=/path/to/bags
rosservice call /kaist_rosbag/start "{}"
rosservice call /kaist_rosbag/stop "{}"
```

`MISSION_NAME` supplies the filename prefix, as before; set it before launching
(the tmux workflows already do). Rosbag adds its timestamp. Use a local disk with enough
free space; stop recording and wait for finalization before powering off.

One fixed topic list covers TF, MAVROS/RC/health/setpoints, T265/watchdog,
compressed RGB + calibration, AprilTag detections/debug image, docking
measurements/estimates/state, contact/terminal/control status, authority/readiness,
Gazebo/Jackal/fake lock, endoscope and estimator comparison outputs.

Missing/disabled topics do not prevent other topics from recording. Verify actual
topic names/rates before each experiment; non-default estimator names or topic
overrides need matching entries in the script. Depth and point clouds are not
recorded by default. The obsolete `/docking/target_pose` entry is removed.

`/kaist_rosbag/recording` is a latched Boolean reporting whether the child
recorder process is running, **not** a guarantee that every topic is arriving
or the disk is healthy. Inspect rosbag console errors and the finished bag.
Early/unexpected exits are reported; there is no silent automatic restart.
In armed mode, correct the fault and restart the node or disarm/re-arm safely;
do not change flight state merely to recover recording during a flight.

Stop/shutdown sends SIGINT only to this node's recorder process group and waits
up to 10 seconds. Other recorders are untouched. A stalled recorder is not
force-killed: an explicit error tells you to inspect it and keep power on.
Automatic mode omits disarmed bench/preflight and post-disarm events; choose
manual mode when those are required. No arming or actuator services are called.
