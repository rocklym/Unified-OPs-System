# -*- coding: UTF-8 -*-
import json
from os import path
from sys import argv

from flask import redirect, render_template, request, url_for
from werkzeug.wrappers import Response
from flask_login import current_user
from flask_restful import Resource

from app.auth.privileged import CheckPrivilege
from app.models import MethodType, Server, SystemType, TradeSystem
from restful.protocol import RestProtocol


class UIDataApi(Resource):
    def get(self, name):
        if hasattr(self, name):
            response = getattr(self, name)()
            if isinstance(response, Response):
                return response
            else:
                return RestProtocol(response)
        else:
            return RestProtocol(message='resource not found.'), 404

    def inventory(self):
        svrs = Server.query.filter(Server.disabled == False).all()
        rtn = [{
            'svr_name': svr.name,
            'svr_id': svr.id,
            'svr_uuid': svr.uuid,
            'svr_desc': svr.description,
            'svr_ip': svr.ip,
            'svr_platform': svr.platform and svr.platform.name,
            'systems': [{
                'sys_name': sys.name,
                'sys_id': sys.id,
                'sys_uuid': sys.uuid,
                'sys_desc': sys.description,
                'sys_type': sys.type and sys.type.name,
                'sys_ip': sys.ip,
                'sys_ver': sys.version,
                'processes': [{
                    'proc_name': proc.name,
                    'proc_id': proc.id,
                    'proc_uuid': proc.uuid,
                    'proc_desc': proc.description,
                    'proc_ver': proc.version
                } for proc in svr.processes.all() if proc.sys_id == sys.id]
            } for sys in svr.systems.all()]
        } for svr in svrs]
        return rtn

    def sideBarCtrl(self):
        systems = TradeSystem.query.filter(
            TradeSystem.parent_sys_id == None,
            TradeSystem.disabled == False
        ).all()
        rtn = []
        # privileged = CheckPrivilege(current_user, '/api/emerge_ops', MethodType.Authorize)
        for sys in systems:
            system = {
                'id': sys.id,
                'icon': 'am-icon-table',
                'name': sys.name,
                'desc': sys.description,
                'isSecond': len(sys.operation_groups.all()) > 0,
                'isShow': False,
                'Url': '#statics/{}'.format(sys.id),
                'secondName': [
                    {
                        'id': group.id,
                        'name': group.name,
                        'trigger_time': group.trigger_time,
                        'Url': '#system/{}/op_group/{}'.format(sys.id, group.id),
                        'is_emerge': group.is_emergency
                    } for group in sys.operation_groups]
            }
            # if privileged:
            system['emerge_ops'] = {
                'name': u'全部操作节点',
                'Url': '#system/{}/operate-books'.format(sys.id)
            }
            rtn.append(system)
        return rtn

    def map(self):
        try:
            name = request.values['name']
        except KeyError:
            return {
                'message': 'no name specified.'
            }, 404
        uri = url_for('static', filename='json/map/{}.json'.format(name))
        base_path = path.dirname(argv[0])
        abs_path = path.join(base_path, 'app{}'.format(uri))
        if path.isfile(abs_path):
            return redirect(uri)
        else:
            return {
                'message': 'no map data for {}.'.format(name)
            }, 404

    def idc(self):
        return [
            {'name': u'上海', 'value': [121.48, 31.22, 20]},
            {'name': u'大连', 'value': [121.46, 39.03, 15]},
            {'name': u'郑州', 'value': [113.65, 34.76, 10]},
        ]

    def relation(self):
        root_systems = TradeSystem.query.filter(
            TradeSystem.parent_system == None
        ).all()
        series = {}
        legend = ['System', 'Process', 'Server']

        def find_nodes(sys, nodes, relations):
            for proc in sys.processes:
                nodes.add(json.dumps({
                    'name': proc.uuid,
                    'value': [proc.name, "{} {}".format(proc.exec_file, proc.param or '')],
                    'category': 'Process',
                    'label': {
                        'normal': {
                            'show': False
                        }
                    }
                }))
                nodes.add(json.dumps({
                    'name': proc.server.uuid,
                    'value': [proc.server.name, proc.server.ip],
                    'category': 'Server',
                    'symbolSize': 30
                }))
                relations.add(json.dumps({
                    'source': proc.uuid,
                    'target': sys.uuid
                }))
                relations.add(json.dumps({
                    'source': proc.uuid,
                    'target': proc.server.uuid
                }))
                relations.add(json.dumps({
                    'source': sys.uuid,
                    'target': proc.server.uuid,
                    'value': len([x for x in sys.processes if x.server == proc.server]) * 15
                }))
            for child in sys.child_systems:
                nodes.add(json.dumps({
                    'name': child.uuid,
                    'value': [child.name, child.ip],
                    'category': 'System',
                    'symbolSize': (len(child.child_systems) + 1) * 30
                }))
                relations.add(json.dumps({
                    'source': child.uuid,
                    'target': sys.uuid
                }))
                find_nodes(child, nodes, relations)

        for root in root_systems:
            legend.append(root.name)
            if not series.has_key(root.name):
                series[root.name] = {}
                series[root.name]['nodes'] = set()
                series[root.name]['relations'] = set()
            series[root.name]['nodes'].add(json.dumps({
                'name': root.uuid,
                'value': [root.name, root.ip],
                'category': 'System',
                'symbolSize': (len(root.child_systems) + 1) * 15
            }))
            find_nodes(
                root,
                series[root.name]['nodes'],
                series[root.name]['relations']
            )

        option = {
            'backgroundColor': '#fff',
            'title': {
                'text': "系统关系图",
                'top': "top",
                'left': "center"
            },
            'tooltip': {},
            'legend': [{
                'tooltip': {
                    'show': True
                },
                'selectedMode': 'false',
                'bottom': 20,
                'data': legend
            }],
            'toolbox': {
                'show': True,
                'feature': {
                    'dataView': {'show': True, 'readOnly': True},
                    'restore': {'show': True}
                }
            },
            'animationDuration': 3000,
            'animationEasingUpdate': 'quinticInOut',
            'series': []
        }
        for k, v in series.iteritems():
            option['series'].append({
                'name': k,
                'type': 'graph',
                'layout': 'force',
                'force': {
                    'repulsion': [50, 80],
                    'gravity': 0.1,
                    'edgeLength': [100, 200],
                },
                'draggable': True,
                'data': [json.loads(x) for x in v['nodes']],
                'links': [json.loads(y) for y in v['relations']],
                'categories': [
                    {'name': 'System'},
                    {'name': 'Process'},
                    {'name': 'Server'}
                ],
                'label': {
                    'normal': {
                        'show': True,
                        'formatter': '{c0}',
                        'position': 'top'
                    }
                },
                'focusNodeAdjacency': True,
                'roam': True,
                'lineStyle': {
                    'normal': {
                        'color': 'source',
                        'curveness': 0.3,
                        'type': "solid"
                    }
                }
            })
        return option
