from flask import Flask,jsonify,request
from flask_sqlalchemy import SQLAlchemy
import requests,os,json

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.String(80))
    name = db.Column(db.String(80))
    referralId = db.Column(db.String(80))
    verified = db.Column(db.String(80))
    hasPerk = db.Column(db.String(80))
    location = db.relationship('Location', backref='venue')
    categories = db.relationship('Categories', backref='venue')
    stats = db.relationship('Stats', backref='venue')
    beenHere = db.relationship('BeenHere', backref='venue')
    hereNow = db.relationship('HereNow', backref='venue')


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
    address = db.Column(db.String(80))
    crossStreet = db.Column(db.String(80))
    lat = db.Column(db.Integer)
    lgn = db.Column(db.Integer)
    distance = db.Column(db.Integer)
    postalCode = db.Column(db.String(80))
    cc = db.Column(db.String(80))
    state = db.Column(db.String(80))
    country = db.Column(db.String(80))

    def setPC(self,deger):
        self.postalCode = deger

class Categories(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    category_id = db.Column(db.String(80))
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
    name = db.Column(db.String(80))
    pluralName = db.Column(db.String(80))
    shortName = db.Column(db.String(80))
    primary = db.Column(db.String(80))

class Stats(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
    tipCount = db.Column(db.Integer)
    usersCount = db.Column(db.Integer)
    checkinsCount = db.Column(db.Integer)
    visitsCount = db.Column(db.Integer)

class BeenHere(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
    count = db.Column(db.Integer)
    lastCheckinExpiredAt = db.Column(db.Integer)
    marked = db.Column(db.Integer)
    unconfirmedCount = db.Column(db.Integer)

class HereNow(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
    count = db.Column(db.Integer)
    summary = db.Column(db.String(80))


@app.route("/return/<whatiwrote>")
def hello(whatiwrote):
    return jsonify({'parameter' : whatiwrote})

@app.route("/currency/<parameter>")
def trying(parameter):
    response = requests.get('https://api.exchangeratesapi.io/latest?base=' + str(parameter.upper()))
    return jsonify(response.json())

@app.route('/foursquare')
def foursquare():
    latitude = request.args.get('latitude', None)
    longitude = request.args.get('longitude', None)
    return searchAndStoreOnFoursquare(latitude,longitude)

@app.route('/youlooked')
def youlooked():
    return  jsonify({"venues" : getVenuiesName()})

def searchAndStoreOnFoursquare(latitude,longitude):
    try:
        url = 'https://api.foursquare.com/v2/venues/search'

        params = dict(
            client_id='TZAL3OPXILKGCF2P12HPDB4C3O5OWMWBRI4UWAG4GFEKHQT4',
            client_secret='2PAMPPSLWDUAXWYKDP3YLALE0CMO4Q4HCNPHFJCJITOKXZQ5',
            v='20170801',
            ll=str(latitude) + "," + str(longitude),
            intent='checkin',
            limit=1
        )
        resp = requests.get(url=url, params=params)
        data = json.loads(resp.text)

        store(data)

        return  json.dumps(data, indent=4)

    except:
        return jsonify({"Dont be": "a bad boy."})


def store(data):
    ourPlace = data['response']['venues'][0]

    if (ourPlace['name'] in getVenuiesName()):
        pass

    else:
        location = data['response']['venues'][0]['location']
        category = data['response']['venues'][0]['categories'][0]
        stats = data['response']['venues'][0]['stats']
        bhere = data['response']['venues'][0]['beenHere']
        hereNow = data['response']['venues'][0]['hereNow']

        ourVenue = Venue(venue_id=ourPlace['id'], name=ourPlace['name'],
                         referralId=ourPlace['referralId'], verified=str(ourPlace['verified']),
                         hasPerk=str(ourPlace['hasPerk']))

        den = Location(lat=location["lat"], lgn=location["lng"], distance=location["distance"],
                         cc=location["cc"], state=location["state"],
                       country=location["country"], venue=ourVenue)

        #--- OLUP OLMAYABİLEN DEĞİŞKENLER ---
        try:
            den.postalCode = location["postalCode"]
        except:
            den.postalCode = "-"

        try:
            den.address = location["address"]
        except:
            den.address = "-"

        try:
            den.crossStreet = location["crossStreet"]
        except:
            den.crossStreet = "-"

        category = Categories(category_id = category["id"], name = category["name"],
                              pluralName = category["pluralName"],
                              shortName = category["shortName"],
                              primary = str(category["primary"]),venue = ourVenue)

        stats = Stats(venue = ourVenue, tipCount = stats["tipCount"], usersCount = stats["usersCount"],
                      checkinsCount = stats["checkinsCount"], visitsCount = stats["visitsCount"])

        beenHere = BeenHere(venue = ourVenue, count = bhere["count"], lastCheckinExpiredAt = bhere["lastCheckinExpiredAt"],
                            marked = bhere["marked"], unconfirmedCount = bhere["unconfirmedCount"])

        herenow = HereNow(venue = ourVenue, count = hereNow["count"], summary = hereNow["summary"])

        db.session.add(ourVenue)
        db.session.commit()

def getVenuiesName():
    names = []
    for item in Venue.query.all():
        names.append(item.name)

    return names

if __name__ == '__main__':
    app.run(debug=True)