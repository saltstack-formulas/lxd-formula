#!jinja|yaml
# -*- coding: utf-8 -*-
# vi: set ft=yaml.jinja :

{% from "lxd/map.jinja" import datamap, sls_block with context %}

{% if datamap.python.use_pip or datamap.python.use_pip_formula %}
include:
  - pip
  - pip.extensions
{% endif %}

{% if datamap.python.use_pip or datamap.python.use_pip_formula %}
lxd_python_pip:
  pkg:
    - {{ datamap.python.pip_package.action }}
    {{ sls_block(datamap.python.pip_package.opts )}}
    - pkgs: {{ datamap.lookup.python.pip_packages }}
{% endif %}

lxd_python:
  pkg:
    {% if datamap.python.use_pip or datamap.python.use_pip_formula %}
    - removed
    {% else %}
    - {{ datamap.python.package.action }}
    {% endif %}
    {{ sls_block(datamap.python.package.opts )}}
    - pkgs: {{ datamap.lookup.python.packages }}
    - reload_modules: True

  {% if datamap.python.use_pip or datamap.python.use_pip_formula %}
  pip:
    - {{ datamap.python.pip_package.action }}
    {% if datamap.python.get('pip_version') %}
    - name: pylxd=={{ datamap.python.pip_version }}
    {% else %}
    - name: pylxd
    {% endif %}
    - reload_modules: True
    - require:
      - pkg: lxd_python_pip
  {% endif %}
