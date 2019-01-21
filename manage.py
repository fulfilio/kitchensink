#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from flask_script import Manager, Server, Shell
import requests
import fulfil_client

from kitchensink.app import create_app


app = create_app()
manager = Manager(app)


@manager.command
def reassign_all_shipments():
    from .kitchensink.extensions import fulfil

    Shipment = fulfil.model('stock.shipment.out')

    shipments = list(
        Shipment.search_read_all(
            [('state', 'in', ('waiting', 'assigned'))],
            None, None
        )
    )
    for shipment in shipments:
        print(f"Making shimpent { shipment['id'] } wait")
        Shipment.wait([shipment['id']])
    process_waiting_shipments()


@manager.command
def process_waiting_shipments():
    from .kitchensink.extensions import fulfil

    Shipment = fulfil.model('stock.shipment.out')
    shipments = list(
        Shipment.search_read_all(
            [('state', '=', 'waiting')],
            [('sale_date', 'ASC'), ('priority', 'ASC')],
            ['sale_date', 'priority']
        )
    )
    results = []
    for shipment in shipments:
        print(shipment)
        count = 5   # Initial count
        while count:
            if count < 5:
                print("Retrying")
            try:
                results.append(
                    Shipment.assign_try([shipment['id']])
                )
            except fulfil_client.client.ServerError:
                count -= 1  # Decrement the count, try again
            else:
                break
        else:
            print("Yuck! This one is pretty bad", shipment)

    requests.post(
        os.environ['SLACK_WEBHOOK_URL'],
        json={
            'text': 'Tried to assign Shipments',
            'attachments': [{
                'title': 'Assigning Shipments',
                'thumb_url': 'http://example.com/path/to/thumb.png',
                'fields': [{
                    'title': 'Attempted',
                    'value': str(len(shipments)),
                }, {
                    'title': 'Assigned',
                    'value': str(len([r for r in results if r])),
                    'short': True,
                }, {
                    'title': 'Still Waiting',
                    'value': str(len([r for r in results if not r])),
                    'short': True,
                }]
            }]
        }
    )


manager.add_command('server', Server())
manager.add_command('shell', Shell())


if __name__ == '__main__':
    manager.run()
