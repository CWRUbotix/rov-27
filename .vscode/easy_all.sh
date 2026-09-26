# Done to suppress setup.py install deprecated warnings
# Can be removed once ROS redoes their python build system
export PYTHONWARNINGS="ignore:::setuptools.command.install,ignore:::setuptools.command.easy_install,ignore:::pkg_resources,ignore:pkg_resources is deprecated as an API"
#. /opt/ros/lyrical/setup.sh
unset AMENT_PREFIX_PATH
unset CMAKE_PREFIX_PATH
# Install any missing dependencies
source "$(pwd)/.vscode/install_dependencies.sh"

colcon build --symlink-install
source install/setup.bash
