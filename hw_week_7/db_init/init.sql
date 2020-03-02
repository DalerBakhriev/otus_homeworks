create user if not exists hasker_admin with password 'password';
alter role hasker_admin set client_encoding to 'utf8';
alter role hasker_admin set default_transaction_isolation to 'read committed';
alter role hasker_admin set timezone to 'UTC';

create database if not exists hasker_db owner hasker_admin;