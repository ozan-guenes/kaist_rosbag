# bash

export MISSION_NAME="CL_rosbag_record";
export DATE=$(date "+%Y-%m-%d_%H-%M-%S");
# roscd kaist_rosbag;
PKG_PATH=$(rospack find kaist_rosbag);
BAGS_DIR="${PKG_PATH}/bags";
cd "${BAGS_DIR}" || exit 1;
mkdir -p ${MISSION_NAME}_${DATE};
roslaunch kaist_rosbag kaist_rosbag.launch record_folder:=${BAGS_DIR}/${MISSION_NAME}_${DATE} 