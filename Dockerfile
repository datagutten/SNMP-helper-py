FROM python:3.11

# set work directory
WORKDIR /usr/src/app
ARG SNMP_LIBRARY
# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SNMP_LIBRARY=${SNMP_LIBRARY}
ENV SNMPSIM_HOST=snmpsim

# install system dependencies
RUN apt-get update && apt-get install -y libsnmp-dev libzmq3-dev libczmq-dev


RUN pip install --upgrade pip uv[toml]

COPY snmp_compat snmp_compat
COPY mib_parser mib_parser
COPY tests tests
COPY pyproject.toml pyproject.toml
COPY README.md .

RUN uv sync --no-default-groups --group dev --group ${SNMP_LIBRARY}

CMD uv run coverage run -m unittest tests.compat.test_compat