#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from .models import VirtualFolderTreeItem


def make_vfolder_treeitem_dict(vfolder_treeitem):
    return {
        'href_all': vfolder_treeitem.get_translate_url(),
        'href_todo': vfolder_treeitem.get_translate_url(
            state='incomplete'),
        'href_sugg': vfolder_treeitem.get_translate_url(
            state='suggestions'),
        'href_critical': vfolder_treeitem.get_critical_url(),
        'title': vfolder_treeitem.vfolder.name,
        'code': vfolder_treeitem.code,
        'priority': vfolder_treeitem.vfolder.priority,
        'is_grayed': not vfolder_treeitem.is_visible,
        'stats': vfolder_treeitem.get_stats(
            include_children=False),
        'icon': 'vfolder'}


def extract_vfolder_from_path(request_path):
    """
    Matches request_path to a VirtualFolderTreeItem pootle_path

    If a match is found, the associated VirtualFolder and Directory.pootle_path
    are returned. Otherwise the original request_path is returned.

    :param request_path: a path that may contain a virtual folder
    :return: (`VirtualFolder`, path)
    """
    if not (request_path.count('/') > 3 and request_path.endswith('/')):
        return None, request_path

    try:
        vfti = VirtualFolderTreeItem.objects.get(pootle_path=request_path)
    except VirtualFolderTreeItem.DoesNotExist:
        return None, request_path
    else:
        return vfti.vfolder, vfti.directory.pootle_path
