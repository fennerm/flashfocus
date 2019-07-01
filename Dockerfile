FROM fennerm/arch-i3-novnc

LABEL maintainer="fmacrae.dev@gmail.com"

RUN pacman -Sy --noconfirm archlinux-keyring
RUN pacman -Syu --noconfirm
RUN pacman -S --noconfirm \
        gcc \
        glib2 \
        gtk3 \
        python-cairo \
        python-gobject \
        python-pip \
        libxcb
        

USER user
ENV PATH="/home/user/.local/bin:${PATH}"

RUN pip install --no-cache-dir --user "pytest==4.2" pytest-cov pytest-runner \
        pytest-factoryboy pytest-lazy-fixture pdbpp

COPY --chown=user requirements.txt requirements.txt
RUN pip install --user -r requirements.txt

COPY --chown=user . /home/user/flashfocus
WORKDIR /home/user/flashfocus
RUN pip3 install --no-deps -e . --user .


CMD test/docker_startup.sh
