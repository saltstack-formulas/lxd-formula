#!jinja|yaml
# -*- coding: utf-8 -*-
# vi: set ft=yaml.jinja :

{% from "lxd/map.jinja" import datamap, sls_block with context %}

include:
  - lxd.python

{% for name, remote in datamap.remotes.items() %}
{% if 'password' in remote %}
lxd_remote_{{ name }}:
  lxd.authenticate:
    - remote_addr: "{{ remote.remote_addr }}"
    - password: "{{ remote.password }}"
    - cert: "{{ remote.cert }}"
    - key: "{{ remote.key }}"
    - verify_cert: {{ remote.get('verify_cert', True) }}
{% endif %}
{% endfor %}
