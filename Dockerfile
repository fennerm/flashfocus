FROM fennerm/arch-i3-novnc

LABEL maintainer="fmacrae.dev@gmail.com"

RUN pacman -S --noconfirm \
        gcc \
        glib2 \
        gtk3 \
        python-cairo \
        python2-cairo \
        python-gobject \
        python2-gobject \
        python-pip \
        python2-pip \
        libxcb
        

USER user
ENV PATH="/home/user/.local/bin:${PATH}"

RUN pip3 install --no-cache-dir --user pytest pytest-cov pytest-runner \
        pytest-factoryboy pytest-lazy-fixture pdbpp
RUN pip2 install --no-cache-dir --user pytest pytest-cov pytest-runner mock \
        pytest-factoryboy pytest-lazy-fixture pdbpp

COPY --chown=user requirements.txt requirements.txt
RUN pip3 install --user -r requirements.txt
RUN pip2 install --user -r requirements.txt

COPY --chown=user . flashfocus
WORKDIR flashfocus
RUN pip3 install --no-deps -e . --user .
RUN pip2 install -e . --no-deps --user .


CMD test/docker_startup.sh
