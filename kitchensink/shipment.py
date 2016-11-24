from itertools import chain, groupby

from flask_login import login_required
from flask import Blueprint, render_template
from .extensions import fulfil

shipment = Blueprint('shipment', __name__, url_prefix="/shipment")


Shipment = fulfil.model('stock.shipment.out')
StockMove = fulfil.model('stock.move')


@shipment.route('/items-waiting')
@login_required
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


@shipment.route('/plan-by-product')
@login_required
def plan_by_product():
    """
    Show a plan by product
    """
    fields = [
        'product',
        'product.code',
        'product.variant_name',
        'product.template.name',
        'internal_quantity',
        'planned_date',
    ]
    outgoing_moves = StockMove.search_read([
        ('to_location.type', '=', 'customer'),
        ('state', 'in', ('draft', 'assigned')),
    ], None, None, [('planned_date', 'ASC')], fields)
    df = pd.DataFrame(outgoing_moves)
    pivot_table = pd.pivot_table(
        df,
        index=["product.template.name", "product.code"],
        columns=["planned_date"],
        values=["internal_quantity"],
        fill_value=0,
        aggfunc="sum"
    )
    return render_template(
        'plan-by-product.html',
        table_html=pivot_table.to_html()

    )
