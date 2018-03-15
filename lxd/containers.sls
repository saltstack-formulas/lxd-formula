#!jinja|yaml
# -*- coding: utf-8 -*-
# vi: set ft=yaml.jinja :

{% from "lxd/map.jinja" import datamap, sls_block with context %}

include:
  - lxd.python
  - lxd.remotes
  - lxd.profiles
  - lxd.images

{% for remotename, containers in datamap.containers.items() %}
    {%- set remote = datamap.remotes.get(remotename, {}) %}

    {%- for name, container in containers.items() %}
      {%- if 'migrated' not in container and 'absent' not in container %}
lxd_container_{{ remotename }}_{{ name }}:
  lxd_container.present:
    {%- if 'name' in container %}
    - name: "{{ container['name'] }}"
    {%- else %}
    - name: "{{ name }}"
    {%- endif %}
        {%- if 'running' in container %}
    - running: {{ container.running }}
        {%- endif %}
    - source: {{ container.source }}
    {%- if 'profiles' in container %}
    - profiles: {{ container.profiles }}
    {%- endif %}
    {%- if 'config' in container %}
    - config: {{ container.config }}
    {%- endif %}
    {%- if 'devices' in container %}
    - devices: {{ container.devices }}
    {%- endif %}
    {%- if 'architecture' in container %}
    - architecture: "{{ container.architecture }}"
    {%- endif %}
    {%- if 'ephemeral' in container %}
    - ephemeral: {{ container.ephemeral }}
    {%- endif %}
    {%- if 'restart_on_change' in container %}
    - restart_on_change: {{ container.restart_on_change }}
    {%- endif %}
    - remote_addr: "{{ remote.remote_addr }}"
    - cert: "{{ remote.cert }}"
    - key: "{{ remote.key }}"
    - verify_cert: {{ remote.verify_cert }}
        {%- if remote.get('password', False) %}
    - require:
      - lxd: lxd_remote_{{ remotename }}
        {%- endif %}
        {%- if 'opts' in container %}
    {{ sls_block(container.opts )}}
        {%- endif %}

    {%- if 'bootstrap_scripts' in container %}
# Touch marker file, so nonexistance do not throws exception in container_file_get
lxd_container_{{ remotename }}_{{ name }}_touch_executed:
    module.run:
        - name: lxd.container_execute
    {%- if 'name' in container %}
        - m_name: "{{ container['name'] }}"
    {%- else %}
        - m_name: "{{ name }}"
    {%- endif %}
        - cmd: [ 'touch', '/etc/salt_lxd_bootstraped']
        - remote_addr: "{{ remote.remote_addr }}"
        - cert: "{{ remote.cert }}"
        - key: "{{ remote.key }}"
        - verify_cert: {{ remote.verify_cert }}
        - onchanges:
            - lxd_container: lxd_container_{{ remotename }}_{{ name }}
        {%- if remote.get('password', False) %}
        - require:
            - lxd: lxd_remote_{{ remotename }}
        {%- endif %}

# Save marker file locally per remote and container
lxd_container_{{ remotename }}_{{ name }}_check_executed:
    module.run:
        - name: lxd.container_file_get
    {%- if 'name' in container %}
        - m_name: "{{ container['name'] }}"
    {%- else %}
        - m_name: "{{ name }}"
    {%- endif %}
        - src: "/etc/salt_lxd_bootstraped"
        - dst: "/tmp/salt_lxd_bootstraped_{{ remotename }}_{{ name }}"
        - uid: 0
        - gid: 0
        - overwrite: True
        - remote_addr: "{{ remote.remote_addr }}"
        - cert: "{{ remote.cert }}"
        - key: "{{ remote.key }}"
        - verify_cert: {{ remote.verify_cert }}
        - onchanges:
            - lxd_container: lxd_container_{{ remotename }}_{{ name }}
        - require:
            - module: lxd_container_{{ remotename }}_{{ name }}_touch_executed
        {%- if remote.get('password', False) %}
            - lxd: lxd_remote_{{ remotename }}
        {%- endif %}

      {%- for script in container['bootstrap_scripts'] %}
      {%- if 'src' in script %}
lxd_container_{{ remotename }}_{{ name }}_bsc_{{ loop.index }}:
    module.run:
        - name: lxd.container_file_put
    {%- if 'name' in container %}
        - m_name: "{{ container['name'] }}"
    {%- else %}
        - m_name: "{{ name }}"
    {%- endif %}
        - src: "{{ script.src }}"
        - dst: "{{ script.dst }}"
        - mode: 0700
        - remote_addr: "{{ remote.remote_addr }}"
        - cert: "{{ remote.cert }}"
        - key: "{{ remote.key }}"
        - verify_cert: {{ remote.verify_cert }}
        - onchanges:
            - lxd_container: lxd_container_{{ remotename }}_{{ name }}
        # Do not run if there is True in the marker file (bootstrap already executed)
        - unless:
            - "grep -s -q True /tmp/salt_lxd_bootstraped_{{ remotename }}_{{ name }}"
      {%- endif %}

