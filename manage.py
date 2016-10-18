#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask_script import Manager, Server, Shell

from kitchensink.app import create_app


app = create_app()
manager = Manager(app)


manager.add_command('server', Server())
manager.add_command('shell', Shell())


if __name__ == '__main__':
    manager.run()
