CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE bronze.passenger_satisfaction_test (
    raw_id INTEGER,
    id INTEGER PRIMARY KEY,
    gender VARCHAR(10) CHECK (gender IN ('Female', 'Male')),
    customer_type VARCHAR(30) CHECK (customer_type IN ('Loyal Customer', 'disloyal Customer', 'Loyal customer', 'disloyal customer')),
    age SMALLINT CHECK (age >= 0 AND age <= 120),
    type_of_travel VARCHAR(30) CHECK (type_of_travel IN ('Personal Travel', 'Business travel', 'Business Travel')),
    class VARCHAR(15) CHECK (class IN ('Business', 'Eco', 'Eco Plus')),
    flight_distance INTEGER CHECK (flight_distance >= 0),
    inflight_wifi_service SMALLINT,
    departure_arrival_time_convenient SMALLINT,
    ease_of_online_booking SMALLINT,
    gate_location SMALLINT,
    food_and_drink SMALLINT,
    online_boarding SMALLINT,
    seat_comfort SMALLINT,
    inflight_entertainment SMALLINT,
    on_board_service SMALLINT,
    leg_room_service SMALLINT,
    baggage_handling SMALLINT,
    checkin_service SMALLINT,
    inflight_service SMALLINT,
    cleanliness SMALLINT,
    departure_delay_in_minutes INTEGER,
    arrival_delay_in_minutes NUMERIC(6, 1),
    satisfaction VARCHAR(30)
);

COPY bronze.passenger_satisfaction_test (
    raw_id, id , gender, customer_type, age, type_of_travel, class,
    flight_distance, inflight_wifi_service, departure_arrival_time_convenient,
    ease_of_online_booking, gate_location, food_and_drink, online_boarding,
    seat_comfort, inflight_entertainment, on_board_service, leg_room_service,
    baggage_handling, checkin_service, inflight_service, cleanliness,
    departure_delay_in_minutes, arrival_delay_in_minutes, satisfaction
)
FROM '/datasets/test.csv'
DELIMITER ','
CSV HEADER;

CREATE TABLE bronze.passenger_satisfaction_train (
    raw_id INTEGER,
    id INTEGER PRIMARY KEY,
    gender VARCHAR(10) CHECK (gender IN ('Female', 'Male')),
    customer_type VARCHAR(30) CHECK (customer_type IN ('Loyal Customer', 'disloyal Customer', 'Loyal customer', 'disloyal customer')),
    age SMALLINT CHECK (age >= 0 AND age <= 120),
    type_of_travel VARCHAR(30) CHECK (type_of_travel IN ('Personal Travel', 'Business travel', 'Business Travel')),
    class VARCHAR(15) CHECK (class IN ('Business', 'Eco', 'Eco Plus')),
    flight_distance INTEGER CHECK (flight_distance >= 0),
    inflight_wifi_service SMALLINT,
    departure_arrival_time_convenient SMALLINT,
    ease_of_online_booking SMALLINT,
    gate_location SMALLINT,
    food_and_drink SMALLINT,
    online_boarding SMALLINT,
    seat_comfort SMALLINT,
    inflight_entertainment SMALLINT,
    on_board_service SMALLINT,
    leg_room_service SMALLINT,
    baggage_handling SMALLINT,
    checkin_service SMALLINT,
    inflight_service SMALLINT,
    cleanliness SMALLINT,
    departure_delay_in_minutes INTEGER,
    arrival_delay_in_minutes NUMERIC(6, 1),
    satisfaction VARCHAR(30)
);

COPY bronze.passenger_satisfaction_train (
    raw_id, id, gender, customer_type, age, type_of_travel, class,
    flight_distance, inflight_wifi_service, departure_arrival_time_convenient,
    ease_of_online_booking, gate_location, food_and_drink, online_boarding,
    seat_comfort, inflight_entertainment, on_board_service, leg_room_service,
    baggage_handling, checkin_service, inflight_service, cleanliness,
    departure_delay_in_minutes, arrival_delay_in_minutes, satisfaction
)
FROM '/datasets/train.csv'
DELIMITER ','
CSV HEADER;