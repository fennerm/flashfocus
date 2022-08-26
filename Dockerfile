FROM fennerm/arch-i3-novnc

LABEL maintainer="fmacrae.dev@gmail.com"

RUN pacman -Sy --noconfirm archlinux-keyring
RUN yes | pacman-key --init
RUN yes | pacman-key --populate archlinux
RUN pacman -Syyu --noconfirm
RUN pacman -S --noconfirm \
        gcc \
        glib2 \
        gtk3 \
        python-pip \
        libxcb

USER user
ENV PATH="/home/user/.local/bin:${PATH}"

RUN pip install --user \
    pdbpp \
    pytest \
    pytest-cov \
    pytest-factoryboy \
    pytest-runner \
    pytest-lazy-fixture

COPY --chown=user requirements.txt requirements.txt
RUN pip install --user -r requirements.txt

COPY --chown=user . /home/user/flashfocus
WORKDIR /home/user/flashfocus
RUN pip3 install --no-deps --user -e .

ENV DISPLAY=":0"
CMD supervisord </dev/null &>/dev/null \
    & sleep 2; \
    pytest --failed-first --verbosity=3 --cov-report term-missing --log-level=DEBUG --capture=no \
        --cov="$PWD" --color yes --showlocals --durations 10 ${PYTEST_ARGS}
