"""These are the models for the wordseer website.
"""

from sqlalchemy.ext.declarative import declared_attr

from app import db
from app.models import Base
from app.models import User

#TODO: these might all be many-to-many, futher research required

class Set(object):
    """This is the basic Set class.

    Sets are made of either Sequences (a.k.a Phrases), Sentences and Documents.
    A Set model has an association with a User and has some properties like a
    name and a creation date.

    Kwargs:
        user_id (int): The ID of the user that owns this Set
        name (str): The name of this Set
        creation_date (str): A date.DateTime object of when this Set was created
    """

    @declared_attr
    def user_id(cls):
        return cls.__table__.c.get(db.Integer, db.ForeignKey("user.id"))

    name = db.Column(db.String)
    creation_date = db.Column(db.Date)

class SequenceSet(db.Model, Base, Set):
    """SequenceSet is a Set that can have a list of Sequences in it.

    Keyword Args:
        sequences (list?): A list of Sequences (by ID) in this SequenceSet
    """

    #sequences = db.relationship("Sequence") TODO: relationship
    pass

class SentenceSet(db.Model, Base, Set):
    """A Set that can have a list of Sentences in it.

    Keyword Args:
        sentences (list?): A list of Sentences (by ID) in this SentenceSet
    """

    sentences = db.relationship("Sentence", backref="set")

class DocumentSet(db.Model, Base, Set):
    """A Set that can have a list of Documents in it.

    Keyword Args:
        document (list?): A list of Documents (by ID) in this DocumentSet
    """

    documents = db.relationship("Unit", backref="set")

class CachedSentences(db.Model, Base):
    """Cached list of sentences for a query.

    When a User does a query we pre-compute the set of sentences that matches
    this query so that the 5 default views (of the JavaScript frontend) don't
    all have to compute it separately.

    This model stores the relevant query ID and a list of Sentences. The
    query ID of a given entry is its ID.

    Keyword Args:
        sentences (list?): A list of Sentences connected with this query.
    """

    #sentences = db.relationship("Sentence")
    pass
