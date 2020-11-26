ARG APACHE_STORM_VER="2.2.0"
FROM apache-storm:${APACHE_STORM_VER}

# Environment variables
ARG TIKA_VER="1.24.1" 
ARG SPAMSCOPE_BRANCH="develop"

ENV FAUP_PATH="/opt/faup-master" \
    # Disable warning when running lein as root
    LEIN_ROOT="yes" \
    SPAMASSASSIN_ENABLED="True" \
    SPAMSCOPE_CONF_FILE="/etc/spamscope/spamscope.yml" \
    SPAMSCOPE_PATH="/opt/spamscope" \
    THUG_ENABLED="True" \
    TIKA_APP_JAR="/opt/tika-app-${TIKA_VER}.jar"

COPY ./ ${SPAMSCOPE_PATH}/

# Install system packages
RUN set -ex; \
    apt-get -y update; \
    apt-get -y --no-install-recommends install \
        build-essential \
        cmake \
        file \
        git \
        libgraphviz-dev \
        leiningen \
        libboost-dev \
        libboost-python-dev \
        libboost-system-dev \
        libemu-dev \
        libemail-outlook-message-perl \
        libmagic1 \
        libfuzzy-dev \
        p7zip-full \
        pkg-config \
        python3-graphviz \
        python3-pip \
        spamassassin \
        unrar \
        unzip; \
# Upgrade python tools
    pip3 install --upgrade pip setuptools; \
# Apache Tika
    curl -So ${TIKA_APP_JAR} https://archive.apache.org/dist/tika/tika-app-${TIKA_VER}.jar; \
# Faup
    git clone https://github.com/stricaud/faup.git ${FAUP_PATH} && mkdir -p $FAUP_PATH/build && cd $FAUP_PATH/build && cmake .. && make && make install && echo '/usr/local/lib' | tee -a /etc/ld.so.conf.d/faup.conf && ldconfig; \
# Thug
    git clone --depth 1 --branch v8.6.395.24 https://github.com/area1/stpyv8.git /opt/stpyv8 && cd /opt/stpyv8 && python2 setup.py v8 && python3 setup.py stpyv8 && python3 setup.py install; \
    # Make sure python3-wheel is not installed, because of https://stackoverflow.com/questions/47460804/copy-configuration-file-on-installation
    pip install thug; \  
# SpamScope
    mkdir -p "/var/log/spamscope" "/etc/spamscope"; \
    cd $SPAMSCOPE_PATH; \
    pip install -r requirements_optional.txt; \
    python3 setup.py install; \
    sparse jar -s; \
# Purge unused packages
    apt-get -yqq purge \
        build-essential \
        cmake; \
    apt-get -yqq autoremove && dpkg -l | grep ^rc | awk '{print $2}' | xargs dpkg --purge; \
# Cleaning
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*
    
WORKDIR ${SPAMSCOPE_PATH}
