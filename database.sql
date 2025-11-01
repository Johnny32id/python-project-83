DROP TABLE IF EXISTS urls CASCADE;
DROP TABLE IF EXISTS url_checks CASCADE;

CREATE TABLE urls (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar UNIQUE NOT NULL,
    created_at timestamp
);

CREATE TABLE url_checks (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id bigint REFERENCES urls (id),
    h1 varchar(255),
    title varchar(255),
    description varchar(255),
    status_code smallint,
    created_at timestamp
);

-- Индексы для улучшения производительности запросов
CREATE INDEX idx_url_checks_url_id ON url_checks(url_id);
CREATE INDEX idx_url_checks_created_at ON url_checks(created_at DESC);
CREATE INDEX idx_urls_created_at ON urls(created_at DESC);