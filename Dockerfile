FROM archlinux:base

RUN pacman -Sy --noconfirm archlinux-keyring
RUN yes | pacman-key --init
RUN yes | pacman-key --populate archlinux
RUN pacman -Syyu --noconfirm
RUN pacman -S --noconfirm \
        gcc \
        glib2 \
        gtk3 \
        i3status \
        i3-wm \
        python-pip \
        libxcb \
        ttf-dejavu \
        xorg-apps \
        xorg-server \
        xorg-server-xvfb \
        xorg-xinit

# Setup locale (required for i3)
RUN sed -i '/en_US.UTF-8/s/^#//g' /etc/locale.gen
RUN locale-gen

RUN useradd -m user
WORKDIR /home/user
USER user

ENV PATH="/home/user/.local/bin:${PATH}"

COPY --chown=user requirements.txt requirements.txt
RUN pip install --user -r requirements.txt

COPY --chown=user . /home/user/flashfocus
WORKDIR /home/user/flashfocus
RUN pip3 install --no-deps --user -e .

ENV DISPLAY=":0"

# For some reason Xvfb tries to create this dir but fails because its not running as root.
RUN mkdir /tmp/.x11-unix

# We see a few errors on startup which are safe to ignore:
# _XSERVTransmkdir: ERROR: euid != 0,directory /tmp/.X11-unix will not be created.
# /bin/sh: line 1: dex: command not found
# /bin/sh: line 1: xss-lock: command not found
# /bin/sh: line 1: nm-applet: command not found
CMD Xvfb :0 -screen 0 1280x1024x24 & \
        sleep 2; \
        i3 & \
        sleep 2; \
        pytest \
            --failed-first \
            --verbosity=3 \
            --cov-report=term-missing \
            --log-level=DEBUG \
            --capture=no \
            --cov="flashfocus" \
            --color=yes \
            --showlocals \
            --durations 10 \
            ${PYTEST_ARGS}