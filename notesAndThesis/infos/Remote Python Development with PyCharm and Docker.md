# Remote python development with PyCharm and Docker



PyCharm can be used together with a ssh remote interpreter for very convenient python remote development. For this the __Pro__ version of PyCharm is required (free for students, requires an account with an institutional email address). 

## 1. Setup a Docker Container with ssh

Your docker container will need a running ssh server. Authorization should be done via SSH keys.

### SSH-Key Setup

Follow https://www.ssh.com/academy/ssh/keygen to generate a private-public key pair. Copy your __public__ key into a file named `authorized_keys` and put it in the same folder as your Dockerfile.

Example Dockerfile:

```dockerfile
FROM nvidia/cuda:11.2.2-cudnn8-devel-ubuntu20.04 # Or any other ubuntu based image

ENV DEBIAN_FRONTEND noninteractive
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG TARGET_UID=1001
ARG TARGET_GID=1001

# Setup the default user.
ENV TARGET_UID=$TARGET_UID
ENV TARGET_GID=$TARGET_GID
RUN groupadd -g ${TARGET_GID} devel
RUN useradd -rm -d /home/devel -s /bin/bash -g devel -G sudo -u ${TARGET_UID} devel
RUN echo 'devel:devel' | chpasswd
USER devel
WORKDIR /home/devel

USER root

# Install ssh server package
RUN apt-get update && apt-get install -y openssh-server

# Configure SSHD.
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
RUN mkdir /run/sshd
RUN bash -c 'install -m755 <(printf "#!/bin/sh\nexit 0") /usr/sbin/policy-rc.d'
RUN ex +'%s/^#\zeListenAddress/\1/g' -scwq /etc/ssh/sshd_config
RUN ex +'%s/^#\zeHostKey .*ssh_host_.*_key/\1/g' -scwq /etc/ssh/sshd_config
RUN RUNLEVEL=1 dpkg-reconfigure openssh-server
RUN ssh-keygen -A -v
RUN update-rc.d ssh defaults

# Configure sudo.
RUN ex +"%s/^%sudo.*$/%sudo ALL=(ALL:ALL) NOPASSWD:ALL/g" -scwq! /etc/sudoers

USER devel
RUN mkdir -p /home/devel/.ssh
COPY authorized_keys /home/devel/.ssh/

# Add your Python/pip setup code here...

EXPOSE 22
CMD ["/usr/bin/sudo", "/usr/sbin/sshd", "-D", "-o", "ListenAddress=0.0.0.0"]

```

When building the docker image add

```bash
--build-arg TARGET_UID=`id -u` --build-arg TARGET_GID=`id -g`
```

to yout docker build command (on *nix systems).

By adding

```bash
--user `id -u`:`id -g`
```

to your docker run command the UID and GID of user `devel` inside the container will be mapped to your host user account. (Optional)

## 2. Tunnel Setup

Ensure that the docker container is running on your MIP workstation. On a *nix (including macOS) machine open a terminal and type

```bash
ssh -N -p 64222 -C YOUR_USERNAME@nil.mip.informatik.uni-kiel.de -o StrictHostKeyChecking=no -L 2233:colorado:2233
```

to create a ssh tunnel to your docker container. Now you can access your container using:

```bash
ssh -p 2233 devel@localhost
```



## 4. PyCharm Setup

Open PyCharm and start a new python project.

### 4.1 Remote Interpreter

Follow the guide at https://www.jetbrains.com/help/pycharm/configuring-remote-interpreters-via-ssh.html#prereq with the following modifications:

4. host: localhost, port: 2233, username: devel
5. Check "Key Pair" and locate your private ssh key

Follow the guide to the end. This will give you a new remote ssh interpreter.

### 4.2 Deplyment Setup

Go to Configuration -> Build, Execution, Deployment -> Deployment -> Add button

1. Choose sftp
2. Give it a name
3. Under SSH configuration select the one you've created for the remote interpreter
4. Under mapping: set the deployment path to `/home/devel/YOUR_PROJECT_NAME`
5. Ensure that the deplyment configuration is the default one (by clicking the hook)
6. Under Deployment -> Options -> "Upload changed files automatically to the default server" choose either "On explicit save" or "Always". This will keep your local monification in sync with the remote server.
7. Close the configuration. Under the Prject tab right click your priject root folder and choose "Deployment -> Upload to ... " to upload all of your project files to the remote server. 

