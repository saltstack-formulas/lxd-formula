#!jinja|yaml
# -*- coding: utf-8 -*-
# vi: set ft=yaml.jinja :

{% from "lxd/map.jinja" import datamap, sls_block with context %}

include:
  - lxd.python
  - lxd.remotes

{% for remotename, profiles in datamap.profiles.items() %}
    {%- set remote = False %}
    {%- if remotename != 'local' %}
        {%- set remote = datamap.remotes.get(remotename, False) %}
    {%- endif %}

    {% for name, profile in profiles.items() %}
lxd_profile_{{ remotename }}_{{ name }}:
  lxd_profile:
    - name: {{ name }}
        {%- if profile.get('removed', False) %}
    - removed
        {%- else %}
    - managed
        {%- endif %}
        {%- if profile.get('description', False) %}
    - description: "{{ profile.description }}"
        {%- endif %}
        {%- if profile.get('config', False) %}
    - config: {{ profile.config }}
        {%- endif %}
        {%- if profile.get('devices', False) %}
    - devices: {{ profile.devices }}
        {%- endif %}
        {%- if remote %}
    - remote_addr: "{{ remote.remote_addr }}"
    - cert: "{{ remote.cert }}"
    - key: "{{ remote.key }}"
    - verify_cert: {{ remote.verify_cert }}
            {%- if remote.get('password', False) %}
    - require:
      - lxd: lxd_remote_{{ remotename }}
            {%- endif %}
        {%- endif %}
    {%- endfor %}
{%- endfor %}
