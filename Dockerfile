FROM fennerm/arch-i3-novnc

MAINTAINER Fenner Macrae <fmacrae.dev@gmail.com>

RUN pacman -S --noconfirm \
        gtk3 \
        python-gobject \
        python2-gobject \
        python-pip \
        python2-pip \
        xdotool \
        xorg-xprop

USER user

COPY --chown=user . flashfocus
WORKDIR flashfocus
RUN pip3 install --user pytest pytest-cov pytest-runner plumbum
RUN pip2 install --user pytest pytest-cov pytest-runner plumbum
RUN pip3 install --user -r requirements.txt --user .
RUN pip2 install --user -r requirements.txt --user .

ENV PATH="/home/user/.local/bin:${PATH}"

CMD test/docker_startup.sh
