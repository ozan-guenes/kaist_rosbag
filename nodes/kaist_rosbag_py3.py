#!/usr/bin/env python3

'''
@date: 2021-08-17
@author: Seungwook Lee, KAIST
@source: https://gist.github.com/marco-tranzatto/8be49b81b1ab371dcb5d4e350365398a
'''

import rospy
import subprocess
import os
import signal
import threading

from mavros_msgs.msg import State
from std_msgs.msg import Bool
from std_srvs.srv import Trigger, TriggerResponse


class RosbagRecord:
    def __init__(self):
        self.record_script = os.path.abspath(os.path.expanduser(rospy.get_param('~record_script')))
        self.record_folder = os.path.abspath(os.path.expanduser(rospy.get_param('~record_folder')))
        self.trigger_topic_name = rospy.get_param('~trigger_topic_name', '/mavros/state')
        self.verbose = rospy.get_param('~verbose', False)
        self.mode = rospy.get_param('~mode', 'armed')
        if self.mode not in ('armed', 'manual'):
            raise ValueError('mode must be armed or manual')
        if not os.path.isfile(self.record_script) or not os.access(self.record_script, os.R_OK):
            raise ValueError('Cannot read record script: ' + self.record_script)
        os.makedirs(self.record_folder, exist_ok=True)
        if not os.access(self.record_folder, os.W_OK):
            raise ValueError('Cannot write record folder: ' + self.record_folder)

        self.lock = threading.RLock()
        self.p = None
        self.shutting_down = False
        self.monitor_stop = threading.Event()
        self.trigger = False
        self.last_trigger = self.trigger
        self.recording_pub = rospy.Publisher('~recording', Bool, queue_size=1, latch=True)
        self.publish_recording(False)
        rospy.on_shutdown(self.shutdown)

        self.start_service = rospy.Service('~start', Trigger, self.handle_start)
        self.stop_service = rospy.Service('~stop', Trigger, self.handle_stop)
        self.trigger_topic_subscriber = None
        if self.mode == 'armed':
            self.trigger_topic_subscriber = rospy.Subscriber(
                self.trigger_topic_name, State, self.trigger_subscriber_callback, queue_size=10)
        # Check process health even while Gazebo /clock is paused.
        self.monitor = threading.Thread(target=self.monitor_recording, daemon=True)
        self.monitor.start()
        rospy.loginfo('Rosbag ready: mode=%s trigger=%s folder=%s',
                      self.mode, self.trigger_topic_name, self.record_folder)

    def publish_recording(self, recording):
        # Process status only, not completeness of every recorded topic.
        try:
            self.recording_pub.publish(Bool(data=recording))
        except rospy.ROSException:
            pass

    def start_recording_handler(self):
        with self.lock:
            if self.shutting_down or rospy.is_shutdown():
                return False, 'Recorder is shutting down'
            if self.p is not None and self.p.poll() is None:
                return True, 'Already recording'
            self.p = None
            try:
                # Keep the topic script unchanged in form, but execute the recorder
                # binary directly so wait() includes bag finalization, not just the
                # Python rosbag CLI wrapper exiting after SIGINT.
                command = 'rosbag() { exec rosrun rosbag "$@"; }; source "$1"'
                # A separate session lets us interrupt only our recorder.
                self.p = subprocess.Popen(
                    ['/bin/bash', '-c', command, 'kaist_rosbag', self.record_script],
                    stdin=subprocess.DEVNULL, cwd=self.record_folder,
                    start_new_session=True)
                try:
                    code = self.p.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    self.publish_recording(True)
                    rospy.loginfo('Rosbag recording started in %s', self.record_folder)
                    return True, 'Recorder process started'
                self.p = None
                message = 'Recorder exited during startup (status %s); inspect rosbag output' % code
            except OSError as error:
                self.p = None
                message = 'Cannot start recorder: %s' % error
            self.publish_recording(False)
            rospy.logerr(message)
            return False, message


    def stop_recording_handler(self):
        with self.lock:
            if self.p is None:
                return True, 'Already stopped'
            if self.p.poll() is None:
                rospy.loginfo('Stopping own rosbag recorder; waiting for bag finalization')
                try:
                    os.killpg(self.p.pid, signal.SIGINT)
                except ProcessLookupError:
                    pass
                try:
                    self.p.wait(timeout=10.0)
                except subprocess.TimeoutExpired:
                    message = ('Recorder has not stopped after 10 s; it was not force-killed. '
                               'Keep power on and inspect rosbag output (process group %s).' % self.p.pid)
                    rospy.logerr(message)
                    return False, message
            self.p = None
            self.publish_recording(False)
            rospy.loginfo('Rosbag recorder stopped')
            return True, 'Recorder stopped'

    def handle_start(self, _request):
        if self.mode != 'manual':
            return TriggerResponse(False, 'Use mode:=manual for service-controlled recording')
        return TriggerResponse(*self.start_recording_handler())

    def handle_stop(self, _request):
        if self.mode != 'manual':
            return TriggerResponse(False, 'Use mode:=manual for service-controlled recording')
        return TriggerResponse(*self.stop_recording_handler())

    def monitor_recording(self):
        while not self.monitor_stop.wait(1.0):
            self.check_recording()

    def check_recording(self):
        with self.lock:
            if self.p is not None and self.p.poll() is not None:
                rospy.logerr('Rosbag recorder exited unexpectedly (status %s); inspect rosbag output. '
                             'Correct the problem, then restart manually or on the next arming edge.',
                             self.p.returncode)
                self.p = None
                self.publish_recording(False)

    def shutdown(self):
        with self.lock:
            self.shutting_down = True
            self.monitor_stop.set()
        self.stop_recording_handler()

    def trigger_subscriber_callback(self, msg):
        with self.lock:
            self.trigger = bool(msg.armed)
            if self.verbose and self.trigger != self.last_trigger:
                rospy.loginfo('Recording trigger armed=%s', self.trigger)
            if self.trigger and not self.last_trigger:
                self.start_recording_handler()
            elif not self.trigger and self.last_trigger:
                self.stop_recording_handler()
            self.last_trigger = self.trigger


if __name__ == '__main__':
    rospy.init_node('rosbag_record')
    rospy.loginfo(rospy.get_name() + '.py start')

    # Go to class functions that do all the heavy lifting. Do error checking.
    try:
        rosbag_record = RosbagRecord()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    except (KeyError, ValueError, OSError) as error:
        rospy.logfatal('Cannot initialize rosbag recorder: %s', error)
        raise
