FROM fennerm/arch-i3-novnc

LABEL maintainer="fmacrae.dev@gmail.com"

RUN pacman -Sy --noconfirm archlinux-keyring
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
    flake8 \
    flake8-bugbear \
    flake8-blind-except \
    flake8-builtins \
    mypy \
    pdbpp \
    pytest \
    pytest-cov \
    pytest-factoryboy \
    pytest-runner \
    pytest-lazy-fixture \
    vulture

COPY --chown=user requirements.txt requirements.txt
RUN pip install --user -r requirements.txt

COPY --chown=user . /home/user/flashfocus
WORKDIR /home/user/flashfocus
RUN pip3 install --no-deps --user -e .

CMD supervisord </dev/null &>/dev/null \
    & sleep 1; \
    flake8 --exclude "./build,./.eggs"; \
    mypy --ignore-missing-imports .; \
    vulture flashfocus test; \
    pytest --failed-first --verbose --cov-report term-missing \
        --cov="$PWD" --color yes --showlocals --durations 10 --pdb
