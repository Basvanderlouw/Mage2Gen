# A Magento 2 module generator library
# Copyright (C) 2018 Lewis Voncken
#
# This file is part of Mage2Gen.
#
# Mage2Gen is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import os
from .. import Module, Phpclass, Phpmethod, Xmlnode, Snippet, SnippetParam, GraphQlSchema, GraphQlObjectType, \
    GraphQlObjectItem, StaticFile
from ..utils import upperfirst, lowerfirst


class GraphQlUrlLocatorSnippet(Snippet):
    snippet_label = 'GraphQl Url Locator'

    description = """

	"""

    def add(self, pagetype, entity_model_class=None, id_parameter=None, frontname=None, section=None, action=None, extra_params=None):
        splitted_pagetype = [upperfirst(word[0]) + word[1:] for word in pagetype.split('_')]
        pagetype_name = "".join(splitted_pagetype)
        classname = 'Model\\Resolver\\UrlRewrite\\{}UrlLocator'.format(pagetype_name)


        urllocator_construct_params = []
        urllocator_attributes = []
        urllocator_construct_body = ""
        urllocator_construct_docstring = []
        if entity_model_class:
            entity_model_factory_class = "\{}Factory".format(entity_model_class)
            entity_model_factory_class_variable = "{}".format(
                lowerfirst(entity_model_factory_class.split('\\')[-1]))
            urllocator_construct_params = [
                "{} ${}".format(entity_model_factory_class, entity_model_factory_class_variable)
            ]
            urllocator_construct_body = "$this->{entity_model_factory_class_variable} = ${entity_model_factory_class_variable};".format(
                entity_model_factory_class_variable=entity_model_factory_class_variable
            )
            urllocator_construct_docstring = [
                '@param {} ${}'.format(entity_model_factory_class, entity_model_factory_class_variable)
            ]
            urllocator_attributes = [
                'private ${};'.format(entity_model_factory_class_variable)
            ]

        urllocator = Phpclass(
            classname,
            attributes=urllocator_attributes
        )

        urllocator.add_method(
            Phpmethod(
                '__construct',
                params=urllocator_construct_params,
                body=urllocator_construct_body,
                docstring=urllocator_construct_docstring
            )
        )

        locateurlbody_method="return null;"
        if entity_model_class:
            urllocator.add_method(
                Phpmethod(
                    'getIdByUrlKey',
                    params=['$urlKey'],
                    body="""
/** @var \{entity_model_class} ${entity_model_class_variable} */
${entity_model_class_variable} = $this->{entity_model_factory_class_variable}->create();
${entity_model_class_variable}->load($urlKey, 'url_key');
return ${entity_model_class_variable}->getId();""".format(entity_model_class=entity_model_class, entity_model_factory_class_variable=entity_model_factory_class_variable, entity_model_class_variable=entity_model_factory_class_variable.replace('Factory', '')),
                    docstring=[
                        'Retrieves entity ID by URL-Key',
                        '',
                        '@param string $urlKey',
                        '@return int|null',
                    ]
                )
            )
            locateurlbody_method = """
if ($id = $this->getIdByUrlKey($urlKey)) {{
    return [
        'id' => $id,
        'canonical_url' => "{frontname}/{section}/{action}/{id_parameter}/{{$id}}",
        'relative_url' => "{frontname}/{section}/{action}/{id_parameter}/{{$id}}",
        'type' => {pagetype}
    ];
}}
return null;""".format(frontname=frontname,
                       section=section,
                       action=action,
                       id_parameter=id_parameter,
                       pagetype=pagetype)

        urllocator.add_method(
            Phpmethod(
                'locateUrl',
                params=['$urlKey'],
                body=locateurlbody_method,
                docstring=[
                    '@inheritdoc',
                ]
            )
        )

        
        self.add_class(urllocator)

        di_xml = Xmlnode('config', attributes={
            'xsi:noNamespaceSchemaLocation': "urn:magento:framework:ObjectManager/etc/config.xsd"}, nodes=[
            Xmlnode('type', attributes={'name': 'Magento\\UrlRewriteGraphQl\\Model\\Resolver\\UrlRewrite\CustomUrlLocator'},
                    nodes=[
                        Xmlnode('arguments', attributes={'xsi:type': 'array'}, nodes=[
                            Xmlnode('argument', attributes={'name': 'urlLocators'}, nodes=[
                                Xmlnode('item', attributes={'name': "{}UrlLocator".format(lowerfirst(pagetype_name)), 'xsi:type': 'object'},
                                        node_text=urllocator.class_namespace)
                            ])
                        ])
                    ])
        ])
        self.add_xml('etc/di.xml', di_xml)

        sequence_modules = [
            Xmlnode('module', attributes={'name': 'Magento_GraphQl'}),
            Xmlnode('module', attributes={'name': 'Magento_UrlRewriteGraphQl'}),
        ]

        etc_module = Xmlnode('config', attributes={
            'xsi:noNamespaceSchemaLocation': "urn:magento:framework:Module/etc/module.xsd"}, nodes=[
            Xmlnode('module', attributes={'name': self.module_name}, nodes=[
                Xmlnode('sequence', attributes={}, nodes=sequence_modules)
            ])
        ])
        self.add_xml('etc/module.xml', etc_module)


    @classmethod
    def params(cls):
        return [
            SnippetParam(
                name='pagetype',
                required=True,
                description='Example: blog_post_page, blog_category_page or home_page',
                regex_validator=r'^[a-zA-Z]{1}\w+$',
                error_message='Only alphanumeric and underscore characters are allowed, and need to start with a alphabetic character.'),
            SnippetParam(
                name='entity_model_class',
                required=False,
                description='Example: Mage2gen\Blog\Model\Blog',
                regex_validator=r'^[\w\\]+$',
                error_message='Only alphanumeric, underscore and backslash characters are allowed'),
            SnippetParam(name='id_parameter', required=True, default='id',
                         regex_validator=r'^[a-z]{1}\w+$',
                         depend={'entity_model_class': r'(.+)$'},
                         error_message='Only lowercase alphanumeric and underscore characters are allowed, and need to start with a alphabetic character.',
                         repeat=True),
            SnippetParam(name='frontname', required=True, description='Example: blog',
                         regex_validator=r'^[a-z]{1}\w+$',
                         depend={'entity_model_class': r'(.+)$'},
                         error_message='Only lowercase alphanumeric and underscore characters are allowed, and need to start with a alphabetic character.',
                         repeat=True),
            SnippetParam(name='section', required=True, default='index',
                         depend={'entity_model_class': r'(.+)$'},
                         regex_validator=r'^[a-z]{1}\w+$',
                         error_message='Only lowercase alphanumeric and underscore characters are allowed, and need to start with a alphabetic character.',
                         repeat=True),
            SnippetParam(name='action', required=True, default='index',
                         depend={'entity_model_class': r'(.+)$'},
                         regex_validator=r'^[a-z]{1}\w+$',
                         error_message='Only lowercase alphanumeric and underscore characters are allowed, and need to start with a alphabetic character.'),
        ]


