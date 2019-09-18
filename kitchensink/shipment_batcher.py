from collections import defaultdict, Counter
from itertools import groupby
from more_itertools import chunked
from .extensions import fulfil

BATCH_SIZE = 20


def create_optimal_batches_from_orders(order_numbers):
    """
    Get shipments from order numbers
    """
    Shipment = fulfil.model('stock.shipment.out')
    Sale = fulfil.model('sale.sale')

    orders = list(Sale.search_read_all([
        ('reference', 'in', order_numbers)
    ], None, ['shipments']))
    shipment_ids = []
    print("Found {} orders".format(len(orders)))
    for order in orders:
        shipment_ids.extend(order['shipments'])
    print("Found {} shipments".format(len(shipment_ids)))
    for chunk in chunked(shipment_ids, 10):
        print("assigning shipments")
        Shipment.assign(chunk)
    shipments = Shipment.serialize(shipment_ids)
    create_optimal_batches(shipments)


def create_optimal_batches(shipments=None, dry=False):
    """
    Given a collection of shipments, create
    optimal batches.
    """
    ShipmentBatch = fulfil.model('stock.shipment.out.batch')

    warehouse_id = 18
    if not shipments:
        shipments = _get_shipments(warehouse_id)

    singles = [s for s in shipments if len(s['inventory_moves']) == 1]
    print("Single line shipments: {}".format(len(singles)))

    _identify_singles_batch(singles)
    _identify_multi_batch(
        [s for s in shipments if len(s['inventory_moves']) > 1],
    )

    _print_batches(shipments)

    if dry:
        return
    today = fulfil.today()
    key = lambda s: s.get('batch_name', '*Unbatched')   # noqa
    for batch_name, b_shipments in groupby(sorted(shipments, key=key), key=key):
        batch_ids = ShipmentBatch.create([{
            'name': '{}/{}'.format(today.isoformat(), batch_name,),
            'warehouse': warehouse_id,
            'shipments': [('add', [s['id'] for s in b_shipments])]
        }])
        ShipmentBatch.open(batch_ids)


def _print_batches(shipments):
    from terminaltables import AsciiTable

    shipment_counter = Counter()
    item_counter = Counter()
    key = lambda s: s.get('batch_name', '*Unbatched')   # noqa
    for batch_name, b_shipments in groupby(sorted(shipments, key=key), key=key):
        b_shipments = list(b_shipments)
        shipment_counter[batch_name] += len(b_shipments)
        for shipment in b_shipments:
            item_counter[batch_name] += len(shipment['outgoing_moves'])

    data = [
        ['Batch Name', '# of Shipments', '# of items']
    ]
    for batch_name in shipment_counter:
        data.append([
            batch_name, shipment_counter[batch_name], item_counter[batch_name]
        ])
    print(AsciiTable(data).table)


def _get_shipments(warehouse_id):
    """
    Return shipments that qualify to be batched
    """
    Shipment = fulfil.model('stock.shipment.out')

    shipment_ids = Shipment.search([
        ('warehouse', '=', warehouse_id),
        ('state', '=', 'assigned'),
        # ('state', '=', 'waiting'),
        ('shipping_batch', '=', None),
        # ('planned_date', '=', '2019-09-12'),
        ('carrier', '!=', None),
    ], None, 5000)
    shipment_data = []
    print('Collecting shipments')
    per_chunk = 250
    for index, chunk in enumerate(chunked(shipment_ids, per_chunk)):
        print('{} --> {}'.format(
            (index * per_chunk),
            ((index - 1) * per_chunk)
        ))
        shipment_data.extend(Shipment.serialize(chunk))
    return shipment_data


def _identify_multi_batch(shipments, batch_size=BATCH_SIZE):
    """
    Given a collection of multi line shipments
    create batches of Batch size.
    """
    key = lambda shipment: shipment['inventory_moves'][0]['warehouse_location_name'] or 'Z'
    for index, chunk in \
            enumerate(chunked(sorted(shipments, key=key), BATCH_SIZE), 1):
        _set_batch(chunk, "Multi-Item Batch {:0>3}".format(
            index,
        ))


def _identify_singles_batch(shipments, batch_size=BATCH_SIZE):
    """
    Create singles batches with specific items
    """
    key = lambda s: s['inventory_moves'][0]['product']['id']     # noqa
    unbatched = defaultdict(list)
    for product, p_shipments in groupby(sorted(shipments, key=key), key=key):
        p_shipments = list(p_shipments)
        move = p_shipments[0]['inventory_moves'][0]
        if len(p_shipments) > batch_size:
            _set_batch(p_shipments, "Single line item: {}".format(
               move['product']['code']
            ))
        else:
            unbatched[move['warehouse_location_name'] or 'Z-NO-LOC'].extend(
                p_shipments
            )

    # Sort all the unbatched shipments by location
    ordered_unbatched = []
    for location in sorted(unbatched.keys()):
        ordered_unbatched.extend(unbatched[location])

    # Now create a batch for them in buckets of batch size
    for index, chunk in enumerate(chunked(ordered_unbatched, batch_size), 1):
        _set_batch(chunk, "Assorted Single Item Batch {:0>3}".format(index))


def _set_batch(shipments, name):
    for shipment in shipments:
        if shipment.get('batch_name'):
            raise "Batch {} already exists for shipment {}".format(
                shipment['batch_name'],
                shipment['number']
            )
        shipment['batch_name'] = name
