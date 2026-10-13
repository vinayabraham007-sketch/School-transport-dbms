-- SQLite schema: tables, constraints, indexes, triggers, views

CREATE TABLE bus(bus_id INTEGER PRIMARY KEY, reg_no TEXT UNIQUE NOT NULL,
 capacity INTEGER NOT NULL CHECK(capacity BETWEEN 1 AND 80),
 status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN('Active','Maintenance','Retired')));
CREATE TABLE driver(driver_id INTEGER PRIMARY KEY, name TEXT NOT NULL, phone TEXT,
 licence_no TEXT UNIQUE NOT NULL, licence_expiry DATE NOT NULL);
CREATE TABLE attendant(attendant_id INTEGER PRIMARY KEY, name TEXT NOT NULL, phone TEXT);
CREATE TABLE route(route_id INTEGER PRIMARY KEY, route_name TEXT UNIQUE NOT NULL, start_point TEXT, end_point TEXT);
CREATE TABLE stop(stop_id INTEGER PRIMARY KEY, stop_name TEXT UNIQUE NOT NULL, landmark TEXT);
CREATE TABLE route_stop(route_stop_id INTEGER PRIMARY KEY,
 route_id INTEGER NOT NULL REFERENCES route ON DELETE CASCADE,
 stop_id INTEGER NOT NULL REFERENCES stop,
 stop_seq INTEGER NOT NULL CHECK(stop_seq>0), pickup_time TEXT,
 UNIQUE(route_id,stop_seq), UNIQUE(route_id,stop_id));
CREATE TABLE route_allocation(alloc_id INTEGER PRIMARY KEY, route_id INTEGER NOT NULL REFERENCES route,
 bus_id INTEGER NOT NULL REFERENCES bus, driver_id INTEGER NOT NULL REFERENCES driver,
 attendant_id INTEGER REFERENCES attendant, from_date DATE NOT NULL, to_date DATE);
CREATE TABLE student(student_id INTEGER PRIMARY KEY, name TEXT NOT NULL, class TEXT NOT NULL,
 guardian_name TEXT, guardian_phone TEXT);
CREATE TABLE fee_plan(plan_id INTEGER PRIMARY KEY, plan_name TEXT NOT NULL,
 amount REAL NOT NULL CHECK(amount>0), frequency TEXT);
CREATE TABLE transport_registration(reg_id INTEGER PRIMARY KEY,
 student_id INTEGER NOT NULL REFERENCES student, route_stop_id INTEGER NOT NULL REFERENCES route_stop,
 plan_id INTEGER NOT NULL REFERENCES fee_plan, start_date DATE NOT NULL DEFAULT CURRENT_DATE,
 status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN('Active','Cancelled')));
CREATE UNIQUE INDEX one_active_per_student ON transport_registration(student_id) WHERE status='Active';
CREATE TABLE pickup_log(log_id INTEGER PRIMARY KEY, reg_id INTEGER NOT NULL REFERENCES transport_registration ON DELETE CASCADE,
 log_date DATE NOT NULL DEFAULT CURRENT_DATE, trip_type TEXT NOT NULL CHECK(trip_type IN('Pickup','Drop')),
 status TEXT NOT NULL CHECK(status IN('Present','Absent','Late')), UNIQUE(reg_id,log_date,trip_type));
CREATE TABLE payment(payment_id INTEGER PRIMARY KEY, reg_id INTEGER NOT NULL REFERENCES transport_registration,
 pay_date DATE NOT NULL DEFAULT CURRENT_DATE, amount_paid REAL NOT NULL CHECK(amount_paid>0),
 mode TEXT NOT NULL DEFAULT 'Cash' CHECK(mode IN('Cash','UPI','Card')), receipt_no TEXT UNIQUE NOT NULL);
CREATE TABLE maintenance(maint_id INTEGER PRIMARY KEY, bus_id INTEGER NOT NULL REFERENCES bus,
 service_date DATE NOT NULL, type TEXT NOT NULL, cost REAL NOT NULL CHECK(cost>=0), next_due_date DATE,
 status TEXT NOT NULL DEFAULT 'Done' CHECK(status IN('Done','In Progress')));
CREATE INDEX idx_student_name ON student(name);
CREATE INDEX idx_pickup_date ON pickup_log(log_date);
CREATE INDEX idx_reg_stop ON transport_registration(route_stop_id);
CREATE INDEX idx_pay_reg ON payment(reg_id);

CREATE TRIGGER trg_licence BEFORE INSERT ON route_allocation BEGIN
 SELECT RAISE(ABORT,'Driver licence expired or expires before allocation start')
  WHERE (SELECT licence_expiry FROM driver WHERE driver_id=NEW.driver_id) <= NEW.from_date;
 SELECT RAISE(ABORT,'Bus is not Active') WHERE (SELECT status FROM bus WHERE bus_id=NEW.bus_id)<>'Active';
END;
CREATE TRIGGER trg_capacity BEFORE INSERT ON transport_registration WHEN NEW.status='Active' BEGIN
 SELECT RAISE(ABORT,'Bus capacity full (or no bus allocated to this route)')
  WHERE (SELECT COUNT(*) FROM transport_registration t JOIN route_stop x USING(route_stop_id)
         WHERE t.status='Active' AND x.route_id=(SELECT route_id FROM route_stop WHERE route_stop_id=NEW.route_stop_id))
     >= COALESCE((SELECT MIN(b.capacity) FROM route_allocation a JOIN bus b USING(bus_id)
         WHERE a.route_id=(SELECT route_id FROM route_stop WHERE route_stop_id=NEW.route_stop_id) AND a.to_date IS NULL),0);
END;
CREATE TRIGGER trg_payment BEFORE INSERT ON payment BEGIN
 SELECT RAISE(ABORT,'Payment exceeds fee due')
  WHERE NEW.amount_paid + COALESCE((SELECT SUM(amount_paid) FROM payment WHERE reg_id=NEW.reg_id),0)
      > (SELECT fp.amount FROM fee_plan fp JOIN transport_registration t USING(plan_id) WHERE t.reg_id=NEW.reg_id);
END;
CREATE VIEW v_capacity AS
 SELECT r.route_name, b.reg_no bus, b.capacity, COUNT(tr.reg_id) used,
  b.capacity-COUNT(tr.reg_id) free_seats, ROUND(100.0*COUNT(tr.reg_id)/b.capacity,1) util_pct
 FROM route r JOIN route_allocation a ON a.route_id=r.route_id AND a.to_date IS NULL
 JOIN bus b ON b.bus_id=a.bus_id LEFT JOIN route_stop rs ON rs.route_id=r.route_id
 LEFT JOIN transport_registration tr ON tr.route_stop_id=rs.route_stop_id AND tr.status='Active'
 GROUP BY r.route_id;
CREATE VIEW v_dues AS
 SELECT s.name student, s.guardian_phone, fp.amount fee, COALESCE(SUM(p.amount_paid),0) paid,
  fp.amount-COALESCE(SUM(p.amount_paid),0) due
 FROM transport_registration tr JOIN student s USING(student_id) JOIN fee_plan fp USING(plan_id)
 LEFT JOIN payment p ON p.reg_id=tr.reg_id WHERE tr.status='Active' GROUP BY tr.reg_id;
