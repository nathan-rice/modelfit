import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


connection_string = "postgresql://ctools_pre:once848_soon@treehug.its.unc.edu/ctools_pre"
engine = sa.create_engine(connection_string)
Base = declarative_base(bind=engine)
Session = sessionmaker(engine)


class Road(Base):
    __tablename__ = "roads"
    id = sa.Column("gid", sa.Integer, primary_key=True)
    from_x = sa.Column(sa.Numeric(asdecimal=False))
    from_y = sa.Column(sa.Numeric(asdecimal=False))
    to_x = sa.Column(sa.Numeric(asdecimal=False))
    to_y = sa.Column(sa.Numeric(asdecimal=False))
    sf_id = sa.Column(sa.Numeric(asdecimal=False))
    stfips = sa.Column(sa.Numeric(asdecimal=False))
    ctfips = sa.Column(sa.Numeric(asdecimal=False))
    fclass_rev = sa.Column(sa.Numeric(asdecimal=False))
    aadt = sa.Column("aadt07", sa.Numeric(asdecimal=False))
    mph = sa.Column("speed", sa.Integer)


def load_example_roads():
    session = Session()
    distinct_criteria = (Road.stfips, Road.ctfips, Road.fclass_rev, Road.aadt)
    query = session.query(Road).distinct(*distinct_criteria)
    return query.all()