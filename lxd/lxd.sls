#!jinja|yaml
# -*- coding: utf-8 -*-
# vi: set ft=yaml.jinja :

{% from "lxd/map.jinja" import datamap, sls_block with context %}

lxd_lxd:
  pkg:
    - {{ datamap.lxd.package.action }}
    {{ sls_block(datamap.lxd.package.opts )}}
    - pkgs: {{ datamap.lookup.lxd.packages }}

{% if datamap.lxd.run_init -%}
  lxd:
    - init
    - storage_backend: "{{ datamap.lxd.init.storage_backend }}"
    - trust_password: "{{ datamap.lxd.init.trust_password }}"
    - network_address: "{{ datamap.lxd.init.network_address }}"
    - network_port: "{{ datamap.lxd.init.network_port }}"
    - storage_create_device: "{{ datamap.lxd.init.storage_create_device }}"
    - storage_create_loop: "{{ datamap.lxd.init.storage_create_loop }}"
    - storage_pool: "{{ datamap.lxd.init.storage_pool }}"
    - done_file: "{{ datamap.lxd.init.done_file }}"
    - require:
      - pkg: lxd_lxd
      - sls: lxd.python
{%- endif %}

{% for name, cdict in datamap.lxd.config.items() %}
lxd_config_{{ name }}:
  lxd:
    - config_managed
    - name: "{{ cdict.key }}"
    - value: "{{ cdict.value }}"
    - force_password: {{ cdict.get('force_password', False) }}
    - require:
      - pkg: lxd_lxd
      - sls: lxd.python
{% endfor %}
