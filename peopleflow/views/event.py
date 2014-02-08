#!/usr/bin/env python
# -*- coding: utf-8 -*-

import StringIO
import unicodecsv
import os
import re
from . import nav
from .. import app
from .. import lastuser
from ..models import db, Event, Participant
from ..forms import EventForm, ConfirmSignoutForm
from ..helpers import levenshtein
from pytz import utc, timezone
from datetime import datetime
from flask import request, flash, url_for, render_template, jsonify
from werkzeug import secure_filename
from baseframe.forms import render_redirect, ConfirmDeleteForm
from coaster.views import jsonp, load_model, load_models
from coaster.utils import make_name
from mechanize import ParseResponse, urlopen, urljoin

hideemail = re.compile('.{1,3}@')

@app.route('/event/new', methods=['GET', 'POST'])
@nav.init(
    parent='index',
    title="New Event"
    )
@lastuser.requires_permission('siteadmin')
def event_new():
    form = EventForm()
    if form.validate_on_submit():
        event = Event()
        form.populate_obj(event)
        db.session.add(event)
        try:
            db.session.commit()
            flash('Event added')
            return render_redirect(url_for('index'))
        except:
            flash('There was an issue in adding the event')
            pass
    return render_template('form.html', form=form, title=u"New Event", submit=u"Add", cancel_url=url_for('index'))

