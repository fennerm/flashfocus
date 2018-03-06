FROM fennerm/arch-i3-novnc

MAINTAINER Fenner Macrae <fmacrae.dev@gmail.com>

RUN pacman -S --noconfirm python-pip

USER user
RUN pip install --user pytest pytest-cov
COPY . i3flash
WORKDIR i3flash
RUN pip install -r requirements.txt --user .

ENV PATH="/home/user/.local/bin:${PATH}"

ENTRYPOINT pytest

