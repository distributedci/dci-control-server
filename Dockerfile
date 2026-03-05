FROM registry.access.redhat.com/ubi10/ubi-minimal
LABEL name="DCI API" version="1.0.0"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

COPY sso/RH-IT-Root-CA.crt sso/2022-IT-Root-CA.pem /etc/pki/ca-trust/source/anchors/
RUN update-ca-trust

WORKDIR /opt/dci-control-server

# install dependencies first
COPY requirements.txt .

RUN microdnf -y upgrade && \
    microdnf -y install python3 python3-pip && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --requirement requirements.txt && \
    microdnf -y clean all

# install source after
COPY entrypoint-devenv.sh entrypoint.sh /usr/local/sbin/
COPY gunicorn.conf.py /etc/

COPY . /opt/dci-control-server/

RUN pip3 --no-cache-dir install --editable .

EXPOSE 5000

ENTRYPOINT ["/usr/local/sbin/entrypoint.sh"]

CMD ["/usr/local/bin/gunicorn", "-c", "/etc/gunicorn.conf.py", "-b", "0.0.0.0:5000", "dci.app:create_app()"]
