#!jinja|yaml
# -*- coding: utf-8 -*-
# vi: set ft=yaml.jinja :

{% from "lxd/map.jinja" import datamap, sls_block with context %}

include:
  - lxd.python
  - lxd.remotes

{% for remotename, images in datamap.images.items() %}
    {%- set remote = datamap.remotes.get(remotename, False) %}

    {%- for name, image in images.items() %}

    {%- if 'source' in image and 'remote' in image['source'] %}
      {%- set source_remote = datamap.remotes.get(image['source']['remote']) %}
      {%- set _ = image['source'].update(source_remote) %}
    {%- endif %}

lxd_image_{{ remotename }}_{{ name }}:
  lxd_image:
        {%- if image.get('absent', False) %}
    - absent
        {%- else %}
    - present
        {%- endif %}
        {%- if 'name' in image %}
    - name: "{{ image['name'] }}"
        {%- else %}
    - name: "{{ name }}"
        {%- endif %}
        {%- for k in ('source', 'aliases', 'public', 'auto_update',) %}
          {%- if k in image %}
    - {{ k }}: {{ image[k] }}
          {%- endif %}
        {%- endfor %}
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
        {%- if 'opts' in image %}
    {{ sls_block(image.opts )}}
        {%- endif %}
    {%- endfor %}
{%- endfor %}
