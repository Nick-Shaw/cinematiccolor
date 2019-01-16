# -*- coding: utf-8 -*-
"""
Invoke - Tasks
==============
"""

from __future__ import print_function, unicode_literals

import glob
import os
import subprocess
from invoke import task
from invoke.exceptions import Failure
from itertools import chain
from textwrap import TextWrapper

import html

__author__ = 'Cinematic Color Authors'
__copyright__ = 'Copyright (C) 2019 - Cinematic Color Authors'
__license__ = 'New BSD License - http://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Cinematic Color Authors'
__email__ = 'ves-tech-color@googlegroups.com'
__status__ = 'Production'

__all__ = [
    'ROOT_DOCUMENT_NAME', 'ROOT_HTML_DIRECTORY_NAME', 'message_box', 'clean',
    'formatting', 'build_pdf', 'build_html'
]

ROOT_DOCUMENT_NAME = 'cinematic-color.tex'

ROOT_HTML_DIRECTORY_NAME = 'cinematic-color'


def message_box(message, width=79, padding=3, print_callable=print):
    """
    Prints a message inside a box.

    Parameters
    ----------
    message : unicode
        Message to print.
    width : int, optional
        Message box width.
    padding : unicode, optional
        Padding on each sides of the message.
    print_callable : callable, optional
        Callable used to print the message box.

    Returns
    -------
    bool
        Definition success.

    Examples
    --------
    >>> message = ('Lorem ipsum dolor sit amet, consectetur adipiscing elit, '
    ...     'sed do eiusmod tempor incididunt ut labore et dolore magna '
    ...     'aliqua.')
    >>> message_box(message, width=75)
    ===========================================================================
    *                                                                         *
    *   Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do       *
    *   eiusmod tempor incididunt ut labore et dolore magna aliqua.           *
    *                                                                         *
    ===========================================================================
    True
    >>> message_box(message, width=60)
    ============================================================
    *                                                          *
    *   Lorem ipsum dolor sit amet, consectetur adipiscing     *
    *   elit, sed do eiusmod tempor incididunt ut labore et    *
    *   dolore magna aliqua.                                   *
    *                                                          *
    ============================================================
    True
    >>> message_box(message, width=75, padding=16)
    ===========================================================================
    *                                                                         *
    *                Lorem ipsum dolor sit amet, consectetur                  *
    *                adipiscing elit, sed do eiusmod tempor                   *
    *                incididunt ut labore et dolore magna                     *
    *                aliqua.                                                  *
    *                                                                         *
    ===========================================================================
    True
    """

    ideal_width = width - padding * 2 - 2

    def inner(text):
        """
        Formats and pads inner text for the message box.
        """

        return '*{0}{1}{2}{0}*'.format(
            ' ' * padding, text, (' ' * (width - len(text) - padding * 2 - 2)))

    print_callable('=' * width)
    print_callable(inner(''))

    wrapper = TextWrapper(
        width=ideal_width, break_long_words=False, replace_whitespace=False)

    lines = [wrapper.wrap(line) for line in message.split("\n")]
    lines = [' ' if len(line) == 0 else line for line in lines]
    for line in chain(*lines):
        print_callable(inner(line.expandtabs()))

    print_callable(inner(''))
    print_callable('=' * width)

    return True


@task
def clean(ctx, bytecode=False):
    """
    Cleans the project.

    Parameters
    ----------
    bytecode : bool, optional
        Whether to clean the bytecode files, e.g. *.pyc* files.

    Returns
    -------
    bool
        Task success.
    """

    message_box('Cleaning project...')

    patterns = [
        '*.aux',
        '*.dvi',
        '*.idv',
        '*.fdb_latexmk',
        '*.fls',
        '*.lg',
        '*.log',
        '*.pdf',
        '*.synctex.gz',
        '*.toc',
        'cinematic-color/',
    ]

    if bytecode:
        patterns.append('**/*.pyc')

    for pattern in patterns:
        ctx.run("rm -rf {}".format(pattern))


@task
def formatting(ctx, yapf=False):
    """
    Formats the codebase with *Yapf*.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.
    yapf : bool, optional
        Whether to format the codebase with *Yapf*.

    Returns
    -------
    bool
        Task success.
    """

    if yapf:
        message_box('Formatting codebase with "Yapf"...')
        ctx.run('yapf -p -i -r .')


@task
def build_pdf(ctx):
    """
    Builds the *PDF*.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.

    Returns
    -------
    bool
        Task success.
    """

    message_box('Building "PDF"...')

    ctx.run(
        'latex -interaction=nonstopmode {0}'.format(ROOT_DOCUMENT_NAME),
        warn=True)
    ctx.run('pdflatex -interaction=nonstopmode {0}'.format(ROOT_DOCUMENT_NAME))


@task
def build_html(ctx, latex2html=True, copy_assets=True, process_html=True):
    """
    Builds the *HTML* website.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.
    latex2html : bool
        Whether to perform *HTML* conversion.
    copy_assets : bool
        Whether to copy the assets.
    process_html : bool
        Whether to process the *HTML* files.

    Returns
    -------
    bool
        Task success.
    """

    message_box('Building "HTML" website...')

    if latex2html:
        ctx.run('latex2html '
                '-no_info '
                '-long_titles=255 '
                '-no_top_navigation '
                '-bottom_navigation '
                '{0}'.format(ROOT_DOCUMENT_NAME))

    if copy_assets:
        ctx.run('cp -r assets cinematic-color/')

    if process_html:
        message_box('Processing "HTML"...')

        index_file = os.path.join(ROOT_HTML_DIRECTORY_NAME, 'index.html')
        navigation = html.extract_navigation(index_file, ['Contents'])

        for html_file in glob.glob(
                os.path.join(ROOT_HTML_DIRECTORY_NAME, '*.html')):
            if 'index.html' in html_file:
                continue

            print('Processing "{0}" file...'.format(html_file))

            html.process_html(html_file, navigation)


@task(clean, build_html)
def gh_deploy(ctx):
    """
    Deploys the *HTML* website to *Github Pages*.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.

    Returns
    -------
    bool
        Task success.
    """

    message_box('Deploying "HTML" website to "Github Pages"...')

    result = ctx.run('git rev-parse HEAD', hide='both')
    sha = result.stdout.strip().split('\n')[0]
    ctx.run('ghp-import -m "Deploy {0} with \"ghp-import\"." -p {1}'.format(
        sha, ROOT_HTML_DIRECTORY_NAME))
