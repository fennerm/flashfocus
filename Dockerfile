FROM fennerm/arch-i3-novnc

LABEL maintainer="fmacrae.dev@gmail.com"

RUN pacman -S --noconfirm \
        glib2 \
        gtk3 \
        python-cairo \
        python2-cairo \
        python-gobject \
        python2-gobject \
        python-pip \
        python2-pip \
        xdotool \
        libxcb \
        xorg-xprop

USER user
ENV PATH="/home/user/.local/bin:${PATH}"

# Required for testing click command line interface
ENV LC_ALL=en_US.utf8
ENV LANG=en_US.utf8

RUN pip3 install --no-cache-dir --user pytest pytest-cov pytest-runner \
        pytest-factoryboy pytest-lazy-fixture
RUN pip2 install --no-cache-dir --user pytest pytest-cov pytest-runner mock \
        pytest-factoryboy pytest-lazy-fixture

COPY --chown=user . flashfocus

WORKDIR flashfocus
RUN pip3 install --user -r requirements.txt --user .
RUN pip2 install --user -r requirements.txt --user .

CMD test/docker_startup.sh
