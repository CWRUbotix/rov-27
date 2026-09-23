
# Git Commands

| Commands | Descriptions |
| :---- | :---- |
| git status | provides information about what branch you are on, what is staged, and some other useful information. If you forget where you are or what you are doing in git, git status is a good place to start to get back on track  |
| git checkout \-b \[new branch name\] | create a new branch |
| git stash | stash away what you are working on on a branch (useful if you need to switch to a different branch without committing your code) |
| git stash pop | "unstash" the last thing you stashed |
| git add . | stages all your files to be able to commit them |
| git add \[file\] | stage a specific file to be able to commit it |
| git commit \-m "\[message\]" | commit a file with a message |
| git merge \[branch\] | merge the branch you are on with \[branch\] |
| git clone \<url\> | cone a repo |
| git diff \[file1\] \[file2\] | check the difference between \[file1\] and \[file2\] |
| git push | push your code up to github |
| git pull | pull code down from github |
| git log | look at your past commits |

| Linux Commands | Descriptions |
| :---- | :---- |
| ls | list files and directories you have access to based on your current location |
| cd | change directory |
| pwd | see your current location |
| mkdir | make a directory |
| mv \[file\] | move a file |
| rm \[file\] | remove a file (be careful with this, you can't get it back) |
| cat \[file\] | look at a file |
| nano \[file\] | editing tool for files in cmd line |
| vim \[file\] | another editing tool for files in cmd line |
| ps | look at processes running on your machine |

| ROS Commands | Descriptions |
| :---- | :---- |
| ros2 launch \<package\_name\> \<executable\_name\> | launch ros code |
| ros2 run \<package\_name\> \<executable\_name\> \--ros-args \-p \<param\_name\>:=\<value\> | launch rose code with parameters |
| ros2 launch surface\_main surface\_all\_nodes\_launch.py | How to run our code |
| rqt | Lets you see the running nodes and topics in a map |

