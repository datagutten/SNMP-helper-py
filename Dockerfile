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


RUN pip install --upgrade pip poetry poetry-plugin-export

COPY snmp_compat snmp_compat
COPY tests tests
COPY pyproject.toml pyproject.toml

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes --with ${SNMP_LIBRARY}
RUN pip install -r requirements.txt

# ENTRYPOINT ["python3", "-m", "unittest"]