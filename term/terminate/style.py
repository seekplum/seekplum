#!/usr/bin/env python
# -*- coding: utf-8 -*-

from prompt_toolkit.styles import style_from_dict
from pygments.token import Token

QSTYLE = styles = style_from_dict({
    # User input.
    Token: '#ff0066',

    # Prompt.
    Token.Username: '#0fc0fc',
    Token.At: '#00aa00',
    Token.Colon: '#00aa00',
    Token.Pound: '#00aa00',
    Token.Host: '#1975ff',
    Token.Path: '#ofc0fc',
    Token.Toolbar: '#000000',
})

QSTYLE_NOCOLOR = style_from_dict({
    Token.Toolbar: '#000000',
})