@app.route('/event/<event>/sync', methods=['GET'])
@lastuser.requires_permission('siteadmin')
@load_model(Event, {'id': 'event'}, 'event')
def sync_event(event):
    if app.config['DOATTEND_EMAIL'] in [None, ''] or app.config['DOATTEND_PASS'] in [None, ''] or event.doattend_id in [None, '']:
        return 'Data not available'
    uri = 'http://doattend.com/'
    forms = ParseResponse(urlopen(urljoin(uri, 'accounts/sign_in')))
    form = forms[0]
    form['account[email]'] = app.config['DOATTEND_EMAIL']
    form['account[password]'] = app.config['DOATTEND_PASS']
    urlopen(form.click())
    csv_data = urlopen(urljoin(uri, 'events/' + event.doattend_id + '/orders/registration_sheet.csv')).read()
    guests_csv = urlopen(urljoin(uri, 'events/' + event.doattend_id + '/orders/confirmed_guests.csv')).read()
    urlopen(urljoin(uri, 'accounts/sign_out'))
    f = StringIO.StringIO(csv_data)
    headers = [make_name(field).replace(u'-', u'').replace(u'\n', u'') for field in f.next().split(',')]
    users = unicodecsv.reader(f, delimiter=',')
    def indexof(name):
        try:
            return headers.index(name)
        except ValueError:
            return None
    columns = dict(
        ticket_number=indexof(u'ticketnumber'),
        name=indexof(u'name'),
        email=indexof(u'email'),
        company=indexof(u'company'),
        job=indexof(u'jobtitle'),
        city=indexof(u'city'),
        phone=indexof(u'phone'),
        twitter=indexof(u'twitterhandle'),
        regdate=indexof(u'date'),
        order_id=indexof(u'orderid')
        )
    others = dict(
        ticket_type=indexof(u'ticketname'),
        addons=indexof(u'addonspurchased')
        )
    added = 0
    failed = []
    updated = 0
    deleted = 0
    ret = "Starting Participants<br>\n"
    tickets = []
    for user in users:
        append_purchases = False
        participant = None
        ticket_update = False
        ticket = Participant.query.filter_by(ticket_number=user[columns['ticket_number']].strip(), event_id=event.id, online_reg=True).first()
        if ticket is not None:
            ticket_update = True
            participant = ticket
        else:
            participants = Participant.query.filter_by(email=user[columns['email']].strip(), event_id=event.id).all()
            for p in participants:
                if levenshtein(p.name, user[columns['name']].strip()) <= 3:
                    participant = p
                    append_purchases = True
        new = False
        if participant is None:
            new = True
        if new:
            participant = Participant()
            participant.event_id = event.id
            participant.purchases = []
        if new or ticket_update:
            for field in columns.keys():
                setattr(participant, field, user[columns[field]].strip())
            if participant.twitter == "":
                participant.twitter = None
            else:
                participant.twitter = participant.twitter.replace('@', '').strip()
            participant.phone = participant.phone.strip().replace(' ', '').replace('-','')
        if not new or ticket_update:
            if participant.purchases is None or append_purchases == False:
                participant.purchases = []
            else:
                participant.purchases = participant.purchases.split(',')
        if user[others['ticket_type']]:
            participant.purchases.append(user[others['ticket_type']].strip())
        if user[others['addons']]:
            participant.purchases = participant.purchases + (user[others['addons']]).strip().split(',')
        for purchase in participant.purchases:
            purchase = purchase.strip()
        if u"T-shirt" in participant.purchases or u"Corporate" in participant.purchases:
            participant.purchased_tee = True
        participant.purchases = ','.join(list(set(participant.purchases)))
        participant.online_reg = True
        if participant.ticket_number is not None:
            tickets.append(participant.ticket_number)
        try:
            if new:
                db.session.add(participant)
            db.session.commit()
            if new:
                added = added + 1
                ret = ret + "Added " + participant.name.encode('utf-8') + "\n"
            else:
                updated = updated + 1
                ret = ret +  "Updated " + participant.name.encode('utf-8') + "\n"
        except Exception as e:
            ret = ret +  "Error adding " + participant.name.encode('utf-8') + ':' + str(e)
            failed.append(participant.name + ',' + participant.email + "\n")
            db.session.rollback()
    ret = ret + "Done with Participants<br>\n"
    ret = ret + "Starting Guests<br>\n"
    f = StringIO.StringIO(guests_csv)
    headers = [make_name(field).replace(u'-', u'').replace(u'\n', u'') for field in f.next().split(',')]
    users = unicodecsv.reader(f, delimiter=',')
    columns = dict(
        ticket_number=indexof(u'ticketnumber'),
        name=indexof(u'name'),
        email=indexof(u'email'),
        company=indexof(u'company'),
        job=indexof(u'jobtitle'),
        city=indexof(u'city'),
        phone=indexof(u'phone'),
        twitter=indexof(u'twitterhandle'),
        regdate=indexof(u'confirmedon')
        )
    others = dict(
        ticket_type=indexof(u'ticket')
        )
    for user in users:
        append_purchases = False
        participant = None
        ticket_update = False
        ticket = Participant.query.filter_by(ticket_number=user[columns['ticket_number']].strip(), event_id=event.id, online_reg=True).first()
        if ticket is not None:
            ticket_update = True
            participant = ticket
        else:
            participants = Participant.query.filter_by(email=user[columns['email']].strip(), event_id=event.id).all()
            for p in participants:
                if levenshtein(p.name, user[columns['name']].strip()) <= 3:
                    participant = p
                    append_purchases = True
        new = False
        if participant is None:
            new = True
        if new:
            participant = Participant()
            participant.event_id = event.id
            participant.purchases = []
        if new or ticket_update:
            for field in columns.keys():
                setattr(participant, field, user[columns[field]].strip())
            if participant.twitter == "":
                participant.twitter = None
            else:
                participant.twitter = participant.twitter.replace('@', '').strip()
            participant.phone = participant.phone.strip().replace(' ', '').replace('-','')
        if not new or ticket_update:
            if participant.purchases is None or append_purchases == False:
                participant.purchases = []
            else:
                participant.purchases = participant.purchases.split(',')
        if user[others['ticket_type']]:
            participant.purchases.append(user[others['ticket_type']].strip())
        for purchase in participant.purchases:
            purchase = purchase.strip()
        if u"T-shirt" in participant.purchases:
            participant.purchased_tee = True
        participant.purchases = ','.join(list(set(participant.purchases)))
        participant.online_reg = True
        if participant.ticket_number is not None:
            tickets.append(participant.ticket_number)
        try:
            if new:
                db.session.add(participant)
            db.session.commit()
            if new:
                added = added + 1
                ret = ret + "Added " + str(participant) + "\n"
            else:
                updated = updated + 1
                ret = ret +  "Updated " + str(participant) + "\n"
        except Exception as e:
            ret = ret +  "Error adding " + str(participant) + ':' + e
            failed.append(participant.name + ',' + participant.email) + "\n"
            db.session.rollback()
    ret = ret + "Done with Guests<br>\n"
    ret = ret + "Removing deleted tickets<br>\n"
    participants = Participant.query.filter(~Participant.ticket_number.in_(tickets), Participant.online_reg==True, Participant.event_id==event.id).all()
    for participant in participants:
        try:
            db.session.delete(participant)
            db.session.commit()
            deleted = deleted + 1
            ret = ret +  "Deleted " + str(participant) + "\n"
        except Exception as e:
            ret = ret +  "Error deleting  " + str(participant) + ':' + e
    ret = ret + "Deleting complete<br>\n"

    return '<pre>' + ret + "Added " + str(added) + ", Updated " + str(updated) + ", Failed " + str(failed) + " & Deleted " + str(deleted) + '</pre>'

