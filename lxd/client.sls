#!jinja|yaml
# -*- coding: utf-8 -*-
# vi: set ft=yaml.jinja :

{% from "lxd/map.jinja" import datamap, sls_block with context %}

lxd_client:
  pkg:
    - {{ datamap.client.package.action }}
    {{ sls_block(datamap.client.package.opts )}}
    - pkgs: {{ datamap.lookup.client.packages }}
