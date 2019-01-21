from flask_login import login_required
from flask import Blueprint, render_template
from .extensions import fulfil


product = Blueprint('product', __name__, url_prefix="/product")


@product.route('/', methods=['GET'])
@login_required
def products():
    Product = fulfil.model('product.product')
    products = Product.search_read_all([
        ('purchasable', '=', True),
        ('salable', '=', True),
    ], [('variant_name', 'ASC')],
        ['rec_name', 'quantity_on_hand', 'quantity_available',
            'quantity_inbound', 'quantity_outbound']
    )
    return render_template(
        'products.html', products=list(products)
    )


@product.route('/<int:product_id>/next-available-date', methods=['GET'])
@login_required
def next_available_date(product_id):
    "Display the next available date and why it is that way"
    StockMove = fulfil.model('stock.move')
    Product = fulfil.model('product.product')
    IRDate = fulfil.model('ir.date')
    product, = Product.read(
        [product_id],
        ['rec_name', 'quantity_on_hand', 'quantity_available',
            'quantity_inbound', 'quantity_outbound']
    )
    next_date = Product.get_next_available_date(product_id)
    fields = [
        'product',
        'planned_date',
        'shipment',
        'shipment.rec_name',
        'state',
        'quantity',
        'from_location.type'
    ]
    today = IRDate.today()
    moves = StockMove.search_read_all([
        ('product', '=', product_id),
        ('planned_date', '>=', today),
        ('state', '=', 'draft'),
    ], [('planned_date', 'ASC')], fields)
    moves_with_errors = StockMove.search_read_all([
        ('product', '=', product_id),
        ('state', '=', 'draft'),
        [
            'OR',
            ('planned_date', '=', None),
            ('planned_date', '<', today),
            ('shipment', '=', None),
        ]
    ], [('planned_date', 'ASC')], fields)
    return render_template(
        'next-available-date.html',
        next_date=next_date,
        moves=list(moves),
        moves_with_errors=list(moves_with_errors),
        product=product,
    )
