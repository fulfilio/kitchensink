#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask_script import Manager, Server, Shell

from kitchensink.app import create_app


app = create_app()
manager = Manager(app)


@manager.command
def reassign_all_shipments():
    from kitchensink.extensions import fulfil

    Shipment = fulfil.model('stock.shipment.out')

    shipments = list(
        Shipment.search_read_all(
            [('state', 'in', ('waiting', 'assigned'))],
            None, None
        )
    )
    for shipment in shipments:
        print "Making shimpent %s wait" % shipment['id']
        Shipment.wait([shipment['id']])
    process_waiting_shipments()



@manager.command
def process_waiting_shipments():
    from kitchensink.extensions import fulfil

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
        print shipment
        count = 5   # Initial count
        while count:
            if count < 5:
                print "Retrying"
            try:
                results.append(
                    Shipment.assign_try([shipment['id']])
                )
            except fulfil_client.client.ServerError:
                count -= 1  # Decrement the count, try again
            else:
                break
        else:
            print "Yuck! This one is pretty bad", shipment

    requests.post(
        os.environ['SLACK_WEBHOOK_URL'],
        json={
            'text': 'Tried to assign Mejuri Shipments',
            'attachments': [{
                'title': 'Assigning Shipments',
                'thumb_url': 'https://dto508s2j2p46.cloudfront.net/assets/mejuri_label-86c1982b0d84c5017186e435ff666485.png',
                'fields': [{
                    'title': 'Attempted',
                    'value': str(len(shipments)),
                }, {
                    'title': 'Assigned',
                    'value': str(len(filter(lambda r: r, results))),
                    'short': True,
                }, {
                    'title': 'Still Waiting',
                    'value': str(len(filter(lambda r: not r, results))),
                    'short': True,
                }]
            }]
        }
    )

manager.add_command('server', Server())
manager.add_command('shell', Shell())


if __name__ == '__main__':
    manager.run()
