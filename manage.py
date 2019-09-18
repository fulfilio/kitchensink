#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from flask_script import Manager, Server, Shell
import requests
import fulfil_client
import unicodecsv as csv

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
        print("Making shimpent { shipment['id'] } wait")
        Shipment.wait([shipment['id']])
    process_waiting_shipments()


@manager.command
def get_stats():
    from kitchensink.extensions import fulfil
    Shipment = fulfil.model('stock.shipment.out')
    warehouse_id = 18
    domain = [
        ('warehouse', '=', warehouse_id),
        ('state', '=', 'assigned'),
        # ('state', '=', 'waiting'),
        ('shipping_batch', '=', None),
        # ('planned_date', '=', '2019-09-12'),
        ('carrier', '!=', None),
    ]
    unbatched_shipment_count = Shipment.search_count(domain)
    print("Unbatched: {}".format(unbatched_shipment_count))
    domain.append(('priority', 'in', ['0', '1']))
    priority_count = Shipment.search_count(domain)
    print("of which {} are high priority".format(priority_count))


@manager.command
def create_batches(dry=False):
    from kitchensink.extensions import fulfil
    from kitchensink.shipment_batcher import create_optimal_batches
    create_optimal_batches(dry=dry)


@manager.command
def create_batch_shipstation(filename):
    from kitchensink.extensions import fulfil
    from kitchensink.shipment_batcher import create_optimal_batches_from_orders
    with open(filename, 'rb') as f:
        data = list(csv.DictReader(f))
        order_numbers = ['#' + l['Order - Number'] for l in data]
    create_optimal_batches_from_orders(order_numbers)


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
