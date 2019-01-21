from itertools import chain, groupby
import pandas as pd
from datetime import date, datetime

from flask_login import login_required
from flask import Blueprint, render_template, jsonify
from .extensions import fulfil

shipment = Blueprint('shipment', __name__, url_prefix="/shipment")
move = Blueprint('move', __name__, url_prefix="/move")


@move.route('/<int:move_id>/wait', methods=['POST'])
@login_required
def wait(move_id):
    StockMove = fulfil.model('stock.move')
    return jsonify({
        'success': StockMove.draft([move_id])
    })


@move.route('/<int:move_id>/assign', methods=['POST'])
@login_required
def assign(move_id):
    StockMove = fulfil.model('stock.move')
    return jsonify({
        'success': StockMove.assign([move_id])
    })


@shipment.route('/items-waiting')
@login_required
def waiting():
    """
    Waiting shipments
    """
    Shipment = fulfil.model('stock.shipment.out')
    StockMove = fulfil.model('stock.move')
    shipments = Shipment.search_read(
        [('state', 'in', ('assigned', 'waiting'))],
        None, None, None,
        [
            'inventory_moves', 'number',
            'customer.name', 'customer.categories', 'sale_date'
        ]
    )
    move_ids = list(
        chain(*[s['inventory_moves'] for s in shipments])
    )

    # Convert shipments to a dictionary
    shipments = dict(list(zip([s['id'] for s in shipments], shipments)))
    moves = StockMove.search_read(
        [('id', 'in', move_ids), ('state', 'in', ('draft', 'assigned'))],
        None, None, None,
        [
            'product', 'product.code', 'product.rec_name',
            'product.template.account_category',
            'product.template.account_category.rec_name',
            'quantity', 'quantity_available', 'state',
            'product.quantity_on_hand',
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
    today = date.today()
    for product, pmoves in groupby(
            sorted(moves, key=lambda m: (
                m['product'], m['planned_date'] or today)),
            key=lambda m: m['product']):
        moves_by_product.append((product, list(pmoves)))

    return render_template(
        'waiting-shipments.html',
        moves_by_product=moves_by_product,
        categories=sorted(list(categories.items()), key=lambda item: item[1]),
    )


@shipment.route('/waiting/region')
@shipment.route('/waiting/region/<country>')
@login_required
def waiting_by_region(country=None):
    """
    Waiting shipments by region
    """
    Shipment = fulfil.model('stock.shipment.out')
    domain = [('state', 'in', ('assigned', 'waiting'))]
    if country:
        domain.append(
            ('delivery_address.country.code', '=', country)
        )

    shipments = Shipment.search_read_all(
        domain,
        [('delivery_address.subdivision.code', 'ASC')],
        [
            'inventory_moves', 'number',
            'customer.name', 'customer.categories', 'sale_date',
            'delivery_address.country.code',
            'delivery_address.subdivision.code',
        ]
    )

    if country:
        key = lambda shipment: shipment['delivery_address.subdivision.code'] # noqa
    else:
        key = lambda shipment: shipment['delivery_address.country.code'] # noqa

    grouped_shipments = []
    google_array = [
        ['Region', 'Shipments'],
    ]
    for group, items in groupby(sorted(shipments, key=key), key=key):
        items = list(items)
        grouped_shipments.append((group, items))
        if group is not None:
            google_array.append(
                (group, len(items))
            )

    return render_template(
        'waiting-shipments-region.html',
        shipments=grouped_shipments,
        google_array=google_array,
        country=country,
    )


@shipment.route('/plan-by-product')
@login_required
def plan_by_product():
    """
    Show a plan by product
    """
    Shipment = fulfil.model('stock.shipment.out')
    StockMove = fulfil.model('stock.move')
    shipments = list(Shipment.search_read_all(
        [('state', 'in', ('assigned', 'waiting'))],
        None,
        ['inventory_moves']
    ))
    move_ids = list(
        chain(*[s['inventory_moves'] for s in shipments])
    )
    outgoing_moves = list(StockMove.search_read_all(
        [('id', 'in', move_ids), ('state', 'in', ('draft', 'assigned'))],
        None,
        fields=[
            'product', 'product.code',
            'product.template.name',
            'planned_date',
            'internal_quantity',
        ]
    ))
    today = date.today()
    for move in outgoing_moves:
        move['Planned Date'] = move['planned_date'] or today
        move['Product'] = move['product.template.name']
        move['SKU'] = move['product.code']
        move['Quantity'] = move['internal_quantity']

    df = pd.DataFrame(outgoing_moves)
    pivot_table = pd.pivot_table(
        df,
        index=["Product", "SKU"],
        columns=["Planned Date"],
        values=["Quantity"],
        fill_value="",
        aggfunc="sum"
    )
    return render_template(
        'plan-by-product.html',
        pivot_table=pivot_table,
        current_year=datetime.utcnow().year,
    )
