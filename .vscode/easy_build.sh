# Done to suppress setup.py install deprecated warnings
# Can be removed once ROS redoes their python build system
export PYTHONWARNINGS="ignore:::setuptools.command.install,ignore:::setuptools.command.easy_install,ignore:::pkg_resources,ignore:pkg_resources is deprecated as an API"

. /opt/ros/lyrical/setup.sh

# Stolen from colcon build command in VsCode
colcon build --symlink-install
source install/setup.bash