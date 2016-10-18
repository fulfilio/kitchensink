from itertools import chain, groupby

from flask import Blueprint, render_template
from .extensions import fulfil

shipment = Blueprint('shipment', __name__, url_prefix="/shipment")


Shipment = fulfil.model('stock.shipment.out')
StockMove = fulfil.model('stock.move')


@shipment.route('/items-waiting')
def waiting():
    """
    Waiting shipments
    """
    shipments = Shipment.search_read(
        [('state', 'in', ('assigned', 'waiting'))],
        None, None, None,
        [
            'inventory_moves', 'number',
            'customer.name', 'customer.categories', 'sale_date'
        ]
    )
    move_ids = list(
        chain(*map(lambda s: s['inventory_moves'], shipments))
    )

    # Convert shipments to a dictionary
    shipments = dict(zip(map(lambda s: s['id'], shipments), shipments))
    moves = StockMove.search_read(
        [('id', 'in', move_ids), ('state', '=', 'draft')],
        None, None, None,
        [
            'product', 'product.code', 'product.rec_name',
            'product.template.account_category',
            'product.template.account_category.rec_name',
            'quantity', 'quantity_available', 'state',
            'planned_date', 'shipment', 'children'
        ]
    )
    categories = {}
    for move in moves:
        move['shipment'] = shipments[
            int(move['shipment'].split(',')[-1])
        ]
        categories[move['product.template.account_category']] = move[
            'product.template.account_category.rec_name'
        ]

    moves_by_product = []
    for product, pmoves in groupby(
            sorted(moves, key=lambda m: (m['product'], m['planned_date'])),
            key=lambda m: m['product']):
        moves_by_product.append((product, list(pmoves)))

    return render_template(
        'waiting-shipments.html',
        moves_by_product=moves_by_product,
        categories=sorted(categories.items(), key=lambda item: item[1]),
    )

