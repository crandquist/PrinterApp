from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app import db
from app.main import bp
from app.main.forms import AddCartridge, RegisterPrinter, EditPrinter, EditCartridge, Delete
from app.models import User, Printer, Cartridge, Event


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.activity_feed'))
    return render_template('index.html')


@bp.route('/activity_feed', methods=['GET', 'POST'])
@login_required
def activity_feed():
    events = Event.query.filter(
        Event.user_id == current_user.id).order_by(
            Event.creation_timestamp.desc())
    return render_template('activity_feed.html', events=events)


@bp.route('/add_printer', methods=['GET', 'POST'])
@login_required
def add_printer():
    form = RegisterPrinter()
    if form.validate_on_submit():
        printer = Printer(name=form.name.data,
                          brand=form.brand.data,
                          model=form.model.data,
                          num_cartridges=form.num_cartridges.data,
                          vendor=form.vendor.data,
                          product_url=form.product_url.data,
                          user=current_user)
        db.session.add(printer)
        db.session.commit()
        event = Event(event_type='create printer',
                      object_type='Printer',
                      printer_id=printer.id,
                      printer_name=printer.name,
                      user=current_user)
        db.session.add(event)
        db.session.commit()
        flash('New printer added successfully.')
        return redirect(url_for('main.index'))
    return render_template('add_printer.html', title='Add Printer', form=form)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@bp.route('/printer/<printer_id>')
@login_required
def printer(printer_id):
    printer = Printer.query.filter_by(id=printer_id).first_or_404()
    return render_template('printer.html', printer=printer)


@bp.route('/printer/<printer_id>/add_cartridge', methods=["GET", "POST"])
@login_required
def add_cartridge(printer_id):
    printer = Printer.query.filter_by(id=printer_id).first_or_404()
    if current_user != printer.user:
        flash('You cannot add a cartridge to a printer you do not own.')
        return redirect(url_for('main.printer', printer_id=printer_id))
    form = AddCartridge()
    if form.validate_on_submit():
        cartridge = Cartridge(color=form.color.data,
                              brand=form.brand.data,
                              model=form.model.data,
                              vendor=form.vendor .data,
                              product_url=form.product_url.data,
                              quantity=form.quantity.data,
                              printer_id=printer_id)
        db.session.add(cartridge)
        db.session.commit()
        event = Event(event_type='create cartridge',
                      object_type='cartridge',
                      cartridge_id=cartridge.id,
                      cartridge_color=cartridge.color,
                      user=current_user,
                      printer_id=cartridge.printer_id,
                      printer_name=cartridge.printer.name)
        db.session.add(event)
        db.session.commit()
        cartridge.printer.cart_on_hand += cartridge.quantity
        db.session.commit()
        flash("New cartridge added successfully.")
        return redirect(url_for('main.printer', printer_id=printer_id))
    return render_template('add_cartridge.html', form=form)


@bp.route('/printer/<printer_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_printer(printer_id):
    form = Delete()
    printer = Printer.query.get(printer_id)
    if current_user != printer.user:
        flash('You cannot delete a printer you do not own.')
        return redirect(url_for('main.printer', printer_id=printer_id))
    if form.validate_on_submit():
        event = Event(event_type='delete printer',
                      object_type='printer',
                      printer_id=printer.id,
                      printer_name=printer.name,
                      user=current_user,)
        db.session.add(event)
        db.session.commit()
        db.session.delete(printer)
        db.session.commit()
        flash('Printer deleted successfully.')
        return redirect(url_for('main.user', username=current_user.username))
    return render_template('delete_printer.html', printer_id=printer_id, form=form)


@bp.route('/printer/<printer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_printer(printer_id):
    printer = Printer.query.get(printer_id)
    form = EditPrinter(obj=printer)
    if current_user != printer.user:
        flash('You cannot edit a printer you do not own.')
        return redirect(url_for('main.printer', printer_id=printer_id))
    if form.validate_on_submit():
        printer.name = form.name.data
        printer.brand = form.brand.data
        printer.model = form.model.data
        printer.num_cartridges = form.num_cartridges.data
        printer.vendor = form.vendor.data
        printer.product_url = form.product_url.data
        db.session.commit()
        event = Event(event_type='edit printer',
                      object_type='printer',
                      user=current_user,
                      printer_id=printer_id,
                      printer_name=printer.name)
        db.session.add(event)
        db.session.commit()
        flash("{} was successfully edited.".format(printer.name))
        return redirect(url_for('main.user', username=current_user.username))
    return render_template('edit_printer.html',
                           title='Edit Printer',
                           form=form)


@bp.route('/printer/<printer_id>/cartridge/<cartridge_id>/delete',
          methods=['GET', 'POST'])
@login_required
def delete_cartridge(printer_id, cartridge_id):
    form = Delete()
    cartridge = Cartridge.query.get(cartridge_id)
    printer = Printer.query.get(cartridge.printer_id)
    if current_user != cartridge.printer.user:
        flash('You cannot delete a cartridge you do not own.')
        return redirect(url_for('main.printer', printer_id=printer_id))
    if form.validate_on_submit():
        event = Event(event_type='delete cartridge',
                      object_type='cartridge',
                      cartridge_id=cartridge.id,
                      cartridge_color=cartridge.color,
                      printer_id=cartridge.printer_id,
                      printer_name=cartridge.printer.name,
                      user=current_user,)
        db.session.add(event)
        db.session.commit()
        db.session.delete(cartridge)
        db.session.commit()
        flash('Cartridge deleted successfully.')
        return redirect(url_for('main.printer', printer_id=cartridge.printer_id))
    return render_template('delete_cartridge.html', printer_id=printer_id, form=form)


@bp.route('/printer/<printer_id>/cartridge/<cartridge_id>/edit',
          methods=['GET', 'POST'])
@login_required
def edit_cartridge(printer_id, cartridge_id):
    cartridge = Cartridge.query.get(cartridge_id)
    form = EditCartridge(obj=cartridge)
    printer = Printer.query.get(cartridge.printer_id)
    if current_user != cartridge.printer.user:
        flash('You cannot edit a cartridge you do not own.')
        return redirect(url_for('main.printer', printer_id=printer_id))
    if form.validate_on_submit():
        cartridge.color = form.color.data
        cartridge.brand = form.brand.data
        cartridge.model = form.model.data
        cartridge.vendor = form.vendor.data
        cartridge.product_url = form.product_url.data
        cartridge.quantity = form.quantity.data
        db.session.commit()
        event = Event(event_type='edit cartridge',
                      object_type='cartridge',
                      cartridge_id=cartridge.id,
                      cartridge_color=cartridge.color,
                      user=current_user,
                      printer_id=cartridge.printer_id,
                      printer_name=cartridge.printer.name)
        db.session.add(event)
        db.session.commit()
        flash("{} was successfully edited.".format(cartridge.color))
        return redirect(url_for('main.printer', printer_id=printer_id))
    return render_template('edit_cartridge.html',
                           title='Edit Cartridge',
                           form=form)
