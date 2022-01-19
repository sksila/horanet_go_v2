FROM registry-gitlab.horanet.com:4567/horanet/docker/odoo:latest

USER root

# Load SSH key, this is not good solution as the SSH key will be available in the layers
# of the docker image.. But as we don't publish our images publicly, this is ok
ARG SSH_PRIVATE_KEY
RUN mkdir /root/.ssh/
RUN echo "${SSH_PRIVATE_KEY}" >> /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa
RUN touch /root/.ssh/known_hosts
RUN apt-get update && apt-get install -y openssh-client
RUN ssh-keyscan ssh-gitlab.horanet.com >> /root/.ssh/known_hosts
RUN ssh-keyscan gitlab.horanet.com >> /root/.ssh/known_hosts

# Copy project sources in odoo addons directory (for installation and volume creation)
WORKDIR /mnt/extra-addons/
COPY ./ /mnt/extra-addons/

# Install required packages
RUN eval `ssh-agent -s` && ssh-add /root/.ssh/id_rsa && \
  apt-get update && \
  apt-get install -y --no-install-recommends git && \
  pip install -r requirements/ci.txt && \
  apt-get remove --purge -y python-pip openssh-client && \
  apt-get clean && apt-get autoremove -y && \
  rm -rf /var/lib/apt && \
  rm -rf /tmp/* && \
  rm -rf /root/.cache

RUN usermod -aG root odoo
USER odoo
