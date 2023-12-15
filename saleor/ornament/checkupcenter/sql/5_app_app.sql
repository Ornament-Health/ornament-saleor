insert into app_app (private_metadata, metadata, "name", created_at, is_active, "type", is_installed, "uuid") values
('{}', '{}', 'DATA_API', now(), true, 'local', true, 'd371f481-c915-4930-b12d-1a68b4dea813'),
('{}', '{}', 'SEARCH_API', now(), true, 'local', true, '50c06ba0-47c8-4ec4-ad7d-00eab483983f'),
('{}', '{}', 'FSM_API', now(), true, 'local', true, '311172e8-351e-4fd9-9392-119297d1bb0d');

insert into app_apptoken ("name", auth_token, app_id, token_last_4) values
('Default', 'pbkdf2_sha256$260000$7J1GI0Xk8i7Nc5pmQIyVLA$5uJ0Z3lswalK49aci3SzePcApEbGX8tfA0M9Wa+Xqz0=', 1, 'Oz4i'),
('Default', 'pbkdf2_sha256$260000$NTju2bPqNkxIdkuqyV3MyC$8kbxlF6yUyTBGFTWJCGHUz8AC/wUkF+4P7FvHV7jGl0=', 2, 'AoWz'),
('Default', 'pbkdf2_sha256$260000$V96jekyUFaPYF9lvL5sP2G$/osNrPE+NgUNbAkYQOeloVlyXFuysC1qheu9xX8BhqE=', 3, 'htNJ');

insert into app_app_permissions (app_id, permission_id) values
(1, 537),
(2, 131),
(3, 537);