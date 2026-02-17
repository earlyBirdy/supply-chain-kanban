import json
import os
from superset.app import create_app
from superset.extensions import db
from superset.models.core import Database, Dashboard, Slice
from superset.connectors.sqla.models import SqlaTable

ADMIN_USER = os.getenv("SUPERSET_ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("SUPERSET_ADMIN_PASS", "admin")
ADMIN_EMAIL = os.getenv("SUPERSET_ADMIN_EMAIL", "admin@example.com")

DEMO_DB_URI = os.getenv("DEMO_DB_URI", "postgresql+psycopg2://demo:demo@db:5432/demo")
DEMO_DB_NAME = os.getenv("DEMO_DB_NAME", "demo")

def ensure_admin(app):
    sm = app.appbuilder.sm
    user = sm.find_user(username=ADMIN_USER)
    if user:
        return
    sm.add_user(
        username=ADMIN_USER,
        first_name="Admin",
        last_name="User",
        email=ADMIN_EMAIL,
        role=sm.find_role("Admin"),
        password=ADMIN_PASS,
    )

def ensure_database():
    dbobj = db.session.query(Database).filter(Database.database_name == DEMO_DB_NAME).one_or_none()
    if dbobj:
        dbobj.sqlalchemy_uri = DEMO_DB_URI
        db.session.commit()
        return dbobj
    dbobj = Database(database_name=DEMO_DB_NAME, sqlalchemy_uri=DEMO_DB_URI)
    db.session.add(dbobj)
    db.session.commit()
    return dbobj

def ensure_dataset(database_id: int, table_name: str, schema: str | None = None):
    q = db.session.query(SqlaTable).filter(SqlaTable.table_name == table_name, SqlaTable.database_id == database_id)
    if schema:
        q = q.filter(SqlaTable.schema == schema)
    ds = q.one_or_none()
    if ds:
        return ds
    ds = SqlaTable(table_name=table_name, schema=schema, database_id=database_id)
    db.session.add(ds)
    db.session.commit()
    return ds

def ensure_table_slice(datasource_id: int, datasource_type: str, slice_name: str):
    sl = db.session.query(Slice).filter(Slice.slice_name == slice_name).one_or_none()
    if sl:
        return sl
    params = {
        "all_columns": [],
        "order_by_cols": [],
        "page_length": 10,
    }
    sl = Slice(
        slice_name=slice_name,
        viz_type="table",
        params=json.dumps(params),
        datasource_id=datasource_id,
        datasource_type=datasource_type,
    )
    db.session.add(sl)
    db.session.commit()
    return sl

def ensure_dashboard(title: str, slug: str, slice_ids: list[int]):
    d = db.session.query(Dashboard).filter(Dashboard.slug == slug).one_or_none()
    if not d:
        d = Dashboard(dashboard_title=title, slug=slug, json_metadata="{}")
        db.session.add(d)
        db.session.commit()
    # attach slices
    existing = {s.id for s in d.slices}
    for sid in slice_ids:
        if sid not in existing:
            s = db.session.get(Slice, sid)
            if s:
                d.slices.append(s)
    # minimal layout
    d.position_json = json.dumps({"DASHBOARD_VERSION_KEY": "v2", "ROOT_ID": {"type":"ROOT","children":[]}})
    db.session.commit()
    return d

def main():
    app = create_app()
    with app.app_context():
        ensure_admin(app)
        demo_db = ensure_database()

        # datasets (use canonical tables that exist in v0.6)
        ds_cases = ensure_dataset(demo_db.id, "agent_cases")
        ds_signals = ensure_dataset(demo_db.id, "market_signals")

        # slices
        sl_cases = ensure_table_slice(ds_cases.id, ds_cases.datasource_type, "Agent Cases (table)")
        sl_signals = ensure_table_slice(ds_signals.id, ds_signals.datasource_type, "Market Signals (table)")

        # dashboards
        ensure_dashboard("Board Supply Chain Risk View", "board-supply-chain-risk-view", [sl_cases.id, sl_signals.id])
        ensure_dashboard("Crisis Mode Control Room", "crisis-mode-control-room", [sl_cases.id])

        print("Bootstrap complete: admin/admin, DB connected, datasets+slices+dashboards created.", flush=True)

if __name__ == "__main__":
    main()
