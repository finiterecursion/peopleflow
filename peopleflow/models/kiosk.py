
from . import db, BaseMixin
from .event import Event
from datetime import datetime

kiosk_participants = db.Table('kiosk_participants',
db.Column('kiosk_id', db.Integer, db.ForeignKey('kiosk.id')),
db.Column('participant_id', db.Integer, db.ForeignKey('participant.id')),
db.Column('share_date', db.DateTime, default=datetime.utcnow, nullable=False))

class Kiosk(db.Model, BaseMixin):

	__tablename__ = 'kiosk'
	#: Name of the Kiosk
	name = db.Column(db.Unicode(80), nullable=False)

	#: Name of the Sponsor
	company = db.Column(db.Unicode(80), nullable=True)

	#: Tagline/custom message of the Sponsor
	company_tag = db.Column(db.Unicode(150), nullable=True)

	#: Filename for Sponsor's logo
	company_logo = db.Column(db.Unicode(120), nullable=True)

	#: Tap Message - Tap your badge here to ________
	tap_msg = db.Column(db.Unicode(200), nullable=True, default=u"share your details")

	#: Event at which the kiosk is present. kiosk.event gives access.
	event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
	event = db.relationship(Event, primaryjoin=event_id == Event.id)

	#: List of participants who showed up at the Kiosk. kiosk.participants gives access to the objects.
	participants = db.relationship('Participant', secondary=kiosk_participants,
	backref=db.backref('kiosk', lazy='dynamic'))