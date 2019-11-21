# Copyright (c) 2018, Palo Alto Networks
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# Authors: Adam Baumeister, Nathan Embery

import logging
from pathlib import Path
from typing import List

import skilletlib
from skilletlib.panoply import Panoply
from skilletlib.snippet.panos import PanosSnippet
from .base import Skillet
from ..exceptions import SkilletLoaderException
from ..exceptions import SkilletValidationException

logger = logging.getLogger(__name__)


class PanosSkillet(Skillet):
    panoply = None

    def __init__(self, metadata: dict, panoply: Panoply = None):
        """
        Initialize a new PanosSkillet class.
        :param metadata: loaded dict from the Skillet YAML file
        :param panoply: optional panoply object. This can be passed in if the outer application scope has
        already been in contact with the device for things like checking auth, etc. If not passed in,
        you can invoke it in 'online' mode by passing in 'panos_username', 'panos_password' and 'panos_hostname' in the
        context. Otherwise, 'offline' mode requires a 'config' to be passed in via the context.
        """
        if panoply is not None:
            self.panoply = panoply
        super().__init__(metadata)

    def initialize_context(self, initial_context: dict) -> dict:
        """
        In this panos case, we want to stash the current configuration of the panos device in question in the
        context, check for online mode, offline mode, or an existing panoply object
        :param initial_context: dict to use to initialize the context
        :return: context with additional initialized items
        """

        # if the panoply object was not passed in via __init__, then check for online vs offline mode here
        online_required_fields = {'panos_hostname', 'panos_username', 'panos_password'}
        # which set of fields we find in the contexst will determine online vs offline mode
        offline_required_fields = {'config'}

        context = dict()
        context.update(initial_context)

        if self.panoply is None:
            if not online_required_fields.issubset(initial_context) \
                    and not offline_required_fields.issubset(initial_context):
                raise SkilletValidationException('Required fields for panos skillet not found in context!')

            if online_required_fields.issubset(initial_context):
                hostname = initial_context.get('panos_hostname', None)
                username = initial_context.get('panos_username', None)
                password = initial_context.get('panos_password', None)
                port = initial_context.get('panos_port', '443')
                self.panoply = skilletlib.panoply.Panoply(hostname=hostname, api_username=username, api_password=password,
                                                          api_port=port)

                context['config'] = self.panoply.get_configuration()
            else:
                logger.info(f'offline mode detected for {__name__}')
                # init panoply in offline mode
                self.panoply = skilletlib.panoply.Panoply()
        else:
            # we were passed in a panoply object already, check if we are connected and grab the configuration if so
            if self.panoply.connected:
                context['config'] = self.panoply.get_configuration()
            else:
                raise SkilletLoaderException('Could not get configuration as Panoply is not connected!')

        return context

    def get_snippets(self) -> List[PanosSnippet]:
        snippet_path = Path(self.path)
        snippet_list = list()
        for snippet_def in self.snippet_stack:
            if 'cmd' not in snippet_def or snippet_def['cmd'] == 'set':
                snippet_def = self.load_element(snippet_def, snippet_path)

            snippet = PanosSnippet(snippet_def, self.panoply)
            snippet_list.append(snippet)

        return snippet_list

    @staticmethod
    def load_element(snippet_def: dict, snippet_path: Path) -> dict:
        if 'element' not in snippet_def or snippet_def['element'] == '':
            if 'file' not in snippet_def:
                raise SkilletLoaderException(
                    'YAMLError: Could not parse metadata file for snippet %s' % snippet_def['name'])
            snippet_file = snippet_path.joinpath(snippet_def['file']).resolve()
            if snippet_file.exists():
                with snippet_file.open() as sf:
                    snippet_def['element'] = sf.read()
            else:
                # raise SkilletLoaderException('Could not load "file" attribute!')
                logger.error(f'Could not load the referenced file for {snippet_def["name"]}')

        return snippet_def