lxd_container_{{ remotename }}_{{ name }}_bse_{{ loop.index }}:
    module.run:
        - name: lxd.container_execute
    {%- if 'name' in container %}
        - m_name: "{{ container['name'] }}"
    {%- else %}
        - m_name: "{{ name }}"
    {%- endif %}
        - cmd: {{ script.cmd }}
        - remote_addr: "{{ remote.remote_addr }}"
        - cert: "{{ remote.cert }}"
        - key: "{{ remote.key }}"
        - verify_cert: {{ remote.verify_cert }}
        - onchanges:
            - lxd_container: lxd_container_{{ remotename }}_{{ name }}
        {%- if 'src' in script %}
            - module: lxd_container_{{ remotename }}_{{ name }}_bsc_{{ loop.index }}
        {%- endif %}
        # Do not run if there is True in the marker file (bootstrap already executed)
        - unless:
            - "grep -s -q True /tmp/salt_lxd_bootstraped_{{ remotename }}_{{ name }}"

      {%- endfor %}

lxd_container_{{ remotename }}_{{ name }}_restart:
    module.run:
        - name: lxd.container_restart
    {%- if 'name' in container %}
        - m_name: "{{ container['name'] }}"
    {%- else %}
        - m_name: "{{ name }}"
    {%- endif %}
        - remote_addr: "{{ remote.remote_addr }}"
        - cert: "{{ remote.cert }}"
        - key: "{{ remote.key }}"
        - verify_cert: {{ remote.verify_cert }}
        - onchanges:
        {%- for script in container['bootstrap_scripts'] %}
            - module: lxd_container_{{ remotename }}_{{ name }}_bse_{{ loop.index }}
        {%- endfor %}

# Put True in the marker file
lxd_container_{{ remotename }}_{{ name }}_make_executed:
    module.run:
        - name: lxd.container_file_put
    {%- if 'name' in container %}
        - m_name: "{{ container['name'] }}"
    {%- else %}
        - m_name: "{{ name }}"
    {%- endif %}
        - src: "salt://lxd/files/salt_lxd_bootstraped"
        - dst: "/etc/salt_lxd_bootstraped"
        - mode: 0600
        - remote_addr: "{{ remote.remote_addr }}"
        - cert: "{{ remote.cert }}"
        - key: "{{ remote.key }}"
        - verify_cert: {{ remote.verify_cert }}
        - onchanges:
            - module: lxd_container_{{ remotename }}_{{ name }}_restart
        {%- for script in container['bootstrap_scripts'] %}
            - module: lxd_container_{{ remotename }}_{{ name }}_bse_{{ loop.index }}
        {%- endfor %}

    {%- endif %}

      {%- elif 'absent' in container %}
lxd_container_{{ remotename }}_{{ name }}:
  lxd_container.absent:
    - name: "{{ name }}"
        {%- if 'stop' in container %}
    - stop: {{ container.stop }}
        {%- endif %}
    - remote_addr: "{{ remote.remote_addr }}"
    - cert: "{{ remote.cert }}"
    - key: "{{ remote.key }}"
    - verify_cert: {{ remote.verify_cert }}
        {%- if remote.get('password', False) %}
    - require:
      - lxd: lxd_remote_{{ remotename }}
        {%- endif %}
        {%- if 'opts' in container %}
    {{ sls_block(container.opts )}}
        {%- endif %}

      {%- elif 'migrated' in container %}
        {%- set source_name = container.source %}
        {%- set source_remote = datamap.remotes.get(source_name, {}) %}
lxd_container_{{ remotename }}_{{ name }}:
  lxd_container.migrated:
    - name: "{{ name }}"
    - remote_addr: "{{ remote.remote_addr }}"
    - cert: "{{ remote.cert }}"
    - key: "{{ remote.key }}"
    - verify_cert: {{ remote.verify_cert }}
    - stop_and_start: {{ container.get('stop_and_start', False) }}
    - src_remote_addr: "{{ source_remote.remote_addr }}"
    - src_cert: "{{ source_remote.cert }}"
    - src_key: "{{ source_remote.key }}"
    - src_verify_cert: {{ source_remote.verify_cert }}
        {%- if remote.get('password', False) or source_remote.get('password', False) %}
    - require:
          {%- if remote.get('password', False) %}
      - lxd: lxd_remote_{{ remotename }}
          {%- endif %}
          {%- if source_remote.get('password', False) %}
      - lxd: lxd_remote_{{ source_name }}
          {%- endif %}
        {%- endif %}
        {%- if 'opts' in container %}
    {{ sls_block(container.opts )}}
        {%- endif %}

      {%- endif %}
    {%- endfor %}
{%- endfor %}
