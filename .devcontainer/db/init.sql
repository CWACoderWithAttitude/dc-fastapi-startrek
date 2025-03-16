CREATE TABLE hosts (
     id SERIAL PRIMARY KEY,
     hostname character varying(255) NOT NULL,
     ip character varying(16) NOT NULL,
     mac character varying(32) NOT NULL,
     created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
     updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
 );