@app.route('/event/<event>', methods=['GET'])
@lastuser.requires_permission('registrations')
@load_model(Event, {'id': 'event'}, 'event')
@nav.init(
    parent='index',
    title=lambda objects: objects['event'].name,
    objects=['event'],
    urlvars=lambda objects: {'event': objects['event'].id}
    )
def event(event):
    tz = timezone(app.config['TIMEZONE'])
    participants = Participant.query.filter_by(event_id=event.id).order_by('name').all()
    return render_template('participants.html', participants=participants, event=event, hideemail=hideemail, enumerate=enumerate,
        utc=utc, tz=tz)


@app.route('/event/<event>/participant/<participant>/signin', methods=['POST'])
@lastuser.requires_permission('registrations')
@load_models(
    (Event, {'id': 'event'}, 'event'),
    (Participant, {'id': 'participant'}, 'participant')
    )
def event_signin(event, participant):
    if participant.nfc_id is not None:
        return jsonify(status=False, message=u"This participant has already been assigned a badge.")
    else:
        nfc_id = unicode(request.form['nfc_id'])
        someone = Participant.query.filter_by(nfc_id=nfc_id, event_id=event.id).first()
        if someone:
            return jsonify(status=False, message=u"This badge is already assigned to %s" % someone.name)
        else:
            participant.nfc_id = nfc_id
            participant.attended = True
            participant.attend_date = datetime.utcnow()
            try:
                db.session.commit()
                return jsonify(status=True, message=u"The badge has been successfully assigned to %s" % participant.name)
            except:
                db.session.rollback()
                return jsonify(status=False, message=u"There was an error assigning this badge to %s" % participant.name)


@app.route('/event/<event>/participant/<participant>/status', methods=['GET'])
@load_models(
    (Event, {'id':'event'}, 'event'),
    (Participant, {'id':'participant'}, 'participant')
    )
@lastuser.requires_permission('registrations')
def participation_status(event, participant):
    return jsonify(attended=participant.attended, nfc_id=participant.nfc_id)


@app.route('/event/<event>/participant/<participant>/signout', methods=['POST'])
@load_models(
    (Event, {'id':'event'}, 'event'),
    (Participant, {'id':'participant'}, 'participant')
    )
@lastuser.requires_permission('registrations')
def event_signout(event, participant):
    participant.attended = False
    participant.nfc_id = None
    participant.attend_date = None
    db.session.commit()
    return jsonify(status=True)

@app.route('/event/<id>/count', methods=['GET', 'POST'])
@load_model(Event, {'id': 'id'}, 'event')
def get_count(event):
    response = jsonp(signed=event.participants.filter_by(attended=True).count(), total=event.participants.count())
    return response


@app.route('/event/<id>/edit', methods=['GET','POST'])
@lastuser.requires_permission('siteadmin')
@load_model(Event, {'id': 'id'}, 'event')
@nav.init(
    parent='event',
    title="Edit",
    objects=['event'],
    urlvars=lambda objects: {'id': objects['event'].id}
    )
def event_edit(event):
    form = EventForm(obj=event)
    if form.validate_on_submit():
        form.populate_obj(event)
        try:
            db.session.commit()
            flash("Edited event '%s'." % event.title, 'success')
            return render_redirect(url_for('index'), code=303)
        except:
            flash("Could not save event '%s'." % event.title, 'error')
    return render_template('form.html', form=form, title=u"Edit — " + event.title, submit=u"Save", cancel_url=url_for('index'))


@app.route('/event/<id>/delete', methods=['GET','POST'])
@lastuser.requires_permission('siteadmin')
@load_model(Event, {'id':'id'}, 'event')
@nav.init(
    parent='event',
    title="Confirm Delete",
    objects=['event'],
    urlvars=lambda objects: {'id': objects['event'].id}
    )
def event_delete(event):
    form = ConfirmDeleteForm()
    if form.validate_on_submit():
        if 'delete' in request.form:
            db.session.delete(event)
            db.session.commit()
        return render_redirect(url_for('index'), code=303)
    return render_template('baseframe/delete.html', form=form, title=u"Delete '%s' ?" % (event.title),
        message=u"Do you really want to delete the event '%s'?" % (event.title))

