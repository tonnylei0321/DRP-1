-- 债务融资域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO loan (id, entity_id, bank_code, principal, interest_rate, start_date, end_date, status) VALUES
('912f3138-308a-4828-b91d-8d2568c47f3d', 'test_sub_north_a', 'ABC', '408534924.67', '0.0431', '2023-05-31', '2026-03-26', 'active'),
('55e1135d-c5b5-4454-ae8a-970ba0ed520d', 'test_sub_east_b', 'SPDB', '187606782.35', '0.0316', '2023-01-28', '2024-09-23', 'active'),
('1abd549f-1950-408c-92cd-04bc3e8b03bf', 'test_sub_east_b', 'CMB', '465482126.47', '0.0367', '2023-03-25', '2024-10-08', 'active'),
('346e2865-bb46-4697-b93b-5956d2e1491c', 'test_sub_north_a', 'ICBC', '144152819.26', '0.0344', '2023-12-10', '2026-08-26', 'active'),
('070f8d2b-aa27-4fd6-b219-7241c4a222a4', 'test_sub_east_b', 'CEB', '308058780.32', '0.0512', '2023-05-23', '2026-01-04', 'active'),
('11fb1b72-a3b9-427b-a533-266f4bc3ad91', 'test_sub_east_a', 'CCB', '274853318.48', '0.0365', '2023-01-20', '2024-04-06', 'active'),
('11bb54fb-4abf-4813-80ba-611f599fb81b', 'test_sub_north_a', 'BOCOM', '119582473.09', '0.0333', '2024-06-24', '2026-02-27', 'active'),
('b8b28776-f14e-414e-8976-416403dff825', 'test_sub_east_a', 'CEB', '32340768.35', '0.0426', '2023-02-18', '2024-04-17', 'active'),
('3206eae0-e99f-4d44-9604-588724daaf70', 'test_sub_east_b', 'ABC', '359553619.57', '0.0455', '2023-01-17', '2025-04-23', 'active'),
('1c60dcdb-295d-4b2c-9d25-2632824e997f', 'test_sub_east_b', 'CITIC', '94469641.99', '0.0724', '2024-03-15', '2024-09-12', 'active');

INSERT INTO bond (id, entity_id, bond_code, face_value, coupon_rate, maturity_date, status) VALUES
('c3524722-d117-4f81-8840-b2073aa58245', 'test_sub_north_a', 'BD189772', '528249712.10', '0.0408', '2027-12-14', 'active'),
('983c4a25-196f-4f89-b711-ddc017399bdc', 'test_sub_north_a', 'BD631971', '788548212.49', '0.0452', '2025-02-11', 'active'),
('9b696e9f-ca91-465e-a55b-e16823e53bf7', 'test_sub_east_b', 'BD592972', '53099080.92', '0.0416', '2027-02-04', 'active'),
('7bcec8f7-58e0-441e-bd4a-c6daa82976de', 'test_sub_east_b', 'BD883618', '26079808.80', '0.0537', '2026-12-08', 'active'),
('85100bba-611d-446b-9fb3-4717283a1672', 'test_sub_east_a', 'BD868544', '660533356.01', '0.0331', '2028-04-06', 'active');

INSERT INTO finance_lease (id, entity_id, lessor, lease_amount, monthly_payment, start_date, end_date) VALUES
('9d1ae5f8-366f-4795-99d2-979209ceb93a', 'test_sub_north_a', '招银租赁', '13645459.22', '649783.77', '2023-12-07', '2025-09-05'),
('e2d0b98b-c861-419d-b3d9-164df10b5882', 'test_sub_east_b', '交银租赁', '95601465.45', '1648301.13', '2023-06-29', '2028-04-30'),
('a771bd8c-93cf-4d14-9613-1f3a8018b90a', 'test_sub_north_a', '交银租赁', '17304604.72', '824028.80', '2023-07-06', '2025-04-07'),
('52794b39-e60e-401b-bfa4-05e2b17b5ba8', 'test_sub_east_a', '中银租赁', '13542223.75', '541688.95', '2023-10-28', '2025-12-13'),
('c92373d8-7930-479b-818e-9f5d8ee7c421', 'test_sub_east_a', '招银租赁', '105499799.90', '3196963.63', '2023-11-20', '2026-08-16');

