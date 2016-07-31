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
