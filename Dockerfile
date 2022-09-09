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

RUN pip install --user \
        pdbpp \
        pytest \
        pytest-cov \
        pytest-factoryboy \
        pytest-lazy-fixture \
        pytest-runner

COPY --chown=user requirements.txt requirements.txt
RUN pip install --user -r requirements.txt

COPY --chown=user . /home/user/flashfocus
WORKDIR /home/user/flashfocus
RUN pip3 install --no-deps --user -e .

ENV DISPLAY=":0"
# -nolisten unix is necessary or we hit errors:
# _XSERVTransmkdir: ERROR: euid != 0,directory /tmp/.X11-unix will not be created.
CMD Xvfb :0 -nolisten unix -screen 0 1280x1024x24 & \
        sleep 2; \
        i3 & \
        sleep 10; \
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