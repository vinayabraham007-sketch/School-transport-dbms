-- Route list
SELECT r.route_name, rs.stop_seq, s.stop_name, rs.pickup_time FROM route_stop rs JOIN route r USING(route_id) JOIN stop s USING(stop_id) ORDER BY r.route_name, rs.stop_seq;

-- Capacity utilization
SELECT * FROM v_capacity;

-- Absent students today
SELECT s.name, s.class, r.route_name, st.stop_name, s.guardian_phone FROM pickup_log pl JOIN transport_registration tr USING(reg_id) JOIN student s USING(student_id) JOIN route_stop rs USING(route_stop_id) JOIN route r USING(route_id) JOIN stop st USING(stop_id) WHERE pl.status='Absent' AND pl.log_date=date('now');

-- Fee dues
SELECT * FROM v_dues WHERE due>0 ORDER BY due DESC;

-- Students with no payment (nested)
SELECT name, class FROM student WHERE student_id IN (SELECT student_id FROM transport_registration WHERE status='Active' AND reg_id NOT IN (SELECT reg_id FROM payment));

-- Driver assignments
SELECT d.name driver, d.licence_expiry, b.reg_no bus, r.route_name, a.from_date, a.to_date FROM route_allocation a JOIN driver d USING(driver_id) JOIN bus b USING(bus_id) JOIN route r USING(route_id);

-- Maintenance status
SELECT b.reg_no, b.status, MAX(m.service_date) last_service, MAX(m.next_due_date) next_due, SUM(m.cost) total_cost, CASE WHEN MAX(m.next_due_date)<date('now') THEN 'OVERDUE' ELSE 'OK' END flag FROM bus b LEFT JOIN maintenance m USING(bus_id) GROUP BY b.bus_id;
